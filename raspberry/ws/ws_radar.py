"""
ws_radar.py
-----------
WebSocket /ws-radar
Diffusion continue des données radar HC-SR04 vers le cockpit.

Données envoyées :
    {
        "distance": <float>,
        "signal_strength": <float>
    }

Fréquence : 20 Hz (toutes les 50 ms)
"""

import json
import asyncio
from hardware import radar_hcsr04

# ----------------------------------------------------------------------
#  Handler WebSocket /ws-radar
# ----------------------------------------------------------------------
async def ws_radar_handler(websocket):
    print("[WS-RADAR] Client connecté")

    try:
        while True:
            msg = json.dumps({
                "distance": radar_hcsr04.distance_value,
                "signal_strength": radar_hcsr04.signal_strength
            })

            await websocket.send(msg)
            await asyncio.sleep(0.05)  # 20 Hz

    except Exception as e:
        print("[WS-RADAR] ERREUR :", e)

    finally:
        print("[WS-RADAR] Client déconnecté")
