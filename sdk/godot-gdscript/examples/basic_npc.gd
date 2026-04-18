extends Node

func _ready() -> void:
    var session := KnoemaGameSession.new("demo-village")
    session.create_npc(
        "shopkeeper",
        "Mina",
        {"background": "Synthetic shopkeeper coordinating a lantern market stall."},
        {"player": "neighbor"}
    )
    var response := session.interact(
        "shopkeeper",
        "asks whether the lantern market is ready",
        {"location": "Harbor Village", "time": "2026-06-01T18:00:00"}
    )
    print(response["text"])
