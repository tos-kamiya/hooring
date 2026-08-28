# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import numpy as np

from hooring.wind import PRESETS, Flicker, Wind


def test_flicker_replays() -> None:
    def trace(seed: int) -> list[float]:
        flicker = Flicker(np.random.default_rng(seed))
        return [flicker.sample() for _ in range(80)]

    assert trace(99) == trace(99)
    assert trace(99) != trace(100)


def test_flicker_stays_in_range() -> None:
    flicker = Flicker(np.random.default_rng(11))
    for _ in range(2000):
        value = flicker.sample()
        assert -1.0 <= value <= 1.0


def test_flicker_low_freq_dominates() -> None:
    flicker = Flicker(np.random.default_rng(2), n_octaves=8)
    x = np.array([flicker.sample() for _ in range(8192)], dtype=np.float64)
    x -= float(x.mean())
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    freqs = np.fft.rfftfreq(len(x))
    low = float(np.mean(spec[(freqs >= 0.002) & (freqs < 0.02)]))
    high = float(np.mean(spec[(freqs >= 0.12) & (freqs < 0.4)]))
    assert low > high * 4


def test_interval_and_strength_stay_in_range() -> None:
    wind = Wind(PRESETS["moderate"], np.random.default_rng(3))
    p = PRESETS["moderate"]
    for _ in range(400):
        gap = wind.next_interval()
        strength = wind.next_strength()
        assert p.min_gap <= gap <= p.max_gap
        assert 0.2 <= strength <= 1.0


def test_gusty_gaps_are_shorter_than_breeze() -> None:
    breeze = Wind(PRESETS["breeze"], np.random.default_rng(4))
    gusty = Wind(PRESETS["gusty"], np.random.default_rng(4))
    breeze_mean = float(np.mean([breeze.next_interval() for _ in range(200)]))
    gusty_mean = float(np.mean([gusty.next_interval() for _ in range(200)]))
    assert gusty_mean < breeze_mean * 0.5


def test_loudness_and_interval_are_independent() -> None:
    wind = Wind(PRESETS["moderate"], np.random.default_rng(5))
    gaps = np.array([wind.next_interval() for _ in range(300)])
    strengths = np.array([wind.next_strength() for _ in range(300)])
    corr = float(np.corrcoef(gaps, strengths)[0, 1])
    assert abs(corr) < 0.4
