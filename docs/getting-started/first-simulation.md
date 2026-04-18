# First Simulation

This example creates two fictional agents, runs one deterministic simulated day, and exports JSONL logs.

```python
from datetime import datetime

from knoema import Environment, LocalClient, Persona, Personality, Simulator

alice = Persona(
    agent_id='alice',
    name='Alice',
    age=17,
    background='Introverted literature student in a dormitory.',
    personality=Personality(
        openness=0.8,
        conscientiousness=0.6,
        extraversion=0.2,
        agreeableness=0.7,
        neuroticism=0.4,
    ),
    values=['privacy', 'honesty'],
    goals=['finish a short story'],
)

bob = Persona(
    agent_id='bob',
    name='Bob',
    age=17,
    background='Extroverted science student in the same dormitory.',
    personality=Personality(
        openness=0.6,
        conscientiousness=0.8,
        extraversion=0.9,
        agreeableness=0.7,
        neuroticism=0.3,
    ),
    values=['curiosity', 'teamwork'],
    goals=['prepare for a physics contest'],
)

environment = Environment(
    start_time=datetime(2026, 3, 2, 9, 0),
    location_path=('Korea', 'Seoul', 'High School Dormitory', 'Room 201'),
)

simulator = Simulator(
    agents=[alice, bob],
    environment=environment,
    llm=LocalClient(
        lambda messages: '{"action_type": "speak", "target": null, "content": "observes the room."}'
    ),
)

logs = simulator.run(duration_days=1)
simulator.export_logs('runs/dorm_001.jsonl')
print(len(logs))
```

## Inspect Logs

Open the dashboard:

```bash
streamlit run dashboard/app.py
```

Then load `runs/dorm_001.jsonl` or the bundled dashboard sample log.
