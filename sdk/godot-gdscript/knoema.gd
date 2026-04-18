extends RefCounted
class_name KnoemaGameSession

var game_id: String
var provider: String = "local"
var npcs: Dictionary = {}

func _init(new_game_id: String, new_provider: String = "local") -> void:
    game_id = new_game_id
    provider = new_provider

func create_npc(npc_id: String, name: String, persona: Dictionary, initial_relationships: Dictionary = {}) -> Dictionary:
    var npc := {
        "npc_id": npc_id,
        "name": name,
        "persona": persona,
        "initial_relationships": initial_relationships,
    }
    npcs[npc_id] = npc
    return npc

func interact(npc_id: String, player_action: String, context: Dictionary = {}) -> Dictionary:
    var npc: Dictionary = npcs[npc_id]
    var location := str(context.get("location", "unknown location"))
    var relationships: Dictionary = npc.get("initial_relationships", {})
    var relationship := str(relationships.get("player", "stranger"))
    return {
        "text": "%s responds to %s at %s as a %s." % [npc["name"], player_action, location, relationship],
        "emotion": "neutral",
        "branch_flags": ["location:%s" % location, "relationship:%s" % relationship],
        "raw": {"npc_id": npc_id, "player_action": player_action, "context": context},
    }
