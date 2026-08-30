# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
"""Mix overlapping furin strikes under a wandering wind."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from hooring.synth import Chime, choose_chimes, reposition_chimes, synthesize_strike
from hooring.wind import PRESETS, Wind, WIND_NAMES

# Playback time between stereo rearrangements.
REPOSITION_EVERY_S = 3600.0
CONTINUATION_THRESHOLD_S = 0.3


@dataclass(frozen=True)
class SceneSpec:
    sample_rate: int = 44100
    stereo: bool = True
    wind: str = "moderate"
    voices: int = 2
    material: str = "glass"
    once: bool = False
    volume: float = 1.0
    reposition_every: float = REPOSITION_EVERY_S


class Scene:
    def __init__(self, spec: SceneSpec, rng: np.random.Generator, chimes: Optional[Sequence[Chime]] = None) -> None:
        if spec.wind not in WIND_NAMES:
            raise ValueError("wind must be breeze, moderate, or gusty")
        if spec.sample_rate < 8000:
            raise ValueError("sample_rate is too low")
        if not 0.0 <= spec.volume <= 1.0:
            raise ValueError("volume must be between 0 and 1")
        self.spec = spec
        self.rng = rng
        self.chimes: List[Chime] = list(chimes) if chimes is not None else choose_chimes(
            spec.voices, spec.material, rng
        )
        if not self.chimes:
            raise ValueError("at least one chime is required")
        self.wind = Wind(PRESETS[spec.wind], rng)
        self._t = 0
        self._last_hit = np.full(len(self.chimes), -10**9, dtype=np.int64)
        self._tail = np.zeros((0, 2 if spec.stereo else 1), dtype=np.float64)
        if spec.once:
            self._next_hit: Optional[int] = int(spec.sample_rate * 0.06)
        else:
            self._next_hit = int(spec.sample_rate * float(rng.uniform(0.25, 0.9)))
        self._pending: List[tuple[int, int, float]] = []
        self._last_strike: Optional[int] = None
        self._in_continuation = False
        interval = spec.reposition_every
        self._reposition_every = None if interval <= 0.0 else int(spec.sample_rate * interval)
        self._next_reposition = self._reposition_every

    @property
    def channels(self) -> int:
        return 2 if self.spec.stereo else 1

    def render_block(self, n_frames: int) -> np.ndarray:
        if n_frames < 0:
            raise ValueError("n_frames must be >= 0")
        n = int(n_frames)
        ch = self.channels
        out = np.zeros((n, ch), dtype=np.float64)
        if n == 0:
            return out

        self._maybe_reposition()

        if self._tail.shape[0] > 0:
            k = min(n, self._tail.shape[0])
            out[:k] += self._tail[:k]
            self._tail = self._tail[k:]

        events: List[tuple[int, int, float]] = []
        still: List[tuple[int, int, float]] = []
        for abs_t, index, strength in self._pending:
            if abs_t < self._t + n:
                events.append((max(0, abs_t - self._t), index, strength))
            else:
                still.append((abs_t, index, strength))
        self._pending = still
        events.extend(self._schedule_wind(n))

        events.sort(key=lambda item: item[0])
        for offset, index, strength in events:
            self._retrigger(out, offset)
            audio = synthesize_strike(
                self.chimes[index],
                strength,
                self.spec.sample_rate,
                self.rng,
                stereo=self.spec.stereo,
            )
            if audio.ndim == 1:
                audio = audio[:, None]
            self._mix(out, audio, offset)

        self._t += n
        peak = np.max(np.abs(out))
        if peak > 0.98:
            out *= 0.98 / peak
        if self.spec.volume != 1.0:
            out *= self.spec.volume
        return out if self.spec.stereo else out[:, 0]

    def _maybe_reposition(self) -> None:
        if self._reposition_every is None or self._next_reposition is None:
            return
        if self._t < self._next_reposition:
            return
        self.chimes = reposition_chimes(self.chimes, self.spec.material, self.rng)
        while self._next_reposition <= self._t:
            self._next_reposition += self._reposition_every

    def _schedule_wind(self, n: int) -> List[tuple[int, int, float]]:
        events: List[tuple[int, int, float]] = []
        sr = self.spec.sample_rate
        min_gap = int(self.wind.preset.min_gap * sr)
        end = self._t + n
        while self._next_hit is not None and self._next_hit < end:
            abs_t = self._next_hit
            eligible = [i for i, last in enumerate(self._last_hit) if abs_t - last >= min_gap]
            if not eligible:
                soonest = int(np.min(self._last_hit) + min_gap)
                if soonest <= abs_t:
                    soonest = abs_t + 1
                self._next_hit = soonest
                continue
            offset = max(0, abs_t - self._t)
            index = int(eligible[int(self.rng.integers(0, len(eligible)))])
            strength = self.wind.next_strength()
            is_continuation = (
                self._last_strike is not None
                and abs_t - self._last_strike < int(self.spec.sample_rate * CONTINUATION_THRESHOLD_S)
            )
            if self._in_continuation:
                strength *= float(self.rng.uniform(0.45, 0.75))
            events.append((offset, index, strength))
            self._last_hit[index] = abs_t
            self._in_continuation = is_continuation
            self._last_strike = abs_t
            if self.spec.once:
                self._next_hit = None
                break
            gap = self.wind.next_interval()
            self._next_hit = abs_t + max(1, int(round(gap * sr)))
        return events

    def _retrigger(self, out: np.ndarray, offset: int) -> None:
        """Cut the previous ring so only one furin speaks at a time."""
        fade_n = max(1, int(self.spec.sample_rate * 0.008))
        if offset > 0:
            n_fade = min(fade_n, offset)
            ramp = np.linspace(1.0, 0.0, n_fade, dtype=np.float64)[:, None]
            out[offset - n_fade : offset] *= ramp
            out[offset:] = 0.0
        else:
            n_fade = min(fade_n, out.shape[0])
            if n_fade > 0:
                ramp = np.linspace(1.0, 0.0, n_fade, dtype=np.float64)[:, None]
                out[:n_fade] *= ramp
                if n_fade < out.shape[0]:
                    out[n_fade:] = 0.0
        self._tail = np.zeros((0, out.shape[1]), dtype=np.float64)

    def _mix(self, out: np.ndarray, audio: np.ndarray, offset: int) -> None:
        n = out.shape[0]
        if offset >= n:
            extra = audio
        else:
            take = min(audio.shape[0], n - offset)
            out[offset : offset + take] += audio[:take]
            extra = audio[take:]
        if extra.shape[0] == 0:
            return
        if self._tail.shape[0] == 0:
            self._tail = extra.copy()
            return
        if self._tail.shape[0] < extra.shape[0]:
            pad = np.zeros((extra.shape[0] - self._tail.shape[0], extra.shape[1]), dtype=np.float64)
            self._tail = np.vstack((self._tail, pad))
        self._tail[: extra.shape[0]] += extra


def render(
    duration: float,
    *,
    seed: Optional[int] = None,
    wind: str = "moderate",
    voices: int = 2,
    material: str = "glass",
    sample_rate: int = 44100,
    stereo: bool = True,
    once: bool = False,
    volume: float = 1.0,
) -> np.ndarray:
    """Render `duration` seconds of furin audio.

    Returns a 1-D array (mono) or an (n, 2) array (stereo) of float64 samples.
    """
    if duration < 0:
        raise ValueError("duration must be >= 0")
    rng = np.random.default_rng(seed)
    spec = SceneSpec(
        sample_rate=sample_rate,
        stereo=stereo,
        wind=wind,
        voices=voices,
        material=material,
        once=once,
        volume=volume,
    )
    scene = Scene(spec, rng)
    n_total = int(round(duration * sample_rate))
    ch = scene.channels
    out = np.zeros((n_total, ch), dtype=np.float64)
    pos = 0
    block = sample_rate
    while pos < n_total:
        n = min(block, n_total - pos)
        chunk = scene.render_block(n)
        if chunk.ndim == 1:
            chunk = chunk[:, None]
        out[pos : pos + n] = chunk
        pos += n
    return out if stereo else out[:, 0]
