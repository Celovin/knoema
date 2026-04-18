const links = [
  ["GitHub", "https://github.com/Celovin/knoema"],
  ["Playground", "https://huggingface.co/spaces/celovin/knoema-playground"],
  ["Formal Report", "https://github.com/Celovin/knoema/blob/main/benchmarks/formal_report/report.pdf"],
  ["Discord Kit", "https://github.com/Celovin/knoema/blob/main/docs/discord_community.md"],
];

export function CTA() {
  return (
    <section className="section cta">
      <p className="eyebrow">Public artifacts</p>
      <h2>Run It, Inspect It, Fork It</h2>
      <div className="cta-links">
        {links.map(([label, href]) => (
          <a href={href} key={href}>
            {label}
          </a>
        ))}
      </div>
    </section>
  );
}
