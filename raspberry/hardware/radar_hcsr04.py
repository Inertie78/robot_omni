"""
radar_hcsr04.py
---------------
Module d’acquisition radar pour capteur ultrason HC‑SR04 sur Raspberry Pi.

Fonctionnalités :
- Lecture du capteur HC‑SR04 (TRIG/ECHO)
- Boucle radar 20 Hz dans un thread dédié
- Filtrage avancé : Médian + Filtre Exponentiel (EMA)
- Mise à jour continue de la variable globale distance_value
- Calcul d'un signal_strength (0–100%) basé sur la stabilité du signal

Version mise à jour pour architecture cockpit PREMIUM :
- alpha (EMA) réglable dynamiquement
- taille de la fenêtre médiane réglable dynamiquement
"""

import RPi.GPIO as GPIO
import time
import threading
import statistics
from collections import deque

# ---------------------------------------------------------------------------
#  CONFIGURATION GPIO
# ---------------------------------------------------------------------------

# Mode BCM = numérotation des broches GPIO
GPIO.setmode(GPIO.BCM)

# Broches du capteur HC‑SR04
TRIG = 23
ECHO = 24

# Configuration des broches
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# ---------------------------------------------------------------------------
#  VARIABLES GLOBALES
# ---------------------------------------------------------------------------

# Distance filtrée en cm (mise à jour en continu par le thread radar)
distance_value = 0.0

# Qualité du signal (0–100%)
signal_strength = 0

# Fenêtre pour le filtre médian (taille ajustable)
median_window = deque(maxlen=5)

# Fenêtre pour analyse de stabilité (variance)
quality_window = deque(maxlen=10)

# Paramètre du filtre exponentiel (EMA)
# alpha = 0.2–0.3 = très bon compromis stabilité / réactivité
alpha = 0.25

# Flag pour arrêter proprement si besoin (optionnel, pour futur)
_radar_running = False


# ---------------------------------------------------------------------------
#  Réglages dynamiques (pour config cockpit)
# ---------------------------------------------------------------------------
def set_alpha(value: float):
    """
    Définit dynamiquement le coefficient EMA (alpha).

    Args:
        value (float): 0 < alpha <= 1
    """
    global alpha
    try:
        v = float(value)
    except (TypeError, ValueError):
        return

    if v <= 0:
        v = 0.01
    if v > 1:
        v = 1.0

    alpha = v
    print(f"[RADAR] alpha EMA mis à jour : {alpha}")


def set_median_window_size(size: int):
    """
    Définit dynamiquement la taille de la fenêtre du filtre médian.

    Args:
        size (int): taille >= 1
    """
    global median_window
    try:
        n = int(size)
    except (TypeError, ValueError):
        return

    if n < 1:
        n = 1

    # On recrée une nouvelle deque en conservant les dernières valeurs
    old_values = list(median_window)[-n:]
    median_window = deque(old_values, maxlen=n)
    print(f"[RADAR] Fenêtre médiane mise à jour : {n} échantillons")


def compute_signal_strength(values):
    """
    Calcule un score de qualité (0–100%) basé sur la variance.
    Plus la variance est faible → meilleur signal.
    """
    if len(values) < 3:
        return 100  # pas assez de données → on considère bon

    var = statistics.pvariance(values)

    # Conversion variance → score 0–100 (ajustable)
    score = 100 - min(100, var * 2)

    return int(score)


# ---------------------------------------------------------------------------
#  MESURE BRUTE DU HC‑SR04
# ---------------------------------------------------------------------------
def measure_distance():
    """
    Mesure brute de distance via le capteur HC‑SR04.

    Fonctionnement :
    - Envoie une impulsion de 10 µs sur TRIG
    - Attend le front montant sur ECHO (début du signal)
    - Attend le front descendant sur ECHO (fin du signal)
    - Calcule la distance : distance = (temps * vitesse du son) / 2

    Returns:
        float : distance en centimètres
                -1 si timeout ou mesure invalide
    """

    # Assure que TRIG est bas avant l'impulsion
    GPIO.output(TRIG, False)
    time.sleep(0.0002)  # 200 µs

    # Impulsion de 10 µs sur TRIG
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10 µs
    GPIO.output(TRIG, False)

    # Attente du front montant (début du signal ECHO)
    start = time.time()
    timeout = start + 0.02  # timeout 20 ms
    while GPIO.input(ECHO) == 0:
        start = time.time()
        if start > timeout:
            return -1  # pas de front montant → erreur

    # Attente du front descendant (fin du signal ECHO)
    stop = time.time()
    timeout = stop + 0.02
    while GPIO.input(ECHO) == 1:
        stop = time.time()
        if stop > timeout:
            return -1  # pas de front descendant → erreur

    # Durée du signal ECHO
    elapsed = stop - start

    # Distance en cm (vitesse du son ≈ 34300 cm/s)
    distance = (elapsed * 34300) / 2
    return distance


# ---------------------------------------------------------------------------
#  BOUCLE RADAR AVEC FILTRAGE AVANCÉ
# ---------------------------------------------------------------------------
def radar_loop():
    """
    Boucle d’acquisition radar exécutée dans un thread dédié.

    Pipeline de traitement :
    1. Mesure brute via measure_distance()
    2. Filtre médian (supprime les valeurs aberrantes)
    3. Filtre exponentiel EMA (lissage fluide et réactif)
    4. Mise à jour de distance_value + signal_strength

    Fréquence : 20 Hz (toutes les 50 ms)
    """
    global distance_value, signal_strength, _radar_running

    _radar_running = True
    print("[RADAR] Boucle radar démarrée (20 Hz)")

    while _radar_running:
        try:
            d = measure_distance()

            if d > 0:
                # 1) Ajout dans la fenêtre du filtre médian
                median_window.append(d)

                # 2) Calcul du médian (anti-bruit)
                median_val = statistics.median(median_window)

                # 3) Filtre exponentiel EMA
                distance_value = alpha * median_val + (1 - alpha) * distance_value

                # 4) Mise à jour de la fenêtre qualité
                quality_window.append(median_val)

                # 5) Calcul du signal_strength
                signal_strength = compute_signal_strength(quality_window)

            else:
                # Mesure invalide
                distance_value = -1
                signal_strength = 0

        except Exception as e:
            # En cas d’erreur imprévue
            print(f"[RADAR] ERREUR dans radar_loop : {e}")
            distance_value = -1
            signal_strength = 0

        # 20 Hz
        time.sleep(0.05)

    print("[RADAR] Boucle radar arrêtée")


# ---------------------------------------------------------------------------
#  DÉMARRAGE / ARRÊT DU THREAD RADAR
# ---------------------------------------------------------------------------
def start_radar():
    """
    Démarre le thread radar en mode daemon.

    Le thread mettra à jour distance_value en continu.
    """
    t = threading.Thread(target=radar_loop, daemon=True)
    t.start()
    return t


def stop_radar():
    """
    Permet d'arrêter proprement la boucle radar si besoin.
    (non utilisée actuellement, mais prête pour le futur)
    """
    global _radar_running
    _radar_running = False
