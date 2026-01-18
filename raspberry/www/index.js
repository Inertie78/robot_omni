// -------------------------------------------------------------
//  VIDEO + LOG
// -------------------------------------------------------------
const video = document.getElementById("video");
const logEl = document.getElementById("log");

let currentVx = 0;
let currentVy = 0;
let currentW  = 0;
let omniActive = false;

let robotAngle = 0;          // angle absolu du robot (intégré à partir des commandes W)
let radarPoints = [];        // liste des points {x, y}
const maxRadarPoints = 500;  // limite mémoire

function log(msg) {
    if (!logEl) return;

    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    const ss = String(now.getSeconds()).padStart(2, "0");
    const time = `${hh}:${mm}:${ss}`;

    const line = `[${time}] ${msg}`;

    // Dernier message en haut
    if (logEl.textContent) {
        logEl.textContent = line + "\n" + logEl.textContent;
    } else {
        logEl.textContent = line;
    }
}

// Petit utilitaire générique pour HUD
function setText(id, value, digits = null) {
    const el = document.getElementById(id);
    if (!el) return;

    if (typeof value === "number" && digits !== null && !isNaN(value)) {
        el.textContent = value.toFixed(digits);
    } else if (value !== undefined && value !== null) {
        el.textContent = value;
    } else {
        el.textContent = "--";
    }
}

// -------------------------------------------------------------
//  ENCODEURS (/ws-enc)
// -------------------------------------------------------------
const encWs = new WebSocket("ws://" + location.hostname + ":8765/ws-enc");
const encDisplay = document.getElementById("encDisplay");

encWs.onopen = () => log("ENC WS connected");
encWs.onclose = () => log("ENC WS closed");

encWs.onmessage = (ev) => {
    const data = JSON.parse(ev.data);

    // Affichage brut (optionnel)
    if (encDisplay) {
        encDisplay.dataset.raw =
            `TICKS: ${data.ticks.join(" | ")} | SPEED: ${data.speed.map(v => v.toFixed(1)).join(" | ")}`;
    }

    // Mapping correct des données reçues
    const fl   = data.ticks[0];
    const fr   = data.ticks[1];
    const rear = data.ticks[2];

    const vx = data.speed[0];
    const vy = data.speed[1];
    const w  = data.speed[2];

    // HUD encodeurs (3 colonnes)
    setText("enc_fl",   fl,   0);
    setText("enc_fr",   fr,   0);
    setText("enc_rear", rear, 0);

    setText("enc_vx",   vx,   2);
    setText("enc_vy",   vy,   2);
    setText("enc_w",    w,    2);
};


// -------------------------------------------------------------
//  RADAR (/ws-radar) + Canvas radar
// -------------------------------------------------------------
const radarWs = new WebSocket("ws://" + location.hostname + ":8765/ws-radar");

const radarCanvas = document.getElementById("radarCanvas");
const rctx = radarCanvas.getContext("2d");

let radarDistance = 0;

radarWs.onopen = () => log("RADAR WS connected");
radarWs.onclose = () => log("RADAR WS closed");

// MAINTENANT : updateRadarDisplay utilise les spans radar_dist / radar_angle / radar_signal
function updateRadarDisplay(distanceCm, angleDeg, signalStrength) {
    if (typeof distanceCm === "number" && !isNaN(distanceCm)) {
        setText("radar_dist", distanceCm, 1);
    } else {
        setText("radar_dist", null);
    }

    if (typeof angleDeg === "number" && !isNaN(angleDeg)) {
        setText("radar_angle", angleDeg, 1);
    } else {
        setText("radar_angle", null);
    }

    if (typeof signalStrength === "number" && !isNaN(signalStrength)) {
        setText("radar_signal", signalStrength, 0);
    } else {
        setText("radar_signal", null);
    }

}

radarWs.onmessage = (ev) => {
    const data = JSON.parse(ev.data);
    // On suppose que le backend envoie { distance, signal } (ajuste si nécessaire)
    radarDistance = data.distance;

    // robotAngle est en radians → converti en degrés pour l’affichage
    const angleDeg = robotAngle * 180 / Math.PI;
    const signalStrength = data.signal_strength ?? data.signal ?? null;

    updateRadarDisplay(radarDistance, angleDeg, signalStrength);

    // Ajout du point radar sur la carte polaire
    if (radarDistance > 0 && radarDistance < 200) {
        const angle = robotAngle; // radians
        const d = radarDistance;

        const x = d * Math.cos(-angle);
        const y = d * Math.sin(-angle);

        radarPoints.push({ x, y });

        if (radarPoints.length > maxRadarPoints) {
            radarPoints.shift();
        }
    }
};

