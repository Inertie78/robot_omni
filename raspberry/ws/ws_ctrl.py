"""
ws_ctrl.py
----------
WebSocket /ws-ctrl
Gestion des commandes cockpit → robot.

Commandes supportées :
    OMNI vx vy w
    STOP
    MODE MANUAL
    MODE AI
    SAVE_AI
    LOAD_AI
    REBOOT
    SHUTDOWN
"""

import json
from hardware.uart import send_to_mega
from ai.ai_loop import start_ai, stop_ai
from ai.train_rl import init_agent, get_agent


# ----------------------------------------------------------------------
#  Handler WebSocket /ws-ctrl
# ----------------------------------------------------------------------
async def ws_ctrl_handler(websocket):
    print("[WS-CTRL] Client connecté")

    try:
        async for msg in websocket:
            msg = msg.strip()
            print("[WS-CTRL] Reçu :", msg)

            # ----------------------------------------------------------
            #  Commande OMNI vx vy w
            # ----------------------------------------------------------
            if msg.startswith("OMNI"):
                try:
                    _, sx, sy, sw = msg.split()
                    vx, vy, w = float(sx), float(sy), float(sw)
                except:
                    print("[WS-CTRL] Commande OMNI invalide :", msg)
                    continue

                # Clamp sécurité
                vx = max(-1, min(1, vx))
                vy = max(-1, min(1, vy))
                w  = max(-1, min(1, w))

                send_to_mega(f"VEL {vx} {vy} {w}")
                continue

            # ----------------------------------------------------------
            #  STOP
            # ----------------------------------------------------------
            if msg == "STOP":
                await stop_ai()
                send_to_mega("VEL 0 0 0")
                continue

            # ----------------------------------------------------------
            #  MODE MANUAL
            # ----------------------------------------------------------
            if msg == "MODE MANUAL":
                await stop_ai()
                send_to_mega("MODE MANUAL")
                continue

            # ----------------------------------------------------------
            #  MODE AI
            # ----------------------------------------------------------
            if msg == "MODE AI":
                send_to_mega("MODE AI")
                await start_ai()
                continue

            # ----------------------------------------------------------
            #  SAVE IA (TD3)
            # ----------------------------------------------------------
            if msg == "SAVE_AI":
                await init_agent()
                ag = get_agent()
                if ag:
                    ag.save_full("data/agent_td3_full.pth")
                    print("[WS-CTRL] Modèle TD3 sauvegardé.")
                continue

            # ----------------------------------------------------------
            #  LOAD IA (TD3)
            # ----------------------------------------------------------
            if msg == "LOAD_AI":
                await init_agent()
                ag = get_agent()
                if ag:
                    ag.load_full("data/agent_td3_full.pth")
                    print("[WS-CTRL] Modèle TD3 chargé.")
                continue

            # ----------------------------------------------------------
            #  REBOOT
            # ----------------------------------------------------------
            if msg == "REBOOT":
                print("[WS-CTRL] Reboot demandé")
                import os
                os.system("sudo reboot")
                continue

            # ----------------------------------------------------------
            #  SHUTDOWN
            # ----------------------------------------------------------
            if msg == "SHUTDOWN":
                print("[WS-CTRL] Shutdown demandé")
                import os
                os.system("sudo shutdown -h now")
                continue

            # ----------------------------------------------------------
            #  Commande inconnue
            # ----------------------------------------------------------
            print("[WS-CTRL] Commande inconnue :", msg)

    except Exception as e:
        print("[WS-CTRL] ERREUR :", e)

    finally:
        print("[WS-CTRL] Client déconnecté")
