extends Node2D

const INTERACT_DISTANCE := 64.0
const BJORN_AGENT_ID := "bjorn_tavern_keeper"

@onready var player: CharacterBody2D = %Player
@onready var bjorn: Node2D = %Bjorn
@onready var bjorn_sprite: Sprite2D = %BjornSprite
@onready var dialog_panel: PanelContainer = %DialogPanel
@onready var status_label: Label = %StatusLabel
@onready var input_line: LineEdit = %InputLine
@onready var send_button: Button = %SendButton
@onready var transcript: RichTextLabel = %Transcript

var client: LuvoireClient
var idle_phase: float = 0.0


func _ready() -> void:
	client = preload("res://scripts/luvoire_client.gd").new()
	client.endpoint_url = ""
	add_child(client)
	dialog_panel.visible = false
	status_label.text = "WASD로 64px 안으로 이동하면 Bjorn과 대화할 수 있습니다."
	send_button.pressed.connect(_on_send_pressed)
	input_line.text_submitted.connect(_on_text_submitted)
	_append("[b]Bjorn[/b]: Tavern is open. Come closer if you need a drink.")


func _process(delta: float) -> void:
	idle_phase += delta * 3.0
	bjorn_sprite.position.y = sin(idle_phase) * 2.0
	var in_range := player.global_position.distance_to(bjorn.global_position) <= INTERACT_DISTANCE
	dialog_panel.visible = in_range
	if in_range:
		status_label.text = "Bjorn is ready. Type a line and press Send."
	else:
		status_label.text = "Walk within 64px of Bjorn."


func _on_text_submitted(text: String) -> void:
	_send_message(text)


func _on_send_pressed() -> void:
	_send_message(input_line.text)


func _send_message(text: String) -> void:
	var clean_text := text.strip_edges()
	if clean_text.is_empty():
		return
	if not dialog_panel.visible:
		status_label.text = "Bjorn is too far away."
		return

	input_line.text = ""
	_append("[b]Player[/b]: %s" % clean_text)
	status_label.text = "Bjorn is thinking..."
	var context_json := JSON.stringify({
		"location": "Town > Tavern > Bar",
		"mode": "replay_only",
		"distance_px": snappedf(player.global_position.distance_to(bjorn.global_position), 0.1),
	})
	var response: String = await client.ask(BJORN_AGENT_ID, clean_text, context_json)
	status_label.text = "Bjorn replied from the replay-only fallback."
	_append("[b]Bjorn[/b]: %s" % response)


func _append(line: String) -> void:
	transcript.append_text("\n%s" % line)
