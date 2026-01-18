"""
server.py (version PREMIUM factorisée)
--------------------------------------

Ce module NE DOIT PAS être exécuté directement.
Il expose une fonction start_ws_server() utilisée par app.py.

Toute la logique est déportée dans des modules spécialisés :

- ws/         → WebSockets (ctrl, ai, ai_config, radar, enc, rtc, sys)
- ai/         → IA TD3 (ai_loop, config, train_rl)
- hardware/   → UART, radar, caméra
- web/        → serveur HTTP statique

Ce module :
    - démarre le serveur WebSocket
    - fournit un routeur centralisé
"""

import asyncio
import websockets
from ws.ws_router import ws_router
from hardware.uart import set_event_loop


# ----------------------------------------------------------------------
#  Serveur WebSocket principal (appelé depuis app.py)
# ----------------------------------------------------------------------
async def start_ws_server():
    """
    Démarre le serveur WebSocket principal.
    Cette fonction est appelée par app.py.
    """
    loop = asyncio.get_running_loop() 
    set_event_loop(loop)
    print("[SERVER] WebSocket sur ws://0.0.0.0:8765")

    async with websockets.serve(ws_router, "0.0.0.0", 8765):
        # Boucle infinie pour garder le serveur actif
        while True:
            await asyncio.sleep(3600)
