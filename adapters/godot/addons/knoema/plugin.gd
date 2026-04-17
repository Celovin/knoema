@tool
extends EditorPlugin


func _enter_tree() -> void:
	print("Knoema Adapter plugin loaded.")


func _exit_tree() -> void:
	print("Knoema Adapter plugin unloaded.")
