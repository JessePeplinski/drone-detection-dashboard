"""Central configuration for the Drone Detection Dashboard."""

# Simulation
SIM_TICK_INTERVAL = 1.0          # seconds between simulation ticks
MAX_ACTIVE_DRONES = 3            # max simultaneous drones
DRONE_SPAWN_CHANCE = 0.15        # probability per tick of spawning a new drone
DRONE_DESPAWN_CHANCE = 0.02      # probability per tick a drone leaves

# Geography — protected zone center (Syracuse University campus)
ZONE_CENTER_LAT = 43.0381
ZONE_CENTER_LON = -76.1354
ZONE_RADIUS_KM = 0.5            # geofence radius

# Sensors
SENSORS = [
    {
        "sensor_id": "sensor-001",
        "name": "Syracuse HQ Roof",
        "lat": 43.0481,
        "lon": -76.1474,
        "range_km": 2.0,
    },
    {
        "sensor_id": "sensor-002",
        "name": "Eastwood Tower",
        "lat": 43.0475,
        "lon": -76.1100,
        "range_km": 1.8,
    },
    {
        "sensor_id": "sensor-003",
        "name": "Lakeside Station",
        "lat": 43.0700,
        "lon": -76.1650,
        "range_km": 2.2,
    },
    {
        "sensor_id": "sensor-004",
        "name": "University South",
        "lat": 43.0300,
        "lon": -76.1350,
        "range_km": 1.5,
    },
]

# Database
DB_PATH = "detections.db"

# Server
HOST = "0.0.0.0"
PORT = 8000
