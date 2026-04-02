"""Main simulation engine — spawns drones, moves them, generates detections."""

from __future__ import annotations

import asyncio
import math
import random
import uuid
from datetime import datetime

from config import (
    MAX_ACTIVE_DRONES,
    DRONE_SPAWN_CHANCE,
    DRONE_DESPAWN_CHANCE,
    SIM_TICK_INTERVAL,
    SENSORS,
    ZONE_CENTER_LAT,
    ZONE_CENTER_LON,
    ZONE_RADIUS_KM,
)
from models import SimulatedDrone, Detection, Alert, SensorConfig
from simulation.drone_profiles import DRONE_PROFILES
from simulation.flight_path import update_position, haversine_km
from detection.classifier import classify
from detection.threat import assess, clear_drone
from routers.ws import broadcast
import database


class SimulationEngine:
    def __init__(self):
        self.drones: dict[str, SimulatedDrone] = {}
        self.sensors = [SensorConfig(**s) for s in SENSORS]
        self.tick_count = 0
        self._alerted_drones: dict[str, float] = {}  # drone_id -> last alert time

    async def run(self):
        while True:
            try:
                await self.tick()
            except Exception as e:
                print(f"Simulation error: {e}")
            await asyncio.sleep(SIM_TICK_INTERVAL)

    async def tick(self):
        self.tick_count += 1
        now = datetime.utcnow()
        now_iso = now.isoformat() + "Z"

        # Spawn new drones
        if len(self.drones) < MAX_ACTIVE_DRONES and random.random() < DRONE_SPAWN_CHANCE:
            self._spawn_drone(now)

        # Move all drones
        for drone in list(self.drones.values()):
            update_position(drone)

        # Generate detections for each drone-sensor pair
        all_detections: list[Detection] = []
        all_alerts: list[Alert] = []

        for drone in list(self.drones.values()):
            for sensor in self.sensors:
                dist = haversine_km(drone.lat, drone.lon, sensor.lat, sensor.lon)
                if dist > sensor.range_km:
                    continue

                # RSSI from free-space path loss (simplified)
                dist_m = max(dist * 1000, 1)
                rssi = -30 - 20 * math.log10(dist_m)
                rssi += random.gauss(0, 3)
                rssi = round(max(-100, min(-20, rssi)), 1)

                # Confidence from signal strength
                confidence = min(0.98, max(0.55, (rssi + 100) / 80 + random.uniform(-0.05, 0.05)))

                # Add noise to observed RF signature
                obs_freq = drone.profile.frequency_ghz + random.gauss(0, 0.02)
                obs_bw = drone.profile.bandwidth_mhz + random.gauss(0, 1)

                # Classify
                classified_type, class_conf = classify(
                    obs_freq, obs_bw, drone.profile.protocol
                )

                # Use classification confidence as detection confidence
                confidence = round(min(confidence, class_conf), 2)

                # Threat assessment
                dist_to_zone = haversine_km(
                    drone.lat, drone.lon, ZONE_CENTER_LAT, ZONE_CENTER_LON
                )
                threat_score, threat_level = assess(
                    drone.drone_id, drone.lat, drone.lon,
                    drone.altitude_m, drone.speed_mps,
                )

                detection = Detection(
                    detection_id=str(uuid.uuid4()),
                    timestamp=now_iso,
                    drone_id=drone.drone_id,
                    drone_type=classified_type,
                    sensor_id=sensor.sensor_id,
                    lat=round(drone.lat, 6),
                    lon=round(drone.lon, 6),
                    altitude_m=round(drone.altitude_m, 1),
                    frequency_ghz=round(obs_freq, 3),
                    bandwidth_mhz=round(obs_bw, 1),
                    protocol=drone.profile.protocol,
                    rssi_dbm=rssi,
                    confidence=confidence,
                    threat_level=threat_level,
                    threat_score=threat_score,
                    distance_to_zone_km=round(dist_to_zone, 3),
                )
                all_detections.append(detection)

                # Broadcast detection
                await broadcast({"type": "detection", "data": detection.model_dump()})

            # Check geofence
            dist_to_zone = haversine_km(
                drone.lat, drone.lon, ZONE_CENTER_LAT, ZONE_CENTER_LON
            )
            last_alert_time = self._alerted_drones.get(drone.drone_id, 0)
            if dist_to_zone < ZONE_RADIUS_KM and (now.timestamp() - last_alert_time) > 30:
                alert = Alert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=now_iso,
                    drone_id=drone.drone_id,
                    drone_type=drone.profile.drone_type,
                    alert_type="geofence_breach",
                    message=f"{drone.profile.drone_type} entered protected zone ({dist_to_zone:.2f} km from center)",
                    threat_score=assess(
                        drone.drone_id, drone.lat, drone.lon,
                        drone.altitude_m, drone.speed_mps,
                    )[0],
                )
                all_alerts.append(alert)
                self._alerted_drones[drone.drone_id] = now.timestamp()
                await broadcast({"type": "alert", "data": alert.model_dump()})

            # Broadcast drone track
            await broadcast({
                "type": "drone_track",
                "data": {
                    "drone_id": drone.drone_id,
                    "drone_type": drone.profile.drone_type,
                    "positions": drone.path[-100:],
                    "lat": round(drone.lat, 6),
                    "lon": round(drone.lon, 6),
                    "active": True,
                },
            })

        # Despawn drones
        for drone_id in list(self.drones.keys()):
            drone = self.drones[drone_id]
            dist_from_zone = haversine_km(
                drone.lat, drone.lon, ZONE_CENTER_LAT, ZONE_CENTER_LON
            )
            if random.random() < DRONE_DESPAWN_CHANCE or dist_from_zone > 5.0:
                await broadcast({
                    "type": "drone_track",
                    "data": {
                        "drone_id": drone_id,
                        "drone_type": drone.profile.drone_type,
                        "positions": [],
                        "lat": drone.lat,
                        "lon": drone.lon,
                        "active": False,
                    },
                })
                clear_drone(drone_id)
                self._alerted_drones.pop(drone_id, None)
                del self.drones[drone_id]

        # Sensor status heartbeat every 5 ticks
        if self.tick_count % 5 == 0:
            for sensor in self.sensors:
                det_count = sum(
                    1 for d in all_detections if d.sensor_id == sensor.sensor_id
                )
                sensor.detections_last_min = det_count * 12  # rough extrapolation
                sensor.last_seen = now_iso
                sensor.signal_strength = max(
                    0, min(100, sensor.signal_strength + random.randint(-3, 3))
                )
                await broadcast({
                    "type": "sensor_status",
                    "data": sensor.model_dump(),
                })

        # Persist
        await database.save_detections(all_detections)
        for alert in all_alerts:
            await database.save_alert(alert)

    def _spawn_drone(self, now: datetime):
        profile = random.choice(DRONE_PROFILES)
        # Spawn 1.5-3 km from zone center, random direction
        angle = random.uniform(0, 360)
        dist = random.uniform(1.5, 3.0)
        from simulation.flight_path import move_point
        lat, lon = move_point(ZONE_CENTER_LAT, ZONE_CENTER_LON, angle, dist)

        # Head roughly toward the zone
        toward_zone = (angle + 180) % 360
        heading = toward_zone + random.gauss(0, 30)

        drone = SimulatedDrone(
            drone_id=str(uuid.uuid4())[:8],
            profile=profile,
            lat=lat,
            lon=lon,
            altitude_m=profile.typical_altitude_m + random.gauss(0, 20),
            heading_deg=heading % 360,
            speed_mps=random.uniform(3, profile.max_speed_mps * 0.7),
            spawned_at=now,
            path=[[lat, lon]],
        )
        self.drones[drone.drone_id] = drone
        print(f"[SIM] Spawned {profile.drone_type} (id={drone.drone_id})")
