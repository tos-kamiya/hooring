# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
"""A wandering breeze that decides when the tanzaku hits the bell."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

WIND_NAMES = ("breeze", "moderate", "gusty")


@dataclass(frozen=True)
class WindPreset:
    mean: float
    tau: float
    sigma: float
    rate: float
    threshold: float
    min_gap: float


PRESETS: Dict[str, WindPreset] = {
    "breeze": WindPreset(mean=0.22, tau=4.5, sigma=0.09, rate=1.4, threshold=0.32, min_gap=1.1),
    "moderate": WindPreset(mean=0.38, tau=2.6, sigma=0.16, rate=2.8, threshold=0.24, min_gap=0.40),
    "gusty": WindPreset(mean=0.56, tau=1.15, sigma=0.28, rate=5.4, threshold=0.16, min_gap=0.12),
}


class Wind:
    def __init__(self, preset: WindPreset, rng: np.random.Generator, speed: float | None = None) -> None:
        self.preset = preset
        self._rng = rng
        self.speed = float(preset.mean if speed is None else speed)

    def step(self, dt: float) -> float:
        p = self.preset
        theta = 1.0 / p.tau
        self.speed += theta * (p.mean - self.speed) * dt
        self.speed += p.sigma * np.sqrt(max(dt, 0.0)) * float(self._rng.normal())
        self.speed = float(np.clip(self.speed, 0.0, 1.4))
        return self.speed

    def strike_probability(self, dt: float) -> float:
        p = self.preset
        excess = max(0.0, self.speed - p.threshold)
        lam = p.rate * (excess * excess)
        if lam <= 0.0 or dt <= 0.0:
            return 0.0
        return float(1.0 - np.exp(-lam * dt))
