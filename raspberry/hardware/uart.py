"""
uart.py
-------
Gestion UART Mega pour AxisOne (version PREMIUM factorisée).

Fonctions :
    - start_uart_thread() : lance un thread dédié à la lecture UART
    - send_to_mega(cmd)   : envoie une commande texte à la Mega
    - latest_enc          : dernière mesure encodeurs (ticks + vitesses)

Le thread UART :
    - lit /dev/serial1
    - parse les lignes ENC
    - met à jour latest_enc
    - diffuse vers ws_enc.broadcast_enc() via la boucle asyncio du serveur
"""

import serial
import threading
import asyncio
from ws.ws_enc import broadcast_enc


# ----------------------------------------------------------------------
#  Boucle asyncio principale (injectée par le serveur WebSocket)
# ----------------------------------------------------------------------
_event_loop = None


def set_event_loop(loop: asyncio.AbstractEventLoop):
    """
    Configure la boucle asyncio principale utilisée pour envoyer
    des messages WebSocket depuis le thread UART.
    """
    global _event_loop
    _event_loop = loop
    print("[UART] Boucle asyncio principale configurée.")


# ----------------------------------------------------------------------
#  Port UART
# ----------------------------------------------------------------------
try:
    ser = serial.Serial("/dev/serial1", 115200, timeout=1)
    print("[UART] Port /dev/serial1 ouvert")
except Exception as e:
    print("[UART] ERREUR ouverture UART :", e)
    ser = None


# ----------------------------------------------------------------------
#  Dernière mesure encodeurs
# ----------------------------------------------------------------------
latest_enc = {
    "ticks": [0, 0, 0, 0],
    "speed": [0.0, 0.0, 0.0, 0.0]
}


# ----------------------------------------------------------------------
#  Parsing ligne ENC
# ----------------------------------------------------------------------
def parse_enc_line(line: str):
    """
    Parse une ligne de type :
        ENC t1 t2 t3 t4 v1 v2 v3 v4
    """
    parts = line.strip().split()
    if len(parts) != 9 or parts[0] != "ENC":
        return None

    try:
        ticks = list(map(int, parts[1:5]))
        speed = list(map(float, parts[5:9]))
        return {"ticks": ticks, "speed": speed}
    except Exception:
        return None


# ----------------------------------------------------------------------
#  Thread UART
# ----------------------------------------------------------------------
def uart_reader():
    """
    Thread dédié à la lecture UART.
    - lit caractère par caractère
    - reconstruit les lignes
    - parse les lignes ENC
    - met à jour latest_enc
    - diffuse via broadcast_enc() dans la boucle asyncio du serveur
    """
    global _event_loop

    if ser is None:
        print("[UART] Impossible de lire : port non ouvert")
        return

    print("[UART] Thread UART démarré")

    buffer = ""

    while True:
        try:
            c = ser.read().decode(errors="ignore")
        except Exception:
            continue

        if not c:
            continue

        if c == "\n":
            line = buffer.strip()
            buffer = ""

            if line.startswith("ENC"):
                parsed = parse_enc_line(line)
                if parsed:
                    latest_enc.update(parsed)

                    # Diffusion vers WebSocket encodeurs (si boucle dispo)
                    if _event_loop is not None:
                        try:
                            asyncio.run_coroutine_threadsafe(
                                broadcast_enc(latest_enc),
                                _event_loop
                            )
                        except Exception as e:
                            print("[UART] ERREUR run_coroutine_threadsafe :", e)

            continue

        buffer += c


# ----------------------------------------------------------------------
#  Envoi vers la Mega
# ----------------------------------------------------------------------
def send_to_mega(cmd: str):
    """
    Envoie une commande texte à la Mega.
    Exemple :
        send_to_mega("VEL 0.2 -0.1 0.0")
    """
    if ser is None:
        print("[UART] ERREUR : port non ouvert")
        return

    try:
        ser.write((cmd + "\n").encode())
    except Exception as e:
        print("[UART] ERREUR envoi :", e)


# ----------------------------------------------------------------------
#  Démarrage du thread UART
# ----------------------------------------------------------------------
def start_uart_thread():
    """
    Lance le thread UART en mode daemon.
    """
    t = threading.Thread(target=uart_reader, daemon=True)
    t.start()
    print("[UART] Thread UART lancé")
