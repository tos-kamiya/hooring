# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
"""1/f flicker that times strikes and sets how hard the clapper hits."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

WIND_NAMES = ("breeze", "moderate", "gusty")
N_OCTAVES = 8


@dataclass(frozen=True)
class WindPreset:
    mean_gap: float
    gap_ratio: float
    min_gap: float
    max_gap: float
    loud_mean: float
    loud_spread: float
    bounce_at: float = 0.75


PRESETS: Dict[str, WindPreset] = {
    "breeze": WindPreset(
        mean_gap=9.6, gap_ratio=3.0, min_gap=3.3, max_gap=42.0, loud_mean=0.48, loud_spread=0.28
    ),
    "moderate": WindPreset(
        mean_gap=3.9, gap_ratio=2.8, min_gap=1.2, max_gap=21.0, loud_mean=0.58, loud_spread=0.32
    ),
    "gusty": WindPreset(
        mean_gap=1.26, gap_ratio=2.4, min_gap=0.36, max_gap=7.2, loud_mean=0.70, loud_spread=0.28
    ),
}


class Flicker:
    """Voss–McCartney 1/f samples, clipped to [-1, 1]."""

    def __init__(self, rng: np.random.Generator, n_octaves: int = N_OCTAVES) -> None:
        if n_octaves < 2:
            raise ValueError("n_octaves must be at least 2")
        self._rng = rng
        self._n = int(n_octaves)
        self._dice = self._rng.uniform(-1.0, 1.0, size=self._n)
        self._counter = 0
        self._scale = float(np.sqrt(3.0 * self._n))

    def sample(self) -> float:
        self._counter += 1
        changed = self._counter ^ (self._counter - 1)
        for i in range(self._n):
            if changed & (1 << i):
                self._dice[i] = self._rng.uniform(-1.0, 1.0)
        return float(np.clip(float(np.mean(self._dice)) * self._scale, -1.0, 1.0))


class Wind:
    def __init__(self, preset: WindPreset, rng: np.random.Generator) -> None:
        self.preset = preset
        self._interval = Flicker(rng)
        self._loudness = Flicker(rng)

    def next_interval(self) -> float:
        x = self._interval.sample()
        gap = self.preset.mean_gap * (self.preset.gap_ratio ** x)
        return float(np.clip(gap, self.preset.min_gap, self.preset.max_gap))

    def next_strength(self) -> float:
        x = self._loudness.sample()
        strength = self.preset.loud_mean + self.preset.loud_spread * x
        return float(np.clip(strength, 0.2, 1.0))
