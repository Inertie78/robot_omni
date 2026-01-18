"""
ws_sys.py
---------
WebSocket /ws-sys
Envoie au cockpit les informations système du Raspberry Pi.

Données envoyées :
{
    "cpu": <float>,          # %
    "ram": <float>,          # %
    "temp": <float>,         # °C
    "uptime": <float>,       # secondes
    "ip": "<string>"
}

Fréquence : 1 Hz
"""

import json
import asyncio
import psutil
import socket
import time
import subprocess


def get_ip():
    """Retourne l'adresse IP locale."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"


# ----------------------------------------------------------------------
#  Handler WebSocket /ws-sys
# ----------------------------------------------------------------------
async def ws_sys_handler(websocket):
    print("[WS-SYS] Client connecté")

    try:
        while True:
            cpu_load = psutil.cpu_percent()
            ram = psutil.virtual_memory()
            uptime = time.time() - psutil.boot_time()
            disk = psutil.disk_usage("/")
            ip = get_ip()

            msg = json.dumps({
                "cpu_temp": get_cpu_temp(),
                "cpu_load": cpu_load,
                "ram_used": ram.used,
                "ram_total": ram.total,
                "disk_used": disk.used,
                "disk_total": disk.total,
                "uptime": uptime,
                "wifi_rssi": get_wifi_signal(),
                "ip": ip,
            })

            await websocket.send(msg)
            await asyncio.sleep(1.0)  # 1 Hz

    except Exception as e:
        print("[WS-SYS] ERREUR :", e)

    finally:
        print("[WS-SYS] Client déconnecté")

def get_wifi_signal():
    try:
        out = subprocess.check_output(["iwconfig", "wlan0"], stderr=subprocess.STDOUT).decode()
        for line in out.split("\n"):
            if "Signal level" in line:
                # Exemple : "Link Quality=70/70  Signal level=-40 dBm"
                parts = line.split("Signal level=")
                if len(parts) > 1:
                    level = parts[1].split(" ")[0]
                    return int(level.replace("dBm", ""))
    except:
        pass
    return None

def get_cpu_temp():
    temps = psutil.sensors_temperatures()

    # Cherche une clé contenant "cpu" ou "thermal"
    for key, entries in temps.items():
        if "cpu" in key.lower() or "thermal" in key.lower():
            if len(entries) > 0:
                return entries[0].current

    # Fallback : lecture directe du fichier système
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read()) / 1000.0
    except:
        return 0.0
