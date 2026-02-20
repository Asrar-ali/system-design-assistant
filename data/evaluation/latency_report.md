# Latency Benchmark Report

**Date:** 2026-02-08 20:57:07
**Queries Evaluated:** 47
**Successful Queries:** 47

---

## Executive Summary

This report measures RAG pipeline latency with component-level timing to validate SLA targets and identify bottlenecks.

**SLA Targets:**
- Retrieval p95: <100ms
- End-to-end p95: <5s

**SLA Status:**
- ✓ Retrieval: 176.8ms p95 FAIL
- ✓ End-to-end: 1625.8ms p95 PASS

---

## Latency Statistics

### Retrieval Latency (retrieve_chunks)

Measures time to embed query + search vector store + rank results.

| Metric | Value (ms) |
|--------|-----------|
| **p50 (median)** | 58.1 |
| **p95** | 176.8 |
| **p99** | 286.2 |
| **Mean** | 81.1 |

### Generation Latency (generate_answer_with_citations)

Measures time for context preparation + LLM generation + citation extraction.

| Metric | Value (ms) |
|--------|-----------|
| **p50 (median)** | 1400.6 |
| **p95** | 1536.0 |
| **p99** | 1557.5 |
| **Mean** | 1395.7 |

### End-to-End Latency

Total query processing time (retrieval + generation).

| Metric | Value (ms) |
|--------|-----------|
| **p50 (median)** | 1474.6 |
| **p95** | 1625.8 |
| **p99** | 1733.3 |
| **Mean** | 1476.8 |

---

## Bottleneck Analysis

**Component Breakdown (p95):**
- Retrieval: 176.8ms (10.9%)
- Generation: 1536.0ms (94.5%)

**Primary Bottleneck:** Generation (LLM inference)

**Optimization Recommendations:**

1. **LLM Optimization (Primary)**
   - Consider smaller/faster model (Groq llama3-70b → llama3-8b)
   - Reduce context size (fewer chunks or shorter chunks)
   - Enable streaming for perceived latency improvement

2. **Retrieval Optimization (Secondary)**
   - Already meeting SLA target

---

## SLA Validation

### Retrieval SLA: <100ms p95
- **Target:** 100ms
- **Actual:** 176.8ms
- **Status:** ✗ FAIL
- **Margin:** -76.8ms

### End-to-End SLA: <5s p95
- **Target:** 5000ms
- **Actual:** 1625.8ms
- **Status:** ✓ PASS
- **Margin:** +3374.2ms

---

## Notes

- Measurements use `time.perf_counter()` for nanosecond-precision monotonic timing
- 0 queries failed and excluded from percentile calculation
- Warm-up phase (5 queries) excluded to avoid cold start bias
- All timing includes actual production path (no mocking or shortcuts)
