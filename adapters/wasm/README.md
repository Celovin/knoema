# Browser-Side Runtime

Phase 54 adds a static browser runtime for deterministic Luvoire demos. The runtime is a small TypeScript-source module copied into `demo/luvoire-core.js` by the build script. It does not require Pyodide, Python, or an LLM API key.

## Run

```powershell
cd C:\Users\admin\Projects\luvoire
npm --prefix adapters\wasm run build
npm --prefix adapters\wasm test
npm --prefix adapters\wasm run e2e
```

Serve the directory with any static file server, then open `index.html`. ES modules require an HTTP origin in current browsers.

## Static Hosting

The demo directory is static. It can be copied to GitHub Pages, Vercel static hosting, or any object storage bucket. Public deployment remains an operator-side account configuration step.