// Radar animé (sonar 360°)
function drawRadar360() {
    const w = radarCanvas.width;
    const h = radarCanvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const scale = 1.2; // pixels par cm

    rctx.clearRect(0, 0, w, h);

    // Cercle extérieur
    rctx.strokeStyle = "#0f3";
    rctx.lineWidth = 2;
    rctx.beginPath();
    rctx.arc(cx, cy, 200 * scale, 0, Math.PI * 2);
    rctx.stroke();

    // Points radar
    for (const p of radarPoints) {
        const px = cx + p.x * scale;
        const py = cy + p.y * scale;

        rctx.beginPath();
        rctx.arc(px, py, 3, 0, Math.PI * 2);
        rctx.fillStyle = "rgba(0,255,0,0.8)";
        rctx.fill();
    }

    // Orientation du robot
    rctx.beginPath();
    rctx.moveTo(cx, cy);
    rctx.lineTo(
        cx + 200 * scale * Math.cos(-robotAngle),
        cy + 200 * scale * Math.sin(-robotAngle)
    );
    rctx.strokeStyle = "yellow";
    rctx.lineWidth = 2;
    rctx.stroke();

    requestAnimationFrame(drawRadar360);
}

drawRadar360();

// -------------------------------------------------------------
//  COMMANDES ROBOT (/ws-ctrl)
// -------------------------------------------------------------
const ctrlWs = new WebSocket("ws://" + location.hostname + ":8765/ws-ctrl");

ctrlWs.onopen = () => log("CTRL WS connected");

ctrlWs.onclose = () => {
    log("CTRL WS closed");
    omniActive = false;
    currentVx = 0;
    currentVy = 0;
    currentW  = 0;

    try { ctrlWs.send("STOP"); } catch(e) {}
};

function sendRaw(cmd, logIt = true) {
    if (ctrlWs.readyState !== WebSocket.OPEN) return;
    if (logIt) log("SEND: " + cmd);
    ctrlWs.send(cmd);
}

function sendOmni(vx, vy, w) {
    currentVx = vx;
    currentVy = vy;
    currentW  = w;
    omniActive = true;

    sendRaw(`OMNI ${vx} ${vy} ${w}`);
}

function sendStop() {
    omniActive = false;
    currentVx = 0;
    currentVy = 0;
    currentW  = 0;
    sendRaw("STOP");
}

function setMode(mode) {
    sendRaw(`MODE ${mode}`);
}

// SAVE / LOAD IA
function saveAI() {
    sendRaw("SAVE_AI");
    log("Commande cockpit: SAVE_AI");
}

function loadAI() {
    sendRaw("LOAD_AI");
    log("Commande cockpit: LOAD_AI");
}

// -------------------------------------------------------------
//  WEBRTC VIDEO (/ws-rtc)
// -------------------------------------------------------------
const rtcWs = new WebSocket("ws://" + location.hostname + ":8765/ws-rtc");
let pc = null;

rtcWs.onopen = async () => {
    log("RTC WS connected");
    await startWebRTC();
};

rtcWs.onclose = () => {
    log("RTC WS closed");
};

rtcWs.onmessage = async (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "answer") {
        await pc.setRemoteDescription(data.answer);
        log("Answer set");
    } else if (data.type === "candidate") {
        await pc.addIceCandidate(data.candidate);
    }
};

async function startWebRTC() {
    pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
    });

    pc.ontrack = (event) => {
        const stream = event.streams[0];
        video.srcObject = stream;
        video.play().catch(err => {
            console.error("video.play() failed:", err);
            log("video.play() failed: " + err);
        });
    };

    pc.onicecandidate = (event) => {
        if (event.candidate) {
            rtcWs.send(JSON.stringify({
                type: "candidate",
                candidate: event.candidate
            }));
        }
    };

    pc.addTransceiver("video", { direction: "recvonly" });

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    rtcWs.send(JSON.stringify({
        type: "offer",
        offer: {
            type: pc.localDescription.type,
            sdp: pc.localDescription.sdp
        }
    }));

    log("Offer sent");
}

// -------------------------------------------------------------
//  LOOP OMNI 20 Hz (maintien de la consigne + angle robot)
// -------------------------------------------------------------
setInterval(() => {
    if (omniActive && ctrlWs.readyState === WebSocket.OPEN) {
        sendRaw(`OMNI ${currentVx} ${currentVy} ${currentW}`, false);
    }
    // Intégration grossière de l’angle à partir de W (robotAngle en radians)
    robotAngle += currentW * 0.05; // dt = 0.05s
}, 50);

// -------------------------------------------------------------
//  INIT
// -------------------------------------------------------------
window.addEventListener("load", () => {
    console.log("Page loaded, connecting WebRTC...");
});
