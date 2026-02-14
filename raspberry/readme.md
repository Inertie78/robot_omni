# Robot Omni – Cockpit Web + IA DQN + WebRTC

Ce projet fournit une architecture complète pour piloter un robot omni-directionnel via :
- un cockpit web (interface temps réel)
- un serveur Python sur Raspberry Pi
- une carte Mega (Arduino) pour les moteurs et encodeurs
- un flux vidéo WebRTC faible latence
- un radar ultrason
- une IA DQN capable d’apprendre en temps réel

Objectif : un robot pilotable, observé, sécurisé et apprenant.

# Architecture globale

Cockpit (navigateur) <---- WebRTC ----> Raspberry Pi (server.py)
       |                                      |
       | WebSocket CTRL                       | UART
       | WebSocket ENC / RADAR                |
       v                                      v
Encodeurs / Radar -------------------------> Mega (moteurs)



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


# Composants principaux

1. Cockpit Web (www/)
- Interface HTML/JS/CSS
- Boutons OMNI
- Affichage vidéo WebRTC
- Radar en temps réel
- Modes MANUAL / AI

2. Serveur Python (server.py)
- WebSocket :
  /ws-ctrl : commandes cockpit vers robot
  /ws-enc  : encodeurs vers cockpit
  /ws-radar : radar vers cockpit
  /ws-rtc : signalisation WebRTC
- WebRTC vidéo CSI
- UART vers Mega
- Radar ultrason (thread)
- IA DQN (boucle RL temps réel)

3. Arduino Mega
- Reçoit "VEL vx vy w"
- Gère les moteurs
- Envoie "ENC t1 t2 t3 t4 v1 v2 v3 v4"

4. IA DQN
- agent_dqn.py : réseau + replay buffer
- env_rl.py : environnement robot réel
- train_rl.py : boucle d’apprentissage

# Fonctionnement de l’IA

1. Le cockpit active MODE AI
2. Le serveur lance une boucle :
   - observe l’état (radar, vitesse, commandes)
   - choisit une action
   - envoie OMNI
   - reçoit une récompense
   - apprend
3. Si collision : reset

L’agent apprend en continu, sans simulation.

# Pipeline vidéo WebRTC

libcamerasrc -> videoconvert -> appsink -> aiortc -> WebRTC -> navigateur

Avantages :
- faible latence
- pas de buffering
- compatible navigateur

# Communication WebSocket

/ws-ctrl :
- OMNI vx vy w
- STOP
- MODE MANUAL
- MODE AI

/ws-enc :
- JSON encodeurs (ticks + speed)

/ws-radar :
- distance radar (20 Hz)

/ws-rtc :
- signalisation WebRTC (offer/answer)

# Installation

1. Dépendances système :

sudo apt update
sudo apt install python3-opencv python3-pip python3-numpy \
                 gstreamer1.0-tools gstreamer1.0-plugins-base \
                 gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
                 gstreamer1.0-plugins-ugly gstreamer1.0-libav \
                 gstreamer1.0-webrtc libatlas-base-dev

2. Environnement Python :

python3 -m venv .venv
source .venv/bin/activate
pip install aiortc websockets av

3. Lier OpenCV système dans .venv :

ln -s /usr/lib/python3/dist-packages/cv2*.so .venv/lib/python3.11/site-packages/
pip install "numpy<2"

# Lancement

source .venv/bin/activate
python3 server.py

Puis ouvrir dans un navigateur :
http://<ip_du_pi>:8080

# Tests rapides

Encodeurs :
ws://<ip>:8765/ws-enc

Radar :
ws://<ip>:8765/ws-radar

OMNI :
Utiliser les boutons du cockpit

IA :
Bouton MODE AI

# Dépannage

Video noire :
- vérifier pipeline GStreamer
- vérifier caméra CSI activée
- tester "libcamera-hello"

IA immobile :
- vérifier /ws-ctrl
- vérifier UART Mega
- vérifier que MODE AI est envoyé

Radar = -1 :
- vérifier câblage TRIG/ECHO
- vérifier alimentation 5V
- vérifier radar.start_radar()


Installation :
pip install -r requirements.txt



python3 server/web/http_server.py




🟩 2. DÉPENDANCES PYTHON
Créer un fichier :

Code
requirements.txt
Avec :

Code
aiortc
opencv-python
numpy
websockets
RPi.GPIO
av
torch
Installation :

Code
pip install -r requirements.txt
🟩 3. SERVICES À LANCER
🔧 1. Serveur HTTP (cockpit)
Code
python3 server/web/http_server.py
Accessible sur :

Code
http://<ip_du_pi>:8080
🔧 2. Serveur principal (WebSockets + IA + UART + Radar + WebRTC)
Code
python3 server/server.py
Ce serveur :

démarre UART

démarre radar

démarre WebRTC

démarre WebSockets

attend les commandes cockpit

🟩 4. FLUX COMPLET DE FONCTIONNEMENT
🟦 1. Le cockpit charge index.html
WebRTC → vidéo CSI

WebSocket /ws-ctrl → commandes

WebSocket /ws-radar → radar

WebSocket /ws-enc → encodeurs

🟦 2. Le cockpit IA charge ia.html
WebSocket /ws-ai → infos IA temps réel

WebSocket /ws-ai-config → paramètres IA

🟦 3. Le serveur reçoit MODE AI
ws_ctrl.py → start_ai()

ai_loop.py → boucle IA 20 Hz

train_rl.py → TD3 temps réel

robot_env.py → step()

ws_ai.py → diffusion cockpit

🟦 4. Le cockpit IA affiche :
distance

vitesse

reward

critic_loss

actor_loss

épisode

actions vx/vy/w

🟩 5. TESTS FINAUX
✔️ Test 1 — Radar
Code
python3 -c "import hardware.radar_hcsr04 as r; r.start_radar(); import time; 
           [print(r.distance_value) or time.sleep(0.1) for _ in range(20)]"
✔️ Test 2 — UART
Code
python3 -c "from hardware.uart import send_to_mega; send_to_mega('VEL 0 0 0')"
✔️ Test 3 — WebRTC
Ouvre index.html → vidéo doit apparaître.

✔️ Test 4 — IA
Dans cockpit → MODE AI → les graphes IA doivent bouger.

🟩 6. CONSEILS PRODUCTION
🔥 Démarrer automatiquement au boot
Créer un service systemd :

Code
sudo nano /etc/systemd/system/axisone.service
Contenu :

Code
[Unit]
Description=AxisOne Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/AxisOne/server/server.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
Activer :

Code
sudo systemctl enable axisone
sudo systemctl start axisone