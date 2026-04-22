import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Research | Luvoire",
  description:
    "Reproducible benchmark inputs, deterministic logs, summary tables, and reports for Luvoire.",
  alternates: {
    canonical: "/research",
  },
};

const reports = [
  ["50-Agent Benchmark", "https://github.com/Celovin/luvoire/blob/main/docs/reports/50_agent_benchmark.pdf"],
  ["Formal Benchmark Report", "https://github.com/Celovin/luvoire/blob/main/benchmarks/formal_report/report.pdf"],
  ["Reproducibility Report", "https://github.com/Celovin/luvoire/blob/main/docs/reports/reproducibility.md"],
  ["Technical Report Draft", "https://github.com/Celovin/luvoire/blob/main/paper/luvoire_technical_report.pdf"],
];

export default function ResearchPage() {
  return (
    <main className="subpage research-page">
      <Link className="back-link" href="/">
        Luvoire
      </Link>
      <h1>Reproducible Agent Simulation Evidence</h1>
      <p>
        The public bundle keeps benchmark inputs, deterministic logs, summary tables, and PDF
        reports together so research claims can be inspected from source.
      </p>
      <div className="figure-strip" aria-label="Formal benchmark figures">
        <img
          alt="Memory recall benchmark figure"
          decoding="async"
          height="420"
          loading="lazy"
          src="/figures/memory_recall.svg"
          width="960"
        />
        <img
          alt="Token efficiency benchmark figure"
          decoding="async"
          height="420"
          loading="lazy"
          src="/figures/token_efficiency.svg"
          width="960"
        />
        <img
          alt="Narrative branching benchmark figure"
          decoding="async"
          height="420"
          loading="lazy"
          src="/figures/branching.svg"
          width="960"
        />
        <img
          alt="Scalability benchmark figure"
          decoding="async"
          height="420"
          loading="lazy"
          src="/figures/scalability.svg"
          width="960"
        />
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
