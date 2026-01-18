#include "Protocol.h"
#include "MecanumControl.h"

/**
 * @file Protocol.cpp
 * @brief Gestion du protocole de communication série avec la Raspberry Pi
 *
 * Ce module gère :
 *  - la réception non bloquante des commandes via Serial3
 *  - le parsing sécurisé des messages texte
 *  - le pilotage du robot (vitesse, mode)
 *  - un watchdog de sécurité en cas de perte de communication
 */

// ======================================================
// ETAT DU PROTOCOLE
// ======================================================

/**
 * @brief Dernier instant où une commande valide a été reçue
 *
 * Utilisé par le watchdog pour détecter une perte de communication.
 */
static unsigned long lastCommandTime = 0;

// ======================================================
// OUTILS INTERNES
// ======================================================

/**
 * @brief Conversion robuste String → float
 *
 * Nettoie la chaîne d’entrée afin d’éviter :
 *  - caractères non numériques
 *  - séparateurs décimaux ',' (convertis en '.')
 *
 * @param s Chaîne à convertir
 * @return Valeur flottante convertie
 */
static float safeParseFloat(const String &s) {
  String clean = "";
  for (char c : s) {
    if ((c >= '0' && c <= '9') || c == '-' || c == '.' || c == ',')
      clean += c;
  }
  clean.replace(',', '.');
  return clean.toFloat();
}

/**
 * @brief Traite une ligne complète reçue sur Serial3
 *
 * @param line Ligne brute reçue (sans retour chariot)
 *
 * Commandes supportées :
 *  - VEL vx vy w    : commande omnidirectionnelle
 *  - MODE MANUAL   : mode open-loop
 *  - MODE AI       : mode PID
 *  - PING          : test de communication (répond PONG)
 */
static void handleLine(String &line) {
  Serial.print("[Protocol] Ligne brute: ");
  // Serial.println(line);

  // Nettoyage : conservation des caractères ASCII imprimables
  String clean = "";
  for (char c : line) {
    if (c >= 32 && c <= 126) clean += c;
  }
  clean.trim();

  Serial.print("[Protocol] Ligne nettoyée: ");
  // Serial.println(clean);

  // ====================================================
  // COMMANDE VEL
  // ====================================================
  if (clean.startsWith("VEL")) {
    // Découpage manuel pour éviter String.split()
    int p1 = clean.indexOf(' ');
    int p2 = clean.indexOf(' ', p1 + 1);
    int p3 = clean.indexOf(' ', p2 + 1);

    if (p1 < 0 || p2 < 0 || p3 < 0) {
      // Serial.println("[Protocol] ERREUR: format VEL incomplet");
      return;
    }

    float vx = safeParseFloat(clean.substring(p1, p2));
    float vy = safeParseFloat(clean.substring(p2, p3));
    float w  = safeParseFloat(clean.substring(p3));

    Serial.print("[Protocol] VEL OK -> ");
    Serial.print(vx); Serial.print(", ");
    Serial.print(vy); Serial.print(", ");
    // Serial.println(w);

    mecanumSetCommand(vx, vy, w);
    lastCommandTime = millis();
    return;
  }

  // ====================================================
  // COMMANDE MODE
  // ====================================================
  if (clean.startsWith("MODE")) {
    lastCommandTime = millis();

    if (clean.indexOf("MANUAL") > 0) {
      mecanumSetMode(MODE_MANUAL);
      Serial3.println("MODE MANUAL");
    } else if (clean.indexOf("AI") > 0) {
      mecanumSetMode(MODE_AI);
      Serial3.println("MODE AI");
    }
    return;
  }

  // ====================================================
  // COMMANDE PING
  // ====================================================
  if (clean.startsWith("PING")) {
    Serial3.println("PONG");
    lastCommandTime = millis();
    return;
  }

  // ====================================================
  // COMMANDE INCONNUE
  // ====================================================
  Serial.print("[Protocol] Commande inconnue: ");
  // Serial.println(clean);
}

// ======================================================
// API PUBLIQUE
// ======================================================

/**
 * @brief Initialise le protocole de communication
 *
 * Réinitialise le watchdog.
 */
void protocolInit() {
  lastCommandTime = millis();
  // Serial.println("[Protocol] Initialisation OK");
}

/**
 * @brief Met à jour la communication série (non bloquant)
 *
 * - Lit Serial3 caractère par caractère
 * - Reconstruit les lignes terminées par \\n ou \\r
 * - Transmet les lignes complètes au parser
 *
 * À appeler en continu dans `loop()`.
 */
void protocolUpdate() {
  static String buffer = "";

  while (Serial3.available()) {
    char c = Serial3.read();

    Serial.print("[Serial3] Reçu: ");
    // Serial.println(c);

    if (c == '\n' || c == '\r') {
      if (buffer.length() > 0) {
        handleLine(buffer);
        buffer = "";
      }
    } else {
      buffer += c;
    }
  }
}

/**
 * @brief Watchdog de sécurité
 *
 * Si aucune commande valide n’est reçue pendant
 * WATCHDOG_TIMEOUT millisecondes :
 *  - arrêt immédiat des moteurs
 */
void protocolWatchdog() {
  if (millis() - lastCommandTime > WATCHDOG_TIMEOUT) {
    // Serial.println("[Protocol] WATCHDOG: arrêt d'urgence");
    mecanumEmergencyStop();
  }
}
