# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
"""Additive synthesis for glass and metal furin."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np

# (ratio, amplitude, decay time constant in seconds)
Partials = Sequence[Tuple[float, float, float]]

GLASS_PARTIALS: Partials = (
    (1.00, 1.00, 1.35),
    (2.32, 0.28, 0.62),
    (3.91, 0.14, 0.32),
    (5.18, 0.07, 0.20),
    (7.05, 0.035, 0.12),
    (9.40, 0.018, 0.08),
)

METAL_PARTIALS: Partials = (
    (1.00, 1.00, 3.20),
    (2.76, 0.52, 2.10),
    (5.40, 0.24, 1.15),
    (8.93, 0.12, 0.70),
    (13.34, 0.06, 0.40),
    (18.64, 0.025, 0.22),
)

GLASS_PITCHES = (2349.3, 2637.0, 2793.8, 3136.0, 3520.0, 3951.1, 4186.0)
METAL_PITCHES = (880.0, 987.8, 1108.7, 1318.5, 1480.0, 1760.0)

MATERIALS = ("glass", "metal", "mixed")


@dataclass(frozen=True)
class Chime:
    f0: float
    material: str
    pan: float
    gain: float


def strike_length(material: str, sample_rate: int) -> int:
    """Samples needed for a strike to decay into silence."""
    partials = METAL_PARTIALS if material == "metal" else GLASS_PARTIALS
    tau = max(p[2] for p in partials)
    seconds = min(8.0, max(2.5, -tau * np.log(1e-4)))
    return int(sample_rate * seconds)


def synthesize_strike(
    chime: Chime,
    strength: float,
    sample_rate: int,
    rng: np.random.Generator,
    stereo: bool = True,
) -> np.ndarray:
    """Render one strike as float64 audio in [-1, 1].

    `strength` is 0..1 (how hard the clapper hit).
    """
    strength = float(np.clip(strength, 0.05, 1.0))
    material = chime.material
    partials = METAL_PARTIALS if material == "metal" else GLASS_PARTIALS
    n = strike_length(material, sample_rate)
    t = np.arange(n, dtype=np.float64) / float(sample_rate)
    y = np.zeros(n, dtype=np.float64)

    f0 = chime.f0 * rng.uniform(0.997, 1.003)
    # Harder hits pull in more high partials and a touch of extra inharmonicity.
    bright = 0.55 + 0.65 * strength
    stretch = 1.0 + 0.0015 * strength

    for ratio, amp, tau in partials:
        freq = f0 * (ratio ** stretch) * rng.uniform(0.999, 1.001)
        if freq >= sample_rate * 0.48:
            continue
        phase = rng.uniform(0.0, 2.0 * np.pi)
        high = max(0.0, (ratio - 1.0) / 8.0)
        a = amp * (1.0 + bright * high)
        tau_hit = tau * (0.88 + 0.12 * (1.0 - 0.5 * strength))
        y += a * np.exp(-t / tau_hit) * np.sin(2.0 * np.pi * freq * t + phase)

    # Slow beating on the fundamental, like a thin glass wall.
    beat = rng.uniform(0.7, 2.2)
    y += 0.22 * np.exp(-t / partials[0][2]) * np.sin(
        2.0 * np.pi * (f0 + beat) * t + rng.uniform(0.0, 2.0 * np.pi)
    )

    attack = 1.0 - np.exp(-t / 0.0012)
    y *= attack

    y += _clapper(t, n, sample_rate, f0, strength, material, rng)
    peak = np.max(np.abs(y))
    if peak > 0.0:
        y /= peak
    y *= 0.32 * (0.35 + 0.65 * strength) * chime.gain
    if not stereo:
        return y
    return _pan(y, chime.pan)


def _clapper(
    t: np.ndarray,
    n: int,
    sample_rate: int,
    f0: float,
    strength: float,
    material: str,
    rng: np.random.Generator,
) -> np.ndarray:
    """Short contact transient: glass ping vs metal tick."""
    width = 0.010 if material == "glass" else 0.007
    burst_n = max(8, int(sample_rate * width * 3))
    burst_n = min(burst_n, n)
    tb = t[:burst_n]
    noise = rng.normal(0.0, 1.0, size=burst_n)
    # Crude highpass: first difference.
    if burst_n > 1:
        noise = np.concatenate([[noise[0]], np.diff(noise)])
    env = np.exp(-tb / (width * (0.6 + 0.4 * strength)))
    noise *= env * (0.12 if material == "glass" else 0.18) * strength

    # Downward chirp into the ringing pitch.
    f_start = min(sample_rate * 0.42, f0 * (3.2 if material == "glass" else 2.4))
    chirp_f = f_start + (f0 - f_start) * (1.0 - np.exp(-tb / 0.003))
    chirp = env * 0.16 * strength * np.sin(2.0 * np.pi * np.cumsum(chirp_f) / sample_rate)
    out = np.zeros(n, dtype=np.float64)
    out[:burst_n] = noise + chirp
    return out


def _pan(mono: np.ndarray, pan: float) -> np.ndarray:
    angle = (float(np.clip(pan, -1.0, 1.0)) + 1.0) * (np.pi / 4.0)
    left = mono * np.cos(angle)
    right = mono * np.sin(angle)
    return np.column_stack((left, right))


def choose_chimes(
    voices: int,
    material: str,
    rng: np.random.Generator,
) -> List[Chime]:
    if voices < 1:
        raise ValueError("voices must be at least 1")
    if material not in MATERIALS:
        raise ValueError("material must be glass, metal, or mixed")

    chimes: List[Chime] = []
    glass_pool = list(GLASS_PITCHES)
    metal_pool = list(METAL_PITCHES)
    rng.shuffle(glass_pool)
    rng.shuffle(metal_pool)

    for i in range(voices):
        if material == "mixed":
            kind = "glass" if (i % 2 == 0) else "metal"
        else:
            kind = material
        pool = glass_pool if kind == "glass" else metal_pool
        f0 = pool[i % len(pool)]
        # Spread a little, nearer chime slightly louder and less panned.
        if voices == 1:
            pan = float(rng.uniform(-0.15, 0.15))
            gain = 1.0
        else:
            pan = float(np.clip(-0.45 + 0.9 * i / (voices - 1) + rng.uniform(-0.08, 0.08), -0.7, 0.7))
            gain = float(0.55 + 0.45 * rng.random())
            if i == 0:
                gain = max(gain, 0.85)
        chimes.append(Chime(f0=f0, material=kind, pan=pan, gain=gain))
    return chimes
