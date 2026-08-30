# Changelog

## 0.5.1 — 2026-08-30 — Honest edges (audit fixes)

Fixed
- **Stale update notice.** `install.sh` now removes `UPDATE_AVAILABLE` when
  applying a new server version; previously a served notice repeated
  forever after the user had updated.
- **REPEAT is validated.** Repeating a missing or non-WRITE id is now an
  explicit error, not a silent no-op record.
- **Weight math.** `math.exp` instead of a truncated hand-rolled constant;
  repeats are counted in one journal pass (O(N) per read instead of O(N²));
  `MMI_TAU_SCALE` ≤ 0 or NaN falls back to 1.0.
- **status.layers counts WRITE records only** — REPEAT acts no longer
  inflate layer counts.

Docs
- SPEC synced with the code (no hardcoded spec version; REPEAT added to the
  acts table; TICK documented as a write-only beat log; provenance wording
  now states plainly that `curl | bash` installs `main`, not a tag).
- README/README.ru: removed a duplicated sentence, the stale "~8 KB" claim,
  the misleading unconditional "asks for confirmation" (piped runs proceed
  non-interactively), and stated plainly that decay is symbolic physics in
  this executor (research target unchanged).
- Instruction block: a tick is a beat marker, not readable memory — durable
  priorities go through WRITE.
- DEVELOPERS.md: MONETIZATION.md reference points to .dev-exchange (the file
  is not in the repo); release procedure includes the .zenodo.json bump.

## 0.5.0 — 2026-08-30 — Friction: the matryoshka layers come alive

This release starts the final implementation of the core principle: layers
are not places but speeds. Every memory trace now decays continuously, and
the model itself decides what to re-learn.

Added
- **`matryoshka_repeat`** — the REPEAT act, conscious re-learning (learning
  by repetition, like a poem). Creates a NEW record referencing the original
  (append-only, history never rewritten); each repeat doubles the trace
  signal.
- **Trace weight** — every read now returns a `weight` per record:
  `(1 + repeats) · e^(−dt/τ)`. The layer is a time constant τ (beat 1h,
  episode 24h, day 168h, project 720h, life 8760h). A fresh trace is loud,
  an old one quiets down naturally — and a repeated one stays loud. Physics
  only: nothing is filtered, ranked or deleted by weight; quiet traces are
  still fully readable and repeatable.
- `MMI_TAU_SCALE` — owner dial in the temperature class: multiplies all τ
  (2.0 = the instance forgets twice as slowly). Factory τ per layer are
  documented in SPEC.md.
- `matryoshka_status` now reports the friction model, per-layer τ and the
  total repeat count.
- Instruction block: decisions are recorded as decision → outcome → lesson
  with a source; critical domains keep a pointer to the verifiable source,
  not the claim (memory hygiene doctrine, owner-approved).

This release starts the final implementation of the main principle — the
matryoshka memory with self-nested layers of different weights: fast traces
live inside slow ones, decay separates them by speed, and only the model's
own REPEAT act fights the friction. No thresholds, no content scoring, no
external deciders — the owner sets the physics, the model owns the content.

## 0.4.2 — 2026-08-30 — The program is replaceable; memory is not

The safety audit of the distribution found destructive defaults. All fixed.

Fixed
- **`uninstall.sh` no longer deletes the user's memory.** The default
  uninstall removes the program (server, MCP registrations, instruction
  blocks) and moves the memory data (`PHI.jsonl`, `PHI-archive.jsonl`,
  `TICKS.log`) to `~/.matryoshka-removed-<timestamp>/` with restore
  instructions printed. Deleting everything is an explicit opt-in:
  `uninstall.sh --purge` asks to type `PURGE` and refuses to run
  non-interactively.
- **Atomic journal rewrite.** Archive passes (memory dials) previously
  rewrote `PHI.jsonl` in place; a crash mid-write could truncate the
  journal. Rewrites now go to a temp file with `fsync` and `os.replace`.
- **`install.sh` versions itself from the repo's `VERSION` file**
  (single source of truth); the piped `curl | bash` path fetches the
  version from the same source. Previously a hardcoded stale `0.2.0`
  was stamped into `~/.matryoshka/VERSION`.
- **`install.sh` backs up everything it replaces**: previous server copy
  (`mmi_mcp.py.prev-<ts>`), previous `VERSION`, OpenCode config, and any
  instruction file that already contains a Matryoshka block. Existing
  Claude Code registrations are printed before being replaced.

Security
- Development constitution extended with "Force without destruction"
  (program vs data, opt-in destruction, unhappy-path testing) after an
  internal investigation of how the destructive uninstall came to be.

## 0.4.0 — 2026-08-29 — Memory dials

Added
- **Memory dials** — owner-set physics for the journal, continuous, no content
  decisions (constitutional class of `temperature`):
  - `MMI_MEMORY_VOLUME_MB` — active journal size cap in MB; when exceeded,
    oldest records move mechanically to `PHI-archive.jsonl` (append-only
    preserved, all fields intact). `0` = unlimited (default).
  - `MMI_FORGETTING_TEMPO_DAYS` — records older than N days (by `record_time`)
    leave the active journal into the archive at the next tool call. `0` =
    never (default).
- `matryoshka_status` now reports `dials` and `archived` count.
- Reads by `ids`/`range` search the active journal **and** the archive;
  recency reads (`last`) see the active journal only.

Factory settings (not exposed, research scope)
- `write_gain`, `curiosity_gain`, `recall_sharpness`, `repeat_gain` —
  require the plastic parameter body (private research repo). Documented in
  SPEC as factory settings; do not expose or emulate in the journal.

Constitutional note
- Both dials are continuous time/size physics: no thresholds on content, no
  scoring, no selection. `forgetting_tempo` does not decide *what* to forget —
  only when, by `record_time`, exactly like `temperature` does not decide
  *what* to say.
