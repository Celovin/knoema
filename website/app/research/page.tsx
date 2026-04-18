import Link from "next/link";

const reports = [
  ["50-Agent Benchmark", "https://github.com/Celovin/knoema/blob/main/docs/reports/50_agent_benchmark.pdf"],
  ["Formal Benchmark Report", "https://github.com/Celovin/knoema/blob/main/benchmarks/formal_report/report.pdf"],
  ["Reproducibility Report", "https://github.com/Celovin/knoema/blob/main/docs/reports/reproducibility.md"],
  ["Technical Report Draft", "https://github.com/Celovin/knoema/blob/main/paper/knoema_technical_report.pdf"],
];

export default function ResearchPage() {
  return (
    <main className="subpage research-page">
      <Link className="back-link" href="/">
        Knoema Engine
      </Link>
      <h1>Reproducible Agent Simulation Evidence</h1>
      <p>
        The public bundle keeps benchmark inputs, deterministic logs, summary tables, and PDF
        reports together so research claims can be inspected from source.
      </p>
      <div className="figure-strip" aria-label="Formal benchmark figures">
        <img alt="Memory recall benchmark figure" src="/figures/memory_recall.svg" />
        <img alt="Token efficiency benchmark figure" src="/figures/token_efficiency.svg" />
        <img alt="Narrative branching benchmark figure" src="/figures/branching.svg" />
        <img alt="Scalability benchmark figure" src="/figures/scalability.svg" />
      </div>
      <div className="link-grid">
        {reports.map(([label, href]) => (
          <a className="link-tile" href={href} key={href}>
            <span>{label}</span>
            <strong>Read</strong>
          </a>
        ))}
      </div>
    </main>
  );
}
