# DocuVault AI: Enterprise Document Intelligence & Hybrid RAG Workbench

![Python](https://img.shields.io/badge/-Python_3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Angular](https://img.shields.io/badge/-Angular_18-DD0031?style=flat-square&logo=angular&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL_16-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/-Redis_7-DC382D?style=flat-square&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/-Celery-37814A?style=flat-square&logo=celery&logoColor=white)

An enterprise-grade Document Intelligence platform designed to solve the two fundamental document processing bottlenecks in fintech, legal, and procurement back-offices: **Hallucination in ledger arithmetic** and **recall failure in dense vector search**. 

DocuVault AI implements a Zero-Disk In-Memory ingestion engine, a Self-Healing LLM Reflection Loop for deterministic data extraction, and a 4-Tier Hybrid RAG cascade with local cross-encoder reranking.

## 🏗️ System Architecture & Data Flow

```mermaid
graph TD
    subgraph Client_Layer ["Client Layer"]
        UI["Angular 18 Enterprise Workbench"]
    end

    subgraph API_Queuing ["API & Queuing Layer"]
        API["FastAPI Async Gateway"]
        Redis[("Redis Ephemeral Buffer")]
        Worker["Celery Distributed Worker"]
    end

    subgraph Processing_Engine ["Zero-Disk Processing Engine"]
        PyMuPDF["PyMuPDF In-Memory BytesIO"]
        TrackA["Track A: Deterministic Extraction"]
        TrackB["Track B: Hybrid RAG Pipeline"]
    end

    subgraph AI_Data ["AI & Data Persistence"]
        Groq["Groq LPU / Instructor"]
        Pydantic["Pydantic v2 Validator"]
        Embed["FastEmbed BAAI/bge-small"]
        DB[("PostgreSQL 16")]
        VectorDB[("pgvector HNSW")]
    end

    UI -->|"1MB Chunked Streams"| API
    API -->|"HTTP 202 / Cache"| Redis
    Redis -->|"Dequeue"| Worker
    Worker --> PyMuPDF
    PyMuPDF --> TrackA
    PyMuPDF --> TrackB

    %% Track A Flow
    TrackA --> Groq
    Groq -->|"JSON Outputs"| Pydantic
    Pydantic -->|"Self-Healing Reflection"| Groq
    Pydantic -->|"Validated Schema"| DB

    %% Track B Flow
    TrackB --> Embed
    Embed -->|"384d Vectors"| VectorDB
