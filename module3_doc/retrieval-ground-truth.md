# Retrieval Ground-Truth Query Set

Project: proj-lessons. Corpus: `.memory/reference/`. Threshold: similarity score >= 0.65, expected document must appear in the top 3 results.

## Q1 — chmod does not enforce read-only against root (plain precision)

- Query: "Why doesn't chmod actually protect a directory from being written to inside a container?"
- Expected top result: chmod-root-bypass.md
- Filters: project = proj-lessons, classification_ceiling = internal
- Pass: chmod-root-bypass.md appears in top 3 with score >= 0.65

## Q2 — git identity vs. git worktree paths (near-miss)

- Query: "Why did my git commits show no author name after starting a new container?"
- Expected top result: git-identity-not-persisted.md
- Decoy present in corpus: git-worktree-windows-paths.md (also "git behaving oddly inside a container," but a different root cause -- worktree path resolution, not commit identity)
- Filters: project = proj-lessons, classification_ceiling = internal
- Pass: git-identity-not-persisted.md appears in top 3 with score >= 0.65, ranked above git-worktree-windows-paths.md

## Q3 — the -32000 connection error (literal keyword)

- Query: "What does the error 'MCP error -32000: Connection closed' actually mean when registering a server?"
- Expected top result: mcp-dependency-pinning.md
- Filters: project = proj-lessons, classification_ceiling = internal
- Pass: mcp-dependency-pinning.md appears in top 3 with score >= 0.65, or via keyword fallback if semantic matching alone does not surface it above threshold

## Q4 — Feign failure handling convention (plain precision)

- Query: "How does OrderServiceImpl distinguish a truly unreachable downstream service from a real HTTP error response?"
- Expected top result: feign-exception-handling-convention.md
- Filters: project = proj-lessons, classification_ceiling = internal
- Pass: feign-exception-handling-convention.md appears in top 3 with score >= 0.65

## Q5 — Ceiling enforcement (must NOT leak a confidential doc)

- Query: "What are the typical per-run costs for running an agent session on this project?"
- Best semantic match in corpus: agentic-run-cost-tracking.md (classification: confidential)
- Filters: project = proj-lessons, classification_ceiling = internal
- Pass: agentic-run-cost-tracking.md does NOT appear in results; the tool returns only internal-or-below matches, or an empty result if none qualify

## Q6 — Claude Code's network requirement (plain precision)

- Query: "Why can't I use --network none for a session that runs Claude Code?"
- Expected top result: network-egress-claude-code.md
- Filters: project = proj-lessons, classification_ceiling = internal
- Pass: network-egress-claude-code.md appears in top 3 with score >= 0.65
