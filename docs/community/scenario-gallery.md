# Community Scenario Gallery

The community gallery is designed for a separate GitHub repository, `Celovin/knoema-scenarios`, while Knoema keeps the loader, validation rules, and Playground browsing surface in this repository.

## Manifest

The external repository should publish `manifest.json` at its root.

The expected manifest shape is:

```json
{
  "scenarios": [
    {
      "id": "classroom_peer_review",
      "title": "Classroom Peer Review",
      "summary": "Students negotiate feedback norms after a draft exchange.",
      "author": "Contributor name",
      "tags": ["education", "feedback"],
      "source_url": "https://github.com/Celovin/knoema-scenarios/blob/main/scenarios/classroom_peer_review.yaml",
      "yaml": "schema_version: \"1.0\"\\nscenario_id: classroom_peer_review\\n..."
    }
  ]
}
```

The loader validates every YAML payload with the Scenario DSL before exposing it.

## Playground Flow

1. Open Community scenario gallery.
2. Choose a seed or fetched community scenario.
3. Load it into the agent editors, event injection box, and preview panel.
4. Run the scenario or adapt the generated YAML into a local config.

## Contribution Flow

- Open an issue with the new scenario template.
- Submit a PR with one YAML scenario and a manifest entry.
- CI should run Scenario DSL validation and a replay dry run.
- Reviewers check safety boundaries, no real-person modeling, and clear artifact naming.

Starter templates are included under `docs/community/gallery_templates/`.
