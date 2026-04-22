import assert from "node:assert/strict";
import { performance } from "node:perf_hooks";

globalThis.performance = performance;

const runtime = await import("../demo/luvoire-core.js");

const twoAgent = runtime.runSimulation({
  personas: runtime.createDormAgents(2),
  environment: new runtime.Environment({ locationPath: ["Node", "Dorm"] }),
  ticks: 100,
});

assert.equal(twoAgent.agents, 2);
assert.equal(twoAgent.actions, 200);
assert.ok(twoAgent.elapsed_ms < 2000);

const fiveAgent = runtime.runSimulation({
  personas: runtime.createDormAgents(5),
  ticks: 100,
});

assert.equal(fiveAgent.agents, 5);
assert.equal(fiveAgent.actions, 500);

const sallyAnne = runtime.runSallyAnneDemo();
assert.equal(sallyAnne.result.predicted_search_location, "basket");
assert.equal(sallyAnne.result.accuracy, 1);
