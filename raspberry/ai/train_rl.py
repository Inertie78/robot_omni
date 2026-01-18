"""
train_rl.py (version PREMIUM cockpit-driven)
-------------------------------------------
Boucle d'entraînement RL pour le robot omni en actions continues (TD3).

Améliorations :
- Compatible cockpit (config.py dynamique)
- Compatible RobotEnv mis à jour
- Logging plus propre et robuste
- Gestion améliorée des épisodes
- Intégration parfaite avec ai_loop.py
"""

import os
import json
import time
import numpy as np

from ai.robot_env import RobotEnv
from ai.agent_td3 import TD3Agent
from ai import config as cfg

# Dimensions
STATE_DIM = 7
ACTION_DIM = 3

# Logging
LOG_DIR = "data/logs"
STEP_LOG_PATH = os.path.join(LOG_DIR, "train_steps.jsonl")
EPISODE_LOG_PATH = os.path.join(LOG_DIR, "episodes.jsonl")

# Globals
env = None
agent = None
state = None

episode_idx = 0
episode_step = 0
global_step = 0

episode_states = []
episode_actions = []
episode_rewards = []
episode_next_states = []
episode_dones = []


# ---------------------------------------------------------------------------
#  LOGGING
# ---------------------------------------------------------------------------
def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def _append_jsonl(path, record):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _save_episode_replay(ep_idx):
    if len(episode_states) == 0:
        return

    filename = f"replay/replay_ep_{ep_idx:05d}.npz"
    path = os.path.join(LOG_DIR, filename)

    np.savez_compressed(
        path,
        states=np.array(episode_states, dtype=np.float32),
        actions=np.array(episode_actions, dtype=np.float32),
        rewards=np.array(episode_rewards, dtype=np.float32),
        next_states=np.array(episode_next_states, dtype=np.float32),
        dones=np.array(episode_dones, dtype=np.float32),
    )
    print(f"[LOG] Replay épisode sauvegardé : {path}")


def _log_step(ep_idx, ep_step, g_step, state, action, reward, next_state, done, info, train_info):
    _ensure_log_dir()

    record = {
        "t": time.time(),
        "episode": ep_idx,
        "episode_step": ep_step,
        "global_step": g_step,
        "reward": float(reward),
        "done": bool(done),

        # Action
        "action_vx": float(action[0]),
        "action_vy": float(action[1]),
        "action_w": float(action[2]),

        # Env metrics
        "speed_x": float(info.get("speed_x", 0.0)),
        "speed_y": float(info.get("speed_y", 0.0)),
        "distance": float(info.get("distance", 0.0)),
        "steps_updates": int(info.get("steps_updates", 0)),
    }

    # Losses
    if train_info:
        record["critic_loss"] = float(train_info.get("critic_loss", 0.0))
        actor_loss = train_info.get("actor_loss", None)
        record["actor_loss"] = float(actor_loss) if actor_loss is not None else None
    else:
        record["critic_loss"] = None
        record["actor_loss"] = None

    _append_jsonl(STEP_LOG_PATH, record)


def _log_episode_summary(ep_idx, total_reward, length):
    _ensure_log_dir()
    record = {
        "t": time.time(),
        "episode": ep_idx,
        "length": int(length),
        "total_reward": float(total_reward),
    }
    _append_jsonl(EPISODE_LOG_PATH, record)
    print(f"[LOG] Épisode {ep_idx} terminé - steps={length}, R={total_reward:.3f}")


# ---------------------------------------------------------------------------
#  INIT
# ---------------------------------------------------------------------------
async def init_agent(mode="real"):
    global env, agent, state
    global episode_idx, episode_step, global_step
    global episode_states, episode_actions, episode_rewards, episode_next_states, episode_dones

    # Environnement
    if env is None:
        env = RobotEnv(dt=0.1, mode=mode)
        await env.connect()

    # Agent
    if agent is None:
        agent = TD3Agent(state_dim=STATE_DIM, action_dim=ACTION_DIM)

        cfg.apply_to_agent(agent)
        
        if os.path.exists("data/agent_td3_full.pth"):
            agent.load_full("data/agent_td3_full.pth")
            print("[TD3] Modèle chargé depuis data/agent_td3_full.pth")

    # Premier état
    if state is None:
        state = await env.reset()

    # Logging init
    if episode_idx == 0 and episode_step == 0 and global_step == 0:
        _ensure_log_dir()
        print("[LOG] Logging RL initialisé.")

        episode_states = []
        episode_actions = []
        episode_rewards = []
        episode_next_states = []
        episode_dones = []


# ---------------------------------------------------------------------------
#  UNE ÉTAPE RL
# ---------------------------------------------------------------------------
async def run_agent_once():
    global env, agent, state
    global episode_idx, episode_step, global_step
    global episode_states, episode_actions, episode_rewards, episode_next_states, episode_dones

    await init_agent()

    # 1. Action TD3
    action = agent.select_action(state, noise_scale=cfg.CONFIG["noise_scale"])

    # 2. Step env
    next_state, reward, done = await env.step(action)

    # 3. Replay buffer
    agent.push_transition(state, action, reward, next_state, float(done))

    # 4. Train TD3
    train_info = agent.train_step(batch_size=cfg.CONFIG["batch_size"])

    # 5. Sauvegarde périodique
    if agent.total_it > 0 and agent.total_it % 1000 == 0:
        agent.save_full("data/agent_td3_full.pth")
        print("[TD3] Modèle sauvegardé.")

    # Infos cockpit
    info = {
        "action_vx": float(action[0]),
        "action_vy": float(action[1]),
        "action_w": float(action[2]),
        "reward": float(reward),
        "steps_updates": int(agent.total_it),
        "speed_x": float(env.speed_x),
        "speed_y": float(env.speed_y),
        "distance": float(env.distance),
    }

    if train_info:
        info["critic_loss"] = float(train_info.get("critic_loss", 0.0))
        if train_info.get("actor_loss") is not None:
            info["actor_loss"] = float(train_info["actor_loss"])

    # 6. Logging
    global_step += 1
    episode_step += 1

    _log_step(
        ep_idx=episode_idx,
        ep_step=episode_step,
        g_step=global_step,
        state=state,
        action=action,
        reward=reward,
        next_state=next_state,
        done=done,
        info=info,
        train_info=train_info,
    )

    # Replay épisode
    episode_states.append(np.array(state, dtype=np.float32))
    episode_actions.append(np.array(action, dtype=np.float32))
    episode_rewards.append(float(reward))
    episode_next_states.append(np.array(next_state, dtype=np.float32))
    episode_dones.append(float(done))

    # Mise à jour état
    state = next_state

    # Fin d'épisode
    if done:
        total_reward = float(sum(episode_rewards))

        _save_episode_replay(episode_idx)
        _log_episode_summary(episode_idx, total_reward, episode_step)

        episode_idx += 1
        episode_step = 0

        episode_states = []
        episode_actions = []
        episode_rewards = []
        episode_next_states = []
        episode_dones = []

        state = await env.reset()

    return reward, info, episode_idx


# ---------------------------------------------------------------------------
#  ACCÈS À L'AGENT
# ---------------------------------------------------------------------------
def get_agent():
    global agent
    return agent