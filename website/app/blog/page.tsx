import Link from "next/link";

const drafts = [
  "Why Knoema for Korean indie games",
  "LLM NPC memory design principles",
  "Godot integration step by step",
  "Academic research reproducibility",
  "Ethics and guards for synthetic replay scenarios",
];

export default function BlogPage() {
  return (
    <main className="subpage">
      <Link className="back-link" href="/">
        Knoema Engine
      </Link>
      <h1>Publication Queue</h1>
      <p>Draft topics are kept public so early users can see what is being documented next.</p>
      <ol className="draft-list">
        {drafts.map((draft) => (
          <li key={draft}>{draft}</li>
        ))}
      </ol>
      <a className="primary-link" href="https://github.com/Celovin/knoema/blob/main/docs/tutorial_blog.md">
        Read Tutorial Draft
      </a>
    </main>
  );
}
