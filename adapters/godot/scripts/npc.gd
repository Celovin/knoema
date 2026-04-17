extends Control

@export var npc_agent_id: String = "school_nurse"

@onready var npc_line: Label = %NpcLine
@onready var input: LineEdit = %Input
@onready var send_button: Button = %SendButton
@onready var history: RichTextLabel = %History


func _ready() -> void:
	send_button.pressed.connect(_on_send_pressed)
	input.text_submitted.connect(_on_text_submitted)


func _on_text_submitted(text: String) -> void:
	_send_message(text)


func _on_send_pressed() -> void:
	_send_message(input.text)


func _send_message(text: String) -> void:
	var clean_text := text.strip_edges()
	if clean_text.is_empty():
		return
	input.text = ""
	history.append_text("\n[b]Player:[/b] %s" % clean_text)
	var response: String = await KnoemaClient.ask(npc_agent_id, clean_text)
	npc_line.text = "School Nurse: %s" % response
	history.append_text("\n[b]School Nurse:[/b] %s" % response)
