import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkbenchStateService } from '../../services/workbench-state.service';

@Component({
  selector: 'app-extraction-inspector',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm h-full flex flex-col">
      <!-- Section Header & View Mode Switcher -->
      <div class="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h2 class="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            Structured Extraction (Track A)
          </h2>
          <p class="text-xs text-slate-400">Strict Pydantic v2 Contract with Self-Healing Validation</p>
        </div>

        <!-- View Mode Tabs -->
        <div class="inline-flex rounded-lg bg-slate-950 p-1 border border-slate-800 text-xs font-medium">
          <button
            type="button"
            (click)="activeTab.set('table')"
            [class.bg-emerald-600]="activeTab() === 'table'"
            [class.text-white]="activeTab() === 'table'"
            [class.text-slate-400]="activeTab() !== 'table'"
            class="px-3 py-1 rounded-md transition-all duration-150"
          >
            Relational Table
          </button>
          <button
            type="button"
            (click)="activeTab.set('json')"
            [class.bg-emerald-600]="activeTab() === 'json'"
            [class.text-white]="activeTab() === 'json'"
            [class.text-slate-400]="activeTab() !== 'json'"
            class="px-3 py-1 rounded-md transition-all duration-150"
          >
            Raw JSON
          </button>
        </div>
      </div>

      <!-- Main Inspector Content -->
      @if (state.activeDocument(); as doc) {
        <div class="mt-4 flex-1 flex flex-col space-y-4 overflow-hidden">
          
          <!-- Mathematical Validation Status Banner -->
          <div
            [class]="doc.extraction_validation_passed 
              ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300' 
              : 'bg-amber-950/40 border-amber-800/80 text-amber-300'"
            class="p-3 rounded-lg border text-xs flex items-center justify-between"
          >
            <div class="flex items-center gap-2">
              <span class="text-base font-bold">
                {{ doc.extraction_validation_passed ? '✓' : '⚠' }}
              </span>
              <div>
                <span class="font-semibold">
                  {{ doc.extraction_validation_passed ? 'Mathematical Reflection Audit Passed' : 'Arithmetic Discrepancy Flagged' }}
                </span>
                <p class="text-[11px] opacity-80">
                  @if (doc.telemetry.extraction_retries > 0) {
                    Self-healing reflection loop executed {{ doc.telemetry.extraction_retries }} retry iteration(s) to balance totals.
                  } @else {
                    All line items sum to subtotal, and subtotal + tax equals grand total on the first inference pass.
                  }
                </p>
              </div>
            </div>
            <div class="font-mono text-xs px-2.5 py-1 rounded bg-slate-900 border border-slate-700">
              {{ doc.telemetry.extraction_time_ms.toFixed(0) }} ms
            </div>
          </div>

          <!-- Document Header Metadata Cards -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div class="p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span class="text-slate-500 uppercase tracking-wider text-[10px] block font-mono">Invoice Number</span>
              <span class="font-semibold text-slate-200 mt-1 block truncate">{{ doc.extraction.invoice_number }}</span>
            </div>
            <div class="p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span class="text-slate-500 uppercase tracking-wider text-[10px] block font-mono">Invoice Date</span>
              <span class="font-semibold text-slate-200 mt-1 block">{{ doc.extraction.invoice_date }}</span>
            </div>
            <div class="p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span class="text-slate-500 uppercase tracking-wider text-[10px] block font-mono">Vendor</span>
              <span class="font-semibold text-slate-200 mt-1 block truncate">{{ doc.extraction.vendor_name }}</span>
            </div>
            <div class="p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
              <span class="text-slate-500 uppercase tracking-wider text-[10px] block font-mono">Grand Total</span>
              <span class="font-bold text-emerald-400 mt-1 block font-mono text-sm">
                {{ doc.extraction.currency }} {{ doc.extraction.grand_total.toFixed(2) }}
              </span>
            </div>
          </div>

          <!-- Tab Content: Table vs JSON -->
          @if (activeTab() === 'table') {
            <!-- Line Items Relational Table -->
            <div class="flex-1 overflow-y-auto border border-slate-800 rounded-lg bg-slate-950/40">
              <table class="w-full text-left text-xs text-slate-300">
                <thead class="bg-slate-950 border-b border-slate-800 sticky top-0 text-[11px] uppercase tracking-wider text-slate-400 font-mono">
                  <tr>
                    <th class="py-2.5 px-3">Description</th>
                    <th class="py-2.5 px-3 text-right">Qty</th>
                    <th class="py-2.5 px-3 text-right">Unit Price</th>
                    <th class="py-2.5 px-3 text-right">Line Total</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/60">
                  @for (item of doc.extraction.line_items; track item.description) {
                    <tr class="hover:bg-slate-900/60 transition-colors">
                      <td class="py-2.5 px-3 font-medium text-slate-200">{{ item.description }}</td>
                      <td class="py-2.5 px-3 text-right font-mono text-slate-400">{{ item.quantity }}</td>
                      <td class="py-2.5 px-3 text-right font-mono text-slate-400">\${{ item.unit_price.toFixed(2) }}</td>
                      <td class="py-2.5 px-3 text-right font-mono font-semibold text-slate-100">\${{ item.total.toFixed(2) }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>

            <!-- Totals Ledger Summary -->
            <div class="p-3 bg-slate-950 border border-slate-800 rounded-lg flex justify-end space-x-6 text-xs font-mono">
              <div class="text-right">
                <span class="text-slate-500 block">Subtotal:</span>
                <span class="font-semibold text-slate-300">\${{ doc.extraction.subtotal.toFixed(2) }}</span>
              </div>
              <div class="text-right">
                <span class="text-slate-500 block">Tax:</span>
                <span class="font-semibold text-slate-300">\${{ doc.extraction.tax_amount.toFixed(2) }}</span>
              </div>
              <div class="text-right">
                <span class="text-slate-500 block">Grand Total:</span>
                <span class="font-bold text-emerald-400 text-sm">\${{ doc.extraction.grand_total.toFixed(2) }}</span>
              </div>
            </div>
          } @else {
            <!-- Raw JSON Inspector -->
            <div class="flex-1 overflow-y-auto p-4 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-indigo-300 leading-relaxed">
              <pre>{{ doc.extraction | json }}</pre>
            </div>
          }
        </div>
      } @else {
        <!-- Empty State Prompt -->
        <div class="flex-1 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-lg text-slate-500 p-8 text-center">
          <svg class="w-12 h-12 text-slate-700 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <p class="text-sm font-medium text-slate-400">No Document Ingested</p>
          <p class="text-xs text-slate-600 mt-1">Upload a PDF on the left to inspect Pydantic-validated relational fields.</p>
        </div>
      }
    </div>
  `,
})
export class ExtractionInspectorComponent {
  state = inject(WorkbenchStateService);
  activeTab = signal<'table' | 'json'>('table');
}
