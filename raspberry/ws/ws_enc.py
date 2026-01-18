"""
ws_enc.py
---------
WebSocket /ws-enc
Diffusion des données encodeurs vers le cockpit.

Les données sont mises à jour par hardware/uart.py :
    latest_enc = {
        "ticks": [...],
        "speed": [...]
    }
"""

import json

# Liste des clients encodeurs
enc_clients = set()


# ----------------------------------------------------------------------
#  Diffusion encodeurs
# ----------------------------------------------------------------------
async def broadcast_enc(data):
    """
    Diffuse les données encodeurs à tous les clients connectés.
    Appelé par hardware/uart.py via asyncio.run_coroutine_threadsafe().
    """
    msg = json.dumps(data)

    for ws in list(enc_clients):
        try:
            await ws.send(msg)
        except:
            enc_clients.discard(ws)
            print("[WS-ENC] Client retiré (erreur d’envoi)")


# ----------------------------------------------------------------------
#  Handler WebSocket /ws-enc
# ----------------------------------------------------------------------
async def ws_enc_handler(websocket):
    print("[WS-ENC] Client connecté")
    enc_clients.add(websocket)

    try:
        async for _ in websocket:
            # Le client ne parle pas, il ne fait que recevoir.
            pass

    except Exception as e:
        print("[WS-ENC] ERREUR :", e)

    finally:
        enc_clients.discard(websocket)
        print("[WS-ENC] Client déconnecté")
