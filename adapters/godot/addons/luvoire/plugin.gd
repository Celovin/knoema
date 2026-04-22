@tool
extends EditorPlugin


func _enter_tree() -> void:
	print("Luvoire Adapter plugin loaded.")


func _exit_tree() -> void:
	print("Luvoire Adapter plugin unloaded.")
