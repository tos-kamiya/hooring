# Repository Guidelines

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) (semantic
commit messages) for every commit. Write them in English.

```
<type>(<scope>): <subject>

<body>
```

- `type` is required. Common types:
  - `feat`: a user-visible feature
  - `fix`: a bug fix or sound-design correction
  - `docs`: README, session notes, release notes, this file
  - `chore`: version bumps, tooling, lockfile-only work
  - `refactor`, `test`, `perf` as needed
- `scope` is optional (`synth`, `audio`, `cli`, …). Omit it for repo-wide
  changes.
- `subject` is imperative, lowercase, with no trailing period. Aim for
  ≤ 50 characters.
- `body` is optional. Separate it from the subject with a blank line.
  Explain why, wrap at ~72 characters, and keep one logical change per
  commit.

Examples from this repository:

```
feat(audio): add a volume control capped at the current level

Introduce --volume in the range 0–1, where 1 is today's maximum.
```

```
chore: bump version to 0.1.0
```

Bump `hooring.__about__.__version__` in a dedicated `chore:` commit.
Record the matching public notes in `release-notes.md` as part of that
bump (see below).

## Documentation Roles

Keep public release history and internal session history in separate
files. Do not mix user-visible shipped behavior with implementation
rationale.

### `release-notes.md`

Public, user-facing release history. Linked from the README.

- Record shipped behavior: CLI flags, timbres, playback, WAV export, the
  `render()` API. Write for people who install and run `hooring`.
- Do not record internals: uv/Hatch, decay constants, test counts, or
  commit tactics. Those belong in `dev-notes/`.
- Layout, with `Unreleased` first and dated versions newest after it:

  ```markdown
  # hooring Release Notes

  ## Unreleased

  ## 0.1.0 - 2026-08-28

  - User-facing bullet.
  ```

- While work is unreleased, append bullets under `## Unreleased`.
- On a version bump, move those bullets into a new
  `## X.Y.Z - YYYY-MM-DD` section and leave `Unreleased` empty. Review
  the change set back to the previous version-bump commit so the entry
  covers the full release window, not only the immediate parent commit.

### `dev-notes/`

Internal development history. Not user documentation.

- Session logs live at `dev-notes/session-YYYY-MM-DD.md`.
- Capture the why: topic, decision, rationale, and a result when useful.
  Command transcripts are secondary.
- This is the place for internals that `release-notes.md` omits
  (tooling, constants, rejected alternatives).
- At the start of work, create the session file with a short header
  (date, scope). At the end, add a short summary if commits, a version
  bump, or follow-ups landed.

```markdown
# Session YYYY-MM-DD

Scope: …

- Topic: {feature or problem}
  - Decision: …
  - Rationale: …
  - Result: …          # optional
```
