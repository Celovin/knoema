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
    this.npcId = requiredText(config.npcId, "npcId");
    this.name = requiredText(config.name, "name");
    this.persona = copyUnknownRecord(config.persona, "persona");
    this.initialRelationships = copyStringRecord(
      config.initialRelationships,
      "initialRelationships",
    );
  }

  interact(playerAction: string, context?: Record<string, unknown>): NPCResponse {
    const resolvedAction = requiredText(playerAction, "playerAction");
    const resolvedContext =
      context !== undefined ? copyUnknownRecord(context, "context") : {};
    const locationValue =
      resolvedContext.location !== undefined && resolvedContext.location !== null
        ? resolvedContext.location
        : "unknown location";
    const relationship = textOrDefault(this.initialRelationships.player, "stranger");
    const location = textOrDefault(locationValue, "unknown location");
    return {
      text: `${this.name} responds to ${resolvedAction} at ${location} as a ${relationship}.`,
      emotion: "neutral",
      branchFlags: [`location:${location}`, `relationship:${relationship}`],
      raw: { npcId: this.npcId, playerAction: resolvedAction, context: resolvedContext },
    };
  }
}

export class GameSession {
  readonly gameId: string;
  readonly provider: string;
  private readonly npcs = new Map<string, NPC>();

  constructor(config: { gameId: string; provider?: string }) {
    this.gameId = requiredText(config.gameId, "gameId");
    this.provider =
      config.provider !== undefined ? requiredText(config.provider, "provider") : "local";
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

function requiredText(value: unknown, fieldName: string): string {
  if (typeof value !== "string") {
    throw new Error(`${fieldName} must be a string`);
  }
  const text = value.trim();
  if (text.length === 0) {
    throw new Error(`${fieldName} must not be empty`);
  }
  return text;
}

function textOrDefault(value: unknown, defaultValue: string): string {
  if (value === undefined || value === null) {
    return defaultValue;
  }
  const text = String(value).trim();
  return text.length > 0 ? text : defaultValue;
}

function copyUnknownRecord(value: unknown, fieldName: string): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${fieldName} must be an object`);
  }
  return { ...(value as Record<string, unknown>) };
}

function copyStringRecord(value: unknown, fieldName: string): Record<string, string> {
  if (value === undefined) {
    return {};
  }
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${fieldName} must be an object`);
  }
  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>).map(([key, entry]) => [
      requiredText(key, `${fieldName} key`),
      requiredText(entry, `${fieldName}.${key}`),
    ]),
  );
}
