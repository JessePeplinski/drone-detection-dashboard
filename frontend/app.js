/* ========= CONFIG ========= */
const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = `${wsProto}//${window.location.host}/ws`;
const ZONE_CENTER = [43.0381, -76.1354];
const ZONE_RADIUS_M = 500;

/* ========= STATE ========= */
let ws;
let detectionCount = 0;
let activeDrones = {};       // drone_id -> { marker, polyline, color, type }
let sensorState = {};        // sensor_id -> last status data
let highestThreat = 'low';
const DRONE_COLORS = ['#e74c3c','#e67e22','#f1c40f','#2ecc71','#9b59b6','#3498db','#1abc9c','#e84393'];
let colorIndex = 0;

/* ========= HELPERS ========= */
const fmtTime = iso => {
  const d = new Date(iso);
  const ms = String(d.getMilliseconds()).padStart(3, '0');
  return d.toLocaleTimeString([], { hour12: false }) + '.' + ms;
};

const threatClass = level => `threat-badge threat-${level}`;

const THREAT_ORDER = { low: 0, medium: 1, high: 2, critical: 3 };

function getDroneColor(droneId) {
  if (!activeDrones[droneId]) return DRONE_COLORS[0];
  return activeDrones[droneId].color;
}

function assignDroneColor(droneId) {
  const color = DRONE_COLORS[colorIndex % DRONE_COLORS.length];
  colorIndex++;
  return color;
}

