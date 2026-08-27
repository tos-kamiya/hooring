# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

import numpy as np

from hooring.__about__ import __version__
from hooring.io import play_scene, write_wav_from_scene
from hooring.scene import Scene, SceneSpec
from hooring.synth import MATERIALS, strike_length
from hooring.wind import WIND_NAMES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hooring",
        description="Play furin (Japanese wind chime) sounds driven by a wandering breeze.",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=None,
        metavar="SEC",
        help="seconds to play or write; omit to keep ringing",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        metavar="FILE",
        help="write a WAV file instead of playing",
    )
    parser.add_argument("--seed", type=int, default=None, help="random seed")
    parser.add_argument(
        "--wind",
        choices=WIND_NAMES,
        default="moderate",
        help="wind strength (default: moderate)",
    )
    parser.add_argument(
        "--voices",
        type=int,
        default=2,
        help="number of furin, 1–6 (default: 2)",
    )
    parser.add_argument(
        "--material",
        choices=MATERIALS,
        default="glass",
        help="timbre (default: glass)",
    )
    parser.add_argument("--once", action="store_true", help="play a single strike and exit")
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=44100,
        metavar="HZ",
        help="sample rate (default: 44100)",
    )
    parser.add_argument("--mono", action="store_true", help="output mono audio")
    parser.add_argument(
        "--volume",
        type=float,
        default=1.0,
        metavar="GAIN",
        help="volume 0–1, where 1 is the current maximum (default: 1)",
    )
    parser.add_argument("--version", action="version", version=f"hooring {__version__}")
    return parser


def _duration_for(args: argparse.Namespace) -> Optional[float]:
    if args.duration is not None:
        if args.duration < 0:
            raise ValueError("duration must be >= 0")
        return float(args.duration)
    if args.once:
        kind = "metal" if args.material in ("metal", "mixed") else "glass"
        return strike_length(kind, args.sample_rate) / float(args.sample_rate) + 0.15
    if args.output:
        return 30.0
    return None


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.voices < 1 or args.voices > 6:
        parser.error("voices must be between 1 and 6")
    if args.sample_rate < 8000:
        parser.error("sample-rate must be at least 8000")
    if not 0.0 <= args.volume <= 1.0:
        parser.error("volume must be between 0 and 1")
    try:
        duration = _duration_for(args)
    except ValueError as exc:
        parser.error(str(exc))

    seed = int(args.seed) if args.seed is not None else int(np.random.default_rng().integers(0, 2**31 - 1))
    rng = np.random.default_rng(seed)
    spec = SceneSpec(
        sample_rate=args.sample_rate,
        stereo=not args.mono,
        wind=args.wind,
        voices=args.voices,
        material=args.material,
        once=bool(args.once),
        volume=float(args.volume),
    )
    scene = Scene(spec, rng)

    if args.output:
        assert duration is not None
        write_wav_from_scene(args.output, scene, duration)
        print(f"wrote {args.output}  ({duration:g}s, seed={seed})", file=sys.stderr)
        return 0

    print(
        f"hooring  seed={seed}  wind={args.wind}  {args.material}x{args.voices}  vol={args.volume:g}  (Ctrl+C to stop)",
        file=sys.stderr,
    )
    try:
        play_scene(scene, duration)
    except RuntimeError as exc:
        print(f"hooring: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
