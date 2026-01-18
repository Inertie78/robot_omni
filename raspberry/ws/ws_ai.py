"""
ws_ai.py
--------
WebSocket /ws-ai
Diffusion des informations IA (TD3 Live) vers le cockpit.

Ce module ne génère aucune donnée IA.
Il se contente de diffuser ce que ai_loop.py lui envoie.
"""

import json

# Liste des clients IA connectés
ia_clients = set()


def get_ia_clients():
    """Permet à ai_loop.py de récupérer la liste des clients IA."""
    return ia_clients


# ----------------------------------------------------------------------
#  Handler WebSocket /ws-ai
# ----------------------------------------------------------------------
async def ws_ai_handler(websocket):
    print("[WS-AI] Client IA connecté")
    ia_clients.add(websocket)

    try:
        async for _ in websocket:
            # Le client IA ne parle pas, il ne fait que recevoir.
            pass

    except Exception as e:
        print("[WS-AI] ERREUR :", e)

    finally:
        ia_clients.discard(websocket)
        print("[WS-AI] Client IA déconnecté")
