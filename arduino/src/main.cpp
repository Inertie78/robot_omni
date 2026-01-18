#include <Arduino.h>
#include "RobotConfig.h"
#include "MecanumControl.h"
#include "Protocol.h"

/**
 * @file main.cpp
 * @brief Programme principal du robot à roues Mecanum
 *
 * Ce fichier gère :
 *  - l'initialisation des communications série (USB et Raspberry Pi)
 *  - l'initialisation du contrôle des moteurs Mecanum
 *  - la réception des commandes via un protocole série
 *  - la lecture des encodeurs
 *  - la régulation PID des moteurs
 *  - un watchdog de sécurité
 *
 * La boucle principale est conçue pour être temps réel et non bloquante.
 */

/**
 * @brief Fonction d'initialisation Arduino
 *
 * Cette fonction est exécutée une seule fois au démarrage du microcontrôleur.
 * Elle initialise :
 *  - la communication série USB pour le debug
 *  - la communication série avec le Raspberry Pi
 *  - le contrôle Mecanum (moteurs, encodeurs, PID)
 *  - le protocole de communication (incluant le watchdog)
 */
void setup() {
  // Communication série USB (monitor série PC)
  Serial.begin(115200);

  // Communication série matérielle avec le Raspberry Pi
  Serial3.begin(115200);

  // Initialisation du système Mecanum :
  // moteurs, encodeurs, PID, paramètres mécaniques
  mecanumInit();

  // Initialisation du protocole de communication
  // (gestion des commandes et watchdog)
  protocolInit();

  // Message de confirmation au démarrage
  Serial.println("Robot READY");
}

/**
 * @brief Boucle principale Arduino
 *
 * Cette fonction est exécutée en continu.
 * Elle suit l'ordre logique suivant :
 *
 * 1. Réception et traitement des commandes venant du Raspberry Pi
 * 2. Mise à jour des encodeurs et envoi des informations de retour
 * 3. Mise à jour des PID moteurs (si le mode l'exige)
 * 4. Vérification du watchdog pour la sécurité
 *
 * ⚠️ Cette boucle doit rester non bloquante pour garantir
 * un comportement temps réel stable.
 */
void loop() {
  // 1) Traitement des commandes reçues depuis le Raspberry Pi
  //    (vitesses, mode, reset, etc.)
  protocolUpdate();

  // 2) Lecture des encodeurs, calcul des vitesses réelles
  //    et envoi des informations "ENC ..." vers la Raspberry Pi
  mecanumUpdateEncoders();

  // 3) Mise à jour des PID moteurs
  //    (actif uniquement si le robot est en MODE_AI)
  mecanumUpdatePID();

  // 4) Watchdog de sécurité :
  //    si aucune commande n'est reçue pendant un certain temps,
  //    le robot s'arrête automatiquement
  protocolWatchdog();
}
