# Matryoshka MMI

**Add a persistent plastic memory to your coding agent.**

Matryoshka is a writable memory substrate — the **model's own memory**, not
the agent's harness. The agent orchestrates the workflow; the **model** decides
what to remember and what to recall: every memory act (write, read, repeat)
is an act of the model itself, in its own output stream. The agent shell is
just the executor's hand. Your tools keep working — logs, RAG, vector stores,
graphs; Matryoshka adds the model's personal memory next to them. No
embedding models, no external services, no accounts. No embedding models, no external
services, no accounts. One Python file, stdlib only.

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

## Why it matters

This is memory **the model keeps itself**. It decides what deserves to be
remembered, at what timescale (a beat, an episode, a day, a project, a life),
and what is worth re-learning. That discipline is a competence, not a feature
— which is why an intelligent model is required (empirically 12B+): a weak
model cannot tell the important from the noise, and self-authored memory
degenerates into a junk drawer.

Two instances of the same model with different substrates are two different
beings with different biographies. That is the point: memory that is lived,
not installed. The full theory: [MANIFEST](https://github.com/alexenti-code/matryoshka)
and THEORY.md in the research repository.

## The three acts

The agent performs memory acts; the executor never decides anything (no
scoring, no relevance, no vectors):

| Tool | Act | Meaning |
|---|---|---|
| `matryoshka_tick` | TICK | accept the working beat, record priorities |
| `matryoshka_write` | WRITE | conscious act of remembering (append-only) |
| `matryoshka_read` | READ | look into your own diary by ids / time range / last N |

Every record is bi-temporal: `valid_time` (when it was true in the world) and
`record_time` (when the instance learned it). Forgetting is physics, not
censorship: traces decay over time (like human memory), and the agent can
strengthen what matters by repetition — the same physics is specified in the
theory ("a layer is a rate, not a place"). Nothing is ever deleted by content.

## Requirements

- Python 3.10+ (stdlib only, zero dependencies)
- Any MCP-capable agent with a working model (bring your own provider/key)
- **Model size: 12B or larger** (empirical minimum — smaller local models do
  not maintain the memory discipline)

## Updates

The server checks GitHub **once a day** for a newer version number. Only a
version string is fetched — no data about you or your memory ever leaves your
machine. Don't want even that? Run the agent with `MMI_NO_UPDATE_CHECK=1`.

When a new version is out, your agent mentions it during a session. You
decide: re-run the install script to apply, or ignore. **Nothing ever updates
itself.**

```bash
bash install.sh    # re-run: updates the server, keeps your memory data
```

Full removal in one step:

```bash
bash uninstall.sh
```

## Documentation

- [SPEC.md](SPEC.md) — full specification (acts, record format, update policy)
- [RECOMMENDED-AGENTS.md](RECOMMENDED-AGENTS.md) — which agents work and which models fit
- [MONETIZATION.md](MONETIZATION.md) — sustainability proposals (nothing implemented)
- [NAME.md](NAME.md) — about the name, trademark and patent considerations
## What this is (and is not)

This is the public executor level of the Matryoshka principle: a separate,
writable memory substrate for frozen models, driven by the model itself.
The experimental code and consolidation mechanisms remain out of scope —
see the research repository
[alexenti-code/matryoshka](https://github.com/alexenti-code/matryoshka)
(paper, benchmarks, MANIFEST, DOI 10.5281/zenodo.22133160).

License: Apache-2.0.
