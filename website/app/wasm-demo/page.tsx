export default function WasmDemoPage() {
  return (
    <main className="subpage">
      <a className="back-link" href="/">
        Back to home
      </a>
      <section className="section">
        <p className="eyebrow">Browser demo</p>
        <h1>Luvoire runs in a static browser page.</h1>
        <p className="lede">
          Open the packaged demo to run deterministic agents without a server, API key, or
          Python runtime.
        </p>
        <a className="primary-link" href="/wasm/index.html">
          Open browser runtime
        </a>
      </section>
    </main>
  );
}
