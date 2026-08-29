#!/usr/bin/env bash
# Matryoshka MMI uninstaller — removes everything the installer added.
set -euo pipefail
DEST="$HOME/.matryoshka"

command -v claude >/dev/null 2>&1 && claude mcp remove matryoshka --scope user 2>/dev/null || true
command -v prime-agent >/dev/null 2>&1 && prime-agent mcp remove matryoshka 2>/dev/null || true

python3 - <<'PYEOF'
import json, os
p = os.path.expanduser("~/.config/opencode/opencode.json")
if os.path.exists(p):
    cfg = json.load(open(p))
    if cfg.get("mcp", {}).pop("matryoshka", None) is not None:
        json.dump(cfg, open(p, "w"), indent=2, ensure_ascii=False)
        print("removed: OpenCode entry")
PYEOF

python3 - <<'PYEOF'
import os, re
for p in [os.path.expanduser("~/.claude/CLAUDE.md"),
          os.path.expanduser("~/.config/opencode/AGENTS.md"),
          os.path.expanduser("~/AGENTS.md")]:
    if not os.path.exists(p):
        continue
    t = open(p).read()
    i, j = t.find("# BEGIN MATRYOSHKA MEMORY"), t.find("# END MATRYOSHKA MEMORY")
    if i != -1 and j != -1:
        t = (t[:i] + t[j + len("# END MATRYOSHKA MEMORY"):]).strip() + "\n"
        open(p, "w").write(t)
        print(f"removed instruction block: {p}")
PYEOF

rm -rf "$DEST"
echo "Matryoshka MMI fully removed (memory data at $DEST deleted)."
