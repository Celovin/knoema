import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Showcase | Knoema Engine",
  description:
    "Knoema Engine paths for browser playground demos, game SDK prototyping, and research SaaS inspection.",
  alternates: {
    canonical: "/showcase",
  },
};

const paths = [
  ["Browser Playground", "Run replay-only demos or provide a session key for live LLM trials."],
  ["Game SDK", "Prototype deterministic NPC response contracts in Python, TypeScript, or Godot."],
  ["Research SaaS", "Inspect memory retrieval, relationships, cost budget, and citation exports."],
];

export default function ShowcasePage() {
  return (
    <main className="subpage">
      <Link className="back-link" href="/">
        Knoema Engine
      </Link>
      <h1>Three Paths Into The Engine</h1>
      <div className="path-list">
        {paths.map(([title, body]) => (
          <article key={title}>
            <h2>{title}</h2>
            <p>{body}</p>
          </article>
        ))}
      </div>
      <a className="primary-link" href="https://huggingface.co/spaces/celovin/knoema-playground">
        Open Playground
      </a>
    </main>
  );
}
