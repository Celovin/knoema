# Godot GDScript Game SDK

Use `sdk/godot-gdscript/luvoire.gd` as a lightweight Godot facade when the full adapter package is unnecessary.

```gdscript
var session := LuvoireGameSession.new("demo-village")
session.create_npc(
    "shopkeeper",
    "Mina",
    {"background": "Synthetic shopkeeper."},
    {"player": "neighbor"}
)
var response := session.interact(
    "shopkeeper",
    "asks about the lantern market",
    {"location": "Harbor Village"}
)
print(response["text"])
```

The facade returns a dictionary with `text`, `emotion`, `branch_flags`, and `raw` fields.
