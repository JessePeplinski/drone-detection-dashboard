"""REST API endpoints for detection history and sensor info."""

from typing import Optional

from fastapi import APIRouter, Query
from config import SENSORS
from models import SensorConfig
from simulation.drone_profiles import DRONE_PROFILES
import database

router = APIRouter()


@router.get("/detections")
async def list_detections(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sensor_id: Optional[str] = None,
    drone_type: Optional[str] = None,
    min_threat: Optional[float] = None,
):
    return await database.get_detections(limit, offset, sensor_id, drone_type, min_threat)


@router.get("/alerts")
async def list_alerts(limit: int = Query(20, ge=1, le=100)):
    return await database.get_alerts(limit)


@router.get("/sensors")
async def list_sensors():
    return [SensorConfig(**s).model_dump() for s in SENSORS]


@router.get("/stats")
async def get_stats():
    return await database.get_stats()


@router.get("/drone-profiles")
async def list_profiles():
    return [p.model_dump() for p in DRONE_PROFILES]
