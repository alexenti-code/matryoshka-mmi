#!/usr/bin/env bash
# Matryoshka MMI uninstaller.
#
# The program is yours to remove; the memory data belongs to the user and
# the user's model. Therefore:
#
#   bash uninstall.sh            remove the PROGRAM (server, MCP registrations,
#                                instruction blocks). Memory data
#                                (PHI.jsonl, PHI-archive.jsonl, TICKS.log)
#                                is MOVED to ~/.matryoshka-removed-<timestamp>/
#                                and kept.
#   bash uninstall.sh --purge    delete EVERYTHING, including memory data.
#                                Asks to type PURGE; refuses in non-interactive
#                                shells. This is the only destructive path.
set -euo pipefail

DEST="$HOME/.matryoshka"
STAMP="$(date +%Y%m%d-%H%M%S)"
KEEP="$HOME/.matryoshka-removed-$STAMP"
PURGE=0
[ "${1:-}" = "--purge" ] && PURGE=1

command -v claude >/dev/null 2>&1 && claude mcp remove matryoshka --scope user 2>/dev/null || true
command -v prime-agent >/dev/null 2>&1 && prime-agent mcp remove matryoshka 2>/dev/null || true

python3 - <<'PYEOF'
import json, os, shutil
p = os.path.expanduser("~/.config/opencode/opencode.json")
if os.path.exists(p):
    cfg = json.load(open(p))
    if cfg.get("mcp", {}).pop("matryoshka", None) is not None:
        shutil.copy2(p, p + ".bak-mmi-uninstall")
        json.dump(cfg, open(p, "w"), indent=2, ensure_ascii=False)
        print("removed: OpenCode entry (config backup: opencode.json.bak-mmi-uninstall)")
PYEOF

python3 - "$STAMP" <<'PYEOF'
import os, shutil, sys
stamp = sys.argv[1]
for p in [os.path.expanduser("~/.claude/CLAUDE.md"),
          os.path.expanduser("~/.config/opencode/AGENTS.md"),
          os.path.expanduser("~/AGENTS.md")]:
    if not os.path.exists(p):
        continue
    t = open(p).read()
    i, j = t.find("# BEGIN MATRYOSHKA MEMORY"), t.find("# END MATRYOSHKA MEMORY")
    if i != -1 and j != -1:
        shutil.copy2(p, p + ".bak-mmi-" + stamp)
        t = (t[:i] + t[j + len("# END MATRYOSHKA MEMORY"):]).strip() + "\n"
        open(p, "w").write(t)
        print(f"removed instruction block: {p} (backup: {p}.bak-mmi-{stamp})")
PYEOF

if [ "$PURGE" = "1" ]; then
  if [ ! -t 0 ]; then
    echo "refusing to purge memory data in a non-interactive shell."
    echo "run it interactively: bash uninstall.sh --purge"
    exit 1
  fi
  printf '%s\n' "This deletes EVERYTHING under $DEST," \
    "including PHI.jsonl — the memory your model has written." \
    "Type PURGE to confirm (anything else aborts):"
  read -r REPLY
  [ "$REPLY" = "PURGE" ] || { echo "Aborted. Memory data kept."; exit 1; }
  rm -rf "$DEST"
  echo "Matryoshka MMI and all memory data deleted."
else
  mkdir -p "$KEEP"
  moved=0
  for f in PHI.jsonl PHI-archive.jsonl TICKS.log; do
    if [ -f "$DEST/$f" ]; then mv "$DEST/$f" "$KEEP/$f"; moved=$((moved+1)); fi
  done
  rm -rf "$DEST"
  echo "Matryoshka MMI removed. Memory data kept: $KEEP ($moved file(s))."
  echo "To restore after a future install:  mv $KEEP/* ~/.matryoshka/"
fi
