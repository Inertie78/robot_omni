#ifndef MECANUM_CONTROL_H
#define MECANUM_CONTROL_H

#include <Arduino.h>
#include <AFMotor.h>
#include "RobotConfig.h"
#include "PID.h"

/**
 * @file MecanumControl.h
 * @brief Interface du module de contrôle Mecanum
 *
 * Ce module fournit les fonctions nécessaires pour :
 *  - initialiser les moteurs, encodeurs et PID
 *  - piloter un robot à roues Mecanum
 *  - gérer deux modes de contrôle (manuel et automatique)
 *  - assurer la sécurité via un arrêt d’urgence
 */

// ======================================================
// INITIALISATION
// ======================================================

/**
 * @brief Initialise le système de locomotion Mecanum
 *
 * Configure :
 *  - les moteurs (Adafruit Motor Shield)
 *  - les encodeurs en quadrature (interruptions)
 *  - les contrôleurs PID
 *  - les variables internes et le mode par défaut
 *
 * Doit être appelée une seule fois dans `setup()`.
 */
void mecanumInit();

// ======================================================
// MODE DE CONTROLE
// ======================================================

/**
 * @brief Change le mode de contrôle du robot
 *
 * @param mode MODE_MANUAL ou MODE_AI
 *
 * Effets :
 *  - réinitialise les commandes et consignes
 *  - libère les moteurs en MODE_MANUAL
 */
void mecanumSetMode(ControlMode mode);

// ======================================================
// COMMANDE OMNIDIRECTIONNELLE
// ======================================================

/**
 * @brief Définit une commande de déplacement omnidirectionnelle
 *
 * @param vx Vitesse avant/arrière normalisée [-1 ; 1]
 * @param vy Vitesse latérale (strafe) normalisée [-1 ; 1]
 * @param w  Vitesse de rotation normalisée [-1 ; 1]
 *
 * Selon le mode actif :
 *  - MODE_MANUAL : application directe en open-loop
 *  - MODE_AI     : conversion en consignes PID par roue
 */
void mecanumSetCommand(float vx, float vy, float w);

// ======================================================
// ENCODEURS
// ======================================================

/**
 * @brief Met à jour les vitesses des roues à partir des encodeurs
 *
 * - Calcule les vitesses en ticks/s
 * - Envoie les données sur Serial3
 *
 * Format :
 * `ENC ticks_FL ticks_FR ticks_RR ticks_RL speed_FL speed_FR speed_RR speed_RL`
 *
 * À appeler périodiquement dans `loop()`.
 */
void mecanumUpdateEncoders();

// ======================================================
// REGULATION PID
// ======================================================

/**
 * @brief Met à jour les PID et applique les commandes moteurs
 *
 * - Actif uniquement si le mode est MODE_AI
 * - Utilise les vitesses mesurées et les consignes
 * - Génère les PWM et le sens de rotation
 *
 * À appeler périodiquement dans `loop()`.
 */
void mecanumUpdatePID();

// ======================================================
// SECURITE
// ======================================================

/**
 * @brief Arrêt d’urgence du robot
 *
 * - Coupe immédiatement tous les moteurs
 * - Réinitialise les consignes de vitesse
 *
 * Typiquement appelée par le watchdog
 * si la communication est perdue.
 */
void mecanumEmergencyStop();

#endif // MECANUM_CONTROL_H
