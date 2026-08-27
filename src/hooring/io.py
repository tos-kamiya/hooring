# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
"""WAV writing and local playback."""

from __future__ import annotations

import shutil
import subprocess
import wave
from typing import Any, Callable, List, Optional

import numpy as np

from hooring.scene import Scene


def to_s16(audio: np.ndarray) -> np.ndarray:
    x = np.clip(np.asarray(audio, dtype=np.float64), -1.0, 1.0)
    if x.ndim == 1:
        x = x[:, None]
    return np.ascontiguousarray((x * 32767.0).astype("<i2"))


def write_wav(path: str, audio: np.ndarray, sample_rate: int) -> None:
    pcm = to_s16(audio)
    with wave.open(path, "wb") as handle:
        handle.setnchannels(pcm.shape[1])
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def write_wav_from_scene(path: str, scene: Scene, duration: float) -> None:
    sample_rate = scene.spec.sample_rate
    n_total = int(round(duration * sample_rate))
    with wave.open(path, "wb") as handle:
        handle.setnchannels(scene.channels)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        remain = n_total
        while remain > 0:
            n = min(remain, sample_rate)
            handle.writeframes(to_s16(scene.render_block(n)).tobytes())
            remain -= n


def _player_commands(sample_rate: int, channels: int) -> List[List[str]]:
    commands: List[List[str]] = []
    if shutil.which("aplay"):
        commands.append(
            ["aplay", "-q", "-t", "raw", "-f", "S16_LE", "-c", str(channels), "-r", str(sample_rate), "-"]
        )
    if shutil.which("ffplay"):
        commands.append(
            [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-loglevel",
                "quiet",
                "-f",
                "s16le",
                "-ar",
                str(sample_rate),
                "-ac",
                str(channels),
                "-i",
                "pipe:0",
            ]
        )
    return commands


def play_scene(
    scene: Scene,
    duration: Optional[float],
    *,
    popen: Callable[..., Any] = subprocess.Popen,
) -> None:
    commands = _player_commands(scene.spec.sample_rate, scene.channels)
    if not commands:
        raise RuntimeError("再生できるコマンドがありません。aplay か ffplay をインストールしてください。")

    err: Optional[Exception] = None
    for cmd in commands:
        try:
            _stream(scene, duration, cmd, popen)
            return
        except FileNotFoundError as exc:
            err = exc
            continue
        except OSError as exc:
            err = exc
            continue
    raise RuntimeError("音声の再生に失敗しました。") from err


def _stream(
    scene: Scene,
    duration: Optional[float],
    cmd: List[str],
    popen: Callable[..., Any],
) -> None:
    proc = popen(cmd, stdin=subprocess.PIPE)
    if proc.stdin is None:
        proc.kill()
        raise RuntimeError("failed to open audio player stdin")
    target = None if duration is None else int(round(duration * scene.spec.sample_rate))
    played = 0
    block = scene.spec.sample_rate
    try:
        while True:
            n = block
            if target is not None:
                remain = target - played
                if remain <= 0:
                    break
                n = min(n, remain)
            proc.stdin.write(to_s16(scene.render_block(n)).tobytes())
            proc.stdin.flush()
            played += n
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
