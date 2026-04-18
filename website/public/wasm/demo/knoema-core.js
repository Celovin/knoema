const ACTIONS = ["observe", "speak", "move", "work"];

export class Persona {
  constructor({ agentId, name, goals = [], location = "Dormitory" }) {
    if (!agentId || !name) {
      throw new Error("agentId and name are required");
    }
    this.agentId = agentId;
    this.name = name;
    this.goals = [...goals];
    this.location = location;
    this.memory = [];
  }
}

export class Environment {
  constructor({ locationPath = ["Browser", "Demo"], tickMinutes = 30 } = {}) {
    this.locationPath = [...locationPath];
    this.tickMinutes = tickMinutes;
    this.tick = 0;
  }

  currentLocation() {
    return this.locationPath[this.locationPath.length - 1] || "Demo";
  }
}

export class LocalClient {
  constructor(responder = null) {
    this.responder = responder;
  }

  decide({ persona, tick, rng }) {
    if (this.responder) {
      return this.responder({ persona, tick, rng });
    }
    const actionType = ACTIONS[Math.floor(rng() * ACTIONS.length)];
    const target = actionType === "speak" ? "neighbor" : null;
    return {
      action_type: actionType,
      target,
      content: `${persona.name} ${actionType}s at tick ${tick}.`,
    };
  }
}

export function seededRandom(seed = 1) {
  let state = seed >>> 0;
  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

export function runSimulation({
  personas,
  environment = new Environment(),
  ticks = 100,
  seed = 20260419,
  client = new LocalClient(),
}) {
  if (!Array.isArray(personas) || personas.length === 0) {
    throw new Error("personas must contain at least one agent");
  }
  const rng = seededRandom(seed);
  const logs = [];
  const started = performance.now();
  for (let tick = 0; tick < ticks; tick += 1) {
    environment.tick = tick;
    for (const persona of personas) {
      const decision = client.decide({ persona, tick, rng });
      const entry = {
        tick,
        agent_id: persona.agentId,
        name: persona.name,
        action_type: decision.action_type,
        target: decision.target,
        content: decision.content,
        location: persona.location || environment.currentLocation(),
      };
      persona.memory.push(entry.content);
      if (persona.memory.length > 20) {
        persona.memory.shift();
      }
      logs.push(entry);
    }
  }
  const elapsedMs = Math.max(0, performance.now() - started);
  return {
    agents: personas.length,
    ticks,
    actions: logs.length,
    elapsed_ms: Number(elapsedMs.toFixed(3)),
    logs,
  };
}

export function createDormAgents(count = 2) {
  return Array.from({ length: count }, (_, index) => {
    const number = index + 1;
    return new Persona({
      agentId: `agent-${number}`,
      name: `Agent ${number}`,
      goals: ["keep a coherent routine", "respond to neighbors"],
      location: number % 2 === 0 ? "Common Room" : "Study Room",
    });
  });
}

export function runSallyAnneDemo() {
  const timeline = [
    "Sally puts the marble in the basket.",
    "Sally leaves the room.",
    "Anne moves the marble to the box.",
    "Sally returns without seeing the move.",
  ];
  const result = {
    object: "marble",
    actual_location: "box",
    sally_belief_location: "basket",
    predicted_search_location: "basket",
    correct: true,
    accuracy: 1,
  };
  return { timeline, result };
}
