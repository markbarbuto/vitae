---
source: config/assistant.toml
visibility: public
generated: true
---

# This assistant

## How this assistant works

I built this assistant, Vitae AI, to answer questions about my career, projects and interests. It runs Qwen3.5-4B (Q4_0) on llama.cpp v0.8.0, self-hosted on Oracle Cloud as an Ampere A1 virtual machine with 2 ARM cores and 12 GB of memory. It doesn't send questions to a third-party AI service.

## Architecture

The assistant uses cache-augmented generation. My whole knowledge base, which is my resume, my website's content and answers I wrote myself, sits in the model's cached context. Hybrid retrieval combines BAAI/bge-small-en-v1.5 embeddings with BM25 keyword search, fuses them with reciprocal rank fusion, and reranks the results with a cross-encoder reranker. Retrieval picks the most relevant sections as focus hints, refuses questions my knowledge base can't answer, and records which sources were used.

## Why not classic retrieval-augmented generation

On the 2-core host, a classic RAG prompt took about 32 seconds before the first word appeared. Keeping the whole knowledge base cached brought first answers down to about 5.5 seconds, so I chose cache-augmented generation.
