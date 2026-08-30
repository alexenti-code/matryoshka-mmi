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

### Models verified in daily real use (30.08.2026)

The 12B+ threshold above is not abstract: it is the floor observed on the
owner's setup, where these models run the memory discipline daily in real
work (long multi-session agent, real tasks):

| Model | Parameters | Status |
|---|---|---|
| DeepSeek V4 Flash 0731 | 284B total / 13B active (MoE, verified) | primary working model, ~17.5k sessions of daily use |
| DeepSeek V4 Pro 0813 | 1.6T total / 49B active (MoE, verified) | heavy reasoning |
| GLM 5.3 Flash | not officially disclosed | verified in daily use |
| Muse Spark 1.2 Contributor | not officially disclosed | verified in daily use |
| Qwen 3.7 Flash | not officially disclosed | verified in daily use (vision) |
| MiMo V2.5 | not officially disclosed | verified in daily use (vision) |
| Ring 2.6 1T | not officially disclosed | verified in daily use (reasoning) |

Local floor: **Gemma 4 12B** (quantized, ollama) — the smallest model on the
setup; smaller local models (e.g. Phi-4-mini ~3.8B) fail to run a tool-using
agent at all, and therefore cannot maintain the memory discipline either.

Parameter counts are listed only where officially confirmed; the rule is:
never invent parameters — verify against vendor documentation.
