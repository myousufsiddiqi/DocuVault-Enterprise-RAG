import { ApplicationConfig, provideExperimentalZonelessChangeDetection } from '@angular/core';
import { provideHttpClient, withFetch } from '@angular/common/http';

export const appConfig: ApplicationConfig = {
  providers: [
    // Non-negotiable guardrail: Strictly Zoneless Change Detection (No Zone.js)
    provideExperimentalZonelessChangeDetection(),
    // Modern Fetch-based HttpClient for reactive streaming & high performance
    provideHttpClient(withFetch()),
  ],
};
