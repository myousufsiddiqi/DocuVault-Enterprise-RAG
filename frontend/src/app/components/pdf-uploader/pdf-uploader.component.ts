import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkbenchStateService } from '../../services/workbench-state.service';

@Component({
  selector: 'app-pdf-uploader',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <svg class="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          In-Memory PDF Ingestion
        </h2>
        <span class="text-[11px] text-slate-500 font-mono">Zero Disk I/O (Direct RAM Stream)</span>
      </div>

      <!-- Drag & Drop Zone -->
      <div
        (dragover)="onDragOver($event)"
        (dragleave)="onDragLeave($event)"
        (drop)="onDrop($event)"
        (click)="fileInput.click()"
        [class.border-indigo-500]="isDragging"
        [class.bg-indigo-950]="isDragging"
        class="border-2 border-dashed border-slate-700 hover:border-indigo-500/80 rounded-lg p-6 text-center cursor-pointer transition-all duration-200 bg-slate-950/40"
      >
        <input
          #fileInput
          type="file"
          accept=".pdf"
          class="hidden"
          (change)="onFileSelected($event)"
        />

        @if (state.isIngesting()) {
          <!-- Ingestion Spinner Animation -->
          <div class="flex flex-col items-center justify-center py-4">
            <div class="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mb-3"></div>
            <p class="text-sm font-medium text-slate-200">Processing Document In-Memory...</p>
            <p class="text-xs text-slate-400 mt-1">Parsing PyMuPDF → Pydantic Reflection Loop → FastEmbed 384d Embeddings</p>
          </div>
        } @else {
          <!-- Upload Prompt -->
          <div class="flex flex-col items-center justify-center">
            <div class="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 mb-3 group-hover:scale-105 transition-transform">
              <svg class="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p class="text-sm font-medium text-slate-300">
              Drag & drop enterprise PDF here, or <span class="text-indigo-400 underline">browse</span>
            </p>
            <p class="text-xs text-slate-500 mt-1">Invoices, financial reports, vendor statements</p>
          </div>
        }
      </div>

      <!-- Active Ingested Document Metadata Pill -->
      @if (state.activeDocument(); as doc) {
        <div class="mt-4 p-3 bg-slate-800/70 border border-slate-700/60 rounded-lg flex items-center justify-between text-xs">
          <div class="flex items-center space-x-2 truncate">
            <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span class="font-medium text-slate-200 truncate">{{ doc.filename }}</span>
          </div>
          <div class="flex items-center space-x-3 text-slate-400 font-mono flex-shrink-0">
            <span>{{ doc.page_count }} pg</span>
            <span>•</span>
            <span>{{ doc.total_chunks }} chunks</span>
            <span>•</span>
            <span>{{ (doc.file_size_bytes / 1024).toFixed(1) }} KB</span>
          </div>
        </div>
      }
    </div>
  `,
})
export class PdfUploaderComponent {
  state = inject(WorkbenchStateService);
  isDragging = false;

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      const file = event.dataTransfer.files[0];
      if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
        this.state.ingestFile(file);
      }
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.state.ingestFile(input.files[0]);
    }
  }
}
