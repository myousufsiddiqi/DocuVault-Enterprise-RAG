import { Injectable, computed, signal, inject } from '@angular/core';
import { ApiService } from './api.service';
import {
  ChunkSearchResult,
  IngestResponse,
  SearchMode,
  SearchTelemetry,
  SystemHealth,
} from '../models/workbench.types';

@Injectable({
  providedIn: 'root',
})
export class WorkbenchStateService {
  private api = inject(ApiService);

  // Core Reactive Signals
  readonly activeDocument = signal<IngestResponse | null>(null);
  readonly searchResults = signal<ChunkSearchResult[]>([]);
  readonly searchTelemetry = signal<SearchTelemetry | null>(null);
  readonly activeSearchMode = signal<SearchMode>('hybrid');
  readonly isIngesting = signal<boolean>(false);
  readonly isSearching = signal<boolean>(false);
  readonly systemHealth = signal<SystemHealth | null>(null);
  readonly errorMessage = signal<string | null>(null);
  readonly topK = signal<number>(5);
  readonly rerankEnabled = signal<boolean>(true);

  // Computed Derivations
  readonly hasDocument = computed(() => !!this.activeDocument());
  readonly validationPassed = computed(
    () => this.activeDocument()?.extraction_validation_passed ?? true
  );
  readonly extractionRetries = computed(
    () => this.activeDocument()?.telemetry.extraction_retries ?? 0
  );
  readonly lineItems = computed(
    () => this.activeDocument()?.extraction?.line_items ?? []
  );
  readonly hasSearchResults = computed(() => this.searchResults().length > 0);
  readonly totalIngestLatency = computed(
    () => this.activeDocument()?.telemetry.total_time_ms ?? 0
  );

  constructor() {
    this.refreshHealth();
  }

  refreshHealth(): void {
    this.api.getHealth().subscribe({
      next: (health) => this.systemHealth.set(health),
      error: (err) => console.warn('Health probe failed:', err),
    });
  }

  setSearchMode(mode: SearchMode): void {
    this.activeSearchMode.set(mode);
  }

  setTopK(k: number): void {
    this.topK.set(k);
  }

  toggleRerank(): void {
    this.rerankEnabled.update((v) => !v);
  }

  ingestFile(file: File): void {
    this.isIngesting.set(true);
    this.errorMessage.set(null);

    this.api.ingestDocument(file).subscribe({
      next: (response) => {
        this.activeDocument.set(response);
        this.isIngesting.set(false);
      },
      error: (err) => {
        const errorDetail = err?.error?.detail || err?.message || 'Failed to ingest document';
        this.errorMessage.set(errorDetail);
        this.isIngesting.set(false);
      },
    });
  }

  executeSearch(query: string): void {
    if (!query.trim()) return;

    this.isSearching.set(true);
    this.errorMessage.set(null);

    const docId = this.activeDocument()?.document_id;

    this.api
      .searchDocuments({
        query: query.trim(),
        mode: this.activeSearchMode(),
        document_id: docId,
        top_k: this.topK(),
        rerank: this.rerankEnabled(),
      })
      .subscribe({
        next: (resp) => {
          this.searchResults.set(resp.results);
          this.searchTelemetry.set(resp.telemetry);
          this.isSearching.set(false);
        },
        error: (err) => {
          const detail = err?.error?.detail || err?.message || 'Search execution failed';
          this.errorMessage.set(detail);
          this.isSearching.set(false);
        },
      });
  }
}
