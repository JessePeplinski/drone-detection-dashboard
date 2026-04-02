"""SQLite database for persisting detections and alerts."""

from __future__ import annotations

import aiosqlite
from config import DB_PATH
from models import Detection, Alert


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                detection_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                drone_id TEXT NOT NULL,
                drone_type TEXT,
                sensor_id TEXT NOT NULL,
                lat REAL, lon REAL, altitude_m REAL,
                frequency_ghz REAL, bandwidth_mhz REAL, protocol TEXT,
                rssi_dbm REAL, confidence REAL,
                threat_level TEXT, threat_score REAL,
                distance_to_zone_km REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                drone_id TEXT NOT NULL,
                drone_type TEXT,
                alert_type TEXT,
                message TEXT,
                threat_score REAL
            )
        """)
        await db.commit()


async def save_detections(detections: list[Detection]):
    if not detections:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            """INSERT OR IGNORE INTO detections VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )""",
            [
                (
                    d.detection_id, d.timestamp, d.drone_id, d.drone_type,
                    d.sensor_id, d.lat, d.lon, d.altitude_m,
                    d.frequency_ghz, d.bandwidth_mhz, d.protocol,
                    d.rssi_dbm, d.confidence, d.threat_level, d.threat_score,
                    d.distance_to_zone_km,
                )
                for d in detections
            ],
        )
        await db.commit()


async def save_alert(alert: Alert):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                alert.alert_id, alert.timestamp, alert.drone_id,
                alert.drone_type, alert.alert_type, alert.message,
                alert.threat_score,
            ),
        )
        await db.commit()


async def get_detections(
    limit: int = 50,
    offset: int = 0,
    sensor_id: str | None = None,
    drone_type: str | None = None,
    min_threat: float | None = None,
) -> list[dict]:
    query = "SELECT * FROM detections WHERE 1=1"
    params: list = []
    if sensor_id:
        query += " AND sensor_id = ?"
        params.append(sensor_id)
    if drone_type:
        query += " AND drone_type = ?"
        params.append(drone_type)
    if min_threat is not None:
        query += " AND threat_score >= ?"
        params.append(min_threat)
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_alerts(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM detections") as cur:
            total_detections = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(DISTINCT drone_id) FROM detections") as cur:
            unique_drones = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM alerts") as cur:
            total_alerts = (await cur.fetchone())[0]
        return {
            "total_detections": total_detections,
            "unique_drones": unique_drones,
            "total_alerts": total_alerts,
        }
