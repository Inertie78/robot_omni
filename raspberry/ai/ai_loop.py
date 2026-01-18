"""
ai_loop.py
----------
Boucle IA TD3 en temps réel pour AxisOne (version PREMIUM).

Fonctionnalités :
- Exécution de l'agent TD3 à 20 Hz
- Interaction avec RobotEnv
- Diffusion des infos IA vers /ws-ai
- Application dynamique des paramètres via config.py
- Gestion robuste des erreurs
- Démarrage / arrêt propre
"""

import asyncio
import json
from ai.train_rl import init_agent, get_agent, run_agent_once
from ai import config as cfg
from ws.ws_ai import get_ia_clients

# Instance globale de l'environnement (optionnel)
_env_instance = None

# État IA
ia_running = False
ia_task = None


# ----------------------------------------------------------------------
#  Accès à l'environnement (pour config.py)
# ----------------------------------------------------------------------
def set_env_instance(env):
    global _env_instance
    _env_instance = env


def get_env_instance():
    return _env_instance


# ----------------------------------------------------------------------
#  Boucle IA (20 Hz)
# ----------------------------------------------------------------------
async def _ai_loop():
    """
    Boucle IA exécutée tant que ia_running = True.
    Appelle run_agent_once() qui :
        - observe
        - choisit action
        - step env
        - apprend
        - retourne reward, info, episode
    """
    global ia_running

    print("[IA] Boucle IA démarrée (20 Hz)")

    # Initialisation agent TD3
    await init_agent()
    agent = get_agent()

    # Application des paramètres cockpit
    cfg.apply_to_agent(agent)
    cfg.apply_to_env(_env_instance)

    while ia_running:
        try:
            # Exécute un pas d'IA
            reward, info, episode = await run_agent_once()

            # Ajout du numéro d'épisode
            info["episode"] = episode

            # Diffusion vers tous les clients IA
            msg = json.dumps(info)
            for ws in list(get_ia_clients()):
                try:
                    await ws.send(msg)
                except:
                    get_ia_clients().discard(ws)

        except Exception as e:
            print("[IA] ERREUR dans ai_loop :", e)

        # Fréquence IA : 20 Hz
        await asyncio.sleep(0.05)

    print("[IA] Boucle IA arrêtée")


# ----------------------------------------------------------------------
#  Démarrage IA
# ----------------------------------------------------------------------
async def start_ai():
    global ia_running, ia_task

    if ia_running:
        print("[IA] Déjà en cours")
        return

    ia_running = True
    ia_task = asyncio.create_task(_ai_loop())
    print("[IA] IA démarrée")


# ----------------------------------------------------------------------
#  Arrêt IA
# ----------------------------------------------------------------------
async def stop_ai():
    global ia_running, ia_task

    if not ia_running:
        return

    ia_running = False

    if ia_task:
        ia_task.cancel()
        ia_task = None

    print("[IA] IA arrêtée")
