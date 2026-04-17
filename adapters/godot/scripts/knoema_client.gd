extends Node

class_name KnoemaClient

@export var endpoint_url: String = ""
@export var session_id: String = "demo-session"

var history: Array[Dictionary] = []


func ask(agent_id: String, message: String) -> String:
	history.append({
		"role": "player",
		"agent_id": agent_id,
		"content": message,
	})

	if endpoint_url.strip_edges().is_empty():
		return _fallback_response(agent_id, message)

	var request := HTTPRequest.new()
	add_child(request)
	var payload := JSON.stringify({
		"session_id": session_id,
		"agent_id": agent_id,
		"message": message,
	})
	var error := request.request(
		endpoint_url,
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		payload
	)
	if error != OK:
		request.queue_free()
		return _fallback_response(agent_id, message)

	var response = await request.request_completed
	request.queue_free()
	var status_code: int = response[1]
	var body: PackedByteArray = response[3]
	if status_code < 200 or status_code >= 300:
		return _fallback_response(agent_id, message)

	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY or not parsed.has("content"):
		return _fallback_response(agent_id, message)

	var content := str(parsed["content"])
	history.append({
		"role": "npc",
		"agent_id": agent_id,
		"content": content,
	})
	return content


func _fallback_response(agent_id: String, message: String) -> String:
	var content := "I will remember that you said: %s" % message
	history.append({
		"role": "npc",
		"agent_id": agent_id,
		"content": content,
	})
	return content
