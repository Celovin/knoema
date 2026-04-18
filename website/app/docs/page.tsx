import Link from "next/link";

const docs = [
  ["Architecture", "https://github.com/Celovin/knoema/blob/main/docs/architecture.md"],
  ["Scenario DSL", "https://github.com/Celovin/knoema/blob/main/docs/dsl/tutorial.md"],
  ["Python SDK", "https://github.com/Celovin/knoema/blob/main/docs/sdk/python-api.md"],
  ["TypeScript SDK", "https://github.com/Celovin/knoema/blob/main/docs/sdk/typescript-api.md"],
  ["Godot SDK", "https://github.com/Celovin/knoema/blob/main/docs/sdk/godot-api.md"],
  ["CLI", "https://github.com/Celovin/knoema/blob/main/docs/cli.md"],
];

export default function DocsPage() {
  return (
    <main className="subpage">
      <Link className="back-link" href="/">
        Knoema Engine
      </Link>
      <h1>Build From The Public Artifacts</h1>
      <p>
        Start with the architecture notes, run a deterministic YAML scenario, then choose the SDK
        surface that matches your engine or tooling stack.
      </p>
      <div className="link-grid">
        {docs.map(([label, href]) => (
          <a className="link-tile" href={href} key={href}>
            <span>{label}</span>
            <strong>Open</strong>
          </a>
        ))}
      </div>
    </main>
  );
}
