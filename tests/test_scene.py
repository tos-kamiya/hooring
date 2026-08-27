# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import numpy as np

from hooring import render
from hooring.scene import Scene, SceneSpec
from hooring.synth import Chime


def test_render_length_and_seed() -> None:
    a = render(duration=1.5, seed=1, sample_rate=8000, stereo=True, once=True)
    b = render(duration=1.5, seed=1, sample_rate=8000, stereo=True, once=True)
    c = render(duration=1.5, seed=2, sample_rate=8000, stereo=True, once=True)
    assert a.shape == (12000, 2)
    assert np.allclose(a, b)
    assert not np.allclose(a, c)
    assert np.isfinite(a).all()
    assert np.max(np.abs(a)) <= 1.0
    assert np.max(np.abs(a)) > 0.05


def test_mono_once_has_energy() -> None:
    audio = render(duration=2.0, seed=4, sample_rate=8000, stereo=False, once=True, material="metal")
    assert audio.ndim == 1
    assert audio.shape == (16000,)
    assert float(np.sqrt(np.mean(audio**2))) > 0.001


def test_ambient_has_intro_strike() -> None:
    audio = render(duration=1.2, seed=8, sample_rate=8000, stereo=False, wind="breeze", voices=1)
    assert float(np.max(np.abs(audio))) > 0.05


def test_tail_survives_block_boundary() -> None:
    spec = SceneSpec(sample_rate=8000, stereo=False, once=True, voices=1, material="glass")
    scene = Scene(spec, np.random.default_rng(1), chimes=[Chime(2637.0, "glass", 0.0, 1.0)])
    first = scene.render_block(200)
    rest = scene.render_block(8000)
    # First block is almost all pre-delay plus a sliver of the attack;
    # the ring lives in the next block.
    assert float(np.max(np.abs(rest))) > float(np.max(np.abs(first)))


def test_zero_duration() -> None:
    audio = render(duration=0, seed=0, sample_rate=8000)
    assert audio.shape == (0, 2)


def test_intro_survives_short_blocks() -> None:
    spec = SceneSpec(sample_rate=8000, stereo=False, once=False, voices=1, wind="breeze")
    scene = Scene(spec, np.random.default_rng(3), chimes=[Chime(2637.0, "glass", 0.0, 1.0)])
    parts = [scene.render_block(200) for _ in range(40)]
    audio = np.concatenate(parts)
    assert float(np.max(np.abs(audio))) > 0.05
