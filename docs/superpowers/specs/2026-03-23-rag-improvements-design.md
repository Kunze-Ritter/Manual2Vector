# RAG Improvements Design
**Date:** 2026-03-23
**Status:** Approved
**Scope:** Backend — Agent, Search, Evaluation

## Background

KRAI's retrieval stack (LangGraph + pgvector + Ollama) is solid but has three concrete gaps:

1. Agent tools use `ILIKE %query%` keyword matching instead of vector search, limiting semantic recall.
2. No reranking step — pgvector cosine-similarity is used as the final ranking signal.
3. No systematic way to measure whether retrieval or prompt changes improve answer quality.

This spec covers targeted fixes for all three. LlamaIndex was evaluated and rejected: the project already uses LangChain/LangGraph for the agent layer, has a domain-specific `SmartChunker` that no generic framework can replace, and a custom pgvector schema that doesn't map cleanly to LlamaIndex abstractions. Adding LlamaIndex would introduce a second RAG framework with no net benefit.

---

## Area 1: Vector Search in Agent Tools

### Problem

`agent_api.py` tools (`search_error_codes`, `_fetch_related_documents`, etc.) use `ILIKE %query%` as the primary lookup. Semantic queries like "paper jam in fuser area" won't match error codes described as "13.B9.Az" without exact keyword overlap.

### Design

Each affected tool gains a **hybrid retrieval** step:

1. **Embed the query** via the existing Ollama embedding call (nomic-embed-text / embeddinggemma, 768-dim).
2. **pgvector similarity search** against `krai_intelligence.chunks` → returns `chunk_ids` and their parent `document_ids`, `product_ids`.
3. These IDs are passed as `matched_chunk_ids` / `matched_document_ids` into the existing SQL queries via `AND id = ANY($n::uuid[])` — acting as a relevance seed.
4. **Fallback:** If the vector search returns zero results, the existing ILIKE path runs unchanged.

### Affected Tools

| Tool | Change |
|------|--------|
| `search_error_codes` | Vector → chunk_ids → filter error codes by chunk_id |
| `_fetch_related_documents` | Vector → document_ids seed |
| `_fetch_related_videos` | Vector → document_ids / product_ids seed |

### What Does Not Change

- `build_scope_filters` logic and scope system
- SQL serialisation format
- LangGraph agent structure
- `SmartChunker`, pipeline processors, pgvector schema

### Embedding Reuse

The Ollama HTTP call is already made by `AIService.generate_embeddings()`. The agent tools will call this same method — no new HTTP client needed.

---

## Area 2: Reranking

### Problem

pgvector returns Top-K by cosine similarity. This is a good first-pass signal but does not capture query-document relevance as accurately as a CrossEncoder, which reads query and document together.

### Design

A `RerankingService` wraps `sentence-transformers` `CrossEncoder`:

1. Vector search retrieves **Top-20** candidates (up from current ~5–10).
2. `RerankingService.rerank(query, chunks)` scores each query-chunk pair with the CrossEncoder.
3. Results are sorted by CrossEncoder score; **Top-5** are passed to the LLM.

```
query → pgvector (top-20) → CrossEncoder rerank → top-5 → LLM
```

### Configuration

| Env var | Default | Notes |
|---------|---------|-------|
| `ENABLE_RERANKING` | `true` | Set to `false` to bypass |
| `RERANKING_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Swap for larger model as hardware improves |
| `RERANKING_TOP_N` | `5` | How many results to pass to LLM after reranking |
| `RERANKING_CANDIDATES` | `20` | How many candidates to fetch before reranking |

The model is loaded once at startup and cached in memory. When `ENABLE_RERANKING=false` the service is a no-op passthrough.

### Integration Points

- `MultimodalSearchService.search_multimodal()` — rerank after vector retrieval, before result enrichment.
- Agent flow — rerank chunk results before they enter the LLM context window.

### Dependencies

`sentence-transformers` is already in `requirements.txt`. No new packages needed.

---

## Area 3: RAG Evaluation with Ragas

### Problem

There is no systematic baseline to measure retrieval or answer quality. Changes to chunking, prompts, or retrieval strategy cannot be objectively compared.

### Design

A standalone evaluation script `scripts/evaluate_rag.py` using [Ragas](https://docs.ragas.io) (`pip install ragas` — no LlamaIndex dependency).

**Metrics:**

| Metric | What it measures |
|--------|-----------------|
| `faithfulness` | Does the answer stay grounded in retrieved context? |
| `answer_relevancy` | Does the answer address the question? |
| `context_precision` | Are the retrieved chunks actually relevant? |
| `context_recall` | Were all important chunks retrieved? |

**Test dataset format** (`scripts/eval_dataset.json`):

```json
[
  {
    "question": "What causes error 13.B9.Az on the bizhub C450i?",
    "ground_truth": "Paper jam in the fuser area caused by worn separation claws.",
    "relevant_document_ids": ["uuid-1", "uuid-2"]
  }
]
```

The script:
1. Runs each question through the live retrieval + agent stack.
2. Collects (question, answer, retrieved_contexts, ground_truth).
3. Passes to `ragas.evaluate()`.
4. Outputs a summary table to stdout and a JSON report to `scripts/eval_results/`.

### Constraints

- Runs manually or in CI — **never** in production.
- Requires a running backend (or test database snapshot).
- Initial dataset: ~20 representative questions covering error codes, parts, documents, and multimodal queries.

### New Dependency

```
ragas>=0.1.0   # RAG evaluation framework (dev/CI only)
```

---

## Out of Scope

- LlamaIndex adoption (evaluated and rejected — see Background).
- Changes to `SmartChunker` or any pipeline processor.
- Changes to the pgvector schema or migrations.
- Production monitoring / real-time quality dashboards (future work).

---

## Rollout Order

1. **Vector search in agent tools** — highest impact on RAG quality, self-contained change.
2. **Reranking** — builds on top of the expanded candidate set from step 1.
3. **Ragas evaluation** — establishes a quality baseline before and after steps 1+2, then runs ongoing.
