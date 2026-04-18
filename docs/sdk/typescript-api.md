# TypeScript Game SDK

The TypeScript package is a client-side or Node-compatible facade for game tooling.

```ts
import { GameSession } from "@celovin/knoema-game";

const session = new GameSession({ gameId: "demo-village" });
const npc = session.createNPC({
  npcId: "shopkeeper",
  name: "Mina",
  persona: { background: "Synthetic shopkeeper." },
  initialRelationships: { player: "neighbor" },
});

const response = npc.interact("asks about the lantern market", {
  location: "Harbor Village",
});
```

## API

- `GameSession.createNPC(config)`: registers and returns an NPC.
- `NPC.interact(playerAction, context)`: returns a deterministic `NPCResponse`.
- `GameSession.summary()`: returns a serializable session summary.
