import { GameSession } from "../src/index";

const session = new GameSession({ gameId: "demo-village" });
const npc = session.createNPC({
  npcId: "shopkeeper",
  name: "Mina",
  persona: { background: "Synthetic shopkeeper coordinating a lantern market stall." },
  initialRelationships: { player: "neighbor" },
});

const response = npc.interact("asks whether the lantern market is ready", {
  location: "Harbor Village",
  time: "2026-06-01T18:00:00",
});

console.log(response.text);
