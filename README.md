# Matryoshka MMI

**Add a persistent plastic memory to your coding agent.**

Matryoshka is a writable memory substrate your agent treats as part of
itself — not a vector database, not RAG. The agent decides what to remember,
writes facts into an append-only bi-temporal store, and flips through its own
diary with explicit reads. No embedding models, no external services, no
accounts. One Python file, stdlib only.

Works with **Claude Code**, **OpenCode**, and **Prime Agent** (anything that
speaks MCP). Your model, your key, your memory — everything stays on your
machine.

## What the installer does — exactly

Everything happens **on your own machine, in your own home directory**.
Nothing is uploaded, nothing is sent anywhere, no remote account is involved.

Before changing anything the installer prints the list of files it will touch
and asks for confirmation. It only ever:

1. Creates `~/.matryoshka/` and puts two files there:
   - `mmi_mcp.py` — the memory server (a local program, ~8 KB of Python);
   - later, your own memory data: `PHI.jsonl`, `TICKS.log`.
2. Adds **one entry** named `matryoshka` to the config of each coding agent
   it finds **on your machine** — only so that agent knows the memory server
   exists:
   - Claude Code: `~/.claude.json` → `mcpServers`
   - OpenCode: `~/.config/opencode/opencode.json` → `mcp`
   - Prime Agent: its user MCP list
3. Appends a clearly-marked text block (`BEGIN/END MATRYOSHKA MEMORY`) to the
   agent's instruction file (`~/.claude/CLAUDE.md` etc.), teaching the agent
   when to read and write its memory.

That is all. No other files are read or modified. Full removal:

```bash
claude mcp remove matryoshka --scope user   # if you use Claude Code
prime-agent mcp remove matryoshka           # if you use Prime Agent
# + delete the "matryoshka" entry in ~/.config/opencode/opencode.json, if you use OpenCode
# + delete the MATRYOSHKA MEMORY block from ~/.claude/CLAUDE.md
rm -rf ~/.matryoshka
```

## Install

```bash
git clone https://github.com/alexenti-code/matryoshka-mmi
cd matryoshka-mmi && bash install.sh
```

or one line:

```bash
curl -fsSL https://raw.githubusercontent.com/alexenti-code/matryoshka-mmi/main/install.sh | bash
```

## Use it

Restart your agent. That's it — after that you just work with your agent as
usual. Nothing to type, no commands to learn.

Under the hood the agent reads its memory at the start of every session and
writes down durable facts on its own (who you are, your project, decisions
you made together). Ask it next day "what do you remember about me?" and it
will answer — no special phrases were ever needed.

Curious what it stored? Your data is right there:

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

## What this is (and is not)

This is the public executor level of the Matryoshka principle: a separate,
writable memory substrate for frozen models, driven by the model itself.
The experimental code and consolidation mechanisms remain out of scope —
see the research repository
[alexenti-code/matryoshka](https://github.com/alexenti-code/matryoshka)
(paper, benchmarks, MANIFEST, DOI 10.5281/zenodo.22133160).

License: Apache-2.0.
