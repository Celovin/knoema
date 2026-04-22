extends RefCounted
class_name KnoemaGameSession

var game_id: String
var provider: String = "local"
var npcs: Dictionary = {}

func _init(new_game_id: String, new_provider: String = "local") -> void:
    game_id = _required_text(new_game_id, "game_id")
    provider = _required_text(new_provider, "provider")

func create_npc(npc_id: String, name: String, persona: Dictionary, initial_relationships: Dictionary = {}) -> Dictionary:
    var resolved_npc_id := _required_text(npc_id, "npc_id")
    var resolved_name := _required_text(name, "name")
    if resolved_npc_id.is_empty() or resolved_name.is_empty():
        return {}

    var npc := {
        "npc_id": resolved_npc_id,
        "name": resolved_name,
        "persona": persona.duplicate(true),
        "initial_relationships": initial_relationships.duplicate(true),
    }
    npcs[resolved_npc_id] = npc
    return npc

func interact(npc_id: String, player_action: String, context: Dictionary = {}) -> Dictionary:
    var resolved_npc_id := _required_text(npc_id, "npc_id")
    var resolved_action := _required_text(player_action, "player_action")
    var resolved_context := context.duplicate(true)
    if resolved_npc_id.is_empty() or resolved_action.is_empty():
        return _error_response(resolved_npc_id, resolved_action, resolved_context, "invalid_input")
    if not npcs.has(resolved_npc_id):
        return _error_response(resolved_npc_id, resolved_action, resolved_context, "npc_not_found")

    var npc: Dictionary = npcs[resolved_npc_id]
    var location := _text_or_default(resolved_context.get("location", "unknown location"), "unknown location")
    var relationships: Dictionary = npc.get("initial_relationships", {})
    var relationship := _text_or_default(relationships.get("player", "stranger"), "stranger")
    return {
        "text": "%s responds to %s at %s as a %s." % [npc["name"], resolved_action, location, relationship],
        "emotion": "neutral",
        "branch_flags": ["location:%s" % location, "relationship:%s" % relationship],
        "raw": {"npc_id": resolved_npc_id, "player_action": resolved_action, "context": resolved_context},
    }

func _required_text(value: Variant, field_name: String) -> String:
    var text := str(value).strip_edges()
    if text.is_empty():
        push_error("%s must not be empty" % field_name)
    return text

func _text_or_default(value: Variant, default_value: String) -> String:
    if value == null:
        return default_value
    var text := str(value).strip_edges()
    return default_value if text.is_empty() else text

func _error_response(npc_id: String, player_action: String, context: Dictionary, error_code: String) -> Dictionary:
    return {
        "text": "",
        "emotion": "error",
        "branch_flags": ["error:%s" % error_code],
        "raw": {"npc_id": npc_id, "player_action": player_action, "context": context},
    }
