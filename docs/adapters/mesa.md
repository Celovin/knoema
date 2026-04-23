# Mesa 3 Adapter

Install the optional Mesa integration with:

```bash
pip install "luvoire[mesa]"
```

The adapter wraps an existing Luvoire `Simulator` as a Mesa 3 `Model`. It does not import or depend on `mesa-llm`; LLM calls, when a simulation uses them, remain inside `luvoire.llm.gateway` and can use the replay cache by setting `LUVOIRE_REPLAY_CACHE_PATH`.

```python
from datetime import datetime

from luvoire import Environment, Persona, Personality, Simulator
from luvoire.adapters.mesa import to_mesa_model


def persona(agent_id: str) -> Persona:
    return Persona(
        agent_id=agent_id,
        name=agent_id.title(),
        age=31,
        background="Synthetic participant in a coordination scenario.",
        personality=Personality(0.55, 0.65, 0.45, 0.7, 0.35),
        values=["coordination", "clarity"],
        goals=["keep the scenario stable"],
    )


env = Environment(
    start_time=datetime(2026, 4, 23, 19, 0),
    location_path=("Luvoire Demo World", "Gangnam Plaza"),
)
sim = Simulator(
    agents=[persona(f"agent_{i}") for i in range(10)],
    environment=env,
    tick_duration_minutes=30,
)
model = to_mesa_model(sim, seed=42)

for _ in range(5):
    model.step()

print(len(sim.logs))
```

Plain Mesa 3 is the stable publication and teaching layer for Python agent-based modeling. `mesa-llm` is intentionally not used here because the adapter boundary should stay deterministic and small: Luvoire owns the LLM gateway, memory, replay, and safety behavior; Mesa owns the ABM stepping surface and downstream analysis ecosystem.
