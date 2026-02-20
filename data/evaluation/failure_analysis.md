# Failure Analysis Report

**Analysis Date:** 2026-02-08 21:10:59
**Total Questions Evaluated:** 50

## Summary

| Category | Count | % of Total |
|----------|-------|------------|
| Retrieval Error | 28 | 56.0% |
| Hallucination | 37 | 74.0% |
| Irrelevant Answer | 25 | 50.0% |
| Formatting Issue | 23 | 46.0% |
| Edge Case Failure | 0 | 0.0% |

## Detailed Failure Examples

### Hallucination

**Definition:** Answer contains unsupported claims (low faithfulness)

**Count:** 37 failures

**Example 1:**
- Question: How do you design a URL shortener like bit.ly?
- Answer: ## Requirements Clarification
To design a URL shortener like bit.ly [1], we need to understand the functional and non-functional requirements. The system should be able to take a long URL as input and...
- Reason: Faithfulness score 0.50 indicates unsupported claims

**Example 2:**
- Question: Explain consistent hashing and when to use it
- Answer: ## Requirements Clarification
Consistent hashing is a technique used in distributed systems to map keys to nodes in a way that minimizes the number of keys that need to be remapped when nodes are adde...
- Reason: Faithfulness score 0.50 indicates unsupported claims

**Example 3:**
- Question: How do you design Twitter's newsfeed?
- Answer: ## Requirements Clarification
To design Twitter's newsfeed, we need to consider both functional and non-functional requirements. Functionally, the system should be able to handle a large volume of twe...
- Reason: Faithfulness score 0.50 indicates unsupported claims

### Retrieval Error

**Definition:** Relevant chunks not retrieved (low context precision)

**Count:** 28 failures

**Example 1:**
- Question: How does Redis implement caching?
- Reason: Context precision 0.20 indicates poor retrieval quality

**Example 2:**
- Question: How do you design a parking lot system?
- Reason: Context precision 0.20 indicates poor retrieval quality

**Example 3:**
- Question: How do you implement API versioning?
- Reason: Context precision 0.40 indicates poor retrieval quality

### Irrelevant Answer

**Definition:** Answer doesn't address question (low answer relevancy)

**Count:** 25 failures

**Example 1:**
- Question: What is the difference between partitioning and replication?
- Answer: ## Requirements Clarification
The question asks for the difference between partitioning and replication, which are two concepts related to data management and distribution in systems. However, the pro...
- Reason: Answer relevancy 0.50 suggests off-topic response

**Example 2:**
- Question: Design Uber's ride matching system
- Answer: ### Requirements Clarification
The ride matching system for Uber is responsible for efficiently matching riders with available drivers [2]. This involves handling a large number of concurrent requests...
- Reason: Answer relevancy 0.00 suggests off-topic response

**Example 3:**
- Question: Explain message queues with examples
- Answer: Error generating answer: Both Groq and Ollama providers failed. Ensure Ollama is running (ollama serve) and llama3.2 model is pulled (ollama pull llama3.2)...
- Reason: Answer relevancy 0.00 suggests off-topic response

### Formatting Issue

**Definition:** Poor structure, missing citations, unclear

**Count:** 23 failures

**Example 1:**
- Question: Explain message queues with examples
- Answer: Error generating answer: Both Groq and Ollama providers failed. Ensure Ollama is running (ollama serve) and llama3.2 model is pulled (ollama pull llama3.2)...
- Reason: No citations found 

**Example 2:**
- Question: How do you design a notification system?
- Answer: Error generating answer: Both Groq and Ollama providers failed. Ensure Ollama is running (ollama serve) and llama3.2 model is pulled (ollama pull llama3.2)...
- Reason: No citations found 

**Example 3:**
- Question: What are the benefits of denormalization?
- Answer: Error generating answer: Both Groq and Ollama providers failed. Ensure Ollama is running (ollama serve) and llama3.2 model is pulled (ollama pull llama3.2)...
- Reason: No citations found 

## Performance Issues

- **Retrieval latency:** p95 = 176.8ms (target: <100ms)
  - Recommendation: Consider caching frequent queries or optimizing BM25 index

## Recommendations

- **High hallucination rate (>20%):** Review system prompt for citation discipline, expand corpus coverage
- **High retrieval errors (>30%):** Expand corpus with more sources, tune BM25 weights, improve chunking strategy
- **Formatting issues (>15%):** Enforce citation format in prompt, add post-processing validation
