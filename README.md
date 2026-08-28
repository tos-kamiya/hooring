# hooring 🎐

[English](README.md) · [日本語](README_ja-JP.md)

Play cool-sounding furin (Japanese wind chime) tones, driven by a wandering breeze.

Glass (Edo furin) and metal (iron furin) timbres are additively synthesized and struck at irregular intervals, following the wind. Strike loudness and spacing wander with 1/f fluctuation, like a tanzaku paper strip catching the air and moving the clapper.

## Installation

Install with [pipx](https://pipx.pypa.io/) from GitHub:

```console
pipx install git+https://github.com/tos-kamiya/hooring.git
```

That puts `hooring` on your `PATH`. Upgrade later with `pipx upgrade hooring`.

Playback needs `aplay` (ALSA) or `ffplay` (ffmpeg). Writing a WAV file does not.

### Development

Clone the repository and set up the virtualenv with [uv](https://docs.astral.sh/uv/):

```console
uv sync
uv run hooring
```

Tests:

```console
uv run pytest
```


## Usage

```console
hooring
```

It keeps ringing. Stop with `Ctrl+C`. To hear the same breeze again, pass the printed `seed=` to `--seed`.

```console
# A single strike
hooring --once

# Light breeze, three furin, 45 seconds
hooring -d 45 --wind breeze --voices 3

# Metal timbre
hooring --material metal --wind gusty

# Write a WAV file (defaults to 30 seconds if duration is omitted)
hooring -o natsu.wav -d 20 --seed 7

# Half volume (1 is the current maximum)
hooring --volume 0.5
```

### Options

| Flag | Meaning |
| --- | --- |
| `-d`, `--duration SEC` | Seconds to play or write. Omit to keep ringing |
| `-o`, `--output FILE` | Write a WAV file instead of playing |
| `--seed N` | Random seed |
| `--wind breeze\|moderate\|gusty` | Wind strength |
| `--voices N` | Number of furin (1–6, default 2) |
| `--material glass\|metal\|mixed` | Timbre |
| `--once` | Play a single strike and exit |
| `--mono` | Mono output |
| `--sample-rate HZ` | Sample rate |
| `--volume GAIN` | Volume 0–1 (1 is the current maximum, default 1) |

From Python:

```python
from hooring import render

audio = render(duration=8, seed=1, wind="breeze", material="glass", volume=0.5)
# stereo: shape (n, 2), float64 in [-1, 1]
```

## Release notes

→ [Release Notes](release-notes.md)

## License

`hooring` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
