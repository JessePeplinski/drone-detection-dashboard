"""Drone type classification from RF signature."""

from __future__ import annotations

import random
from models import DroneProfile
from simulation.drone_profiles import DRONE_PROFILES


def classify(frequency_ghz: float, bandwidth_mhz: float, protocol: str) -> tuple[str, float]:
    """Match an RF signature to a known drone profile.

    Returns (drone_type, confidence).
    5% chance of misclassification for realism.
    """
    if random.random() < 0.05:
        # Misclassify: pick a random different profile
        decoy = random.choice(DRONE_PROFILES)
        return decoy.drone_type, round(random.uniform(0.55, 0.72), 2)

    best_match: str = "Unknown UAV"
    best_score: float = 0.0

    for profile in DRONE_PROFILES:
        score = 0.0
        # Frequency match (most important)
        freq_diff = abs(profile.frequency_ghz - frequency_ghz)
        if freq_diff < 0.1:
            score += 0.5
        elif freq_diff < 0.5:
            score += 0.2

        # Bandwidth match
        bw_diff = abs(profile.bandwidth_mhz - bandwidth_mhz)
        if bw_diff < 3:
            score += 0.3
        elif bw_diff < 10:
            score += 0.15

        # Protocol match
        if profile.protocol == protocol:
            score += 0.2

        if score > best_score:
            best_score = score
            best_match = profile.drone_type

    confidence = min(0.98, best_score + random.uniform(-0.05, 0.05))
    confidence = max(0.55, confidence)
    return best_match, round(confidence, 2)