/* ========= MAP SETUP ========= */
const map = L.map('radarMap', { zoomControl: true }).setView(ZONE_CENTER, 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Geofence circle
L.circle(ZONE_CENTER, {
  radius: ZONE_RADIUS_M,
  color: '#f44336',
  fillColor: '#f44336',
  fillOpacity: 0.08,
  weight: 2,
  dashArray: '8, 4',
}).addTo(map).bindPopup('Protected Zone');

// Sensor markers + range circles
const SENSORS = [
  { id: 'sensor-001', name: 'Syracuse HQ Roof', lat: 43.0481, lon: -76.1474, range_km: 2.0 },
  { id: 'sensor-002', name: 'Eastwood Tower', lat: 43.0475, lon: -76.1100, range_km: 1.8 },
  { id: 'sensor-003', name: 'Lakeside Station', lat: 43.0700, lon: -76.1650, range_km: 2.2 },
  { id: 'sensor-004', name: 'University South', lat: 43.0300, lon: -76.1350, range_km: 1.5 },
];

SENSORS.forEach(s => {
  L.circleMarker([s.lat, s.lon], {
    radius: 8, color: '#3498db', fill: true, fillColor: '#3498db', fillOpacity: 0.9
  }).addTo(map).bindPopup(`<b>${s.name}</b><br>ID: ${s.id}<br>Range: ${s.range_km} km`);

  L.circle([s.lat, s.lon], {
    radius: s.range_km * 1000,
    color: '#3498db',
    fillColor: '#3498db',
    fillOpacity: 0.03,
    weight: 1,
    dashArray: '4, 4',
  }).addTo(map);
});

/* ========= SENSOR GRID ========= */
const sensorGrid = document.getElementById('sensorGrid');

function renderSensors() {
  sensorGrid.innerHTML = '';
  SENSORS.forEach(s => {
    const state = sensorState[s.id] || {
      status: 'online', signal_strength: 85, detections_last_min: 0, last_seen: ''
    };
    const barColor = state.signal_strength > 60 ? '#28a745' : state.signal_strength > 30 ? '#ffc107' : '#dc3545';
    sensorGrid.insertAdjacentHTML('beforeend', `
      <div class="col-12 col-md-6 col-lg-3">
        <div class="sensor-card ${state.status}">
          <h6>${s.name}</h6>
          <p><strong>ID:</strong> ${s.id}</p>
          <p><strong>Status:</strong> <span class="text-${state.status === 'online' ? 'success' : 'danger'}">${state.status}</span></p>
          <p><strong>Signal:</strong> ${state.signal_strength}%</p>
          <div class="signal-bar">
            <div class="signal-bar-fill" style="width:${state.signal_strength}%;background:${barColor}"></div>
          </div>
          <p class="mt-1"><strong>Detections/min:</strong> ${state.detections_last_min}</p>
          ${state.last_seen ? `<p><strong>Last seen:</strong> ${fmtTime(state.last_seen)}</p>` : ''}
        </div>
      </div>`);
  });
}

/* ========= DETECTION TABLE ========= */
const tableBody = document.querySelector('#detectionTable tbody');

function addDetectionRow(det) {
  const row = document.createElement('tr');
  row.innerHTML = `
    <td>${fmtTime(det.timestamp)}</td>
    <td>${det.sensor_id}</td>
    <td>${det.drone_type}</td>
    <td>${det.frequency_ghz}</td>
    <td>${det.rssi_dbm}</td>
    <td>${det.altitude_m}</td>
    <td>${(det.confidence * 100).toFixed(0)}%</td>
    <td><span class="${threatClass(det.threat_level)}">${det.threat_level}</span></td>
    <td>${det.distance_to_zone_km}</td>`;
  tableBody.prepend(row);
  if (tableBody.rows.length > 200) tableBody.deleteRow(-1);
}

/* ========= STATUS BAR ========= */
const statDrones = document.getElementById('statDrones');
const statDetections = document.getElementById('statDetections');
const statThreat = document.getElementById('statThreat');

function updateStats(threatLevel) {
  statDrones.textContent = Object.keys(activeDrones).length;
  statDetections.textContent = detectionCount;

  if (THREAT_ORDER[threatLevel] > THREAT_ORDER[highestThreat]) {
    highestThreat = threatLevel;
  }
  statThreat.innerHTML = `<span class="${threatClass(highestThreat)}">${highestThreat}</span>`;

  // Reset highest threat every 30s
  clearTimeout(window._threatResetTimer);
  window._threatResetTimer = setTimeout(() => { highestThreat = 'low'; }, 30000);
}

/* ========= ALERTS ========= */
const alertContainer = document.getElementById('alertContainer');

function showAlert(alert) {
  const el = document.createElement('div');
  el.className = 'alert-toast';
  el.innerHTML = `
    <button class="close-btn" onclick="this.parentElement.remove()">&times;</button>
    <h6>ALERT: ${alert.alert_type.replace('_', ' ').toUpperCase()}</h6>
    <p>${alert.message}</p>
    <small style="color:#888">${fmtTime(alert.timestamp)} — Threat: ${alert.threat_score}</small>`;
  alertContainer.prepend(el);

  // Auto-dismiss after 10s
  setTimeout(() => el.remove(), 10000);

  // Keep max 5 alerts visible
  while (alertContainer.children.length > 5) {
    alertContainer.lastElementChild.remove();
  }
}

/* ========= MAP: DRONE TRACKS ========= */
function updateDroneOnMap(data) {
  const { drone_id, drone_type, positions, lat, lon, active } = data;

  if (!active) {
    // Drone despawned — remove from map
    if (activeDrones[drone_id]) {
      map.removeLayer(activeDrones[drone_id].marker);
      map.removeLayer(activeDrones[drone_id].polyline);
      delete activeDrones[drone_id];
    }
    return;
  }

  if (!activeDrones[drone_id]) {
    const color = assignDroneColor(drone_id);
    const marker = L.circleMarker([lat, lon], {
      radius: 7, color: color, fillColor: color, fillOpacity: 0.9
    }).addTo(map).bindPopup(`<b>${drone_type}</b><br>ID: ${drone_id}`);

    const polyline = L.polyline(positions, { color: color, weight: 2, opacity: 0.7 }).addTo(map);

    activeDrones[drone_id] = { marker, polyline, color, type: drone_type };
  } else {
    const d = activeDrones[drone_id];
    d.marker.setLatLng([lat, lon]);
    d.polyline.setLatLngs(positions);
  }
}

/* ========= WEBSOCKET ========= */
const wsStatusEl = document.getElementById('wsStatus');

function setWsStatus(connected) {
  wsStatusEl.innerHTML = connected
    ? '<span class="ws-dot connected"></span><span>Live</span>'
    : '<span class="ws-dot disconnected"></span><span>Disconnected</span>';
}

function connect() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => setWsStatus(true);

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    switch (msg.type) {
      case 'detection':
        detectionCount++;
        addDetectionRow(msg.data);
        updateStats(msg.data.threat_level);
        break;
      case 'sensor_status':
        sensorState[msg.data.sensor_id] = msg.data;
        renderSensors();
        break;
      case 'alert':
        showAlert(msg.data);
        break;
      case 'drone_track':
        updateDroneOnMap(msg.data);
        break;
    }
  };

  ws.onclose = () => {
    setWsStatus(false);
    setTimeout(connect, 2000);
  };

  ws.onerror = () => ws.close();
}

/* ========= INIT ========= */
renderSensors();
connect();
