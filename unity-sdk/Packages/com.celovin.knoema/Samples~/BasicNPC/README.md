# Basic NPC Sample

This sample is intentionally text-first so the repository can validate it without a Unity editor.
Create an empty Unity scene, add one GameObject named `Guide`, attach `KnoemaNPC`, and use
`BasicNPC.scene.yaml` as the scene contract.

Run the Python API server first:

```bash
uvicorn knoema.api.server:app --host 127.0.0.1 --port 8000
```
