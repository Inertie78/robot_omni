"""
agent_td3.py
------------
Agent TD3 pour robot omniwheel (actions continues).

- Actor : π(s) -> a (vx, vy, w) dans [-1, 1]
- Critic : Q1(s,a), Q2(s,a)
- Replay buffer
- Target networks (actor_target, critic_target)
- TD3 tricks : double critic, policy delay, target policy smoothing
"""

import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


# ----------------------------------------------------------------------
#  Réseaux
# ----------------------------------------------------------------------
class Actor(nn.Module):
    """
    Réseau Actor : état -> action continue dans [-1, 1]^action_dim
    """
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Tanh(),  # bornes [-1, 1]
        )

    def forward(self, x):
        return self.net(x)


class Critic(nn.Module):
    """
    Critic double (Q1 et Q2) : (state, action) -> Q1, Q2
    """
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super().__init__()

        # Q1
        self.q1 = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

        # Q2
        self.q2 = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, state, action):
        x = torch.cat([state, action], dim=1)
        q1 = self.q1(x)
        q2 = self.q2(x)
        return q1, q2

    def q1_only(self, state, action):
        x = torch.cat([state, action], dim=1)
        return self.q1(x)


# ----------------------------------------------------------------------
#  Replay Buffer
# ----------------------------------------------------------------------
class ReplayBuffer:
    def __init__(self, capacity=1000000):
        self.capacity = capacity
        self.buffer = []
        self.pos = 0

    def push(self, s, a, r, ns, d):
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        self.buffer[self.pos] = (s, a, r, ns, d)
        self.pos = (self.pos + 1) % self.capacity

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        s, a, r, ns, d = map(np.array, zip(*batch))
        return s, a, r, ns, d

    def __len__(self):
        return len(self.buffer)


