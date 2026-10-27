# DocuVault AI: Frontend (Angular 22 Enterprise Dashboard)

## Architecture Overview
The frontend is built with **Angular 22** adhering to modern enterprise design principles:
- **Strictly Zoneless:** Configured via `provideExperimentalZonelessChangeDetection()`.
- **Standalone Components:** Zero `NgModules`.
- **Signal-Driven Reactive State:** Full lifecycle managed via `signal()`, `computed()`, and `effect()`.
- **New Control Flow:** Pure `@if`, `@for`, and `@switch` syntax.
- **Styling:** Tailwind CSS with a dark enterprise workbench theme.

## Planned Split-Screen Layout Structure
```text
frontend/
├── src/
│   ├── app/
│   │   ├── app.config.ts                     # Zoneless change detection + HttpClient fetch provider
│   │   ├── app.component.ts                  # Root workbench shell
│   │   ├── app.component.html                # Split-screen Tailwind grid layout
│   │   ├── components/
│   │   │   ├── telemetry-bar/                # Live tokens, latency (ms), LLM retry count
│   │   │   ├── pdf-uploader/                 # In-memory drag-and-drop PDF ingestion
│   │   │   ├── search-debugger/              # Hybrid vs. Vector vs. Keyword RAG debugger
│   │   │   └── extraction-inspector/         # Validated Pydantic JSON/table viewer
│   │   └── services/
│   │       ├── api.service.ts                # Strictly typed async fetch client
│   │       └── workbench-state.service.ts    # Central Signal store for active document & telemetry
│   ├── index.html
│   ├── main.ts
│   └── styles.css
├── angular.json
├── package.json
├── tailwind.config.js
└── tsconfig.json
```
