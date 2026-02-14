// -------------------------------------------------------------
//  IA – WebSocket + stats + debug (/ws-ai)
// -------------------------------------------------------------
const aiWs = new WebSocket("ws://" + location.hostname + ":8765/ws-ai");
const aiDisplay = document.getElementById("aiDisplay");
const aiDebugEl = document.getElementById("aiDebug");

aiWs.onopen = () => console.log("IA WS connected");
aiWs.onclose = () => console.log("IA WS closed");

// Historiques pour les graphiques
const episodeRewardHistory = [];
const rewardHistory = [];
const criticLossHistory = [];
const actorLossHistory = [];
const maxHistory = 200;

let iaDebug = false;

// -------------------------------------------------------------
//  Utilitaire HUD
// -------------------------------------------------------------
function setHudValue(id, value, digits = 2) {
    const el = document.getElementById(id);
    if (!el) return;

    if (typeof value === "number" && !isNaN(value)) {
        el.textContent = value.toFixed(digits);
    } else if (value !== undefined && value !== null) {
        el.textContent = value;
    } else {
        el.textContent = "--";
    }
}

function toggleIADebug() {
    iaDebug = !iaDebug;
    aiDebugEl.style.display = iaDebug ? "block" : "none";
    console.log("DEBUG IA " + (iaDebug ? "ON" : "OFF"));
}

// -------------------------------------------------------------
//  Réception WebSocket IA
// -------------------------------------------------------------
aiWs.onmessage = (ev) => {
    const data = JSON.parse(ev.data);

    const {
        action_vx,
        action_vy,
        action_w,
        reward,
        steps_updates,
        speed_x,
        speed_y,
        distance,
        critic_loss,
        actor_loss,
        episode
    } = data;

    // ------- HUD principal (🤖 IA – Apprentissage) -------
    setHudValue("hud_vx", action_vx);
    setHudValue("hud_vy", action_vy);
    setHudValue("hud_w", action_w);

    setHudValue("hud_reward", reward, 3);
    setHudValue("hud_dist", distance, 1);
    setHudValue("hud_steps", steps_updates, 0);

    setHudValue("hud_sx", speed_x);
    setHudValue("hud_sy", speed_y);

    setHudValue("hud_closs", critic_loss, 4);
    setHudValue("hud_aloss", actor_loss, 4);

    // ------- HUD TD3 Live (🧠 IA – TD3 Live) -------
    setHudValue("ia_vx", action_vx);
    setHudValue("ia_vy", action_vy);
    setHudValue("ia_w", action_w);

    setHudValue("ia_reward", reward, 3);
    setHudValue("ia_critic", critic_loss, 4);
    setHudValue("ia_actor", actor_loss, 4);

    setHudValue("ia_dist", distance, 1);
    setHudValue("ia_sx", speed_x);
    setHudValue("ia_sy", speed_y);

    setHudValue("ia_step", steps_updates, 0);
    setHudValue("ia_updates", steps_updates, 0);
    setHudValue("ia_episode", episode ?? "--");

    // ------- Historiques pour graphes -------
    if (typeof reward === "number" && !isNaN(reward)) {
        rewardHistory.push(reward);
        if (rewardHistory.length > maxHistory) rewardHistory.shift();
    }

    if (typeof critic_loss === "number" && !isNaN(critic_loss)) {
        criticLossHistory.push(critic_loss);
        if (criticLossHistory.length > maxHistory) criticLossHistory.shift();
    }

    if (typeof actor_loss === "number" && !isNaN(actor_loss)) {
        actorLossHistory.push(actor_loss);
        if (actorLossHistory.length > maxHistory) actorLossHistory.shift();
    }

    // Reward par épisode (si l’info d’épisode est présente)
    if (typeof episode === "number" && typeof reward === "number" && !isNaN(reward)) {
        episodeRewardHistory[episode] = reward;
    }

    drawRewardGraph();
    drawLossGraph();
    drawEpisodeRewardGraph();

    // ------- Debug brut -------
    if (iaDebug) {
        aiDebugEl.textContent = JSON.stringify(data, null, 2);
    }
};

