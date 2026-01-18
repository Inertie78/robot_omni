"""
app.py
------
Point d’entrée unique pour AxisOne.

Ce fichier lance :
    - le serveur HTTP (cockpit)
    - le serveur principal (WebSockets + UART + Radar + WebRTC + IA)

Usage :
    python3 app.py
"""

import threading
import asyncio

# Serveur HTTP cockpit
from web.http_server import start_http_server

# Serveur principal
from webSocket.server import start_ws_server
from hardware.uart import start_uart_thread
from hardware.radar_hcsr04 import start_radar


# ----------------------------------------------------------------------
#  Lancement du serveur HTTP dans un thread
# ----------------------------------------------------------------------
def start_http_thread():
    t = threading.Thread(target=start_http_server, daemon=True)
    t.start()
    print("[APP] Serveur HTTP lancé.")


# ----------------------------------------------------------------------
#  Lancement du serveur principal (WebSockets)
# ----------------------------------------------------------------------
def start_main_server():
    print("[APP] Serveur principal en cours de lancement…")
    asyncio.run(start_ws_server())


# ----------------------------------------------------------------------
#  MAIN
# ----------------------------------------------------------------------
def main():
    print("=== AXISONE APP (UN SEUL LANCEMENT) ===")

    # 1) Serveur HTTP cockpit
    start_http_thread()

    # 2) UART
    start_uart_thread()

    # 3) Radar
    start_radar()

    # 4) Serveur WebSockets (bloquant)
    start_main_server()


if __name__ == "__main__":
    main()
