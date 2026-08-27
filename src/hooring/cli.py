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
        description="風鈴の音を、風まかせに鳴らします。",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=None,
        metavar="SEC",
        help="再生（または書き出し）秒数。省略時は鳴り続けます",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        metavar="FILE",
        help="WAV ファイルへ書き出す（再生しない）",
    )
    parser.add_argument("--seed", type=int, default=None, help="乱数シード")
    parser.add_argument(
        "--wind",
        choices=WIND_NAMES,
        default="moderate",
        help="風の強さ (default: moderate)",
    )
    parser.add_argument(
        "--voices",
        type=int,
        default=2,
        help="風鈴の数 1–6 (default: 2)",
    )
    parser.add_argument(
        "--material",
        choices=MATERIALS,
        default="glass",
        help="音色 (default: glass)",
    )
    parser.add_argument("--once", action="store_true", help="一打だけ鳴らして終わる")
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=44100,
        metavar="HZ",
        help="サンプリング周波数 (default: 44100)",
    )
    parser.add_argument("--mono", action="store_true", help="モノラルで出力する")
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
    )
    scene = Scene(spec, rng)

    if args.output:
        assert duration is not None
        write_wav_from_scene(args.output, scene, duration)
        print(f"wrote {args.output}  ({duration:g}s, seed={seed})", file=sys.stderr)
        return 0

    print(
        f"hooring  seed={seed}  wind={args.wind}  {args.material}×{args.voices}  (Ctrl+C で止める)",
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
