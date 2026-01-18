"""
config.py
---------
Module centralisé pour la configuration dynamique du robot, de l'IA TD3,
du radar et de l'environnement RobotEnv.

Version PREMIUM :
- Compatible avec radar_hcsr04.set_alpha() et set_median_window_size()
- Architecture cockpit-driven
"""

import hardware.radar_hcsr04 as radar_hcsr04

# ----------------------------------------------------------------------
#  CONFIGURATION GLOBALE (modifiable en temps réel)
# ----------------------------------------------------------------------
CONFIG = {
    # ---------------- TD3 : Exploration ----------------
    "noise_scale": 0.05,
    "policy_noise": 0.1,
    "noise_clip": 0.20,

    # ---------------- TD3 : Learning ----------------
    "gamma": 0.99,
    "lr_actor": 0.0003,
    "lr_critic": 0.0003,
    "tau": 0.002,
    "policy_delay": 3,
    "batch_size": 256,

    # ---------------- Robot : Vitesse ----------------
    "max_speed_linear": 1.0,
    "max_speed_angular": 1.0,

    # ---------------- Reward shaping ----------------
    "reward_distance_weight": 1.0,
    "reward_speed_weight": 0.1,
    "reward_collision_penalty": -1.0,

    # ---------------- Radar ----------------
    "radar_alpha": 0.25,
    "radar_median_window": 5,
    "danger_threshold_cm": 20.0,

    # ---------------- Debug / Logging ----------------
    "enable_replay_logging": True,
    "enable_loss_logging": True,
    "train_frequency_hz": 20,
}


# ----------------------------------------------------------------------
#  Mise à jour des paramètres
# ----------------------------------------------------------------------
def update_config(new_values: dict):
    """
    Met à jour les paramètres globaux CONFIG avec les valeurs reçues
    depuis le cockpit (config.js).
    """
    for key, value in new_values.items():
        if key in CONFIG:
            CONFIG[key] = value
            print(f"[CONFIG] {key} = {value}")
        else:
            print(f"[CONFIG] Paramètre inconnu ignoré : {key}")


# ----------------------------------------------------------------------
#  Application aux modules
# ----------------------------------------------------------------------
def apply_to_agent(agent):
    """
    Applique les paramètres CONFIG à l'agent TD3.
    """
    if agent is None:
        return

    # Exploration
    agent.noise_scale = CONFIG["noise_scale"]
    agent.policy_noise = CONFIG["policy_noise"]
    agent.noise_clip = CONFIG["noise_clip"]

    # Learning
    agent.gamma = CONFIG["gamma"]
    agent.tau = CONFIG["tau"]
    agent.policy_delay = CONFIG["policy_delay"]

    # Learning rates
    for g in agent.actor_optimizer.param_groups:
        g["lr"] = CONFIG["lr_actor"]

    for g in agent.critic_optimizer.param_groups:
        g["lr"] = CONFIG["lr_critic"]

    print("[CONFIG] Paramètres TD3 appliqués à l'agent.")


def apply_to_radar():
    """
    Applique les paramètres CONFIG au radar HC-SR04 (version PREMIUM).
    Utilise les fonctions dynamiques du module radar_hcsr04.
    """
    radar_hcsr04.set_alpha(CONFIG["radar_alpha"])
    radar_hcsr04.set_median_window_size(CONFIG["radar_median_window"])

    print("[CONFIG] Paramètres radar appliqués (alpha + fenêtre médiane).")


def apply_to_env(env):
    """
    Applique les paramètres CONFIG à l'environnement RobotEnv.
    """
    if env is None:
        return

    env.max_speed_linear = CONFIG["max_speed_linear"]
    env.max_speed_angular = CONFIG["max_speed_angular"]

    env.reward_distance_weight = CONFIG["reward_distance_weight"]
    env.reward_speed_weight = CONFIG["reward_speed_weight"]
    env.reward_collision_penalty = CONFIG["reward_collision_penalty"]

    env.danger_threshold_cm = CONFIG["danger_threshold_cm"]

    print("[CONFIG] Paramètres RobotEnv appliqués.")