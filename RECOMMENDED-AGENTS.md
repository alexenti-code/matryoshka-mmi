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

## Minimal model recommendations

Any modern agentic model handles the three acts. Notes:

- Instruct models (DeepSeek, Qwen, Llama, Mistral): work fine; the instruction
  block in the agent's context file drives the behaviour.
- Smaller local models (7-9B): may skip the "read memory at session start"
  habit. The tool descriptions are written to be self-explanatory; if a model
  still ignores memory, remind it once: "use your matryoshka memory tools".
