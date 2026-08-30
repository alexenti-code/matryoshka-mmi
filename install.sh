#!/usr/bin/env bash
# Matryoshka MMI installer — one command, any MCP-capable agent.
# Usage:  bash install.sh
set -euo pipefail

MMI_VERSION="0.2.0"
DEST="$HOME/.matryoshka"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
SERVER="$DEST/mmi_mcp.py"

echo "== Matryoshka MMI installer =="
echo ""
echo "This runs on YOUR machine and only touches YOUR files:"
echo "  create/replace  $DEST/mmi_mcp.py        (the memory server)"
echo "  add entry       'matryoshka' into each detected agent's MCP config"
echo "  append block    'BEGIN/END MATRYOSHKA MEMORY' into agent instruction files"
echo "  storage         $DEST/PHI.jsonl  (created later, by you/your agent)"
echo "Nothing is sent anywhere. Uninstall: see README."
if [ -t 0 ]; then
  printf "Proceed? [y/N] "
  read -r REPLY
  case "$REPLY" in
    y|Y) ;;
    *) echo "Aborted, nothing changed."; exit 1 ;;
  esac
fi
echo ""

mkdir -p "$DEST"
if [ -f "$SRC_DIR/mmi_mcp.py" ]; then
  cp "$SRC_DIR/mmi_mcp.py" "$SERVER"
else
  curl -fsSL "${MMI_RAW_BASE:-https://raw.githubusercontent.com/alexenti-code/matryoshka-mmi/main}/mmi_mcp.py" -o "$SERVER"
fi
chmod +x "$SERVER"
echo "server -> $SERVER"

printf '%s\n' "$MMI_VERSION" > "$DEST/VERSION"

PY="$(command -v python3)"
have() { command -v "$1" >/dev/null 2>&1; }

if have claude; then
  claude mcp remove matryoshka --scope user >/dev/null 2>&1 || true
  claude mcp add matryoshka --scope user -- "$PY" "$SERVER" && echo "registered: Claude Code (your ~/.claude.json)"
fi

if have opencode; then
  python3 - "$HOME/.config/opencode/opencode.json" "$SERVER" "$PY" <<'PYEOF'
import json, os, sys
cfg_path, server, py = sys.argv[1:4]
os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
cfg = {}
if os.path.exists(cfg_path):
    cfg = json.load(open(cfg_path))
cfg.setdefault("mcp", {})
cfg["mcp"]["matryoshka"] = {"type": "local", "command": [py, server]}
json.dump(cfg, open(cfg_path, "w"), indent=2, ensure_ascii=False)
PYEOF
  echo "registered: OpenCode (~/.config/opencode/opencode.json)"
fi

if have prime-agent; then
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
matryoshka_write, matryoshka_read, matryoshka_tick.
It is YOUR memory, not the agent framework's: you decide what to remember,
what to recall and what to repeat. The agent shell only relays your acts.
Treat it as part of yourself:
- At the start of a session, call matryoshka_read (mode "last", last 20) to recall who you are and what was happening.
- When you learn a durable fact about the user, the project, or your own decisions, call matryoshka_write (choose layer: beat/episode/day/project/life; set valid_time for past events).
- Record your focus with matryoshka_tick when priorities change.
- Memory is append-only: new information is a new record, never a rewrite.
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
echo "by re-running this script. Nothing updates itself."
