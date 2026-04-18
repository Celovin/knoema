# Interactive Tutorial Website

Phase 61 adds `/tutorial` to the Next.js website.

The tutorial has five chapters:

1. Your First Agent
2. Memory & Relationships
3. Scenario DSL
4. Theory of Mind
5. Deploy to Production

Each chapter includes a short task, editable code, a deterministic run button, a quiz, and localStorage progress tracking. The code editor surface is marked with `data-monaco-editor="true"` so it can be replaced with the full Monaco package without changing the page contract.

## Run

```bash
npm --prefix website run build
npm --prefix website run e2e
```

The Playwright suite covers `/tutorial` chapter execution and editor editing, alongside the existing scenario editor flow.
