# Retrieval Quality Report

Corpus: `.memory/reference/` (8 documents, proj-lessons). Ground truth: `module3_doc/retrieval-ground-truth.md`. Threshold: similarity score >= 0.65, expected document in top 3.

## Results

| Query | Result | Method | Score | Pass/Fail |
|---|---|---|---|---|
| Q1 — chmod | chmod-root-bypass.md, chunk 0 | vector | 0.731 | PASS |
| Q2 — git identity (near-miss) | git-identity-not-persisted.md, chunk 0 (decoy git-worktree-windows-paths.md did not appear) | vector | 0.657 | PASS |
| Q3 — MCP -32000 (literal keyword) | mcp-dependency-pinning.md, chunk 1 | vector | 0.655 | PASS |
| Q4 — OrderServiceImpl/Feign | feign-exception-handling-convention.md, chunks 0-2 | keyword | null | FAIL (see below) |
| Q5 — cost ceiling enforcement | agentic-run-cost-tracking.md did NOT appear; only internal-classification docs returned | keyword | null | PASS (ceiling held; see note below) |
| Q6 — --network none | network-egress-claude-code.md, chunk 0 | vector | 0.699 | PASS |

**Pass rate: 5/6 = 83%** — clears the lesson's 80% floor.

## Q4 — documented known gap

The correct document (`feign-exception-handling-convention.md`) is returned in all top-3 results, but only via the keyword fallback, which the server does not assign a numeric similarity score to (`null`, not a low number). The ground truth's pass condition (`score >= 0.65`) is therefore not literally satisfiable through this path, regardless of document relevance.

Two independent fixes were attempted and retested, per the one-hypothesis-at-a-time rule:

1. **Content rewording** — added one bridging sentence to the document, closely mirroring the query's own phrasing ("distinguishes a truly unreachable downstream service... from a case where a real HTTP error response was received"). Re-tested: still fell back to keyword, no score.
2. **Chunking strategy** — restarted the server with `--chunking semantic --boundary-threshold 0.75` instead of the default paragraph mode (chunk count for the corpus changed 20 -> 25, confirming re-chunking took effect). Re-tested: still fell back to keyword, no score.

Both fixes were genuine, targeted at different plausible causes (wording vs. chunk boundaries), and both were retested individually rather than combined. Neither changed the outcome.

**Likely root cause:** the server's vector search pulls the `k` nearest neighbors by raw distance (`pool_size = max(top_k * 5, 20)`) and applies the 0.65 threshold as a hard cutoff, not a best-relative-match ranking. With only 25 chunks in the whole corpus, the candidate pool already covers most of it -- so the limiting factor isn't chunk boundaries or ranking, it's whether this specific chunk's absolute cosine similarity to this specific query phrasing ever clears 0.65 at all. `all-MiniLM-L6-v2` is a small, general-purpose embedding model, not fine-tuned on software engineering vocabulary -- dense technical terms (exception class names, specific HTTP status codes) can pull a chunk's embedding away from a more natural-language paraphrase of the same underlying concept, even where a human reader would call it an obvious match.

**Disposition:** documented as a known gap rather than forced to pass, per the lesson's explicit rule against rewording the expected answer to match tool behavior. The keyword fallback does correctly surface the right document as a safety net, so the practical impact for an agent relying on this tool is limited (it still gets the right answer, just without a numeric confidence score attached) -- but the numeric-score guarantee this query was written to test does not currently hold for this document/query pairing.

## Q5 — note on ceiling enforcement quality

Classification-ceiling enforcement held correctly -- `agentic-run-cost-tracking.md` (confidential) never appeared in results under an `internal` ceiling, across every variant tried. However, the *quality* of what came back instead is weak: the keyword fallback returned three semantically unrelated documents (git identity, Feign handling, network egress), none actually about cost. Inspecting `fts_query()` in `mcp/retrieval/server.py`, the keyword search OR-joins every token in the query, including ordinary filler words ("what," "are," "the," "for," "this") -- in a small corpus, this matches nearly any document rather than genuinely relevant ones. This is a real precision gap in the fallback mechanism itself, separate from the ceiling-enforcement correctness, which was not in question.

**Follow-up (stopword gap addressed):** `fts_query()` now drops a conservative set of English stopwords (`KEYWORD_STOPWORDS` in `mcp/retrieval/server.py`) before building the OR-joined query. Exact-token behavior for identifiers (e.g. `OrderServiceImpl`, `-32000`, snake_case names) is unchanged, and the classification-ceiling and project filtering in `keyword_search()` were not touched. A query made up entirely of stopwords now yields no keyword matches. This change has not been re-measured here; the table and findings above record the results measured before the change.

## Known gap — a single shared content word can match an unrelated document (separate from Q5)

This is a distinct finding from the Q5 filler-word issue above, observed *after* the stopword fix (`266a2fd`) was in place. The Q5 fix drops ordinary English filler words; it does not, and cannot, address the deeper problem that `fts_query()` OR-joins every remaining token, so any one shared content word is enough to make an entirely unrelated document a match.

**Observed instance (planner run for the constructor-injection task, keyword fallback, `proj-lessons`, ceiling `internal`):**

- Query `"constructor injection vs field @Autowired dependency injection style"` returned `git-worktree-windows-paths.md` (chunks 0 and 1).
- Query `"coding standard dependency injection constructor"` returned `feign-exception-handling-convention.md` (chunk 3) and `chmod-root-bypass.md` (chunk 0).

All four hits came from the keyword fallback. `git-worktree-windows-paths.md` and `chmod-root-bypass.md` have nothing to do with dependency injection; the planner itself judged them irrelevant. The Feign document was only a pointer to the coding-standards file, not the standard itself. Which specific shared token caused each unrelated match was not isolated here. That is inferred from how the OR-join works, not measured.

**Why the stopword fix does not cover it:** the tokens involved are content words, not filler, so filtering them out would also remove the words a real query depends on. The cause is the OR-based matching itself, together with the fallback returning results with no relevance floor or ranking signal comparable to the vector path's similarity threshold.

**Impact:** a caller relying on the fallback can receive plausible-looking but irrelevant lessons. It currently falls to the caller to judge relevance; the ceiling and project filtering are unaffected.

**Disposition:** documented as a known, separate gap. The underlying retrieval logic has intentionally not been changed as part of this note, and no fix has been designed or measured.
