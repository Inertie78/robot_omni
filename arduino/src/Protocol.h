#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <Arduino.h>
#include "RobotConfig.h"

/**
 * @file Protocol.h
 * @brief Interface du protocole de communication série
 *
 * Ce module définit l’API permettant :
 *  - la communication avec la Raspberry Pi via Serial3
 *  - le traitement des commandes texte
 *  - la gestion d’un watchdog de sécurité
 */

// ======================================================
// INITIALISATION
// ======================================================

/**
 * @brief Initialise le protocole de communication
 *
 * - Réinitialise l’état interne
 * - Démarre le watchdog
 *
 * Doit être appelée une seule fois dans `setup()`.
 */
void protocolInit();

// ======================================================
// MISE À JOUR DU PROTOCOLE
// ======================================================

/**
 * @brief Met à jour la réception des messages série
 *
 * - Lecture non bloquante de Serial3
 * - Reconstruction des lignes complètes
 * - Décodage et exécution des commandes
 *
 * À appeler en continu dans la fonction `loop()`.
 */
void protocolUpdate();

// ======================================================
// WATCHDOG DE SÉCURITÉ
// ======================================================

/**
 * @brief Vérifie l’état du watchdog de communication
 *
 * Si aucune commande valide n’est reçue pendant
 * `WATCHDOG_TIMEOUT` millisecondes :
 *  - arrêt d’urgence du robot
 *
 * À appeler périodiquement dans `loop()`.
 */
void protocolWatchdog();

#endif // PROTOCOL_H
