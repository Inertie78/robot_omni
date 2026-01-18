#ifndef ROBOT_CONFIG_H
#define ROBOT_CONFIG_H

#include <Arduino.h>

/**
 * @file RobotConfig.h
 * @brief Configuration globale du robot Mecanum
 *
 * Ce fichier centralise :
 *  - les modes de contrôle haut niveau
 *  - les constantes mécaniques et temporelles
 *  - les paramètres globaux utilisés par tous les modules
 *
 * Toute modification ici impacte l’ensemble du comportement du robot.
 */

// ======================================================
// MODES DE CONTROLE
// ======================================================

/**
 * @enum ControlMode
 * @brief Modes de contrôle haut niveau du robot
 */
enum ControlMode {
  MODE_MANUAL = 0,   ///< Commande directe (open-loop, PWM)
  MODE_AI     = 1    ///< Commande en boucle fermée (PID vitesse)
};

// ======================================================
// CONSTANTES GENERALES
// ======================================================

/**
 * @brief Valeur maximale de PWM envoyée aux moteurs
 *
 * Plage réelle du shield : [0 ; 255]
 * La valeur est volontairement limitée pour :
 *  - préserver les moteurs
 *  - améliorer la stabilité du contrôle
 */
const int PWM_MAX = 200;

/**
 * @brief Vitesse maximale d’une roue (ticks par seconde)
 *
 * Utilisée pour :
 *  - normaliser les commandes vx, vy, w dans [-1 ; 1]
 *  - définir l’échelle des consignes PID
 *
 * ⚠️ Doit correspondre à la vitesse réelle max mesurée.
 */
const float MAX_WHEEL_SPEED = 500.0;

/**
 * @brief Délai maximal sans commande avant arrêt d’urgence
 *
 * Si aucune commande valide n’est reçue depuis la Raspberry Pi
 * pendant ce temps, le watchdog stoppe immédiatement le robot.
 */
const unsigned long WATCHDOG_TIMEOUT = 500; // ms

// ======================================================
// PARAMÈTRES PID
// ======================================================

/**
 * @brief Fréquence de mise à jour du PID
 *
 * Typiquement comprise entre 20 et 100 Hz.
 */
const float PID_FREQ = 50.0;

/**
 * @brief Période de mise à jour du PID (millisecondes)
 *
 * Calculée à partir de PID_FREQ.
 */
const unsigned long PID_PERIOD = 1000.0 / PID_FREQ;

#endif // ROBOT_CONFIG_H
