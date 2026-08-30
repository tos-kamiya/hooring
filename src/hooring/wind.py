# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
"""1/f flicker that times strikes and sets how hard the clapper hits."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

WIND_NAMES = ("breeze", "moderate", "gusty")
N_OCTAVES = 8
INTERVAL_BATCH_SIZE = 100


@dataclass(frozen=True)
class WindPreset:
    mean_gap: float
    gap_ratio: float
    min_gap: float
    max_gap: float
    loud_mean: float
    loud_spread: float


PRESETS: dict[str, WindPreset] = {
    "breeze": WindPreset(
        mean_gap=9.6, gap_ratio=10.0, min_gap=0.1, max_gap=42.0, loud_mean=0.48, loud_spread=0.28
    ),
    "moderate": WindPreset(
        mean_gap=3.9, gap_ratio=4.5, min_gap=0.1, max_gap=21.0, loud_mean=0.58, loud_spread=0.32
    ),
    "gusty": WindPreset(
        mean_gap=1.26, gap_ratio=2.4, min_gap=0.1, max_gap=7.2, loud_mean=0.70, loud_spread=0.28
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
        self._interval_buffer = np.empty(0, dtype=np.float64)
        self._interval_pos = 0

    def _refill_intervals(self) -> None:
        values = np.array(
            [self._interval.sample() for _ in range(INTERVAL_BATCH_SIZE)],
            dtype=np.float64,
        )
        mean = self.preset.mean_gap
        low_side = mean * np.power(mean / self.preset.min_gap, values)
        high_side = mean * np.power(self.preset.gap_ratio, values)
        gaps = np.where(values < 0.0, low_side, high_side)
        self._interval_buffer = np.clip(
            gaps, self.preset.min_gap, self.preset.max_gap
        )
        self._interval_pos = 0

    def next_interval(self) -> float:
        if self._interval_pos >= self._interval_buffer.size:
            self._refill_intervals()
        gap = self._interval_buffer[self._interval_pos]
        self._interval_pos += 1
        return float(gap)

    def next_strength(self) -> float:
        x = self._loudness.sample()
        strength = self.preset.loud_mean + self.preset.loud_spread * x
        return float(np.clip(strength, 0.2, 1.0))
