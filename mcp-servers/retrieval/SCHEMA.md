# Vector Retrieval MCP Server Schema

Server name: `retrieval`

Default endpoint: `http://localhost:8002/mcp`

Reference corpus:

- `/memory/reference` inside the container
- `.memory/reference` on the host/repository

The server exposes one named operation: `retrieve`.

## Indexing

At startup, the server:

1. Reads every Markdown document in `/memory/reference`.
2. Parses front matter containing `classification`, `project`, and `doc_type`.
3. Splits documents into chunks.
4. Embeds each chunk with `all-MiniLM-L6-v2`.
5. Stores chunks in an in-memory SQLite database with:
   - `chunks`: text and metadata
   - `vec_chunks`: `sqlite-vec` vector index
   - `fts_chunks`: FTS5 keyword fallback index

The index is derived runtime output and is rebuilt from the committed corpus whenever the server starts.

## Required corpus front matter

Every document must begin with metadata:

```yaml
---
classification: internal
project: proj-csv
doc_type: decision
---
```

If a document lacks a valid classification, the server indexes it as `secret` and prints a warning. This hides the document under normal ceilings rather than leaking it.

## `retrieve`

Searches the reference corpus by meaning, scoped to one project and capped at a classification ceiling. Falls back to keyword search when no vector match clears the confidence threshold.

Parameters:

- `query` (`str`, required): search text, phrased the way an agent would ask it.
- `project_id` (`str`, required): only this project's documents are searched; must match `^[A-Za-z0-9-]+$`.
- `top_k` (`int`, optional, default `3`): maximum number of results to return; must be between 1 and 20.
- `classification_ceiling` (`str`, optional, default `internal`): highest classification a result may carry; one of `public`, `internal`, `confidential`, `secret`.
- `metadata_filters` (`dict`, optional): additional narrowing. Supported key: `doc_type`.

Returns:

A list of up to `top_k` results. Each result always includes:

- `source_document` (`str`): source Markdown file name.
- `chunk_index` (`int`): chunk position in that file.
- `excerpt` (`str`): matching chunk text.
- `classification` (`str`): chunk classification, never above the ceiling.
- `similarity_score` (`float` or `null`): cosine similarity for vector results; `null` for keyword results.
- `retrieval_method` (`str`): `vector` or `keyword`.

Example:

```text
retrieve(
  "What file format did we choose for the export?",
  "proj-csv",
  classification_ceiling="internal",
  metadata_filters={"doc_type": "decision"}
)
```

## Confidence threshold

The vector-confidence threshold is `0.65`.

- If the top vector result after project and classification filtering has `similarity_score >= 0.65`, vector results are returned.
- If no vector result clears the threshold, keyword fallback runs over the same corpus and same filters.
- Keyword results carry `retrieval_method: "keyword"` and `similarity_score: null`.

## Classification enforcement

The server filters out documents above the supplied ceiling before returning results.

For example, a caller with `classification_ceiling="internal"` can receive `public` and `internal` documents, but never `confidential` or `secret` documents.

In the course harness, role definitions pin each granted role to an `internal` ceiling so the agent cannot widen its own access by passing a higher value.

## Citation enforcement

Every result includes `source_document` and `chunk_index`. These fields are not optional. A retrieved claim can always be traced back to a specific source document and chunk.

## Chunking decision

Default strategy: `paragraph`

Alternative implemented: `semantic`

The core path uses paragraph chunking because it is simple, fast, and stable for the included short corpus. Semantic chunking is available with:

```bash
python3 mcp-servers/retrieval/server.py --port 8002 --chunking semantic
```

Semantic chunking can improve precision for multi-topic documents, but it is slower because it embeds every sentence during indexing and adds a boundary-threshold tuning knob. Use `scripts/run-retrieval-comparison.sh` and update `docs/retrieval-quality-report.md` before changing the default.
