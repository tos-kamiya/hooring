# hooring Release Notes

## Unreleased

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
