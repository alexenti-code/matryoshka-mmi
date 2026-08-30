# Changelog

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
