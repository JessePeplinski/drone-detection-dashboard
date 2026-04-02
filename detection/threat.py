"""Threat assessment scoring for detected drones."""

from __future__ import annotations

from datetime import datetime
from simulation.flight_path import haversine_km
from config import ZONE_CENTER_LAT, ZONE_CENTER_LON


# Track how long each drone has been near the zone
_loiter_start: dict[str, datetime] = {}


def assess(
    drone_id: str,
    lat: float,
    lon: float,
    altitude_m: float,
    speed_mps: float,
) -> tuple[float, str]:
    """Score threat 0-100 and return (score, level)."""

    distance_km = haversine_km(lat, lon, ZONE_CENTER_LAT, ZONE_CENTER_LON)

    # Distance score (40 pts max) — closer = higher threat
    if distance_km < 0.2:
        distance_score = 40
    elif distance_km < 0.5:
        distance_score = 30
    elif distance_km < 1.0:
        distance_score = 20
    elif distance_km < 2.0:
        distance_score = 10
    else:
        distance_score = 0

    # Loiter score (30 pts max) — time spent within 1km of zone
    now = datetime.utcnow()
    if distance_km < 1.0:
        if drone_id not in _loiter_start:
            _loiter_start[drone_id] = now
        loiter_seconds = (now - _loiter_start[drone_id]).total_seconds()
        if loiter_seconds > 120:
            loiter_score = 30
        elif loiter_seconds > 60:
            loiter_score = 20
        elif loiter_seconds > 30:
            loiter_score = 10
        else:
            loiter_score = 0
    else:
        _loiter_start.pop(drone_id, None)
        loiter_score = 0

    # Altitude score (15 pts max) — lower altitude = higher threat
    if altitude_m < 30:
        altitude_score = 15
    elif altitude_m < 60:
        altitude_score = 10
    elif altitude_m < 120:
        altitude_score = 5
    else:
        altitude_score = 0

    # Speed score (15 pts max) — very slow (hovering) or very fast = higher threat
    if speed_mps < 2:
        speed_score = 15  # hovering / surveillance
    elif speed_mps > 25:
        speed_score = 12  # fast approach
    elif speed_mps < 5:
        speed_score = 8
    else:
        speed_score = 3

    total = distance_score + loiter_score + altitude_score + speed_score
    total = min(100, max(0, total))

    if total >= 76:
        level = "critical"
    elif total >= 51:
        level = "high"
    elif total >= 26:
        level = "medium"
    else:
        level = "low"

    return round(total, 1), level


def clear_drone(drone_id: str):
    _loiter_start.pop(drone_id, None)
