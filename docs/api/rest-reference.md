# REST API Reference

The Phase 44 API server exposes a small REST surface for simulation lifecycle management and inspection.

## Start the Server

```bash
pip install -e ".[api]"
uvicorn luvoire.api.server:app --host 127.0.0.1 --port 8000
```

Optional bearer authentication is enabled when `LUVOIRE_API_KEY` is present in the environment.

## Endpoints

### `GET /healthz`

Returns API liveness plus current simulation counts.

### `POST /simulations`

Creates a simulation and starts it immediately in the in-memory simulator pool.

Request body:

```json
{
  "runtime": {
    "duration_days": 1,
    "tick_duration_minutes": 120,
    "prompt_language": "en",
    "stream_delay_seconds": 0.01
  },
  "environment": {
    "start_time": "2026-04-19T09:00:00",
    "location_path": ["Korea", "Seoul", "Campus", "Commons"],
    "conditions": {"weather": "clear"}
  },
  "agents": [
    {
      "agent_id": "agent-0",
      "name": "Agent 0",
      "age": 20,
      "background": "Synthetic participant.",
      "personality": {
        "openness": 0.5,
        "conscientiousness": 0.6,
        "extraversion": 0.4,
        "agreeableness": 0.7,
        "neuroticism": 0.3
      },
      "values": ["clarity"],
      "goals": ["cooperate"],
      "theory_of_mind": {"enabled": true}
    }
  ],
  "local_response": "{\"action_type\": \"speak\", \"target\": null, \"content\": \"shares a short update.\"}"
}
```

### `GET /simulations/{simulation_id}`

Returns status, tick progress, scheduled-event count, and any terminal error.

### `DELETE /simulations/{simulation_id}`

Cancels a running simulation and removes it from the in-memory pool.

### `GET /simulations/{simulation_id}/agents`

Returns the current agent list with location, short-term memory count, and theory-of-mind opt-in status.

### `GET /simulations/{simulation_id}/agents/{agent_id}/memory`

Returns recent short-term memories for one agent.

### `POST /simulations/{simulation_id}/events`

Schedules a world event for delivery on the next due tick.

## OpenAPI

FastAPI publishes the generated OpenAPI 3.1 schema at:

- `/openapi.json`
- `/docs`
- `/redoc`
