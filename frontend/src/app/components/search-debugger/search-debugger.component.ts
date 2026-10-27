import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkbenchStateService } from '../../services/workbench-state.service';
import { SearchMode } from '../../models/workbench.types';

@Component({
  selector: 'app-search-debugger',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm mt-5">
      <!-- Header & Mode Selector -->
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h2 class="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <svg class="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Hybrid RAG Search Debugger
          </h2>
          <p class="text-xs text-slate-400">Compare Dense Vector, Sparse FTS, RRF, and Cross-Encoder ranking</p>
        </div>

        <!-- Mode Toggles -->
        <div class="inline-flex rounded-lg bg-slate-950 p-1 border border-slate-800 text-xs font-medium">
          <button
            type="button"
            (click)="state.setSearchMode('hybrid')"
            [class.bg-indigo-600]="state.activeSearchMode() === 'hybrid'"
            [class.text-white]="state.activeSearchMode() === 'hybrid'"
            [class.text-slate-400]="state.activeSearchMode() !== 'hybrid'"
            class="px-3 py-1 rounded-md transition-all duration-150"
          >
            Hybrid (RRF)
          </button>
          <button
            type="button"
            (click)="state.setSearchMode('vector')"
            [class.bg-indigo-600]="state.activeSearchMode() === 'vector'"
            [class.text-white]="state.activeSearchMode() === 'vector'"
            [class.text-slate-400]="state.activeSearchMode() !== 'vector'"
            class="px-3 py-1 rounded-md transition-all duration-150"
          >
            Dense Vector
          </button>
          <button
            type="button"
            (click)="state.setSearchMode('keyword')"
            [class.bg-indigo-600]="state.activeSearchMode() === 'keyword'"
            [class.text-white]="state.activeSearchMode() === 'keyword'"
            [class.text-slate-400]="state.activeSearchMode() !== 'keyword'"
            class="px-3 py-1 rounded-md transition-all duration-150"
          >
            Sparse Keyword
          </button>
        </div>
      </div>

      <!-- Search Input Bar & Controls -->
      <div class="flex gap-2 mb-3">
        <div class="relative flex-1">
          <input
            type="text"
            [(ngModel)]="searchQuery"
            (keyup.enter)="onSearch()"
            placeholder="Ask a question or search document semantics..."
            class="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>
        <button
          type="button"
          (click)="onSearch()"
          [disabled]="state.isSearching()"
          class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors flex items-center gap-2"
        >
          @if (state.isSearching()) {
            <span class="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
            Searching...
          } @else {
            Search
          }
        </button>
      </div>

      <!-- Retrieval Pipeline Controls (Top-K & FlashRank Reranker Toggle) -->
      <div class="flex flex-wrap items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-3 mb-4">
        <div class="flex items-center gap-4">
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              [checked]="state.rerankEnabled()"
              (change)="state.toggleRerank()"
              class="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-0 focus:ring-offset-0"
            />
            <span class="text-slate-300">Local FlashRank Cross-Encoder</span>
          </label>
        </div>

        @if (state.searchTelemetry(); as tel) {
          <div class="flex items-center gap-3 font-mono text-[11px] text-slate-400">
            <span>Dense: <b class="text-slate-300">{{ tel.dense_time_ms.toFixed(1) }}ms</b></span>
            <span>•</span>
            <span>Sparse: <b class="text-slate-300">{{ tel.sparse_time_ms.toFixed(1) }}ms</b></span>
            <span>•</span>
            <span>RRF: <b class="text-slate-300">{{ tel.rrf_time_ms.toFixed(1) }}ms</b></span>
            <span>•</span>
            <span>Rerank: <b class="text-slate-300">{{ tel.rerank_time_ms.toFixed(1) }}ms</b></span>
          </div>
        }
      </div>

      <!-- Ranked Results Cards -->
      <div class="space-y-3 max-h-[520px] overflow-y-auto pr-1">
        @if (state.searchResults().length === 0 && !state.isSearching()) {
          <div class="text-center py-10 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs">
            No search results yet. Ingest a PDF and enter a query above.
          </div>
        }

        @for (item of state.searchResults(); track item.chunk_id) {
          <div class="p-4 bg-slate-950/70 border border-slate-800 hover:border-slate-700 rounded-lg transition-colors">
            <!-- Rank & Citation Header -->
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <span class="w-5 h-5 rounded-full bg-indigo-900/60 text-indigo-300 border border-indigo-700/50 flex items-center justify-center font-bold text-xs">
                  #{{ item.final_rank }}
                </span>
                <span class="text-xs font-semibold text-slate-300">Page {{ item.page_number }}</span>
                <span class="text-xs text-slate-500 font-mono">(Chunk {{ item.chunk_index }})</span>
              </div>

              <!-- Multi-Stage Score Pills -->
              <div class="flex items-center gap-1.5 font-mono text-[11px]">
                @if (item.rerank_score !== undefined && item.rerank_score !== null) {
                  <span class="px-2 py-0.5 rounded bg-emerald-950/70 border border-emerald-800 text-emerald-300">
                    Rerank: {{ item.rerank_score.toFixed(3) }}
                  </span>
                }
                @if (item.rrf_score !== undefined && item.rrf_score !== null) {
                  <span class="px-2 py-0.5 rounded bg-indigo-950/70 border border-indigo-800 text-indigo-300">
                    RRF: {{ item.rrf_score.toFixed(4) }}
                  </span>
                }
                @if (item.vector_score !== undefined && item.vector_score !== null) {
                  <span class="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                    Dense: {{ item.vector_score.toFixed(3) }}
                  </span>
                }
                @if (item.keyword_score !== undefined && item.keyword_score !== null) {
                  <span class="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                    FTS: {{ item.keyword_score.toFixed(3) }}
                  </span>
                }
              </div>
            </div>

            <!-- Snippet Content -->
            <p class="text-xs text-slate-300 leading-relaxed font-sans bg-slate-900/50 p-2.5 rounded border border-slate-800/50">
              {{ item.content }}
            </p>
          </div>
        }
      </div>
    </div>
  `,
})
export class SearchDebuggerComponent {
  state = inject(WorkbenchStateService);
  searchQuery = 'invoice total and line items summary';

  onSearch(): void {
    this.state.executeSearch(this.searchQuery);
  }
}
