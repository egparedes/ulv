# development/ — repo process memory

Everything agents and developers need to work on this repo: conventions,
decisions, and the per-feature work-document lifecycle. This tree is
**repo-internal** — never published, never linked from a documentation site.
User-facing documentation, if the project has any, lives in `docs/` (kept for
that purpose alone, the way `src/` is kept for sources) and is written for
readers, not rewritten from these files mechanically.

| File / folder | What |
| --- | --- |
| [`harness-usage.md`](harness-usage.md) | how to drive the agent harness (Claude Code & OpenCode): phases, subagents, hooks, document liveness |
| [`architecture.md`](architecture.md) | orientation: system structure, boundaries, invariants |
| [`style.md`](style.md) | code style, comments, commit messages, changelog |
| [`glossary.md`](glossary.md) | the project's ubiquitous language: domain terms used in specs, code, and conversation |
| [`testing.md`](testing.md) | test layering, gate commands, gate-output reading rules |
| [`tool-bootstrap.md`](tool-bootstrap.md) | toolchain install and new-machine setup |
| [`adr/`](adr/) | architecture decision records (append-only) + the decision register |
| `work/<YYYY-MM>-<slug>/` | one folder per feature: `spec.md` / `plan.md` / `tasks.md` / `report.md` (+ gitignored `scratch.md`) |

Scaffold markers, used consistently across these files (and the example
`work/` unit):

- `_Fill in: …_` — a block for you to replace with real content, deleting
  the marker. `rg 'Fill in:' development/` lists what is still scaffold.
- `<placeholder>` — inline: replace the bracketed text, keep what's around
  it. The brackets are never given backticks of their own, and they stay
  bare inside a backticked path too (`work/<YYYY-MM>-<slug>/`). That is the
  form the role subagents emit in their output formats, so a scaffold and a
  freshly written document look alike — at the price of a Markdown preview
  swallowing a bare `<word>` as an unknown HTML tag, which these
  read-as-text files accept.
- `> blockquote` — a durable note about how the document itself works;
  it stays.

These documents are living but **trunk-gated**: agents follow them and
propose changes via a dedicated PR — never by silently editing them in the
middle of a feature. Two files are **registers**, not prose docs, and accrete
mid-feature through their own reviewable channels: the decision register in
[`adr/README.md`](adr/README.md) (one row per escalated decision, in the same
PR as its `DECISION-PENDING:` marker) and [`glossary.md`](glossary.md) (entries
promoted from a reviewed spec's Glossary section at `/spec` wrap-up). Which
files freeze, and when:
[`harness-usage.md`](harness-usage.md#document-liveness).
