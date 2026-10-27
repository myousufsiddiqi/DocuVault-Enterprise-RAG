import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TelemetryBarComponent } from './components/telemetry-bar/telemetry-bar.component';
import { PdfUploaderComponent } from './components/pdf-uploader/pdf-uploader.component';
import { SearchDebuggerComponent } from './components/search-debugger/search-debugger.component';
import { ExtractionInspectorComponent } from './components/extraction-inspector/extraction-inspector.component';
import { WorkbenchStateService } from './services/workbench-state.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    TelemetryBarComponent,
    PdfUploaderComponent,
    SearchDebuggerComponent,
    ExtractionInspectorComponent,
  ],
  template: `
    <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <!-- Top Fixed Telemetry Bar -->
      <app-telemetry-bar></app-telemetry-bar>

      <!-- Global Error Toast / Banner -->
      @if (state.errorMessage(); as error) {
        <div class="bg-rose-950/80 border-b border-rose-800 text-rose-300 text-xs px-6 py-2.5 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="font-bold">Error:</span>
            <span>{{ error }}</span>
          </div>
          <button (click)="state.errorMessage.set(null)" class="text-rose-400 hover:text-white font-bold ml-4">
            ✕
          </button>
        </div>
      }

      <!-- Split-Screen Workbench Grid -->
      <main class="flex-1 p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1720px] mx-auto w-full">
        <!-- Left Column: PDF Ingestion & Hybrid RAG Debugger (5 cols) -->
        <section class="lg:col-span-5 flex flex-col space-y-6">
          <app-pdf-uploader></app-pdf-uploader>
          <app-search-debugger class="flex-1"></app-search-debugger>
        </section>

        <!-- Right Column: Live Pydantic Validation & Relational Inspector (7 cols) -->
        <section class="lg:col-span-7 flex flex-col">
          <app-extraction-inspector class="h-full"></app-extraction-inspector>
        </section>
      </main>
    </div>
  `,
})
export class AppComponent {
  state = inject(WorkbenchStateService);
}
