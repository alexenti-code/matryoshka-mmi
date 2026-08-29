# Recommended MCP-capable coding agents

Matryoshka MMI works with any MCP client. Verified:

| Agent | Status | Notes |
|---|---|---|
| **Claude Code** (Anthropic) | verified | `claude mcp add`; free/paid Anthropic account or any compatible provider |
| **OpenCode** (open source) | verified | config-based provider setup; works with OpenAI-compatible endpoints |
| **Prime Agent** | verified | `prime-agent mcp add` |

Recommended, MCP-capable, should work out of the box:

| Agent | Notes |
|---|---|
| **Codex CLI** (OpenAI) | popular terminal agent, MCP support |
| **Cline / Roo Code** (VS Code) | MCP marketplace, large user base |
| **Zed** | editor with built-in MCP support, fast growing |
| **Cursor** | major AI IDE, MCP support |
| **Windsurf** (Codeium) | MCP support in Cascade |
| **Gemini CLI** (Google) | free tier, MCP support |

Requirements for the user's side: any one of these agents, a working model
(any provider/key), Python 3.10+. Matryoshka is model-agnostic: the memory
substrate does not depend on the model provider.

## Minimum model size

**Empirically: 12B+ is required.** Models below 12B reliably fail at the
memory discipline (they skip reads at session start, forget to write, or
misuse the act parameters). This is an empirical limit observed in testing,
not a guess. Recommend to users:

- 12B and up (local or cloud): works.
- Below 12B: not supported. The tools will connect, but the model will not
  maintain the memory habit — do not report this as a Matryoshka bug.
