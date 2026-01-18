#include "MecanumControl.h"

/**
 * @file MecanumControl.cpp
 * @brief Contrôle des moteurs Mecanum avec encodeurs et PID
 *
 * Ce module gère :
 *  - le pilotage des 4 moteurs via l’Adafruit Motor Shield
 *  - la lecture des encodeurs en quadrature
 *  - le mixage cinématique Mecanum (vx, vy, w)
 *  - deux modes de contrôle : manuel (open-loop) et AI (PID)
 *  - l’envoi des données encodeurs vers la Raspberry Pi
 *  - un arrêt d’urgence logiciel
 */

// ======================================================
// MOTEURS – Adafruit Motor Shield
// ======================================================
/**
 * Ordre logique Mecanum :
 *  0 = FL (avant gauche)
 *  1 = FR (avant droite)
 *  2 = RR (arrière droite)
 *  3 = RL (arrière gauche)
 *
 * Correspondance avec le câblage réel du Motor Shield :
 *  - canal 4 → FL
 *  - canal 3 → FR
 *  - canal 2 → RR
 *  - canal 1 → RL
 */
AF_DCMotor motors[4] = {
  AF_DCMotor(4),  // FL
  AF_DCMotor(3),  // FR
  AF_DCMotor(2),  // RR
  AF_DCMotor(1)   // RL
};

// ======================================================
// ENCODEURS (QUADRATURE)
// ======================================================
/**
 * Pins des encodeurs :
 *  - ENCA : front montant → interruption
 *  - ENCB : lecture du sens de rotation
 */
const uint8_t ENCA[4] = {18, 19, 20, 21};
const uint8_t ENCB[4] = {31, 33, 35, 37};

/**
 * @brief Compteurs d’encodeurs
 *
 * ticks       : position absolue
 * speedCount : incréments utilisés pour calculer la vitesse
 */
static volatile long ticks[4]      = {0, 0, 0, 0};
static volatile long speedCount[4] = {0, 0, 0, 0};

/**
 * @brief Vitesses mesurées des roues (ticks/s)
 */
static float wheelSpeed[4] = {0, 0, 0, 0};

/**
 * @brief Consignes de vitesse PID (ticks/s)
 */
static float wheelTarget[4] = {0, 0, 0, 0};

/**
 * @brief Contrôleurs PID individuels par roue
 */
static PID pid[4];

// ======================================================
// GESTION DU TEMPS
// ======================================================
/**
 * lastSpeedTime : dernière mise à jour des vitesses
 * lastPIDTime   : dernière mise à jour PID
 */
static unsigned long lastSpeedTime = 0;
static unsigned long lastPIDTime   = 0;

// ======================================================
// MODE DE CONTROLE
// ======================================================
/**
 * MODE_MANUAL : open-loop (PWM direct)
 * MODE_AI     : boucle fermée PID
 */
static ControlMode currentMode = MODE_MANUAL;

// ======================================================
// COMMANDE OMNI COURANTE
// ======================================================
/**
 * vx_cmd : vitesse avant/arrière
 * vy_cmd : vitesse latérale (strafe)
 * w_cmd  : rotation
 */
static float vx_cmd = 0.0f, vy_cmd = 0.0f, w_cmd = 0.0f;

// ======================================================
// ISR ENCODEURS (QUADRATURE)
// ======================================================
/**
 * @brief Gestion générique d’un encodeur en quadrature
 *
 * @param i Index de la roue (0 à 3)
 *
 * La direction est déterminée en lisant la voie B
 * lors du front montant de la voie A.
 */
inline void handleEncoder(uint8_t i) {
  bool b = digitalRead(ENCB[i]);
  if (b) {
    ticks[i]++;
    speedCount[i]++;
  } else {
    ticks[i]--;
    speedCount[i]--;
  }
}

// ISRs spécifiques par roue
void enc1() { handleEncoder(0); }
void enc2() { handleEncoder(1); }
void enc3() { handleEncoder(2); }
void enc4() { handleEncoder(3); }

// ======================================================
// SENS DES MOTEURS
// ======================================================
/**
 * @brief Inversion logicielle du sens moteur
 *
 * Mettre -1 si une roue tourne à l’envers.
 */
const int motorSign[4] = {
  1,   // FL
  1,   // FR
  1,   // RR
  1    // RL
};

// ======================================================
// APPLICATION PWM + SENS
// ======================================================
/**
 * @brief Applique une commande normalisée à un moteur
 *
 * @param m     Référence du moteur
 * @param cmd   Commande normalisée [-1 ; 1]
 * @param index Index de la roue
 */
static void applyMotor(AF_DCMotor &m, float cmd, int index) {
  cmd *= motorSign[index];

  int pwm = (int)(abs(cmd) * PWM_MAX);
  if (pwm > PWM_MAX) pwm = PWM_MAX;

  m.setSpeed(pwm);

  if (cmd > 0)      m.run(BACKWARD);
  else if (cmd < 0) m.run(FORWARD);
  else              m.run(RELEASE);
}

// ======================================================
// MIXAGE MECANUM – OPEN LOOP
// ======================================================
/**
 * @brief Mixage Mecanum en open-loop (mode manuel)
 *
 * @param vx Vitesse avant/arrière
 * @param vy Vitesse latérale
 * @param w  Vitesse de rotation
 */
