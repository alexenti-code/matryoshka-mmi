# Matryoshka MMI

**Give your coding agent a persistent plastic memory.**

Matryoshka is a writable memory substrate that your agent treats as part of
itself — not a vector database, not RAG. The agent decides what to remember,
writes facts into an append-only bi-temporal store, and flips through its own
diary with explicit reads. No embedding models, no external services, no
accounts. One Python file, stdlib only.

Works with **Claude Code**, **OpenCode**, and **Prime Agent** (anything that
speaks MCP). Your model, your key, your memory — everything stays on your
machine.

## Install

```bash
git clone https://github.com/alexenti-code/matryoshka-mmi
cd matryoshka-mmi && bash install.sh
```

or one line (once published):

```bash
curl -fsSL https://raw.githubusercontent.com/alexenti-code/matryoshka-mmi/main/install.sh | bash
```

The installer:
1. puts the MCP server into `~/.matryoshka/`,
2. registers it in every agent it finds on your machine (Claude Code / OpenCode / Prime Agent),
3. adds a short memory instruction to the agent's context so it starts using the memory as part of itself.

## Try it (60 seconds)

Restart your agent, then say:

```
Read your matryoshka memory. Then remember: my name is <...>, I prefer <...>.
```

Next session, the agent recalls it on its own. Check the store yourself:

```bash
cat ~/.matryoshka/PHI.jsonl
```

## The three acts

The agent performs memory acts; the executor never decides anything (no
scoring, no relevance, no vectors):

| Tool | Act | Meaning |
|---|---|---|
| `matryoshka_tick` | TICK | accept the working beat, record priorities |
| `matryoshka_write` | WRITE | conscious act of remembering (append-only) |
| `matryoshka_read` | READ | look into your own diary by ids / time range / last N |

Every record is bi-temporal: `valid_time` (when it was true in the world) and
`record_time` (when the instance learned it). New information is a new record —
history is never erased.

## Requirements

- Python 3.10+ (stdlib only, zero dependencies)
- Any MCP-capable agent with a working model (bring your own provider/key)

## Files

```
~/.matryoshka/
├── mmi_mcp.py     ← MCP server (the executor "hand")
├── PHI.jsonl      ← plastic substrate: append-only memory records
└── TICKS.log      ← the instance's own time (ticks)
```

## Uninstall

```bash
claude mcp remove matryoshka --scope user 2>/dev/null
prime-agent mcp remove matryoshka 2>/dev/null
rm -rf ~/.matryoshka
```
(and remove the MATRYOSHKA MEMORY block from `~/.claude/CLAUDE.md` if present)

## What this is (and is not)

This is the public executor level of the Matryoshka principle: a separate,
writable memory substrate for frozen models, driven by the model itself.
The experimental code and consolidation mechanisms remain out of scope —
see the research repository
[alexenti-code/matryoshka](https://github.com/alexenti-code/matryoshka)
(paper, benchmarks, MANIFEST, DOI 10.5281/zenodo.22133160).

License: Apache-2.0.
