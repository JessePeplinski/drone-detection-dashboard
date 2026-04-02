"""Pydantic data models for the Drone Detection Dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel


class SensorConfig(BaseModel):
    sensor_id: str
    name: str
    lat: float
    lon: float
    range_km: float
    status: str = "online"
    signal_strength: int = 85
    detections_last_min: int = 0
    last_seen: str = ""


class DroneProfile(BaseModel):
    drone_type: str
    manufacturer: str
    frequency_ghz: float
    bandwidth_mhz: float
    protocol: str
    typical_altitude_m: float
    max_speed_mps: float


class SimulatedDrone(BaseModel):
    drone_id: str
    profile: DroneProfile
    lat: float
    lon: float
    altitude_m: float
    heading_deg: float
    speed_mps: float
    spawned_at: datetime
    path: List[List[float]] = []


class Detection(BaseModel):
    detection_id: str
    timestamp: str
    drone_id: str
    drone_type: str
    sensor_id: str
    lat: float
    lon: float
    altitude_m: float
    frequency_ghz: float
    bandwidth_mhz: float
    protocol: str
    rssi_dbm: float
    confidence: float
    threat_level: str
    threat_score: float
    distance_to_zone_km: float


class Alert(BaseModel):
    alert_id: str
    timestamp: str
    drone_id: str
    drone_type: str
    alert_type: str
    message: str
    threat_score: float
