# Drone Detection Dashboard

Real-time drone RF signal monitoring and threat assessment dashboard. Simulates a network of ground-based sensors detecting drone radio frequencies, classifying drone types, and scoring threats against a protected zone.

Built as a portfolio project demonstrating a Raspberry Pi-based drone detection concept.

## Features

- **Multi-sensor network** — 4 simulated RF sensors around Syracuse, NY with distance-based signal strength modeling
- **Drone classification** — Identifies drone type (DJI Mavic 3, Autel EVO II, Skydio 2+, FPV racers, etc.) from RF fingerprint
- **Threat scoring** — Scores drones 0-100 based on proximity, loiter time, altitude, and speed patterns
- **Geofence alerts** — Real-time notifications when drones breach a protected zone
- **Live map** — Leaflet map with color-coded drone tracks, sensor range circles, and geofence overlay
- **WebSocket streaming** — All data pushed to the browser in real-time
- **REST API** — Query detection history, sensor status, and statistics
- **Dark theme UI** — Clean, professional dashboard interface

## Tech Stack

- **Backend:** Python, FastAPI, WebSockets, SQLite (aiosqlite)
- **Frontend:** Vanilla JS, Bootstrap 5, Leaflet.js
- **Simulation:** Realistic RF signal modeling with free-space path loss, random-walk flight paths, probabilistic drone spawning

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser. The simulation starts automatically — drones will begin spawning within a few seconds.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/detections` | Paginated detection history (supports `limit`, `offset`, `sensor_id`, `drone_type`, `min_threat` filters) |
| GET | `/api/alerts` | Recent geofence breach alerts |
| GET | `/api/sensors` | Sensor network configuration and live status |
| GET | `/api/stats` | Summary statistics (total detections, unique drones, alerts) |
| GET | `/api/drone-profiles` | Known drone RF signature library |
| WS | `/ws` | WebSocket stream of live detections, alerts, and drone tracks |

## Simulated Drone Profiles

| Drone | Frequency | Protocol |
|-------|-----------|----------|
| DJI Mavic 3 | 2.4 GHz | OcuSync 3.0 |
| DJI Mini 4 Pro | 2.4 GHz | OcuSync 4.0 |
| Autel EVO II | 5.8 GHz | Autel Link |
| Skydio 2+ | 5.2 GHz | Skydio Link |
| FPV Racing Drone | 5.8 GHz | Analog VTX |
| Unknown UAV | 900 MHz | Unknown |

## Project Structure

```
├── app.py                  # FastAPI entry point
├── config.py               # Configuration constants
├── models.py               # Pydantic data models
├── database.py             # SQLite persistence
├── simulation/
│   ├── drone_profiles.py   # Known drone RF fingerprints
│   ├── engine.py           # Simulation tick loop
│   └── flight_path.py      # Flight path generation
├── detection/
│   ├── classifier.py       # RF signature classification
│   └── threat.py           # Threat scoring engine
├── routers/
│   ├── api.py              # REST API endpoints
│   └── ws.py               # WebSocket endpoint
└── frontend/
    ├── index.html           # Dashboard UI
    ├── style.css            # Dark theme styles
    └── app.js               # WebSocket client + map rendering
```

## Live Demo

**[https://web-production-6e2519.up.railway.app](https://web-production-6e2519.up.railway.app)**

## Deployment

Deployed on [Railway](https://railway.app). To deploy your own instance:

1. Fork this repo
2. Create a new project in Railway and connect the GitHub repo
3. Railway auto-detects Python, installs dependencies, and starts with the Procfile
