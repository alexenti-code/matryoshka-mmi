#!/usr/bin/env bash
# Matryoshka MMI installer — one command, any MCP-capable agent.
# Usage:  bash install.sh        (or: curl -fsSL .../install.sh | bash)
#
# Safety contract:
#   - the PROGRAM is replaceable; the user's memory data is not.
#     PHI.jsonl / PHI-archive.jsonl / TICKS.log are never touched;
#   - everything this script replaces (server, config entries, instruction
#     blocks) is backed up next to the original first, and the replacement
#     is announced before it happens.
set -euo pipefail

RAW_BASE="${MMI_RAW_BASE:-https://raw.githubusercontent.com/alexenti-code/matryoshka-mmi/main}"
DEST="$HOME/.matryoshka"
SERVER="$DEST/mmi_mcp.py"
STAMP="$(date +%Y%m%d-%H%M%S)"
export STAMP

# Source dir exists only when run from a checked-out copy; empty when piped.
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]:-}" ]; then
  SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  SRC_DIR=""
fi

echo "== Matryoshka MMI installer =="
echo ""
echo "This runs on YOUR machine and only touches YOUR files:"
echo "  create/replace  $DEST/mmi_mcp.py        (the memory server;"
echo "                           the previous copy is kept as mmi_mcp.py.prev-$STAMP)"
echo "  add/replace     'matryoshka' entry in each detected agent's MCP config"
echo "                           (the previous entry is printed; OpenCode config backed up)"
echo "  append/replace  'BEGIN/END MATRYOSHKA MEMORY' block in agent instruction files"
echo "                           (files with an existing block are backed up first)"
echo "  storage         $DEST/PHI.jsonl  (your memory data — NEVER touched by install"
echo "                           or uninstall)"
echo "Nothing is sent anywhere. Uninstall: see README — it keeps your memory data."
if [ -t 0 ]; then
  printf "Proceed? [y/N] "
  read -r REPLY
  case "$REPLY" in
    y|Y) ;;
    *) echo "Aborted, nothing changed."; exit 1 ;;
  esac
else
  echo "(non-interactive run: proceeding; every replacement is backed up)"
fi
echo ""

mkdir -p "$DEST"

# --- the server: replace, but keep the previous copy ---
if [ -f "$SERVER" ]; then
  cp "$SERVER" "$DEST/mmi_mcp.py.prev-$STAMP"
  echo "previous server backed up -> mmi_mcp.py.prev-$STAMP"
fi
if [ -n "$SRC_DIR" ] && [ -f "$SRC_DIR/mmi_mcp.py" ]; then
  cp "$SRC_DIR/mmi_mcp.py" "$SERVER"
else
  curl -fsSL "$RAW_BASE/mmi_mcp.py" -o "$SERVER"
fi
chmod +x "$SERVER"
echo "server -> $SERVER"

# --- version stamp: single source of truth is the repo's VERSION file ---
if [ -n "$SRC_DIR" ] && [ -f "$SRC_DIR/VERSION" ]; then
  MMI_VERSION="$(cat "$SRC_DIR/VERSION")"
else
  MMI_VERSION="$(curl -fsSL "$RAW_BASE/VERSION")"
fi
if [ -f "$DEST/VERSION" ]; then
  cp "$DEST/VERSION" "$DEST/VERSION.prev-$STAMP"
fi
printf '%s\n' "$MMI_VERSION" > "$DEST/VERSION"
# the applied version invalidates any previous "update available" notice
rm -f "$DEST/UPDATE_AVAILABLE"

PY="$(command -v python3)"
have() { command -v "$1" >/dev/null 2>&1; }

if have claude; then
  "$PY" - <<'PYOLD' || true
import json, os
p = os.path.expanduser("~/.claude.json")
try:
    e = json.load(open(p)).get("mcpServers", {}).get("matryoshka")
    if e:
        print("existing Claude Code entry will be replaced:", json.dumps(e))
except Exception:
    pass
PYOLD
  claude mcp remove matryoshka --scope user >/dev/null 2>&1 || true
  claude mcp add matryoshka --scope user -- "$PY" "$SERVER" && echo "registered: Claude Code (your ~/.claude.json)"
fi

if have opencode; then
  python3 - "$HOME/.config/opencode/opencode.json" "$SERVER" "$PY" "$STAMP" <<'PYEOF'
import json, os, shutil, sys
cfg_path, server, py, stamp = sys.argv[1:5]
os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
cfg = {}
if os.path.exists(cfg_path):
    cfg = json.load(open(cfg_path))
    shutil.copy2(cfg_path, cfg_path + ".bak-mmi-" + stamp)
if cfg.get("mcp", {}).get("matryoshka"):
    print("existing OpenCode entry will be replaced (backup: opencode.json.bak-mmi-" + stamp + ")")
