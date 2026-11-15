extends Area2D

## 宫城内的可交互点（如正殿舆图沙盘、西偏院预留地块）。

@export var spot_id: String = ""
@export var display_title: String = ""
@export var prompt_hint: String = "按 [E] 查看"
@export var accent_color: Color = Color(0.88, 0.72, 0.34)
@export var is_council_sandbox: bool = false
@export var info_lines: PackedStringArray = PackedStringArray()

var _is_highlighted: bool = false
var _hint_label: Label


func _ready() -> void:
	collision_layer = 4
	collision_mask = 0
	monitoring = false
	monitorable = true

	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(96.0, 72.0)
	shape.shape = rect
	add_child(shape)

	_hint_label = Label.new()
	_hint_label.text = prompt_hint
	_hint_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hint_label.position = Vector2(-90.0, -56.0)
	_hint_label.size = Vector2(180.0, 24.0)
	_hint_label.add_theme_font_size_override("font_size", 13)
	_hint_label.add_theme_color_override("font_color", Color(1.0, 0.96, 0.80))
	_hint_label.add_theme_color_override("font_outline_color", Color(0.08, 0.08, 0.12))
	_hint_label.add_theme_constant_override("outline_size", 4)
	_hint_label.visible = false
	add_child(_hint_label)


func set_highlighted(enabled: bool) -> void:
	_is_highlighted = enabled
	if _hint_label != null:
		_hint_label.visible = enabled
	queue_redraw()


func interact() -> void:
	if is_council_sandbox:
		var entries: Array = CabinetDatabase.get_council_meeting_entries(GameClock.current_slot)
		DialogueBus.council_meeting_requested.emit("正殿舆图沙盘 · 内阁短议", entries)
		return
	DialogueBus.info_dialogue_requested.emit(display_title, "宫城设施", accent_color, info_lines)


func _draw() -> void:
	if _is_highlighted:
		draw_rect(Rect2(-46.0, -34.0, 92.0, 68.0), Color(accent_color, 0.18), true)
		draw_rect(Rect2(-46.0, -34.0, 92.0, 68.0), accent_color, false, 2.0)
