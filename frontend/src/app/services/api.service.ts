import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  IngestResponse,
  SearchMode,
  SearchResponse,
  SystemHealth,
} from '../models/workbench.types';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = 'http://localhost:8000/api/v1';

  /** Ingests a raw PDF in-memory, extracting structured data and chunk embeddings. */
  ingestDocument(file: File): Observable<IngestResponse> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    return this.http.post<IngestResponse>(`${this.baseUrl}/documents/ingest`, formData);
  }

  /** Executes Hybrid RAG search (Vector + Keyword + RRF + FlashRank Reranker). */
  searchDocuments(params: {
    query: string;
    mode: SearchMode;
    document_id?: string;
    top_k?: number;
    rerank?: boolean;
  }): Observable<SearchResponse> {
    return this.http.post<SearchResponse>(`${this.baseUrl}/documents/search`, params);
  }

  /** Probes backend health, pgvector readiness, and active AI model providers. */
  getHealth(): Observable<SystemHealth> {
    return this.http.get<SystemHealth>(`${this.baseUrl}/health`);
  }

  /** Lists all ingested documents in the system. */
  listDocuments(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/documents`);
  }
}
