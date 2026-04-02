"""Random-walk flight path generator for simulated drones."""

import math
import random
from models import SimulatedDrone


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def move_point(lat: float, lon: float, heading_deg: float, distance_km: float):
    R = 6371.0
    bearing = math.radians(heading_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    d = distance_km / R

    lat2 = math.asin(
        math.sin(lat1) * math.cos(d)
        + math.cos(lat1) * math.sin(d) * math.cos(bearing)
    )
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(d) * math.cos(lat1),
        math.cos(d) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)


def update_position(drone: SimulatedDrone) -> None:
    # Heading drift
    drone.heading_deg = (drone.heading_deg + random.gauss(0, 15)) % 360

    # Speed variation
    drone.speed_mps = max(
        0.5,
        min(drone.profile.max_speed_mps, drone.speed_mps + random.gauss(0, 1)),
    )

    # Altitude drift
    drone.altitude_m = max(
        10, min(400, drone.altitude_m + random.gauss(0, 3))
    )

    # Move position (speed is m/s, tick is 1s, convert to km)
    distance_km = drone.speed_mps / 1000.0
    new_lat, new_lon = move_point(
        drone.lat, drone.lon, drone.heading_deg, distance_km
    )
    drone.lat = new_lat
    drone.lon = new_lon
    drone.path.append([new_lat, new_lon])

    # Keep path to last 300 points
    if len(drone.path) > 300:
        drone.path = drone.path[-300:]
