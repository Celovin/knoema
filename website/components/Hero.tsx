import Link from "next/link";

const proofItems = ["v0.1.0 public release", "122 local tests", "Python, TypeScript, Godot SDKs"];

export function Hero() {
  return (
    <section className="hero">
      <nav className="site-nav" aria-label="Primary navigation">
        <Link href="/">Knoema</Link>
        <div>
          <Link href="/docs">Docs</Link>
          <Link href="/research">Research</Link>
          <Link href="/showcase">Showcase</Link>
          <Link href="/blog">Blog</Link>
        </div>
      </nav>
      <div className="hero-copy">
        <p className="eyebrow">Open multi-agent simulation engine</p>
        <h1>One engine. Three worlds.</h1>
        <p className="hero-lede">
          Persistent NPCs, synthetic replay research, and reproducible social simulation built from
          the same memory, relationship, and event runtime.
        </p>
        <div className="hero-actions" aria-label="Primary actions">
          <a href="https://github.com/Celovin/knoema">GitHub</a>
          <a href="https://huggingface.co/spaces/Celovin/knoema-playground">Playground</a>
        </div>
        <ul className="proof-list" aria-label="Project proof points">
          {proofItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
