export function Architecture() {
  return (
    <section className="section architecture">
      <div className="architecture-copy">
        <p className="eyebrow">Runtime map</p>
        <h2>Memory, Relationships, Environment, Decisions</h2>
        <p>
          Personas, short-term memory, semantic-temporal retrieval, relationship edges, environment
          context, and emotion state feed a decision loop that exports JSONL logs for replay.
        </p>
      </div>
      <svg aria-label="Knoema architecture diagram" viewBox="0 0 720 420" role="img">
        <defs>
          <marker id="arrow" markerHeight="8" markerWidth="8" orient="auto" refX="7" refY="4">
            <path d="M0,0 L8,4 L0,8 Z" fill="currentColor" />
          </marker>
        </defs>
        <g className="diagram-lines" fill="none" markerEnd="url(#arrow)">
          <path d="M160 95 C250 95 300 170 360 170" />
          <path d="M160 180 C240 180 285 190 360 190" />
          <path d="M160 265 C240 265 300 215 360 210" />
          <path d="M490 190 C565 190 590 140 635 120" />
          <path d="M490 190 C565 190 590 240 635 260" />
        </g>
        <g className="diagram-node">
          <rect height="58" rx="8" width="130" x="40" y="66" />
          <text x="105" y="101">Persona</text>
        </g>
        <g className="diagram-node">
          <rect height="58" rx="8" width="130" x="40" y="151" />
          <text x="105" y="186">Memory</text>
        </g>
        <g className="diagram-node">
          <rect height="58" rx="8" width="130" x="40" y="236" />
          <text x="105" y="271">World State</text>
        </g>
        <g className="diagram-core">
          <rect height="82" rx="8" width="150" x="350" y="151" />
          <text x="425" y="187">Decision</text>
          <text x="425" y="210">Loop</text>
        </g>
        <g className="diagram-node">
          <rect height="58" rx="8" width="132" x="590" y="88" />
          <text x="656" y="123">JSONL Logs</text>
        </g>
        <g className="diagram-node">
          <rect height="58" rx="8" width="132" x="590" y="228" />
          <text x="656" y="263">SDK Payload</text>
        </g>
      </svg>
    </section>
  );
}
