const applications = [
  {
    title: "Games",
    body: "Give NPCs stable memory, relationship context, and deterministic response contracts before connecting model providers.",
    link: "https://github.com/Celovin/luvoire/blob/main/docs/sdk/integration_patterns.md",
  },
  {
    title: "Fictional Replay Research",
    body: "Run synthetic, non-identifying scenarios for prevention-oriented analysis without suspect scoring or prediction claims.",
    link: "https://github.com/Celovin/luvoire/blob/main/docs/dsl/tutorial.md",
  },
  {
    title: "Academic Simulation",
    body: "Keep seeds, config, logs, benchmarks, and citations close enough for reproducible inspection.",
    link: "https://github.com/Celovin/luvoire/blob/main/docs/reports/reproducibility.md",
  },
];

export function ThreeApplications() {
  return (
    <section className="section applications" id="applications">
      <div className="section-heading">
        <p className="eyebrow">Application tracks</p>
        <h2>Built For Proof, Not Pitch Decks</h2>
      </div>
      <div className="application-grid">
        {applications.map((item) => (
          <article className="application-panel" key={item.title}>
            <h3>{item.title}</h3>
            <p>{item.body}</p>
            <a href={item.link}>Open path</a>
          </article>
        ))}
      </div>
    </section>
  );
}
