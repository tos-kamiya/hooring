# SPDX-FileCopyrightText: 2026-present Toshihiro Kamiya <kamiya@mbj.nifty.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import wave
from pathlib import Path
from typing import List

import numpy as np

from hooring.cli import main
from hooring.io import play_scene, write_wav
from hooring.scene import Scene, SceneSpec


class FakeStdin:
    def __init__(self) -> None:
        self.chunks: List[bytes] = []
        self.closed = False

    def write(self, data: bytes) -> int:
        self.chunks.append(data)
        return len(data)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class FakeProc:
    def __init__(self) -> None:
        self.stdin = FakeStdin()
        self.killed = False

    def wait(self, timeout: float | None = None) -> int:
        return 0

    def kill(self) -> None:
        self.killed = True


def test_cli_writes_wav(tmp_path: Path) -> None:
    out = tmp_path / "furin.wav"
    assert main(["--once", "-o", str(out), "--seed", "1", "--sample-rate", "8000", "--mono"]) == 0
    assert out.is_file()
    with wave.open(str(out), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getframerate() == 8000
        assert handle.getsampwidth() == 2
        assert handle.getnframes() > 1000


def test_cli_rejects_volume_above_max() -> None:
    raised = False
    try:
        main(["--volume", "1.1", "--once", "-o", "x.wav"])
    except SystemExit as exc:
        raised = True
        assert exc.code != 0
    assert raised


def test_cli_rejects_bad_voices() -> None:
    raised = False
    try:
        main(["--voices", "0", "--once", "-o", "x.wav"])
    except SystemExit as exc:
        raised = True
        assert exc.code != 0
    assert raised


def test_write_wav_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "t.wav"
    audio = np.zeros((100, 2), dtype=np.float64)
    audio[10, 0] = 0.5
    write_wav(str(path), audio, 8000)
    with wave.open(str(path), "rb") as handle:
        raw = handle.readframes(handle.getnframes())
    pcm = np.frombuffer(raw, dtype="<i2").reshape(-1, 2)
    assert pcm[10, 0] == int(0.5 * 32767)


def test_play_scene_streams_pcm() -> None:
    spec = SceneSpec(sample_rate=8000, stereo=True, once=True, voices=1)
    scene = Scene(spec, np.random.default_rng(0))
    proc = FakeProc()

    def popen(cmd, stdin=None):
        assert cmd[0] == "aplay"
        assert stdin is not None
        return proc

    from unittest.mock import patch

    with patch("hooring.io._player_commands", return_value=[["aplay", "-"]]):
        play_scene(scene, 0.25, popen=popen)
    assert proc.stdin.closed
    blob = b"".join(proc.stdin.chunks)
    assert len(blob) == int(0.25 * 8000) * 2 * 2
