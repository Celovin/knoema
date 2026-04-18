export type NPCResponse = {
  text: string;
  emotion: string;
  branchFlags: string[];
  raw: Record<string, unknown>;
};

export type NPCConfig = {
  npcId: string;
  name: string;
  persona: Record<string, unknown>;
  initialRelationships?: Record<string, string>;
};

export class NPC {
  readonly npcId: string;
  readonly name: string;
  readonly persona: Record<string, unknown>;
  readonly initialRelationships: Record<string, string>;

  constructor(config: NPCConfig) {
    this.npcId = config.npcId;
    this.name = config.name;
    this.persona = config.persona;
    this.initialRelationships =
      config.initialRelationships !== undefined ? config.initialRelationships : {};
  }

  interact(playerAction: string, context: Record<string, unknown> = {}): NPCResponse {
    const locationValue =
      context.location !== undefined && context.location !== null
        ? context.location
        : "unknown location";
    const relationship =
      this.initialRelationships.player !== undefined ? this.initialRelationships.player : "stranger";
    const location = String(locationValue);
    return {
      text: `${this.name} responds to ${playerAction} at ${location} as a ${relationship}.`,
      emotion: "neutral",
      branchFlags: [`location:${location}`, `relationship:${relationship}`],
      raw: { npcId: this.npcId, playerAction, context },
    };
  }
}

export class GameSession {
  readonly gameId: string;
  readonly provider: string;
  private readonly npcs = new Map<string, NPC>();

  constructor(config: { gameId: string; provider?: string }) {
    this.gameId = config.gameId;
    this.provider = config.provider !== undefined ? config.provider : "local";
  }

  createNPC(config: NPCConfig): NPC {
    const npc = new NPC(config);
    this.npcs.set(npc.npcId, npc);
    return npc;
  }

  summary(): Record<string, unknown> {
    return {
      gameId: this.gameId,
      provider: this.provider,
      npcCount: this.npcs.size,
      npcs: Array.from(this.npcs.keys()).sort(),
    };
  }
}
