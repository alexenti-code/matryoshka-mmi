# Monetization — proposals (NOT implemented)

Status: design options only. Nothing in the codebase implements any of this
as of v0.3. Decision is reserved for the author.

## Context: how similar projects sustain themselves

| Project | Model |
|---|---|
| MCP servers (Anthropic ecosystem) | free/open, value accrues to the platform |
| Plausible, Ente, Ghost | open core + hosted paid service |
| Ollama, LM Studio | free product; company monetizes adjacent services |
| oh-my-zsh, homebrew | donations/sponsors only |
| Tailscale | OSS client + paid cloud coordination |

Lesson: small open-source tools live on **donations**; sustainable income for
this class of product historically comes from a **hosted/companion paid
service**, not from paywalling local code.

## Option A — Donations (recommended to start; zero product risk)

- GitHub Sponsors (personal, alexenti-code) + a "Sponsor" link in README.
- Optional: "Support Matryoshka" line in the update notice once a year, max.
- Cost: near zero. Risk: none. Ceiling: low.

## Option B — Open core: local free, cloud sync paid

The natural boundary is already in the architecture: memory is a local file.

- Free (Apache-2.0, forever): everything that exists today.
- Paid (later): **Matryoshka Cloud** — encrypted backup/sync of PHI.jsonl
  across machines, plus a web viewer of your memory diary.
- Precedent: Syncthing (free) vs sync.com; Obsidian (local free, paid sync).
- Requires: server component, end-to-end encryption, billing. Big step.

## Option C — Paid tier of the substrate itself

The research repo keeps consolidation and the Rust daemon (mmid) out of the
public scope. A future "Matryoshka Pro" could distribute:

- the compiled Rust daemon (mmap storage, p99 targets from MMI-DEMON-TZ),
- consolidation/compression of the journal,
- priority support for teams.

Danger: fragmenting the community. Use only if a paying user base exists.

## Option D — Dual licensing

Apache-2.0 for the server + a commercial license for companies embedding MMI
into a paid product. Standard (Qt, MongoDB historically). Legal overhead.

## Recommendation

Start with Option A (GitHub Sponsors button, no code changes). Revisit B/C
only when there is evidence of demand (stars, issues asking for sync).
