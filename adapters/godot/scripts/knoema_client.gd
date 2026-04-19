extends Node

@export var endpoint_url: String = ""
@export var session_id: String = "demo-session"

var history: Array[Dictionary] = []


func ask(agent_id: String, message: String, context_json: String = "{}") -> String:
	history.append({
		"role": "player",
		"agent_id": agent_id,
		"content": message,
	})

	if endpoint_url.strip_edges().is_empty():
		return _fallback_response(agent_id, message, context_json)

	var request := HTTPRequest.new()
	add_child(request)
	var payload := JSON.stringify({
		"session_id": session_id,
		"agent_id": agent_id,
		"message": message,
		"player_action": message,
		"context_json": context_json,
	})
	var error := request.request(
		endpoint_url,
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		payload
	)
	if error != OK:
		request.queue_free()
		return _fallback_response(agent_id, message, context_json)

	var response = await request.request_completed
	request.queue_free()
	var status_code: int = response[1]
	var body: PackedByteArray = response[3]
	if status_code < 200 or status_code >= 300:
		return _fallback_response(agent_id, message, context_json)

	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY or not parsed.has("content"):
		return _fallback_response(agent_id, message, context_json)

	var content := str(parsed["content"])
	history.append({
		"role": "npc",
		"agent_id": agent_id,
		"content": content,
	})
	return content


func _fallback_response(agent_id: String, message: String, context_json: String = "{}") -> String:
	var safe_name := "Bjorn" if agent_id == "bjorn_tavern_keeper" else agent_id.capitalize()
	var content := "%s remembers '%s' and folds it into the next tavern beat." % [safe_name, message]
	if context_json.find("Tavern") != -1:
		content = "%s wipes down the bar and says: I noted '%s' for the tavern log." % [safe_name, message]
	history.append({
		"role": "npc",
		"agent_id": agent_id,
		"content": content,
	})
	return content
