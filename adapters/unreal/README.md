# Luvoire Unreal Engine 5 Adapter

This plugin scaffold targets Unreal Engine 5.3 and newer. It is designed for projects that want to keep NPC or crowd logic inside Unreal while delegating simulation lifecycle management to the Luvoire REST API introduced in Phase 44. The plugin does not ship a compiled binary in this repository. Instead, it provides the Runtime module layout, API client, tick-based actor component, and a placeholder Blueprint asset so a UE5 project can pull the source into its own build.

## Install

For a project-local install, copy `adapters/unreal` into:

```text
<YourProject>\Plugins\LuvoireUnreal
```

For an engine-wide install on an Epic Games Launcher build, copy it into:

```text
C:\Program Files\Epic Games\UE_5.3\Engine\Plugins\Marketplace\LuvoireUnreal
```

Then open the project, enable **Luvoire Unreal** in the Plugins window, and restart the editor so the Runtime module is compiled.

## Runtime Layout

- `Source/LuvoireUnreal/Public/LuvoireClient.h`: thin HTTP client for `POST /simulations`, `GET /simulations/{id}`, and `POST /simulations/{id}/events`
- `Source/LuvoireUnreal/Public/NPCAgentComponent.h`: actor component that polls a simulation on tick and exposes simple Blueprint-callable entry points
- `Content/Blueprints/BP_BasicNPC.uasset`: placeholder asset note for the sample actor blueprint you should recreate and save inside the editor

## Blueprint Flow

1. Add `NPCAgentComponent` to an `Actor` or `Character`.
2. Set `BaseUrl` to your Luvoire API server, usually `http://127.0.0.1:8000`.
3. Paste a full `POST /simulations` JSON payload into `BootstrapSimulationJson`.
4. Call `StartScenario` from `BeginPlay`.
5. Use `InjectWorldEvent` when gameplay needs to push a structured event back into the running simulation.

The checked-in `BP_BasicNPC.uasset` file is a text placeholder, not a binary asset exported from Unreal Editor. Open the plugin content folder, create a Blueprint actor, attach `NPCAgentComponent`, save the asset with the same name, and commit the real binary only when your delivery process allows binary review.
