# 🧠 DocuVault: Enterprise Hybrid-RAG Microservice

A high-throughput, zero-disk I/O Retrieval-Augmented Generation (RAG) microservice designed for financial and legal document extraction. Architected to bypass the latency of distributed vector databases, it consolidates dense vector similarity, sparse lexical search, and cross-encoder reranking into a single PostgreSQL 16 engine, paired with a modern Angular 19 zoneless frontend.

---

## 🏗️ System Architecture & Data Flow

```mermaid
flowchart TB
    subgraph Client [Angular Frontend]
        UI[Angular 19 Zoneless SPA]
    end

    subgraph Microservice [FastAPI RAG Pipeline]
        direction TB
        Stream[In-Memory PDF Stream] --> Chunk[LangChain Chunking]
        Chunk --> Embed[FastEmbed ONNX CPU]
        
        Query[Search Gateway] --> Hybrid{Hybrid Cascade}
        Hybrid -->|Cosine Distance| HNSW[pgvector HNSW Index]
        Hybrid -->|Lexical Match| GIN[GIN TSVECTOR Index]
        
        HNSW --> RRF[Reciprocal Rank Fusion]
        GIN --> RRF
        RRF --> Rerank[FlashRank Cross-Encoder]
        Rerank --> Validator[Pydantic Math Validator]
    end

    subgraph Storage [Single-Engine Database]
        DB[(PostgreSQL 16)]
    end

    subgraph AI [Reasoning Tier]
        LLM[Groq Llama-3.3-70b]
    end

    UI -- "POST /ingest" --> Stream
    Embed -- "Atomic Transaction" --> DB
    
    UI -- "POST /search" --> Query
    DB -. "Vector & TSVECTOR" .-> Hybrid
    Validator <-->|"Self-Healing Error Loop"| LLM
    Validator -- "Validated JSONB" --> UI

    classDef backend fill:#1e293b,stroke:#475569,stroke-width:2px,color:#f8fafc
    classDef db fill:#0f172a,stroke:#3b82f6,stroke-width:2px,color:#f8fafc
    classDef ai fill:#4c1d95,stroke:#8b5cf6,stroke-width:2px,color:#f8fafc
    
    class Stream,Chunk,Embed,Query,Hybrid,RRF,Rerank,Validator backend
    class DB,HNSW,GIN db
    class LLM ai
