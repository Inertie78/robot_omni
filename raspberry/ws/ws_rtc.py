"""
ws_rtc.py
---------
WebSocket /ws-rtc
Signalisation WebRTC pour le flux vidéo CSI → cockpit.

Ce module :
    - reçoit l'offre WebRTC du cockpit
    - crée un RTCPeerConnection
    - ajoute la caméra CSI (CameraTrack)
    - renvoie l'answer WebRTC
"""

import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from hardware.camera import CameraTrack


# Liste des PeerConnections pour nettoyage éventuel
pcs = set()


# ----------------------------------------------------------------------
#  Handler WebSocket /ws-rtc
# ----------------------------------------------------------------------
async def ws_rtc_handler(websocket):
    print("[WS-RTC] Client WebRTC connecté")

    pc = RTCPeerConnection()
    pcs.add(pc)

    # Ajouter la caméra CSI
    pc.addTransceiver("video", direction="sendonly")
    pc.addTrack(CameraTrack())

    try:
        async for msg in websocket:
            data = json.loads(msg)

            if data["type"] == "offer":
                offer = data["offer"]

                # Appliquer l'offre du cockpit
                await pc.setRemoteDescription(
                    RTCSessionDescription(
                        sdp=offer["sdp"],
                        type=offer["type"]
                    )
                )

                # Créer l'answer
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)

                # Envoyer l'answer au cockpit
                await websocket.send(json.dumps({
                    "type": "answer",
                    "answer": {
                        "sdp": pc.localDescription.sdp,
                        "type": pc.localDescription.type
                    }
                }))

    except Exception as e:
        print("[WS-RTC] ERREUR :", e)

    finally:
        await pc.close()
        pcs.discard(pc)
        print("[WS-RTC] Client WebRTC déconnecté")
