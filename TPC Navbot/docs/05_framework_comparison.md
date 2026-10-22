# Framework comparison and implementation choice

The course guide (p2 and p6) explicitly asks for LangChain and/or LlamaIndex. The original bespoke Python pipeline did not meet that framework requirement merely by implementing similar functions.

## Comparison

| Concern | LangChain | LlamaIndex | Choice here |
|---|---|---|---|
| Data routing | Composable runnable steps can call a retriever, filter evidence, and render results. | Index/query components organize document and node retrieval. | Explicit retrieval -> approval filter -> fact renderer. |
| Ingestion/indexing | Loaders, splitters, embeddings, and vector-store interfaces are modular. | `IngestionPipeline` transforms documents/nodes; embedded nodes can enter a vector store and a docstore can support deduplication. | Existing bounded chunker, review registry, manifest, and vector-store adapter retained. |
| Memory | Can be connected to explicit application state. | Can be connected to explicit application state. | Application-owned per-session campus context; neither framework grants policy authority to history. |
| Safety | The framework does not verify a campus fact by itself. | The framework does not verify a campus fact by itself. | Current-turn scope, matching file hashes, reviewed fact fields, and deterministic rendering. |

LangChain documents modular loaders, splitters, embeddings, vector stores, and retrievers, with retrieval preceding generation in a two-step pipeline. [Official retrieval documentation](https://docs.langchain.com/oss/python/langchain/retrieval).

LlamaIndex's ingestion interface applies transformations to documents/nodes and optionally stores nodes with embeddings in a vector store; a document store supports document deduplication strategies. [Official ingestion API](https://developers.llamaindex.ai/python/framework-api-reference/ingestion/).

## Actual implementation

`TPCNavBotRAG.__init__` builds a `langchain_core.runnables.RunnableLambda` sequence for `_search_request` followed by `_ground_request`, and a runnable for `_render_request`. `chat()` invokes those chains when the dependency is installed. The bot reports `orchestration_backend="langchain-core"`; without that dependency it runs the same functions directly and reports `stdlib`.

This is a constrained use of LangChain core, not a claim that every pipeline stage is a framework integration. An actual installed-LangChain demo passed eight scenarios; the offline fallback passed the same eight. No LlamaIndex implementation is used. The existing registry and renderer retain simple inspectable trust boundaries. Migrating them wholesale would not supply missing campus evidence.

The optional Gemini step selects an exact allowlisted candidate ID. The final facts, directions, and times remain application-rendered from reviewed fields. Therefore an offline run demonstrates retrieval and safety logic but does not prove a successful generative API call. Retain a model-backed demo separately for the course's API requirement.

## Trade-offs and limits

The explicit chain makes control flow easy to inspect and supports local tests. It does not yet establish scalable production retrieval, distributed state, tracing, or a fully evaluated generative RAG experience. The fallback keeps offline development usable, but a fallback-only run should not be presented as framework execution. A retained framework-backed run must show the actual reported backend.

Before scaling substantially, measure ingestion costs, retrieval relevance/latency, source-filter correctness, and memory limits on the intended backend. The current JSON snapshot is useful for portability; it is not evidence of high-volume performance.
