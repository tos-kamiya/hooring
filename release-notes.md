# hooring Release Notes

## Unreleased

## 0.1.5 - 2026-09-01

- Brighten the glass furin timbre by strengthening its higher partials and
  short attack.

## 0.1.4 - 2026-08-30

- Reduce the probability of unnaturally long runs of very short strikes by
  reshaping the interval distribution while preserving its 1/f fluctuation.

## 0.1.3 - 2026-08-30

- Allow wind-driven strike intervals below one second, so sustained gusts can
  produce naturally clustered furin strikes. Interval fluctuations are
  generated in batches to preserve longer 1/f-shaped runs, with intervals
  reaching about 0.1 seconds at the short end. Strikes less than 0.3 seconds
  apart are softened as part of the same continuous ringing sequence.

## 0.1.2 - 2026-08-29

- Require Python 3.10 or newer.
- Document installing with pipx from the GitHub URL; keep uv for
  development.
- Add a Japanese README at `README_ja-JP.md`.

## 0.1.1 - 2026-08-28

- Rearrange furin every hour of playback: new stereo placement, pitches, and
  glass/metal mix (within `--material`).
- Drop the lowest glass and metal pitches, without raising the top of the set.
- Vary strike loudness and spacing with 1/f fluctuation, at about one
  strike per three of the previous rate.
- Shorten ring decay to about half the previous length.

## 0.1.0 - 2026-08-28

- Add a CLI that synthesizes furin (Japanese wind chime) strikes and plays
  them under a wandering breeze, with optional WAV export.
- Support glass, metal, and mixed timbres, wind presets, multiple voices,
  and a Python `render()` API.
- Shorten ring decay, vary length per strike, and stop the previous tone
  when a new strike starts so two furin do not ring at once.
- Shift the default glass timbre away from a metallic clang.
- Add `--volume` in the range 0–1, where 1 is the current maximum loudness.
