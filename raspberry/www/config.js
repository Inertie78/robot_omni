// ======================================================================
//  CONFIGURATION IA – WebSocket + UI dynamique
// ======================================================================

// WebSocket vers le serveur
const cfgWs = new WebSocket("ws://" + location.hostname + ":8765/ws-ai-config");

cfgWs.onopen = () => console.log("[CONFIG] WebSocket connecté");
cfgWs.onclose = () => console.log("[CONFIG] WebSocket fermé");

cfgWs.onmessage = (ev) => {
    const data = JSON.parse(ev.data);
    console.log("[CONFIG] Confirmation serveur :", data);

    const dbg = document.getElementById("configDebug");
    dbg.textContent = JSON.stringify(data, null, 2);
};


// ======================================================================
//  Liste des paramètres (mappage HTML → config.py)
// ======================================================================
const CONFIG_FIELDS = {
    // TD3 – Exploration
    noise_scale: "cfg_noise_scale",
    policy_noise: "cfg_policy_noise",
    noise_clip: "cfg_noise_clip",

    // TD3 – Learning
    gamma: "cfg_gamma",
    lr_actor: "cfg_lr_actor",
    lr_critic: "cfg_lr_critic",
    tau: "cfg_tau",
    policy_delay: "cfg_policy_delay",
    batch_size: "cfg_batch_size",

    // Robot
    max_speed_linear: "cfg_max_speed_linear",
    max_speed_angular: "cfg_max_speed_angular",

    // Reward shaping
    reward_distance_weight: "cfg_reward_distance_weight",
    reward_speed_weight: "cfg_reward_speed_weight",
    reward_collision_penalty: "cfg_reward_collision_penalty",

    // Radar
    radar_alpha: "cfg_radar_alpha",
    radar_median_window: "cfg_radar_median_window",
    danger_threshold_cm: "cfg_danger_threshold_cm",

    // Debug / Training
    enable_replay_logging: "cfg_enable_replay_logging",
    enable_loss_logging: "cfg_enable_loss_logging",
    train_frequency_hz: "cfg_train_frequency_hz",
};


// ======================================================================
//  Chargement des valeurs par défaut depuis le serveur
// ======================================================================
cfgWs.onopen = () => {
    console.log("[CONFIG] WS ouvert, demande des valeurs actuelles");
    cfgWs.send(JSON.stringify({ cmd: "GET_CONFIG" }));
};

cfgWs.onmessage = (ev) => {
    const data = JSON.parse(ev.data);

    if (data.type === "CONFIG_FULL") {
        console.log("[CONFIG] Configuration reçue :", data.config);
        loadConfigIntoUI(data.config);
    }

    const dbg = document.getElementById("configDebug");
    dbg.textContent = JSON.stringify(data, null, 2);
};


// ======================================================================
//  Injecter les valeurs dans l’UI
// ======================================================================
function loadConfigIntoUI(cfg) {
    for (const key in CONFIG_FIELDS) {
        const id = CONFIG_FIELDS[key];
        const el = document.getElementById(id);
        const valEl = document.getElementById("val_" + id.replace("cfg_", ""));

        if (!el) continue;

        if (el.type === "checkbox") {
            el.checked = !!cfg[key];
        } else {
            el.value = cfg[key];
            if (valEl) valEl.textContent = cfg[key];
        }
    }
}


// ======================================================================
//  Mise à jour dynamique des valeurs affichées
// ======================================================================
for (const key in CONFIG_FIELDS) {
    const id = CONFIG_FIELDS[key];
    const el = document.getElementById(id);
    const valEl = document.getElementById("val_" + id.replace("cfg_", ""));

    if (!el) continue;

    el.addEventListener("input", () => {
        if (el.type === "checkbox") {
            // rien à afficher
        } else if (valEl) {
            valEl.textContent = el.value;
        }
    });
}


// ======================================================================
//  Récupérer la configuration depuis l’UI
// ======================================================================
function collectConfig() {
    const cfg = {};

    for (const key in CONFIG_FIELDS) {
        const id = CONFIG_FIELDS[key];
        const el = document.getElementById(id);

        if (!el) continue;

        if (el.type === "checkbox") {
            cfg[key] = el.checked;
        } else {
            const v = parseFloat(el.value);
            cfg[key] = isNaN(v) ? el.value : v;
        }
    }

    return cfg;
}


// ======================================================================
//  Envoi de la configuration au serveur
// ======================================================================
function sendConfig() {
    const cfg = collectConfig();

    cfgWs.send(JSON.stringify({
        cmd: "SET_CONFIG",
        config: cfg
    }));

    console.log("[CONFIG] Envoyé :", cfg);

    const dbg = document.getElementById("configDebug");
    dbg.textContent = JSON.stringify(cfg, null, 2);
}


// ======================================================================
//  Reset vers valeurs par défaut (côté serveur)
// ======================================================================
function resetConfig() {
    cfgWs.send(JSON.stringify({ cmd: "RESET_CONFIG" }));
    console.log("[CONFIG] Reset demandé");
}
