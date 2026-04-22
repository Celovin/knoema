const code = `from luvoire.game import GameSession

session = GameSession(game_id='demo-village')
npc = session.create_npc(
    persona_file='sdk/python/examples/personas/shopkeeper.yaml',
    initial_relationships={'player': 'neighbor'},
)

response = npc.interact(
    'asks about the lantern market',
    context={'location': 'Harbor Village'},
)`;

export function CodeDemo() {
  return (
    <section className="section code-section">
      <div>
        <p className="eyebrow">SDK contract</p>
        <h2>Start With A Deterministic NPC Surface</h2>
        <p>
          The Phase 24 SDK keeps game integration work testable before provider-backed dialogue is
          connected. The same response contract is mirrored in Python, TypeScript, and GDScript.
        </p>
      </div>
      <pre aria-label="Python SDK example">
        <code>{code}</code>
      </pre>
    </section>
  );
}
