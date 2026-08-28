# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import numpy as np

from hooring import render
from hooring.scene import Scene, SceneSpec
from hooring.synth import Chime, synthesize_strike


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


def test_volume_scales_from_current_max() -> None:
    full = render(duration=1.5, seed=1, sample_rate=8000, stereo=False, once=True, volume=1.0)
    half = render(duration=1.5, seed=1, sample_rate=8000, stereo=False, once=True, volume=0.5)
    silent = render(duration=1.5, seed=1, sample_rate=8000, stereo=False, once=True, volume=0.0)
    np.testing.assert_allclose(half, full * 0.5)
    assert float(np.max(np.abs(silent))) == 0.0


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


def test_new_strike_cuts_previous() -> None:
    sr = 8000
    chime = Chime(2637.0, "glass", 0.0, 1.0)
    spec = SceneSpec(sample_rate=sr, stereo=False, once=True, voices=1)
    scene = Scene(spec, np.random.default_rng(0), chimes=[chime])
    first = synthesize_strike(chime, 0.8, sr, np.random.default_rng(1), stereo=False)[:, None]
    second = synthesize_strike(chime, 0.9, sr, np.random.default_rng(2), stereo=False)[:, None]
    out = np.zeros((sr, 1), dtype=np.float64)
    cut = 400
    scene._mix(out, first, 0)
    scene._retrigger(out, cut)
    scene._mix(out, second, cut)
    take = min(second.shape[0], sr - cut)
    np.testing.assert_allclose(out[cut : cut + take], second[:take])
    leftover = second[take:]
    if leftover.shape[0] > 0:
        np.testing.assert_allclose(scene._tail, leftover)
    else:
        assert scene._tail.shape[0] == 0
    assert float(np.max(np.abs(out[cut - 8 : cut]))) < float(np.max(np.abs(first[:cut]))) * 0.5


def test_repositions_after_interval() -> None:
    spec = SceneSpec(sample_rate=8000, stereo=True, voices=3, wind="breeze", reposition_every=0.05)
    scene = Scene(spec, np.random.default_rng(9))
    before = [(c.f0, c.material, c.pan, c.gain) for c in scene.chimes]
    scene.render_block(int(0.05 * spec.sample_rate))
    assert [(c.f0, c.material, c.pan, c.gain) for c in scene.chimes] == before
    scene.render_block(1)
    after = [(c.f0, c.material, c.pan, c.gain) for c in scene.chimes]
    assert len(after) == len(before)
    assert after != before


def test_intro_survives_short_blocks() -> None:
    spec = SceneSpec(sample_rate=8000, stereo=False, once=False, voices=1, wind="breeze")
    scene = Scene(spec, np.random.default_rng(3), chimes=[Chime(2637.0, "glass", 0.0, 1.0)])
    parts = [scene.render_block(200) for _ in range(40)]
    audio = np.concatenate(parts)
    assert float(np.max(np.abs(audio))) > 0.05
