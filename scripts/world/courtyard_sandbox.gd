extends Node2D

## 最小唐风院落组件独立验证场景：
## 玩家出生在南院门外，可穿门走进天井、沿石阶走至正厅前，体验等距 Y-sort 遮挡与 [E] 互动。

const SmallCourtyardScene = preload("res://scenes/world/small_courtyard.tscn")
const InteractableSpot = preload("res://scripts/world/interactable_spot.gd")
const PlayerRoyal = preload("res://scripts/actors/player.gd")
const GameHUD = preload("res://scripts/ui/hud.gd")

const WORLD_ORIGIN: Vector2 = Vector2(74.0, 56.0)

var _courtyard: SmallCourtyard
var _player: PlayerRoyal


func _ready() -> void:
	var actors_root := Node2D.new()
	actors_root.name = "IsometricWorld"
	actors_root.y_sort_enabled = true
	add_child(actors_root)

	_courtyard = SmallCourtyardScene.instantiate() as SmallCourtyard
	_courtyard.position = WORLD_ORIGIN
	actors_root.add_child(_courtyard)

	_player = PlayerRoyal.new()
	_player.name = "PlayerRoyal"
	_player.position = _courtyard.get_waypoint_global("gate_outside")
	actors_root.add_child(_player)

	var corridor_spot := InteractableSpot.new()
	corridor_spot.name = "WestCorridorSpot"
	corridor_spot.spot_id = "small_courtyard_west_corridor"
	corridor_spot.display_title = "西厢廊庑"
	corridor_spot.prompt_hint = "按 [E] 检视 西厢廊庑"
	corridor_spot.accent_color = Color(0.54, 0.82, 0.78)
	corridor_spot.info_lines = PackedStringArray([
		"【西厢廊庑 · 考成与卷宗抄录处】",
		"单檐灰瓦连廊连接南院门与北正厅，供值房书吏暂存文书与避雨通廊。",
	])
	corridor_spot.position = _courtyard.get_waypoint_global("west_corridor_steps")
	actors_root.add_child(corridor_spot)

	var hud := GameHUD.new()
	hud.name = "GameHUD"
	add_child(hud)

	queue_redraw()


func _draw() -> void:
	draw_rect(Rect2(0.0, 0.0, 1600.0, 1120.0), Color(0.18, 0.21, 0.19), true)
	# 门外石板引导通道（对齐南院门外台阶）
	var gate_out: Vector2 = WORLD_ORIGIN + Vector2(440.0, 844.0)
	var road := PackedVector2Array([
		gate_out + Vector2(-42.0, -35.0),
		gate_out + Vector2(58.0, 4.0),
		gate_out + Vector2(-120.0, 190.0),
		gate_out + Vector2(-220.0, 150.0),
	])
	draw_colored_polygon(road, Color(0.38, 0.37, 0.34))
