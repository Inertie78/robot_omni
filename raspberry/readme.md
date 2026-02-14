# Robot Omni – Cockpit Web + IA TD3 + WebRTC

Robot omni-directionnel piloté en temps réel via un cockpit web, doté d’un pipeline vidéo WebRTC faible latence, d’un radar ultrason, d’une carte Mega pour les moteurs, et d’une IA TD3 capable d’apprendre en continu sur le robot réel.

## Sommaire

- Architecture globale
- Structure du projet
- Composants principaux
- Fonctionnement de l’IA
- Pipeline vidéo WebRTC
- Communication WebSocket
- Installation
- Lancement
- Tests rapides
- Conseils production

## Architecture globale

```
Cockpit (navigateur) <---- WebRTC ----> Raspberry Pi (server.py)
       |                                      |
       | WebSocket CTRL                       | UART
       | WebSocket ENC / RADAR                |
       v                                      v
Encodeurs / Radar -------------------------> Mega (moteurs)
```

## Structure du projet

```
robotOmni/
│
├── server/
│   ├── server.py
│   │
│   ├── ws/
│   │   ├── ws_router.py
│   │   ├── ws_ctrl.py
│   │   ├── ws_ai.py
│   │   ├── ws_ai_config.py
│   │   ├── ws_radar.py
│   │   ├── ws_enc.py
│   │   ├── ws_rtc.py
│   │
│   ├── ai/
│   │   ├── ai_loop.py
│   │   ├── robot_env.py
│   │   ├── agent_td3.py
│   │   ├── config.py
│   │
│   ├── hardware/
│   │   ├── uart.py
│   │   ├── radar_hcsr04.py
│   │   ├── radar.py
│   │   ├── camera.py
│   │
│   ├── web/
│   │   ├── http_server.py
│   │
│   ├── data/
│   │   ├── agent_td3_full.pth
│   │
│   ├── logs/
│       ├── train_steps.jsonl
│       ├── episodes.jsonl
│       ├── replay_ep_XXXXX.npz
│
├── www/
│   ├── index.html
│   ├── ia.html
│   ├── config.html
│   ├── pi.html
│   │
│   ├── css/
│   │   ├── cockpit.css
│   │
│   ├── js/
│       ├── index.js
│       ├── ia.js
│       ├── config.js
│       ├── pi.js
│
└── README.md
```

## Composants principaux

### 1. Cockpit Web (www/)
- Interface HTML/JS/CSS
- Commandes OMNI
- Affichage vidéo WebRTC
- Radar en temps réel
- Modes MANUAL / AI

### 2. Serveur Python (server.py)
- WebSockets :
  - /ws-ctrl : commandes cockpit → robot
  - /ws-enc : encodeurs → cockpit
  - /ws-radar : radar → cockpit
  - /ws-rtc : signalisation WebRTC
- WebRTC vidéo CSI
- UART vers Mega
- Radar ultrason (thread)
- IA TD3 (boucle RL temps réel)

### 3. Arduino Mega
- Reçoit : VEL vx vy w
- Gère les moteurs
- Envoie : ENC t1 t2 t3 t4 v1 v2 v3 v4

### 4. IA TD3
- agent_td3.py : réseau + replay buffer
- robot_env.py : environnement réel
- train_rl.py : apprentissage continu
- ai_loop.py : boucle IA 20 Hz

## Fonctionnement de l’IA

1. Le cockpit active MODE AI  
2. Le serveur lance une boucle :
   - observe l’état (radar, vitesse, commandes)
   - choisit une action
   - envoie OMNI
   - reçoit une récompense
   - apprend  
3. En cas de collision → reset  

L’agent apprend en continu, directement sur le robot réel.

## Pipeline vidéo WebRTC

```
libcamerasrc → videoconvert → appsink → aiortc → WebRTC → navigateur
```

Avantages :
- faible latence
- pas de buffering
- compatible navigateur

## Communication WebSocket

### /ws-ctrl
- OMNI vx vy w
- STOP
- MODE MANUAL
- MODE AI

### /ws-enc
- JSON encodeurs (ticks + vitesse)

### /ws-radar
- distance radar (20 Hz)

### /ws-rtc
- signalisation WebRTC (offer/answer)

## Installation

### 1. Dépendances système

```bash
sudo apt update
sudo apt install python3-opencv python3-pip python3-numpy \
                 gstreamer1.0-tools gstreamer1.0-plugins-base \
                 gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
                 gstreamer1.0-plugins-ugly gstreamer1.0-libav \
                 gstreamer1.0-webrtc libatlas-base-dev
```

### 2. Environnement Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install aiortc websockets av
```

### 3. Lier OpenCV système dans .venv

```bash
ln -s /usr/lib/python3/dist-packages/cv2*.so .venv/lib/python3.11/site-packages/
pip install "numpy<2"
```

## Lancement

```bash
source .venv/bin/activate
python3 server/server.py
```

Puis ouvrir :

http://<ip_du_pi>:8080

## Tests rapides

### Radar

```bash
python3 -c "import hardware.radar_hcsr04 as r; r.start_radar(); import time; 
           [print(r.distance_value) or time.sleep(0.1) for _ in range(20)]"
```

### UART

```bash
python3 -c "from hardware.uart import send_to_mega; send_to_mega('VEL 0 0 0')"
```

### WebRTC

Ouvrir index.html → la vidéo doit apparaître.

### IA

Dans le cockpit → MODE AI

## Conseils production

### Service systemd

Créer :

```bash
sudo nano /etc/systemd/system/robotomni.service
```

Contenu :

```
[Unit]
Description=Robot Omni Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/robotOmni/server/server.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Activer :

```bash
sudo systemctl enable robotomni
sudo systemctl start robotomni
```