// -------------------------------------------------------------
//  Graphiques IA (Reward + Losses TD3 + Reward par épisode)
// -------------------------------------------------------------
const rewardCanvas = document.getElementById("rewardCanvas");
const lossCanvas = document.getElementById("lossCanvas");
const episodeCanvas = document.getElementById("episodeRewardCanvas");

const rwctx = rewardCanvas ? rewardCanvas.getContext("2d") : null;
const losctx = lossCanvas ? lossCanvas.getContext("2d") : null;
const epctx = episodeCanvas ? episodeCanvas.getContext("2d") : null;


function smooth(data, window = 5) {
    if (data.length < window) return data;

    const smoothed = [];
    for (let i = 0; i < data.length; i++) {
        const start = Math.max(0, i - window + 1);
        const slice = data.slice(start, i + 1);
        const avg = slice.reduce((a, b) => a + b, 0) / slice.length;
        smoothed.push(avg);
    }
    return smoothed;
}


// Fonction générique de tracé
function drawLine(ctx, data, color, minY, maxY) {
    if (!ctx || data.length < 2) return;

    const w = ctx.canvas.width;
    const h = ctx.canvas.height;

    const n = data.length;
    const dx = w / (n - 1);

    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;

    data.forEach((v, i) => {
        const x = i * dx;
        const t = (v - minY) / (maxY - minY || 1);
        const y = h - t * h;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.stroke();
}


// Reward Graph (step-by-step)
function drawRewardGraph() {
    if (!rwctx || rewardHistory.length < 2) return;

    let minR = Math.min(...rewardHistory, -1);
    let maxR = Math.max(...rewardHistory, 1);
    if (minR === maxR) { minR -= 1; maxR += 1; }

    rwctx.clearRect(0, 0, rewardCanvas.width, rewardCanvas.height);
    drawLine(rwctx, smooth(rewardHistory, 5), "#0f0", minR, maxR);
}

// Loss Graph (Critic + Actor)
function drawLossGraph() {
    if (!losctx) return;

    const allLosses = [...criticLossHistory, ...actorLossHistory];
    if (allLosses.length < 2) return;

    const w = lossCanvas.width;
    const h = lossCanvas.height;
    losctx.clearRect(0, 0, w, h);

    let minL = Math.min(...allLosses);
    let maxL = Math.max(...allLosses);
    if (minL === maxL) { minL -= 0.01; maxL += 0.01; }

    // Critic Loss (bleu)
    drawLine(losctx, smooth(criticLossHistory, 5), "#00aaff", minL, maxL);

    // Actor Loss (rose)
    drawLine(losctx, smooth(actorLossHistory, 5), "#ff66cc", minL, maxL);
}

// Reward par épisode
function drawEpisodeRewardGraph() {
    if (!epctx) return;

    const data = episodeRewardHistory.filter(v => v !== undefined);
    if (data.length < 2) return;

    const minR = Math.min(...data);
    const maxR = Math.max(...data);

    epctx.clearRect(0, 0, episodeCanvas.width, episodeCanvas.height);
    drawLine(epctx, smooth(data, 3), "#00ffaa", minR, maxR);
}

// -------------------------------------------------------------
//  Commandes SAVE / LOAD envoyées au serveur
// -------------------------------------------------------------
function sendAICommand(cmd) {
    // À adapter : soit via ctrlWs (si exposé global), soit via un WS dédié.
    if (typeof sendRaw === "function") {
        sendRaw(cmd);
        console.log("AI CMD:", cmd);
    } else {
        console.warn("sendRaw non disponible pour envoyer :", cmd);
    }
}

function saveAI() {
    sendAICommand("SAVE_AI");
}

function loadAI() {
    sendAICommand("LOAD_AI");
}
