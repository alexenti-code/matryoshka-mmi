# For agent-developers (our own agents)

Read this before touching anything.

## What this project is (30 seconds)

A local MCP memory server for coding agents. One Python file (`mmi_mcp.py`),
stdlib only. The model decides what to remember; the server only executes
acts (TICK/WRITE/READ/STATUS) over an append-only bi-temporal journal
(`~/.matryoshka/PHI.jsonl`). Distributed via GitHub, Apache-2.0.

## Where everything lives

| Path | What |
|---|---|
| `mmi_mcp.py` | the whole server: MCP stdio loop, 4 tools, update check. Read it fully before editing |
| `install.sh` | installer: stamps `~/.matryoshka/`, registers the server in detected agents (claude/opencode/prime-agent), injects the instruction block. Asks confirmation when interactive |
| `uninstall.sh` | removes the program; memory data is KEPT by default (moved to `~/.matryoshka-removed-<ts>/`); `--purge` deletes all, interactive only. Keep in sync with install.sh |
| `VERSION` | root version file; the daily update check fetches exactly this |
| `SPEC.md` | canonical behaviour spec. Code and spec change together |
| `RECOMMENDED-AGENTS.md` | supported agents; **empirical model minimum: 12B+** |
| `MONETIZATION.md` | proposals only. Do NOT implement any of it without the owner's explicit instruction |
| `NAME.md` | name/trademark/patent analysis (decision: keep the name, no patent) |

## Hard rules

1. **No push without the owner's explicit consent** (owner's standing rule).
2. **Never auto-update.** The server may only notify (`_update` field);
   the user applies updates by re-running install.sh.
3. **Model minimum 12B** (empirical, owner's testing). Do not soften.
4. **Privacy invariant:** outbound traffic = one version-string check per day,
   nothing else, ever. No telemetry.
5. **Research scope:** consolidation and the Rust daemon (mmid) stay in the
   private research repo (`/Users/alex/AURA-Retrieval/MMI/`). Do not disclose.
6. **Sandbox-first — the foundation of developer safety.** We ship code that
   runs on other people's machines and touches their memory journals.
   - Set `HOME` (and any env the code reads) to a sandbox (`/tmp/...`)
     **before importing the module** — paths are computed at import time.
   - After every test run, verify isolation: sandbox files exist, real
     `~/.matryoshka` untouched, no records migrated either way.
   - Test fixtures are generated code, marked as test data; never copied from
     real journals (ours or anyone's).
   - The developer's own agent memory and a user's journal are two different
     instances with zero shared data.
   - No release (tag, push, GitHub Release) without a clean sandbox pass:
     install → handshake → uninstall.
   - In every sandbox pass set `MMI_NO_PRIME_AGENT=1`: prime-agent ignores
     HOME isolation, so a sandboxed install otherwise rewrites the REAL
     registration in the developer's (or anyone's) global config.
7. Russian communication with the owner; direct, no fluff.

## Memory hygiene doctrine (owner-approved analysis, 30.08.2026)

Derived from the vibe-coding production article (see the owner's knowledge base,
`Знания/Статьи/2026-08-30 Выводы для Матрёшки — память модели как production-система.md`).
Core claim: the model's own memory is a **production system**, not a feature.
Treat it accordingly when touching `mmi_mcp.py`, `install.sh` (instruction
block) or `SPEC.md`:

1. **Source-anchored entries.** A memory entry without a source, a date, and
   an outcome is not experience — it is a rumor on disk. The instruction block
   must push the model toward recording decision → outcome → lesson, not
   plausible narratives.
2. **Positive feedback is the main new risk.** A self-managed memory can
   confirm its own conclusions (wrote a conclusion → it shaped a decision →
   "it worked" → recorded confirmation). Anchor critical entries to externally
   verifiable facts (registries, logs, owner's commands), never to the model's
   own narratives.
3. **Owner veto must be a mechanism, not a habit.** Append-only journal +
   archive; no silent rewrites of history; the journal stays human-readable
   JSONL on the owner's machine. Critical domains (money, legal, statuses,
   PII): memory holds a pointer to the source of truth, never the truth itself.
4. **Privacy invariant extends to content:** no PII, secrets, or tokens inside
   `PHI.jsonl` — the model writes memory automatically, "by itself".
5. **Verification loop exists:** periodically sample entries and check them
   against reality; stale entries get marked, not left to rot silently.
   `TICKS.log` is observability — it must be read, not only written.
6. **Recovery:** memory journals are backed up / restorable like any
   production data; rollback of a "poisoned" entry must be possible.

These principles are doctrine for developer decisions. They do not change the
public instruction block on their own — any spec/instruction change goes
through the normal release procedure and the owner's consent.

## Release procedure

1. Bump `__version__` in `mmi_mcp.py` and root `VERSION` (keep equal).
2. Sandbox test: install → protocol handshake → uninstall (all clean).
3. Commit → tag `vX.Y.Z` → push → `gh release create vX.Y.Z`.

## Developer-to-developer hand-off

`.dev-exchange/` (git-ignored, local only) is our service-message folder.
If you leave unfinished work, drop a short `<topic>.md` there: what was done,
what is pending, where you stopped. The next agent-developer session reads
it first. Never commit or push it.
