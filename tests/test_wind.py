# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import numpy as np

from hooring.wind import PRESETS, Wind


def test_wind_stays_in_range() -> None:
    rng = np.random.default_rng(11)
    wind = Wind(PRESETS["gusty"], rng, speed=0.5)
    for _ in range(2000):
        speed = wind.step(0.01)
        assert 0.0 <= speed <= 1.4


def test_same_seed_replays() -> None:
    def trace(seed: int) -> list[float]:
        wind = Wind(PRESETS["moderate"], np.random.default_rng(seed))
        return [wind.step(0.02) for _ in range(80)]

    assert trace(99) == trace(99)
    assert trace(99) != trace(100)


def test_still_air_rarely_strikes() -> None:
    wind = Wind(PRESETS["breeze"], np.random.default_rng(0), speed=0.05)
    assert wind.strike_probability(0.01) == 0.0


def test_strong_wind_strikes_more() -> None:
    rng = np.random.default_rng(3)
    calm = Wind(PRESETS["breeze"], rng, speed=0.2)
    wild = Wind(PRESETS["gusty"], rng, speed=1.0)
    assert wild.strike_probability(0.05) > calm.strike_probability(0.05)
