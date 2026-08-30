# Changelog

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