# ----------------------------------------------------------------------
#  Agent TD3
# ----------------------------------------------------------------------
class TD3Agent:
    """
    Agent TD3 complet pour actions continues.

    API :
        - select_action(state, noise_scale=0.1)
        - push_transition(s, a, r, ns, d)
        - train_step(batch_size=64)
        - save(path) / load(path)
        - save_full(path) / load_full(path)
    """

    def __init__(self,
                 state_dim,
                 action_dim,
                 gamma=0.99,
                 lr_actor=1e-3,
                 lr_critic=1e-3,
                 tau=0.005,
                 policy_noise=0.2,
                 noise_clip=0.5,
                 policy_delay=2):

        # Dimensions
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.tau = tau
        self.policy_noise = policy_noise
        self.noise_clip = noise_clip
        self.policy_delay = policy_delay

        # Réseaux
        self.actor = Actor(state_dim, action_dim)
        self.actor_target = Actor(state_dim, action_dim)
        self.actor_target.load_state_dict(self.actor.state_dict())

        self.critic = Critic(state_dim, action_dim)
        self.critic_target = Critic(state_dim, action_dim)
        self.critic_target.load_state_dict(self.critic.state_dict())

        # Optimiseurs
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=lr_actor)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=lr_critic)

        # Replay buffer
        self.buffer = ReplayBuffer()

        # CPU uniquement
        self.device = torch.device("cpu")
        self.actor.to(self.device)
        self.actor_target.to(self.device)
        self.critic.to(self.device)
        self.critic_target.to(self.device)

        # Pour monitoring
        self.total_it = 0  # nombre total d'updates

    # ------------------------------------------------------------------
    #  Sélection d'action
    # ------------------------------------------------------------------
    def select_action(self, state, noise_scale=0.1):
        """
        Args:
            state (np.array): état courant
            noise_scale (float): amplitude du bruit exploration (0.0 = pas de bruit)

        Returns:
            np.array: action continue dans [-1, 1]^action_dim
        """
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            action = self.actor(state_t).cpu().numpy()[0]

        if noise_scale > 0.0:
            noise = np.random.normal(0, noise_scale, size=self.action_dim)
            action = action + noise

        action = np.clip(action, -1.0, 1.0)
        return action.astype(np.float32)

    # ------------------------------------------------------------------
    #  Stockage transition
    # ------------------------------------------------------------------
    def push_transition(self, s, a, r, ns, d):
        """
        s : état
        a : action (np.array)
        r : reward (float)
        ns: next_state
        d : done (float 0.0 ou 1.0)
        """
        self.buffer.push(s, a, r, ns, d)

    # ------------------------------------------------------------------
    #  Apprentissage
    # ------------------------------------------------------------------
    def train_step(self, batch_size=64):
        """
        Effectue une étape d'apprentissage TD3.

        Returns:
            dict | None :
                {
                    "critic_loss": float,
                    "actor_loss": float | None (pas mis à jour à chaque step),
                }
            ou None si pas assez de données
        """
        if len(self.buffer) < batch_size:
            return None

        self.total_it += 1

        # Échantillonnage
        s, a, r, ns, d = self.buffer.sample(batch_size)

        # Conversion en tenseurs
        state      = torch.FloatTensor(s).to(self.device)
        action     = torch.FloatTensor(a).to(self.device)
        reward     = torch.FloatTensor(r).unsqueeze(1).to(self.device)
        next_state = torch.FloatTensor(ns).to(self.device)
        done       = torch.FloatTensor(d).unsqueeze(1).to(self.device)

        # ---------------- Critic update ----------------
        with torch.no_grad():
            # bruit sur action target
            noise = (torch.randn_like(action) * self.policy_noise).clamp(
                -self.noise_clip, self.noise_clip
            )
            next_action = self.actor_target(next_state) + noise
            next_action = next_action.clamp(-1.0, 1.0)

            # Q-targets
            target_q1, target_q2 = self.critic_target(next_state, next_action)
            target_q = torch.min(target_q1, target_q2)
            target_q = reward + self.gamma * (1.0 - done) * target_q

        # Q actuels
        current_q1, current_q2 = self.critic(state, action)
        critic_loss = nn.functional.mse_loss(current_q1, target_q) + \
                      nn.functional.mse_loss(current_q2, target_q)

        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        nn.utils.clip_grad_norm_(self.critic.parameters(), 1.0)
        self.critic_optimizer.step()

        actor_loss_value = None

        # ---------------- Actor + target update (delay) ----------------
        if self.total_it % self.policy_delay == 0:
            # Actor : maximiser Q -> minimiser -Q
            actor_loss = -self.critic.q1_only(state, self.actor(state)).mean()

            self.actor_optimizer.zero_grad()
            actor_loss.backward()
            nn.utils.clip_grad_norm_(self.actor.parameters(), 1.0)
            self.actor_optimizer.step()

            actor_loss_value = float(actor_loss.item())

            # Soft update des cibles
            self._soft_update(self.actor, self.actor_target)
            self._soft_update(self.critic, self.critic_target)

        return {
            "critic_loss": float(critic_loss.item()),
            "actor_loss": actor_loss_value,
        }

    # ------------------------------------------------------------------
    #  Soft update
    # ------------------------------------------------------------------
    def _soft_update(self, net, target_net):
        for param, target_param in zip(net.parameters(), target_net.parameters()):
            target_param.data.copy_(self.tau * param.data + (1.0 - self.tau) * target_param.data)

    # ------------------------------------------------------------------
    #  Sauvegarde / chargement
    # ------------------------------------------------------------------
    def save(self, path):
        """
        Sauvegarde minimale (actor uniquement)
        """
        torch.save(self.actor.state_dict(), path)

    def load(self, path):
        """
        Charge l'actor, met à jour l'actor_target.
        """
        self.actor.load_state_dict(torch.load(path, map_location=self.device))
        self.actor_target.load_state_dict(self.actor.state_dict())

    def save_full(self, path):
        """
        Sauvegarde complète (réseaux + optim + iters).
        """
        torch.save({
            "actor": self.actor.state_dict(),
            "actor_target": self.actor_target.state_dict(),
            "critic": self.critic.state_dict(),
            "critic_target": self.critic_target.state_dict(),
            "actor_opt": self.actor_optimizer.state_dict(),
            "critic_opt": self.critic_optimizer.state_dict(),
            "total_it": self.total_it,
        }, path)

    def load_full(self, path):
        """
        Chargement complet (reprise d'entraînement parfaite).
        """
        data = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(data["actor"])
        self.actor_target.load_state_dict(data["actor_target"])
        self.critic.load_state_dict(data["critic"])
        self.critic_target.load_state_dict(data["critic_target"])
        self.actor_optimizer.load_state_dict(data["actor_opt"])
        self.critic_optimizer.load_state_dict(data["critic_opt"])
        self.total_it = data["total_it"]
