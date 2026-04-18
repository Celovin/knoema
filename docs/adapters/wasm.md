# Browser WASM Runtime

Phase 54 provides a browser-side runtime for static demos. It uses a compact TypeScript-source module rather than Pyodide so first load stays small and the demo can run without a server.

## Commands

```powershell
npm --prefix adapters\wasm run build
npm --prefix adapters\wasm test
npm --prefix adapters\wasm run e2e
```

The build writes `adapters/wasm/demo/knoema-core.js` and checks that the bundle stays under 500 KB. The current runtime covers:

- `Persona`
- `Environment`
- `LocalClient`
- `runSimulation`
- `createDormAgents`
- `runSallyAnneDemo`

## Demo Pages

- `adapters/wasm/demo/2-agent.html`
- `adapters/wasm/demo/5-agent.html`
- `adapters/wasm/demo/sally-anne.html`

The pages are static and can be served from GitHub Pages at a path such as `https://celovin.github.io/knoema/wasm/` after repository Pages configuration.
