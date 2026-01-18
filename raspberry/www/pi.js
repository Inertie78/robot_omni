const sysWs = new WebSocket("ws://" + location.hostname + ":8765/ws-sys");
const sysDisplay = document.getElementById("sysDisplay");

sysWs.onopen = () => {
    console.log("Connexion au WebSocket système ouverte.");
};

sysWs.onmessage = (ev) => {
    const d = JSON.parse(ev.data);

    // IP
    document.getElementById("sys-ip").textContent = d.ip;

    // Température
    document.getElementById("sys-temp").textContent = d.cpu_temp.toFixed(1) + " °C";
    document.getElementById("bar-temp").style.width = (d.cpu_temp / 85 * 100) + "%";

    // CPU
    document.getElementById("sys-cpu").textContent = d.cpu_load.toFixed(1) + " %";
    document.getElementById("bar-cpu").style.width = d.cpu_load + "%";

    // RAM
    const ramUsed = (d.ram_used / 1024 / 1024).toFixed(1);
    const ramTotal = (d.ram_total / 1024 / 1024).toFixed(1);
    document.getElementById("sys-ram").textContent = `${ramUsed} / ${ramTotal} MB`;
    document.getElementById("bar-ram").style.width = (ramUsed / ramTotal * 100) + "%";

    // Disque
    const diskUsed = (d.disk_used / 1024 / 1024 / 1024).toFixed(2);
    const diskTotal = (d.disk_total / 1024 / 1024 / 1024).toFixed(2);
    document.getElementById("sys-disk").textContent = `${diskUsed} / ${diskTotal} GB`;
    document.getElementById("bar-disk").style.width = (diskUsed / diskTotal * 100) + "%";

    // Uptime
    document.getElementById("sys-uptime").textContent = (d.uptime / 3600).toFixed(1) + " h";

    // WiFi
    const wifi = d.wifi_rssi !== null ? `${d.wifi_rssi} dBm` : "N/A";
    document.getElementById("sys-wifi").textContent = wifi;

    // WiFi bar (RSSI)
    let wifiPercent = 0;
    if (d.wifi_rssi > -50) wifiPercent = 100;
    else if (d.wifi_rssi > -60) wifiPercent = 80;
    else if (d.wifi_rssi > -70) wifiPercent = 60;
    else if (d.wifi_rssi > -80) wifiPercent = 40;
    else wifiPercent = 20;

    document.getElementById("bar-wifi").style.width = wifiPercent + "%";

    // WiFi status
    let wifiStatus = "🟢 Excellent";
    if (d.wifi_rssi < -75) wifiStatus = "🔴 Danger : très faible";
    else if (d.wifi_rssi < -65) wifiStatus = "🟡 Moyen";

    document.getElementById("wifi-status").textContent = wifiStatus;
};

// Reboot / Shutdown
function rebootPi() {
    if (confirm("Redémarrer le Raspberry Pi ?")) {
        sendRaw("REBOOT");
    }
}

function shutdownPi() {
    if (confirm("Éteindre le Raspberry Pi ?")) {
        sendRaw("SHUTDOWN");
    }
}
