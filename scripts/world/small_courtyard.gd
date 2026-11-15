class_name SmallCourtyard
extends Node2D

## 大明宫最小模块化院落组件：「一进值房小院」（一厅 + 两庑 + 南院门 + 天井）。
## 使用 Base 层 + 15 条按脚线 Y-sort 分片的 Front 遮挡层，支持角色穿行南门、走进天井并产生真实前后遮挡。

const InteractableSpot = preload("res://scripts/world/interactable_spot.gd")

const TEX_BASE: Texture2D = preload("res://assets/palace/small_courtyard_base.png")
const TEX_FRONT: Texture2D = preload("res://assets/palace/small_courtyard_front.png")

const CANVAS_SIZE: Vector2 = Vector2(1452.0, 1008.0)

static func _get_wall_polygons() -> Array[PackedVector2Array]:
	return [
		# 南西院墙（门洞左侧）
		PackedVector2Array([Vector2(15.0, 600.8), Vector2(441.0, 759.0), Vector2(429.0, 788.2), Vector2(15.0, 633.0)]),
		# 南东院墙（门洞右侧至南角）
		PackedVector2Array([Vector2(501.0, 780.0), Vector2(985.5, 963.0), Vector2(985.5, 996.0), Vector2(490.5, 807.0)]),
		# 东南外墙（南角向东北延伸）
		PackedVector2Array([Vector2(985.5, 963.0), Vector2(1432.5, 559.5), Vector2(1445.2, 582.0), Vector2(985.5, 996.0)]),
		# 西廊庑内侧台基与墙体
		PackedVector2Array([Vector2(15.0, 600.8), Vector2(552.8, 113.2), Vector2(594.0, 135.8), Vector2(222.8, 544.5), Vector2(54.0, 608.2)]),
		# 东廊庑内侧台基与墙体
		PackedVector2Array([Vector2(1005.0, 413.2), Vector2(1092.8, 338.2), Vector2(1430.2, 465.8), Vector2(1430.2, 559.5), Vector2(982.5, 818.2), Vector2(972.8, 709.5), Vector2(850.5, 660.8)]),
		# 正厅左侧台基
		PackedVector2Array([Vector2(552.8, 113.2), Vector2(755.2, 188.2), Vector2(723.0, 370.5), Vector2(552.8, 308.2)]),
		# 正厅右侧台基
		PackedVector2Array([Vector2(755.2, 188.2), Vector2(1092.8, 338.2), Vector2(1005.0, 413.2), Vector2(822.8, 406.5)]),
		# 正厅台阶后方墙体
		PackedVector2Array([Vector2(710.2, 289.5), Vector2(852.8, 342.0), Vector2(822.8, 383.2), Vector2(723.0, 348.0)]),
	]

const FRONT_STRIPS: Array[Dictionary] = [
	{"x": 0.0, "w": 100.0, "foot_y": 642.9},
	{"x": 100.0, "w": 100.0, "foot_y": 680.9},
	{"x": 200.0, "w": 100.0, "foot_y": 718.9},
	{"x": 300.0, "w": 96.0, "foot_y": 756.1},
	{"x": 396.0, "w": 49.0, "foot_y": 795.8},
	{"x": 445.0, "w": 58.0, "foot_y": 795.8},
	{"x": 503.0, "w": 65.0, "foot_y": 795.8},
	{"x": 568.0, "w": 102.0, "foot_y": 852.8},
	{"x": 670.0, "w": 105.0, "foot_y": 892.4},
	{"x": 775.0, "w": 105.0, "foot_y": 932.6},
	{"x": 880.0, "w": 106.0, "foot_y": 972.9},
	{"x": 986.0, "w": 109.0, "foot_y": 942.4},
	{"x": 1095.0, "w": 110.0, "foot_y": 841.6},
	{"x": 1205.0, "w": 115.0, "foot_y": 738.0},
	{"x": 1320.0, "w": 132.0, "foot_y": 624.3},
]

const LOCAL_WAYPOINTS: Dictionary = {
	"gate_outside": Vector2(440.2, 844.5),
	"gate_threshold": Vector2(472.5, 768.0),
	"courtyard_center": Vector2(627.8, 544.5),
	"hall_stairs": Vector2(770.2, 394.5),
	"west_corridor_steps": Vector2(399.0, 454.5),
}

@export var courtyard_name: String = "内阁值房小院"
@export var hall_title: String = "值房正厅"
@export var hall_description: PackedStringArray = PackedStringArray([
	"【最小宫廷建筑单元 · 一进值房小院】",
	"参照唐大明宫门下省 / 东西朝堂侧院制式：北三间单檐正厅、东西廊庑、南向小门与石板天井。",
	"可作为独立官署模块在宫城中拼接复用。",
])

var _built: bool = false


func _ready() -> void:
	y_sort_enabled = true
	if not _built:
		_build_component()


func _build_component() -> void:
	_built = true

	var base_sprite := Sprite2D.new()
	base_sprite.name = "BaseLayer"
	base_sprite.texture = TEX_BASE
	base_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	base_sprite.centered = false
	base_sprite.z_index = -1
	add_child(base_sprite)

	for i in range(FRONT_STRIPS.size()):
		var spec: Dictionary = FRONT_STRIPS[i]
		var x0: float = spec["x"]
		var w: float = spec["w"]
		var foot_y: float = spec["foot_y"]

		var strip := Sprite2D.new()
		strip.name = "FrontWallStrip_%02d" % i
		strip.texture = TEX_FRONT
		strip.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		strip.centered = false
		strip.region_enabled = true
		strip.region_rect = Rect2(x0, 0.0, w, CANVAS_SIZE.y)
		strip.position = Vector2(x0, foot_y)
		strip.offset = Vector2(0.0, -foot_y)
		add_child(strip)

	var walls_body := StaticBody2D.new()
	walls_body.name = "CourtyardColliders"
	walls_body.collision_layer = 1
	walls_body.collision_mask = 0
	var wall_polygons: Array[PackedVector2Array] = _get_wall_polygons()
	for i in range(wall_polygons.size()):
		var col := CollisionPolygon2D.new()
		col.name = "WallPoly_%02d" % i
		col.polygon = wall_polygons[i]
		walls_body.add_child(col)
	add_child(walls_body)

	var hall_spot := InteractableSpot.new()
	hall_spot.name = "HallEntranceSpot"
	hall_spot.spot_id = "small_courtyard_hall"
	hall_spot.display_title = "%s · %s" % [courtyard_name, hall_title]
	hall_spot.prompt_hint = "按 [E] 检视 %s" % hall_title
	hall_spot.accent_color = Color(0.90, 0.72, 0.36)
	hall_spot.info_lines = hall_description
	hall_spot.position = LOCAL_WAYPOINTS["hall_stairs"]
	add_child(hall_spot)


func get_waypoint_global(waypoint_name: String) -> Vector2:
	if LOCAL_WAYPOINTS.has(waypoint_name):
		return to_global(LOCAL_WAYPOINTS[waypoint_name] as Vector2)
	return to_global(LOCAL_WAYPOINTS["courtyard_center"] as Vector2)