static void mecanumOpenLoop(float vx, float vy, float w) {
  float m[4] = {
    vx - vy - w,  // FL
    vx + vy + w,  // FR
    vx - vy + w,  // RR
    vx + vy - w   // RL
  };

  // Normalisation
  float maxVal = max(max(abs(m[0]), abs(m[1])),
                     max(abs(m[2]), abs(m[3])));

  if (maxVal > 1.0f)
    for (int i = 0; i < 4; i++) m[i] /= maxVal;

  for (int i = 0; i < 4; i++)
    applyMotor(motors[i], m[i], i);
}

// ======================================================
// MIXAGE MECANUM → CIBLES PID
// ======================================================
/**
 * @brief Convertit une commande omni en consignes PID roues
 */
static void mecanumToWheelTargets(float vx, float vy, float w) {
  float m[4] = {
    vx - vy - w,
    vx + vy + w,
    vx - vy + w,
    vx + vy - w
  };

  float maxVal = max(max(abs(m[0]), abs(m[1])),
                     max(abs(m[2]), abs(m[3])));

  if (maxVal > 1.0f)
    for (int i = 0; i < 4; i++) m[i] /= maxVal;

  for (int i = 0; i < 4; i++)
    wheelTarget[i] = m[i] * MAX_WHEEL_SPEED;
}

// ======================================================
// INITIALISATION
// ======================================================
/**
 * @brief Initialise moteurs, encodeurs et PID
 */
void mecanumInit() {
  for (int i = 0; i < 4; i++) {
    pinMode(ENCA[i], INPUT_PULLUP);
    pinMode(ENCB[i], INPUT_PULLUP);
  }

  attachInterrupt(digitalPinToInterrupt(ENCA[0]), enc1, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCA[1]), enc2, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCA[2]), enc3, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCA[3]), enc4, RISING);

  for (int i = 0; i < 4; i++) {
    motors[i].run(RELEASE);
    motors[i].setSpeed(0);

    // PID stable de départ
    pid[i].init(0.005f, 0.0f, 0.0f, -1.0f, 1.0f);
  }

  lastSpeedTime = millis();
  lastPIDTime   = millis();
  currentMode   = MODE_MANUAL;
}

// ======================================================
// CHANGEMENT DE MODE
// ======================================================
/**
 * @brief Change le mode de contrôle du robot
 */
void mecanumSetMode(ControlMode mode) {
  currentMode = mode;

  vx_cmd = vy_cmd = w_cmd = 0.0f;

  for (int i = 0; i < 4; i++)
    wheelTarget[i] = 0.0f;

  if (mode == MODE_MANUAL) {
    for (int i = 0; i < 4; i++)
      motors[i].run(RELEASE);
  }
}

// ======================================================
// COMMANDE OMNI
// ======================================================
/**
 * @brief Définit une commande de déplacement omnidirectionnelle
 */
void mecanumSetCommand(float vx, float vy, float w) {
  // Protection contre une combinaison instable
  if (abs(vx) < 0.1f && abs(vy) > 0.3f && abs(w) > 0.3f) {
    w = 0.0f;
  }

  vx_cmd = vx;
  vy_cmd = vy;
  w_cmd  = w;

  if (currentMode == MODE_MANUAL)
    mecanumOpenLoop(vx, vy, w);
  else
    mecanumToWheelTargets(vx, vy, w);
}

// ======================================================
// ENCODEURS → SERIAL
// ======================================================
/**
 * @brief Met à jour les vitesses et envoie les données encodeurs
 *
 * Format série :
 * ENC ticks[4] wheelSpeed[4]
 */
void mecanumUpdateEncoders() {
  unsigned long now = millis();
  if (now - lastSpeedTime < 100) return;

  float dt = (now - lastSpeedTime) / 1000.0f;
  lastSpeedTime = now;

  for (int i = 0; i < 4; i++) {
    noInterrupts();
    long sc = speedCount[i];
    speedCount[i] = 0;
    interrupts();

    wheelSpeed[i] = sc / dt;
  }

  Serial3.print("ENC ");
  for (int i = 0; i < 4; i++) {
    Serial3.print(ticks[i]); Serial3.print(" ");
  }
  for (int i = 0; i < 4; i++) {
    Serial3.print(wheelSpeed[i]); Serial3.print(" ");
  }
  Serial3.println();
}

// ======================================================
// PID UPDATE
// ======================================================
/**
 * @brief Mise à jour PID (uniquement en MODE_AI)
 */
void mecanumUpdatePID() {
  if (currentMode != MODE_AI) return;

  unsigned long now = millis();
  if (now - lastPIDTime < PID_PERIOD) return;

  float dt = (now - lastPIDTime) / 1000.0f;
  lastPIDTime = now;

  for (int i = 0; i < 4; i++) {
    float u = pid[i].update(wheelTarget[i], wheelSpeed[i], dt);
    applyMotor(motors[i], u, i);
  }
}

// ======================================================
// ARRET D’URGENCE
// ======================================================
/**
 * @brief Arrêt immédiat de tous les moteurs
 */
void mecanumEmergencyStop() {
  vx_cmd = vy_cmd = w_cmd = 0.0f;

  for (int i = 0; i < 4; i++) {
    wheelTarget[i] = 0.0f;
    motors[i].setSpeed(0);
    motors[i].run(RELEASE);
  }
}
