"""
analyze_training.py
-------------------
Script d'analyse des logs d'entraînement RL (TD3).

Analyse :
- train_steps.jsonl : log par step
- episodes.jsonl    : résumé par épisode

Génère :
- logs/img/fig_reward_steps.png     : reward par step
- logs/img/fig_reward_episodes.png  : reward total par épisode
- logs/img/fig_losses.png           : critic/actor loss
- logs/img/fig_distance.png         : distance vs steps

Usage :
    python analyze_training.py
"""

import os
import json
from typing import List, Dict

import numpy as np
import matplotlib.pyplot as plt

LOG_DIR = "data/logs"
STEP_LOG_PATH = os.path.join(LOG_DIR, "train_steps.jsonl")
EPISODE_LOG_PATH = os.path.join(LOG_DIR, "episodes.jsonl")


def load_jsonl(path: str) -> List[Dict]:
    """Charge un fichier JSONL et retourne une liste de dict."""
    if not os.path.exists(path):
        print(f"[WARN] Fichier introuvable : {path}")
        return []

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    print(f"[INFO] Chargé {len(records)} lignes depuis {path}")
    return records


def plot_reward_steps(steps: List[Dict]):
    """Trace le reward par step."""
    if not steps:
        return

    gs = [r["global_step"] for r in steps]
    rw = [r["reward"] for r in steps]

    plt.figure(figsize=(10, 4))
    plt.plot(gs, rw, ".", markersize=2, alpha=0.7)
    plt.xlabel("Global step")
    plt.ylabel("Reward")
    plt.title("Reward par step")
    plt.grid(True, alpha=0.3)
    out = os.path.join(LOG_DIR, "img/fig_reward_steps.png")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"[PLOT] {out}")


def plot_reward_episodes(episodes: List[Dict]):
    """Trace le reward total par épisode."""
    if not episodes:
        return

    ep_ids = [e["episode"] for e in episodes]
    total_r = [e["total_reward"] for e in episodes]

    plt.figure(figsize=(10, 4))
    plt.plot(ep_ids, total_r, "-o", markersize=3)
    plt.xlabel("Episode")
    plt.ylabel("Total reward")
    plt.title("Reward total par épisode")
    plt.grid(True, alpha=0.3)
    out = os.path.join(LOG_DIR, "img/fig_reward_episodes.png")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"[PLOT] {out}")


def plot_losses(steps: List[Dict]):
    """Trace critic_loss et actor_loss en fonction des steps."""
    if not steps:
        return

    gs = [r["global_step"] for r in steps if r.get("critic_loss") is not None]
    critic = [r["critic_loss"] for r in steps if r.get("critic_loss") is not None]
    actor = [r["actor_loss"] for r in steps if r.get("actor_loss") is not None]

    if not gs:
        print("[INFO] Pas de losses dans les logs.")
        return

    plt.figure(figsize=(10, 4))
    plt.plot(gs, critic, label="critic_loss", alpha=0.8)
    if any(a is not None for a in actor):
        plt.plot(gs, actor, label="actor_loss", alpha=0.8)
    plt.xlabel("Global step")
    plt.ylabel("Loss")
    plt.title("Losses TD3")
    plt.legend()
    plt.grid(True, alpha=0.3)
    out = os.path.join(LOG_DIR, "img/fig_losses.png")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"[PLOT] {out}")


def plot_distance(steps: List[Dict]):
    """Trace la distance mesurée par rapport aux steps."""
    if not steps:
        return

    gs = [r["global_step"] for r in steps]
    dist = [r.get("distance", 0.0) for r in steps]

    plt.figure(figsize=(10, 4))
    plt.plot(gs, dist, ".", markersize=2, alpha=0.7)
    plt.xlabel("Global step")
    plt.ylabel("Distance")
    plt.title("Distance vs steps")
    plt.grid(True, alpha=0.3)
    out = os.path.join(LOG_DIR, "img/fig_distance.png")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"[PLOT] {out}")


def print_stats(episodes: List[Dict]):
    """Affiche quelques stats globales sur les épisodes."""
    if not episodes:
        print("[STATS] Aucun épisode loggé.")
        return

    total_r = np.array([e["total_reward"] for e in episodes], dtype=np.float32)
    lengths = np.array([e["length"] for e in episodes], dtype=np.int32)

    print("[STATS] Épisodes :", len(episodes))
    print("[STATS] Reward moyen   :", float(total_r.mean()))
    print("[STATS] Reward min/max :", float(total_r.min()), "/", float(total_r.max()))
    print("[STATS] Longueur moy.  :", float(lengths.mean()))


def main():
    steps = load_jsonl(STEP_LOG_PATH)
    episodes = load_jsonl(EPISODE_LOG_PATH)

    print_stats(episodes)
    plot_reward_steps(steps)
    plot_reward_episodes(episodes)
    plot_losses(steps)
    plot_distance(steps)


if __name__ == "__main__":
    main()