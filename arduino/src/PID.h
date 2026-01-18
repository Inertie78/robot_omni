#ifndef PID_H
#define PID_H

/**
 * @file PID.h
 * @brief Contrôleur PID discret avec anti-windup et dérivée filtrée
 *
 * Implémentation légère et adaptée à l’embarqué (Arduino).
 * Chaque instance gère :
 *  - un correcteur PID classique
 *  - un anti-windup par saturation de sortie
 *  - un filtrage de la dérivée pour réduire le bruit
 */

/**
 * @struct PID
 * @brief Contrôleur PID discret
 *
 * Formule :
 * u = Kp * e + Ki * ∫e dt + Kd * de/dt
 *
 * Avec :
 *  - saturation de la sortie
 *  - intégrale bloquée en cas de saturation
 *  - dérivée filtrée (filtre passe-bas du 1er ordre)
 */
struct PID {

  // ======================================================
  // PARAMÈTRES DU PID
  // ======================================================

  float kp;   ///< Gain proportionnel
  float ki;   ///< Gain intégral
  float kd;   ///< Gain dérivé

  // ======================================================
  // ÉTAT INTERNE
  // ======================================================

  float integral = 0.0f; ///< Terme intégral accumulé
  float prevErr  = 0.0f; ///< Erreur précédente (pour dérivée)

  // ======================================================
  // LIMITES DE SORTIE
  // ======================================================

  float outMin   = -1.0f; ///< Saturation basse de la sortie
  float outMax   =  1.0f; ///< Saturation haute de la sortie

  // ======================================================
  // FILTRAGE DE LA DÉRIVÉE
  // ======================================================

  float derivFilter = 0.0f; ///< Dérivée filtrée
  float alpha = 0.2f;      ///< Coefficient de filtrage
                           ///< 0.0 = très filtré (lent)
                           ///< 1.0 = non filtré (bruit élevé)

  // ======================================================
  // INITIALISATION
  // ======================================================

  /**
   * @brief Initialise le contrôleur PID
   *
   * @param _kp Gain proportionnel
   * @param _ki Gain intégral
   * @param _kd Gain dérivé
   * @param mn  Limite basse de la sortie
   * @param mx  Limite haute de la sortie
   *
   * Réinitialise également l’état interne
   * (intégrale, dérivée, erreur précédente).
   */
  void init(float _kp, float _ki, float _kd, float mn, float mx) {
    kp = _kp;
    ki = _ki;
    kd = _kd;

    outMin = mn;
    outMax = mx;

    integral     = 0.0f;
    prevErr      = 0.0f;
    derivFilter  = 0.0f;
  }

  // ======================================================
  // MISE À JOUR PID
  // ======================================================

  /**
   * @brief Calcule la sortie du PID
   *
   * @param target  Consigne
   * @param measure Mesure actuelle
   * @param dt      Pas de temps (secondes)
   *
   * @return Commande PID saturée dans [outMin ; outMax]
   *
   * Étapes :
   * 1. Calcul de l’erreur
   * 2. Calcul de l’intégrale (pré-accumulation)
   * 3. Calcul de la dérivée filtrée
   * 4. Calcul de la sortie PID
   * 5. Saturation + anti-windup
   */
  float update(float target, float measure, float dt) {
    // Erreur instantanée
    float err = target - measure;

    // Intégrale (pré-calcul pour anti-windup)
    float newIntegral = integral + err * dt;

    // Dérivée brute
    float derivRaw = (err - prevErr) / dt;

    // Filtrage passe-bas de la dérivée
    derivFilter = alpha * derivRaw + (1.0f - alpha) * derivFilter;

    // Calcul PID
    float out = kp * err + ki * newIntegral + kd * derivFilter;

    // Saturation + anti-windup
    if (out > outMax) {
      out = outMax;
    } else if (out < outMin) {
      out = outMin;
    } else {
      // Accumulation uniquement si non saturé
      integral = newIntegral;
    }

    // Mémorisation pour l’itération suivante
    prevErr = err;

    return out;
  }
};

#endif // PID_H
