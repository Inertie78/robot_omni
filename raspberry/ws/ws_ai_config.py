"""
ws_ai_config.py
---------------
WebSocket /ws-ai-config
Gestion de la configuration IA en temps réel.

Commandes supportées :
    GET_CONFIG
    SET_CONFIG { ... }
    RESET_CONFIG

Ce module :
    - lit / met à jour config.py
    - applique les paramètres à TD3Agent, Radar, RobotEnv
    - renvoie la configuration complète au cockpit
"""

import json
from ai import config as cfg
from ai.train_rl import get_agent
from ai.ai_loop import get_env_instance


# ----------------------------------------------------------------------
#  Envoi de la configuration complète au cockpit
# ----------------------------------------------------------------------
async def send_full_config(ws):
    await ws.send(json.dumps({
        "type": "CONFIG_FULL",
        "config": cfg.CONFIG
    }))


# ----------------------------------------------------------------------
#  Handler WebSocket /ws-ai-config
# ----------------------------------------------------------------------
async def ws_ai_config_handler(websocket):
    print("[WS-AI-CONFIG] Client connecté")

    try:
        # Dès connexion → envoyer la config actuelle
        await send_full_config(websocket)

        async for msg in websocket:
            try:
                data = json.loads(msg)
            except:
                print("[WS-AI-CONFIG] JSON invalide :", msg)
                continue

            cmd = data.get("cmd")

            # ----------------------------------------------------------
            #  GET_CONFIG
            # ----------------------------------------------------------
            if cmd == "GET_CONFIG":
                print("[WS-AI-CONFIG] GET_CONFIG")
                await send_full_config(websocket)
                continue

            # ----------------------------------------------------------
            #  RESET_CONFIG
            # ----------------------------------------------------------
            if cmd == "RESET_CONFIG":
                print("[WS-AI-CONFIG] RESET_CONFIG")
                from importlib import reload
                reload(cfg)  # recharge config.py (valeurs par défaut)

                # Appliquer aux modules
                agent = get_agent()
                env = get_env_instance()

                cfg.apply_to_agent(agent)
                cfg.apply_to_radar()
                cfg.apply_to_env(env)

                await send_full_config(websocket)
                continue

            # ----------------------------------------------------------
            #  SET_CONFIG
            # ----------------------------------------------------------
            if cmd == "SET_CONFIG":
                new_cfg = data.get("config", {})
                print("[WS-AI-CONFIG] SET_CONFIG :", new_cfg)

                # Mise à jour des valeurs
                cfg.update_config(new_cfg)

                # Application dynamique
                agent = get_agent()
                env = get_env_instance()

                cfg.apply_to_agent(agent)
                cfg.apply_to_radar()
                cfg.apply_to_env(env)

                # Confirmation au cockpit
                await send_full_config(websocket)
                continue

            # ----------------------------------------------------------
            #  Commande inconnue
            # ----------------------------------------------------------
            print("[WS-AI-CONFIG] Commande inconnue :", data)

    except Exception as e:
        print("[WS-AI-CONFIG] ERREUR :", e)

    finally:
        print("[WS-AI-CONFIG] Client déconnecté")
