# hooring Release Notes

## Unreleased

## 0.1.0 - 2026-08-28

- Add a CLI that synthesizes furin (Japanese wind chime) strikes and plays
  them under a wandering breeze, with optional WAV export.
- Support glass, metal, and mixed timbres, wind presets, multiple voices,
  and a Python `render()` API.
- Shorten ring decay, vary length per strike, and stop the previous tone
  when a new strike starts so two furin do not ring at once.
- Shift the default glass timbre away from a metallic clang.
- Add `--volume` in the range 0–1, where 1 is the current maximum loudness.
