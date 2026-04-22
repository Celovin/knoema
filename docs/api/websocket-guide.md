# WebSocket Guide

The WebSocket stream provides live JSON envelopes while a simulation is running.

## Endpoint

```text
/simulations/{simulation_id}/stream
```

If `LUVOIRE_API_KEY` is configured, send the same bearer token used by the REST routes.

## Event Shapes

Log envelope:

```json
{
  "type": "simulation.log",
  "simulation_id": "abcd1234",
  "payload": {
    "tick": 0,
    "timestamp": "2026-04-19T09:00:00",
    "agent_id": "agent-0",
    "action": {
      "agent_id": "agent-0",
      "timestamp": "2026-04-19T09:00:00",
      "action_type": "speak",
      "target": null,
      "content": "shares a short update.",
      "location": "Korea > Seoul > Campus > Commons"
    }
  }
}
```

Terminal envelope:

```json
{
  "type": "simulation.status",
  "simulation_id": "abcd1234",
  "status": "completed",
  "completed_ticks": 12,
  "total_ticks": 12,
  "error": null
}
```

## Example

1. Create a simulation with `POST /simulations`.
2. Connect the WebSocket to the returned `simulation_id`.
3. Consume `simulation.log` messages until the terminal `simulation.status` envelope arrives.

The stream can also replay already-produced log entries when a client connects after the run has started.
