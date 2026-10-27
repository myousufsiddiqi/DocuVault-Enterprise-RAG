import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkbenchStateService } from '../../services/workbench-state.service';

@Component({
  selector: 'app-telemetry-bar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <header class="bg-slate-900 border-b border-slate-800 px-6 py-3 flex flex-wrap items-center justify-between gap-4">
      <!-- Title & Branding -->
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
          DV
        </div>
        <div>
          <h1 class="text-sm font-bold text-white tracking-wide">DocuVault AI</h1>
          <p class="text-xs text-slate-400">Enterprise Document Intelligence & Hybrid RAG Workbench</p>
        </div>
      </div>

      <!-- Telemetry Metrics & Status Badges -->
      <div class="flex items-center space-x-4 text-xs font-mono">
        <!-- 100% Free Badge -->
        <div class="flex items-center px-2.5 py-1 rounded-md bg-emerald-950/60 border border-emerald-800 text-emerald-400">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-2"></span>
          Mode: 100% Free Tier ($0.00)
        </div>

        <!-- Latency Telemetry -->
        @if (state.activeDocument(); as doc) {
          <div class="flex items-center px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300">
            <span class="text-slate-500 mr-1.5">Latency:</span>
            <span class="text-indigo-400 font-bold">{{ doc.telemetry.total_time_ms }} ms</span>
          </div>

          <!-- Retry Reflection Count -->
          <div class="flex items-center px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300">
            <span class="text-slate-500 mr-1.5">Reflection Retries:</span>
            <span [class]="doc.telemetry.extraction_retries > 0 ? 'text-amber-400 font-bold' : 'text-emerald-400 font-bold'">
              {{ doc.telemetry.extraction_retries }}
            </span>
          </div>

          <!-- Ingest Tokens -->
          <div class="flex items-center px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300">
            <span class="text-slate-500 mr-1.5">Tokens:</span>
            <span class="text-slate-200">{{ doc.telemetry.estimated_prompt_tokens }} in / {{ doc.telemetry.estimated_completion_tokens }} out</span>
          </div>
        }

        <!-- pgvector Status Indicator -->
        <div class="flex items-center px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-400">
          <span class="w-1.5 h-1.5 rounded-full bg-indigo-400 mr-1.5"></span>
          pgvector: 384d HNSW
        </div>
      </div>
    </header>
  `,
})
export class TelemetryBarComponent {
  state = inject(WorkbenchStateService);
}
