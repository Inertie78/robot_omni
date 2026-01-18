"""
ws_router.py
------------
Routeur central pour tous les WebSockets du serveur AxisOne.

Chaque WebSocket est géré dans un module séparé :
    /ws-ctrl       → ws_ctrl.py
    /ws-ai         → ws_ai.py
    /ws-ai-config  → ws_ai_config.py
    /ws-radar      → ws_radar.py
    /ws-enc        → ws_enc.py
    /ws-sys        → ws_sys.py
    /ws-rtc        → ws_rtc.py
"""

from ws.ws_ctrl import ws_ctrl_handler
from ws.ws_ai import ws_ai_handler
from ws.ws_ai_config import ws_ai_config_handler
from ws.ws_radar import ws_radar_handler
from ws.ws_enc import ws_enc_handler
from ws.ws_sys import ws_sys_handler
from ws.ws_rtc import ws_rtc_handler


# ----------------------------------------------------------------------
#  Routeur WebSocket
# ----------------------------------------------------------------------
async def ws_router(websocket):
    """
    Route les connexions WebSocket vers le bon module.
    """
    path = websocket.request.path
    print(f"[WS] Connexion entrante : {path}")

    if path == "/ws-ctrl":
        await ws_ctrl_handler(websocket)

    elif path == "/ws-ai":
        await ws_ai_handler(websocket)

    elif path == "/ws-ai-config":
        await ws_ai_config_handler(websocket)

    elif path == "/ws-radar":
        await ws_radar_handler(websocket)

    elif path == "/ws-enc":
        await ws_enc_handler(websocket)

    elif path == "/ws-sys":
        await ws_sys_handler(websocket)

    elif path == "/ws-rtc":
        await ws_rtc_handler(websocket)

    else:
        print(f"[WS] Chemin inconnu : {path}")
        await websocket.close()
