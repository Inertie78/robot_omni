# ============================
# ARDUINO
# ============================

# ⚙️ RobotConfig — Configuration globale du robot (Arduino)

Le fichier `RobotConfig.h` centralise tous les paramètres globaux du robot à roues **Mecanum**.  
Toute modification impacte directement :

- la dynamique du robot  
- la stabilité du PID  
- la sécurité (watchdog)

---

## 🧭 Modes de contrôle

```cpp
enum ControlMode {
  MODE_MANUAL = 0,
  MODE_AI     = 1
};
```

### MODE_MANUAL

- Commande directe des moteurs (open-loop)
- Pas de régulation PID
- Utilisé pour : tests moteurs, calibration, debug

### MODE_AI

- Commande en boucle fermée (PID vitesse)
- Conversion omni → vitesses roues
- Utilisé pour : navigation autonome, mouvements précis

---

## ⚙️ Constantes générales

### PWM_MAX

```cpp
const int PWM_MAX = 200;
```

- Limite volontaire pour protéger les moteurs
- Plage matérielle : 0–255

### MAX_WHEEL_SPEED (ticks/s)

```cpp
const float MAX_WHEEL_SPEED = 500.0;
```

- Sert à normaliser vx, vy, w dans [-1 ; 1]
- Doit correspondre à la vitesse réelle mesurée

### WATCHDOG_TIMEOUT (ms)

```cpp
const unsigned long WATCHDOG_TIMEOUT = 500;
```

- Temps maximal sans commande venant du Raspberry Pi
- Déclenche un arrêt d’urgence

---

## 🎛️ Paramètres PID

### PID_FREQ

```cpp
const float PID_FREQ = 50.0; // Hz
```

### PID_PERIOD

```cpp
const unsigned long PID_PERIOD = 1000.0 / PID_FREQ;
```

### 🛠️ Méthode simple pour régler le PID

1. **Kp** uniquement
2. Ajouter **Kd** pour réduire les oscillations
3. Ajouter **Ki** très faible
4. Tester vitesses lentes/rapides et transitions brusques

---

## 📘 Architecture Arduino

### 🧱 Matériel

- Arduino Mega
- Motor Shield
- 4 moteurs DC + encodeurs

Communication série avec Raspberry Pi

---

## 🔁 Boucle principale Arduino

```cpp
loop():
 ├─ protocolUpdate()
 ├─ mecanumUpdateEncoders()
 ├─ mecanumUpdatePID()
 └─ protocolWatchdog()
```
Boucle non bloquante, temps réel, sécurisée.
---

## 📡 Protocole série

Commandes envoyées par la Raspberry Pi

```cpp
VEL vx vy w
MODE AI
PING
```

Réponses Arduino

```cpp
ENC ticks speeds
MODE AI
PONG
```

### 🛑 Sécurité

- Watchdog logiciel
- Arrêt automatique si perte de communication
- Libération immédiate des moteurs

---

## 🚀 Évolutions possibles

- Protocole binaire
- Odométrie (x, y, θ)
- Asservissement position
- ROS / micro-ROS