"""Known drone RF fingerprint profiles."""

from models import DroneProfile

DRONE_PROFILES = [
    DroneProfile(
        drone_type="DJI Mavic 3",
        manufacturer="DJI",
        frequency_ghz=2.4,
        bandwidth_mhz=20,
        protocol="OcuSync 3.0",
        typical_altitude_m=120,
        max_speed_mps=21,
    ),
    DroneProfile(
        drone_type="DJI Mini 4 Pro",
        manufacturer="DJI",
        frequency_ghz=2.4,
        bandwidth_mhz=15,
        protocol="OcuSync 4.0",
        typical_altitude_m=80,
        max_speed_mps=16,
    ),
    DroneProfile(
        drone_type="Autel EVO II",
        manufacturer="Autel",
        frequency_ghz=5.8,
        bandwidth_mhz=40,
        protocol="Autel Link",
        typical_altitude_m=150,
        max_speed_mps=20,
    ),
    DroneProfile(
        drone_type="Skydio 2+",
        manufacturer="Skydio",
        frequency_ghz=5.2,
        bandwidth_mhz=20,
        protocol="Skydio Link",
        typical_altitude_m=100,
        max_speed_mps=15,
    ),
    DroneProfile(
        drone_type="FPV Racing Drone",
        manufacturer="Generic",
        frequency_ghz=5.8,
        bandwidth_mhz=25,
        protocol="Analog VTX",
        typical_altitude_m=30,
        max_speed_mps=40,
    ),
    DroneProfile(
        drone_type="Unknown UAV",
        manufacturer="Unknown",
        frequency_ghz=0.9,
        bandwidth_mhz=10,
        protocol="Unknown",
        typical_altitude_m=60,
        max_speed_mps=12,
    ),
]
