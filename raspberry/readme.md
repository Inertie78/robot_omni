# ================================
# RASPBERRY PI
# ================================

# Robot Omni – Cockpit Web + IA + WebRTC

Architecture complète pour piloter un robot omni-directionnel via :

- Cockpit web (temps réel)
- Serveur Python sur Raspberry Pi
- Arduino Mega (moteurs + encodeurs)
- WebRTC faible latence
- Radar ultrason
- IA TD3/DQN en temps réel

---

## 🧱 Architecture globale

```cpp
Cockpit Web <---- WebRTC ----> Raspberry Pi (server.py)
|                               |
| WebSocket CTRL                | UART
| WebSocket ENC / RADAR         |
v                               v
Encodeurs / Radar -------------> Arduino Mega
```

---

## 📦 Structure du projet

```tree
robotOmni/
├── server/
│   ├── server.py
│   ├── ws/
│   ├── ai/
│   ├── hardware/
│   ├── web/
│   ├── data/
│   └── logs/
├── www/
│   ├── html/css/js
└── README.md
```
---

## 🧠 IA (TD3 / DQN)

Pipeline IA :

1. Cockpit active MODE AI  
2. Le serveur lance la boucle IA (20 Hz)  
3. Observe état (radar, vitesse, commandes)  
4. Choisit action  
5. Envoie OMNI  
6. Reçoit récompense  
7. Apprend en continu  

---

## 🎥 Pipeline vidéo WebRTC

```cpp
libcamerasrc → videoconvert → appsink → aiortc → WebRTC → navigateur
```


Avantages :
- faible latence  
- pas de buffering  
- compatible navigateur  

---

## 🔌 WebSockets

### /ws-ctrl  
- OMNI vx vy w  
- STOP  
- MODE MANUAL / MODE AI  

### /ws-enc  
- JSON encodeurs  

### /ws-radar  
- distance radar (20 Hz)

### /ws-rtc  
- signalisation WebRTC  

---

## 🛠️ Installation

### Dépendances système

```cpp
sudo apt update
sudo apt install python3-opencv python3-pip python3-numpy \
gstreamer1.0-tools gstreamer1.0-plugins-base \
gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
gstreamer1.0-plugins-ugly gstreamer1.0-libav \
gstreamer1.0-webrtc libatlas-base-dev
```

## Environnement Python

```cpp
python3 -m venv .venv
source .venv/bin/activate
pip install aiortc websockets av
```

## Lier OpenCV système

```cpp
ln -s /usr/lib/python3/dist-packages/cv2*.so .venv/lib/python3.11/site-packages/
pip install "numpy<2"
```

---

## ▶️ Lancement

```cpp
source .venv/bin/activate
python3 server.py
```

Cockpit :

```cpp
http://<ip_du_pi>:8080
```

---

# 🧪 Tests rapides

### Radar

```cpp
python3 -c "import hardware.radar_hcsr04 as r; r.start_radar(); import time;
[print(r.distance_value) or time.sleep(0.1) for _ in range(20)]"
```

### UART

```cpp
python3 -c "from hardware.uart  import send_to_mega; send_to_mega('VEL 0 0 0')"
```

### WebRTC
→ ouvrir index.html

### IA
→ MODE AI dans cockpit

---

# 🚀 Production (systemd)

Créer service :

```cpp
sudo nano /etc/systemd/system/axisone.service
```

Contenu :

```cpp
[Unit]
Description=AxisOne Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/AxisOne/server/server.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Activer :

```cpp
sudo systemctl enable axisone
sudo systemctl start axisone
```