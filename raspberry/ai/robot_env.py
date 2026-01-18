import math
import numpy as np
import asyncio
import websockets
import random

from ai import config as cfg
import hardware.radar_hcsr04 as radar
from hardware.uart import send_to_mega


class RobotEnv:
    """
    Environnement RL pour robot omniwheel.
    Compatible mode réel + simulation.
    Version améliorée cockpit-driven.
    """

    def __init__(self, dt=0.1, mode="real"):
        self.dt = dt
        self.mode = mode

        # Commandes actuelles (actions continues)
        self.vx_cmd = 0.0
        self.vy_cmd = 0.0
        self.w_cmd  = 0.0

        # Observations
        self.distance = 200.0
        self.angle = 0.0
        self.speed_x = 0.0
        self.speed_y = 0.0

        # WebSocket réel (optionnel)
        self.ws = None

        # Simulation
        self.sim_x = 0.0
        self.sim_y = 0.0
        self.sim_angle = 0.0
        self.sim_obstacles = [
            (100, 100, 40),
            (-80, 50, 30),
            (50, -120, 50)
        ]

        # Paramètres cockpit-driven
        self._apply_config()

        # Episode counter
        self.episode = 0

    # ----------------------------------------------------------------------
    def _apply_config(self):
        """Applique les paramètres cockpit-driven."""
        self.max_speed_linear = cfg.CONFIG["max_speed_linear"]
        self.max_speed_angular = cfg.CONFIG["max_speed_angular"]

        self.reward_distance_weight = cfg.CONFIG["reward_distance_weight"]
        self.reward_speed_weight = cfg.CONFIG["reward_speed_weight"]
        self.reward_collision_penalty = cfg.CONFIG["reward_collision_penalty"]

        self.danger_threshold_cm = cfg.CONFIG["danger_threshold_cm"]

    # ----------------------------------------------------------------------
    async def connect(self):
        """Connexion WebSocket (optionnelle)."""
        if self.mode != "real":
            return
        try:
            self.ws = await websockets.connect("ws://localhost:8765/ws-ctrl")
            print("[ENV] Connecté à server.py")
        except:
            print("[ENV] ERREUR connexion WS")
            self.ws = None

    # ----------------------------------------------------------------------
    async def reset(self):
        """Reset environnement."""
        self._apply_config()
        self.episode += 1

        if self.mode == "real":
            self.angle = 0
            self.distance = radar.distance_value
            self.speed_x = 0
            self.speed_y = 0
        else:
            self.sim_x = 0
            self.sim_y = 0
            self.sim_angle = 0
            self.distance = self._sim_radar()

        return self._get_state()

    # ----------------------------------------------------------------------
    async def step(self, action):
        """
        Action = [vx, vy, w] (continu)
        """
        # Clamp action
        self.vx_cmd = float(np.clip(action[0], -1, 1))
        self.vy_cmd = float(np.clip(action[1], -1, 1))
        self.w_cmd  = float(np.clip(action[2], -1, 1))

        # Application vitesses cockpit
        vx = self.vx_cmd * self.max_speed_linear
        vy = self.vy_cmd * self.max_speed_linear
        w  = self.w_cmd  * self.max_speed_angular

        # Mode réel
        if self.mode == "real":
            send_to_mega(f"VEL {vx} {vy} {w}")

            self.distance = radar.distance_value
            if self.distance < 0:
                self.distance = 200.0

            self.angle += w * self.dt
            self.speed_x = vx
            self.speed_y = vy

        # Mode simulation
        else:
            self._sim_step()

        reward, done = self._compute_reward()
        return self._get_state(), reward, done

    # ----------------------------------------------------------------------
    def _get_state(self):
        """
        État normalisé :
        [distance_norm, angle_norm, vx_cmd, vy_cmd, w_cmd, speed_x, speed_y]
        """
        d = max(0, min(200, self.distance))
        distance_norm = d / 200.0
        angle_norm = (self.angle % (2 * math.pi)) / (2 * math.pi)

        return np.array([
            distance_norm,
            angle_norm,
            self.vx_cmd,
            self.vy_cmd,
            self.w_cmd,
            self.speed_x,
            self.speed_y
        ], dtype=np.float32)

    # ----------------------------------------------------------------------
    def _compute_reward(self):
        """
        Reward cockpit-driven :
            - éviter les obstacles
            - distance parcourue
            - vitesse
            - pénalités rotation inutile
            - pénalités marche arrière
            - pénalités commandes conflictuelles (strafe + rotation)
            - pénalités collision
        """

        reward = 0.0
        done = False
        d = self.distance

        # -----------------------------
        # Collision immédiate
        # -----------------------------
        if d < 5:
            return self.reward_collision_penalty, True

        # -----------------------------
        # Zone dangereuse (soft penalty)
        # -----------------------------
        if d < self.danger_threshold_cm:
            danger_ratio = 1.0 - (d / self.danger_threshold_cm)
            reward -= 0.3 * danger_ratio

        # -----------------------------
        # Distance reward
        # -----------------------------
        reward += self.reward_distance_weight * (d / 200.0)

        # -----------------------------
        # Vitesse reward
        # -----------------------------
        speed_mag = math.sqrt(self.speed_x**2 + self.speed_y**2)
        reward += self.reward_speed_weight * speed_mag

        # -----------------------------
        # Ralentissement proche obstacle
        # -----------------------------
        speed_norm = speed_mag / self.max_speed_linear if self.max_speed_linear > 0 else 0.0
        danger = max(0.0, min(1.0, 1.0 - d / 50.0))
        reward -= 0.2 * danger * speed_norm

        # -----------------------------
        # Rotation penalty
        # -----------------------------
        reward -= abs(self.w_cmd) * 0.1

        # -----------------------------
        # Légère pénalité marche arrière
        # -----------------------------
        if self.vx_cmd < 0:
            reward -= 0.05 * abs(self.vx_cmd)

        # -----------------------------
        # Interdire marche arrière + rotation ou strafe
        # -----------------------------
        if self.vx_cmd < 0 and (abs(self.w_cmd) > 0.1 or abs(self.vy_cmd) > 0.1):
            reward -= 1.0   # malus fort
            done = True     # fin d'épisode pour RL

        # -----------------------------
        # Pénalité commandes conflictuelles (strafe + rotation avec vx faible)
        # -----------------------------
        if abs(self.vx_cmd) < 0.1:
            lateral_rot_mag = math.sqrt(self.vy_cmd**2 + self.w_cmd**2)
            if lateral_rot_mag > 0.3:
                reward -= min(0.5, lateral_rot_mag * 0.5)

        # -----------------------------
        # Optionnel : rotation seule sur place (pour éviter spinning inutile)
        # -----------------------------
        if abs(self.vx_cmd) < 0.1 and abs(self.vy_cmd) < 0.1 and abs(self.w_cmd) > 0.5:
            reward -= 0.5

        return reward, done


    # ----------------------------------------------------------------------
    def _sim_step(self):
        """Simulation simple omniwheel + obstacles."""
        self.sim_angle += self.w_cmd * self.max_speed_angular * self.dt

        self.sim_x += self.vx_cmd * self.max_speed_linear * 20 * self.dt
        self.sim_y += self.vy_cmd * self.max_speed_linear * 20 * self.dt

        self.distance = self._sim_radar()
        self.speed_x = self.vx_cmd * self.max_speed_linear
        self.speed_y = self.vy_cmd * self.max_speed_linear
        self.angle = self.sim_angle

    # ----------------------------------------------------------------------
    def _sim_radar(self):
        """Raycast simple pour obstacles."""
        max_dist = 200
        step = 2

        for d in range(0, max_dist, step):
            x = self.sim_x + d * math.cos(self.sim_angle)
            y = self.sim_y + d * math.sin(self.sim_angle)

            for (ox, oy, r) in self.sim_obstacles:
                if (x - ox)**2 + (y - oy)**2 < r*r:
                    return d

        return max_dist
