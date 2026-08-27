# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import numpy as np

from hooring.synth import Chime, choose_chimes, synthesize_strike


def _centroid(samples: np.ndarray, sample_rate: int) -> float:
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim == 2:
        x = x.mean(axis=1)
    window = np.hanning(len(x))
    spec = np.abs(np.fft.rfft(x * window))
    freqs = np.fft.rfftfreq(len(x), 1.0 / sample_rate)
    denom = float(spec.sum())
    assert denom > 0.0
    return float(np.sum(freqs * spec) / denom)


def test_strike_is_finite_and_bounded() -> None:
    rng = np.random.default_rng(0)
    chime = Chime(f0=2637.0, material="glass", pan=0.0, gain=1.0)
    audio = synthesize_strike(chime, 0.8, 22050, rng, stereo=True)
    assert audio.ndim == 2
    assert audio.shape[1] == 2
    assert np.isfinite(audio).all()
    assert np.max(np.abs(audio)) <= 1.0
    assert np.max(np.abs(audio)) > 0.05


def test_harder_strike_is_louder() -> None:
    chime = Chime(f0=3136.0, material="glass", pan=0.0, gain=1.0)
    soft = synthesize_strike(chime, 0.2, 22050, np.random.default_rng(1), stereo=False)
    hard = synthesize_strike(chime, 1.0, 22050, np.random.default_rng(1), stereo=False)
    assert float(np.sqrt(np.mean(hard**2))) > float(np.sqrt(np.mean(soft**2)))


def test_glass_is_brighter_than_metal() -> None:
    sr = 22050
    glass = synthesize_strike(
        Chime(f0=2637.0, material="glass", pan=0.0, gain=1.0),
        0.8,
        sr,
        np.random.default_rng(2),
        stereo=False,
    )
    metal = synthesize_strike(
        Chime(f0=987.8, material="metal", pan=0.0, gain=1.0),
        0.8,
        sr,
        np.random.default_rng(2),
        stereo=False,
    )
    assert _centroid(glass, sr) > _centroid(metal, sr)
    assert _centroid(glass, sr) > 1500.0


def test_strike_decays() -> None:
    audio = synthesize_strike(
        Chime(f0=3520.0, material="glass", pan=0.0, gain=1.0),
        0.7,
        22050,
        np.random.default_rng(3),
        stereo=False,
    )
    n = len(audio)
    head = float(np.sqrt(np.mean(audio[: n // 10] ** 2)))
    tail = float(np.sqrt(np.mean(audio[-n // 10 :] ** 2)))
    assert head > tail * 8


def test_choose_chimes_mixed_and_count() -> None:
    rng = np.random.default_rng(4)
    chimes = choose_chimes(4, "mixed", rng)
    assert len(chimes) == 4
    kinds = {c.material for c in chimes}
    assert kinds == {"glass", "metal"}


def test_pan_leans_left() -> None:
    audio = synthesize_strike(
        Chime(f0=2637.0, material="glass", pan=-1.0, gain=1.0),
        0.8,
        22050,
        np.random.default_rng(5),
        stereo=True,
    )
    left = float(np.sqrt(np.mean(audio[:, 0] ** 2)))
    right = float(np.sqrt(np.mean(audio[:, 1] ** 2)))
    assert left > right * 4