cfg.setdefault("mcp", {})
cfg["mcp"]["matryoshka"] = {"type": "local", "command": [py, server]}
json.dump(cfg, open(cfg_path, "w"), indent=2, ensure_ascii=False)
PYEOF
  echo "registered: OpenCode (~/.config/opencode/opencode.json)"
fi

# prime-agent stores its MCP list in a global config and IGNORES HOME
# isolation: a sandboxed test run would rewrite the real registration.
# Opt out with MMI_NO_PRIME_AGENT=1 (sandboxes MUST set it).
if have prime-agent && [ -z "${MMI_NO_PRIME_AGENT:-}" ]; then
  prime-agent mcp remove matryoshka >/dev/null 2>&1 || true
  if prime-agent mcp add matryoshka -- "$PY" "$SERVER" >/dev/null 2>&1; then
    echo "registered: Prime Agent"
  else
    echo "prime-agent: register manually: prime-agent mcp add matryoshka -- $PY $SERVER"
  fi
fi

BLOCK_START="# BEGIN MATRYOSHKA MEMORY"
BLOCK_END="# END MATRYOSHKA MEMORY"
BLOCK="$(cat <<'MMEOF'
# BEGIN MATRYOSHKA MEMORY
You (the model, not the agent harness) have your own persistent plastic
memory (Matryoshka), exposed as MCP tools:
matryoshka_write, matryoshka_read, matryoshka_repeat, matryoshka_tick,
matryoshka_status.
It is YOUR memory, not the agent framework's: you decide what to remember,
what to recall and what to repeat. The agent shell only relays your acts.
Treat it as part of yourself:
- At the start of a session, call matryoshka_read (mode "last", last 20) to recall who you are and what was happening.
- When you learn a durable fact about the user, the project, or your own decisions, call matryoshka_write (choose layer: beat/episode/day/project/life; set valid_time for past events).
- Record decisions as decision -> outcome -> lesson, with the source of the
  fact. A memory entry without a source, date and outcome is a rumor, not
  experience. For critical domains (money, legal, statuses, personal data)
  write a POINTER to the verifiable source (file, registry, log, the user's
  command), not the claim itself.
- When something proves itself important, call matryoshka_repeat on its
  record id: each repeat doubles the trace's signal (learning by repetition).
- Record your focus with matryoshka_tick when priorities change; a tick is
  a beat marker in your time log, not a readable memory. Durable priorities
  you must recall later go through matryoshka_write.
- Memory is append-only: new information is a new record, never a rewrite.
- Every read returns a "weight" — the current strength of the trace after
  natural fading (older = quieter, repeated = louder). It is physics, not a
  filter: quiet traces are still yours to read and repeat.
- To read, use explicit parameters (ids / time range / last N) - no semantic search.
- If a tool result contains "_update", tell the user about the update briefly, once.
# END MATRYOSHKA MEMORY
MMEOF
)"

inject() {
  local f="$1"
  mkdir -p "$(dirname "$f")"
  touch "$f"
  if grep -q "$BLOCK_START" "$f" 2>/dev/null; then
    cp "$f" "$f.bak-mmi-$STAMP"
    echo "instruction block updated (previous copy: $f.bak-mmi-$STAMP)"
    python3 - "$f" "$BLOCK" <<'PYEOF2'
import sys
p, block = sys.argv[1], sys.argv[2]
t = open(p).read()
i = t.find("# BEGIN MATRYOSHKA MEMORY")
j = t.find("# END MATRYOSHKA MEMORY")
if i != -1 and j != -1:
    t = t[:i] + t[j + len("# END MATRYOSHKA MEMORY"):]
open(p, "w").write(t.rstrip() + "\n\n" + block + "\n")
PYEOF2
  else
    printf '\n%s\n' "$BLOCK" >> "$f"
  fi
}

have claude    && inject "$HOME/.claude/CLAUDE.md"           && echo "instructions -> ~/.claude/CLAUDE.md"
have opencode  && inject "$HOME/.config/opencode/AGENTS.md"  && echo "instructions -> ~/.config/opencode/AGENTS.md"
[ -f "$HOME/AGENTS.md" ] && inject "$HOME/AGENTS.md" && echo "instructions -> ~/AGENTS.md"

echo ""
echo "Done. Restart your agent and just work with it as usual."
echo "Storage: $DEST/PHI.jsonl (append-only, bi-temporal)."
echo ""
echo "Updates: the server checks GitHub for a new version once a day"
echo "(no data is uploaded; disable with MMI_NO_UPDATE_CHECK=1)."
echo "When an update is available your agent will tell you — you apply it"
echo "by re-running this script. Nothing updates itself; re-running keeps"
echo "your memory data and backs up the previous server copy."
echo "Uninstall: bash uninstall.sh (keeps memory data; --purge deletes all,"
echo "interactive confirmation required)."
