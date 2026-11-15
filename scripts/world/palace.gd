extends Node2D

## 「一轴四区」皇城宫城白模场景：
## 中轴议事正殿、东偏殿内阁值房、中心御苑广场、西偏院匠造与画坊、南宫门。

const InteractableSpot = preload("res://scripts/world/interactable_spot.gd")

const WORLD_SIZE: Vector2 = Vector2(1600.0, 1120.0)

var waypoints: Dictionary = {}
var actors_container: Node2D
var _nav_region: NavigationRegion2D
var _obstacles_root: Node2D
var _ambient_modulate: CanvasModulate
var _night_lamps_layer: Node2D
var _zone_labels: Array[Dictionary] = []
var _furniture_rects: Array[Dictionary] = []
var _wall_rects: Array[Rect2] = []


func _ready() -> void:
	_build_structure()
	_build_waypoints()
	_build_interactables()
	_bake_navigation()
	GameClock.time_slot_changed.connect(_on_time_slot_changed)
	_apply_slot_lighting(GameClock.current_slot)
	queue_redraw()


func get_waypoint_position(waypoint_name: String) -> Vector2:
	if waypoints.has(waypoint_name):
		return waypoints[waypoint_name]
	return Vector2(800.0, 620.0)


func get_zone_name_for_position(pos: Vector2) -> String:
	if pos.y < 410.0 and pos.x >= 520.0 and pos.x <= 1080.0:
		return "议事正殿"
	if pos.x > 1080.0 and pos.y < 520.0:
		return "东偏殿值房"
	if pos.x < 520.0 and pos.y < 520.0:
		return "西偏院工坊"
	if pos.y > 920.0:
		return "南宫门"
	return "中心御苑"


func _build_structure() -> void:
	_nav_region = NavigationRegion2D.new()
	_nav_region.name = "NavigationRegion2D"
	add_child(_nav_region)

	_obstacles_root = Node2D.new()
	_obstacles_root.name = "Obstacles"
	_nav_region.add_child(_obstacles_root)

	actors_container = Node2D.new()
	actors_container.name = "Actors"
	actors_container.y_sort_enabled = true
	add_child(actors_container)

	_night_lamps_layer = Node2D.new()
	_night_lamps_layer.name = "NightLamps"
	_night_lamps_layer.z_index = 5
	add_child(_night_lamps_layer)

	_ambient_modulate = CanvasModulate.new()
	_ambient_modulate.name = "AmbientModulate"
	add_child(_ambient_modulate)

	# 外围宫墙（南宫门留出 200px 宽入口）
	_add_wall(Rect2(40.0, 40.0, 1520.0, 28.0))
	_add_wall(Rect2(40.0, 68.0, 28.0, 984.0))
	_add_wall(Rect2(1532.0, 68.0, 28.0, 984.0))
	_add_wall(Rect2(68.0, 1024.0, 632.0, 28.0))
	_add_wall(Rect2(900.0, 1024.0, 632.0, 28.0))

	# 议事正殿南侧宫墙（中间留 160px 大门）
	_add_wall(Rect2(520.0, 390.0, 200.0, 22.0))
	_add_wall(Rect2(880.0, 390.0, 200.0, 22.0))
	# 正殿左右隔墙（留出穿堂侧门）
	_add_wall(Rect2(520.0, 68.0, 22.0, 140.0))
	_add_wall(Rect2(520.0, 300.0, 22.0, 90.0))
	_add_wall(Rect2(1058.0, 68.0, 22.0, 140.0))
	_add_wall(Rect2(1058.0, 300.0, 22.0, 90.0))

	# 东偏殿 · 内阁值房隔墙（南面留门）
	_add_wall(Rect2(1080.0, 440.0, 150.0, 20.0))
	_add_wall(Rect2(1340.0, 440.0, 192.0, 20.0))

	# 西偏院 · 匠造与画坊隔墙（南面留门）
	_add_wall(Rect2(68.0, 480.0, 170.0, 20.0))
	_add_wall(Rect2(350.0, 480.0, 170.0, 20.0))

	# 家具与地形障碍物
	# 1. 龙椅高台
	_add_furniture(Rect2(745.0, 110.0, 110.0, 48.0), Color(0.72, 0.56, 0.24), "御坐")
	# 2. 正殿舆图沙盘桌
	_add_furniture(Rect2(730.0, 232.0, 140.0, 76.0), Color(0.32, 0.44, 0.38), "舆图沙盘")
	# 3. 东偏殿办公书桌 & 卷宗架
	_add_furniture(Rect2(1150.0, 160.0, 120.0, 50.0), Color(0.45, 0.30, 0.20), "考成案牍")
	_add_furniture(Rect2(1350.0, 160.0, 120.0, 50.0), Color(0.45, 0.30, 0.20), "秘文案桌")
	_add_furniture(Rect2(1240.0, 100.0, 150.0, 28.0), Color(0.38, 0.26, 0.18), "卷宗架")
	_add_furniture(Rect2(1105.0, 318.0, 104.0, 44.0), Color(0.42, 0.30, 0.24), "书记案")
	_add_furniture(Rect2(1386.0, 318.0, 110.0, 44.0), Color(0.34, 0.44, 0.46), "兰台书架")
	# 4. 西偏院工坊台、画架与太医药架
	_add_furniture(Rect2(130.0, 165.0, 125.0, 54.0), Color(0.34, 0.40, 0.48), "工学锻台")
	_add_furniture(Rect2(345.0, 170.0, 95.0, 48.0), Color(0.56, 0.46, 0.34), "画坊长案")
	_add_furniture(Rect2(476.0, 330.0, 36.0, 84.0), Color(0.36, 0.50, 0.38), "太医药架")
	# 5. 御苑莲池、石桌与东西外廊案台
	_add_furniture(Rect2(920.0, 620.0, 200.0, 130.0), Color(0.24, 0.52, 0.64), "御苑莲池")
	_add_furniture(Rect2(675.0, 690.0, 96.0, 64.0), Color(0.62, 0.60, 0.56), "石桌")
	_add_furniture(Rect2(1245.0, 555.0, 115.0, 48.0), Color(0.38, 0.46, 0.44), "军机沙案")
	_add_furniture(Rect2(1245.0, 745.0, 115.0, 48.0), Color(0.42, 0.34, 0.44), "政宣刊案")
	_add_furniture(Rect2(135.0, 575.0, 115.0, 48.0), Color(0.34, 0.38, 0.48), "格物算席")
	_add_furniture(Rect2(140.0, 755.0, 110.0, 54.0), Color(0.50, 0.36, 0.26), "御苑茶亭")

	# 区域标签
	_zone_labels = [
		{"pos": Vector2(800.0, 96.0), "text": "【中轴 · 议事正殿】"},
		{"pos": Vector2(1300.0, 96.0), "text": "【东偏殿 · 内阁值房】"},
		{"pos": Vector2(290.0, 96.0), "text": "【西偏院 · 匠造与画坊】"},
		{"pos": Vector2(800.0, 510.0), "text": "【中心 · 御苑广场】"},
		{"pos": Vector2(800.0, 985.0), "text": "【南宫门】"},
	]

	_build_night_lamps()


func _add_wall(rect: Rect2) -> void:
	_wall_rects.append(rect)
	var body := StaticBody2D.new()
	body.position = rect.get_center()
	body.collision_layer = 1
	var shape := CollisionShape2D.new()
	var box := RectangleShape2D.new()
	box.size = rect.size
	shape.shape = box
	body.add_child(shape)
	_obstacles_root.add_child(body)


func _add_furniture(rect: Rect2, color: Color, label_text: String) -> void:
	_furniture_rects.append({"rect": rect, "color": color, "label": label_text})
	var body := StaticBody2D.new()
	body.position = rect.get_center()
	body.collision_layer = 1
	var shape := CollisionShape2D.new()
	var box := RectangleShape2D.new()
	box.size = rect.size
	shape.shape = box
	body.add_child(shape)
	_obstacles_root.add_child(body)

	var lbl := Label.new()
	lbl.text = label_text
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl.position = rect.position + Vector2(0.0, rect.size.y * 0.5 - 10.0)
	lbl.size = Vector2(rect.size.x, 20.0)
	lbl.add_theme_font_size_override("font_size", 12)
	lbl.add_theme_color_override("font_color", Color(0.98, 0.96, 0.90))
	lbl.add_theme_color_override("font_outline_color", Color(0.10, 0.10, 0.14))
	lbl.add_theme_constant_override("outline_size", 3)
	add_child(lbl)


func _build_waypoints() -> void:
	waypoints = {
		"player_spawn": Vector2(800.0, 860.0),
		"throne_sandbox": Vector2(695.0, 270.0),
		"throne_hall_side": Vector2(895.0, 270.0),
		"throne_guard_post": Vector2(635.0, 340.0),
		"cabinet_office_chizheng": Vector2(1210.0, 250.0),
		"cabinet_office_bina": Vector2(1410.0, 250.0),
		"cabinet_office_taki": Vector2(1157.0, 394.0),
		"cabinet_library_jean": Vector2(1440.0, 394.0),
		"cabinet_strategy_boming": Vector2(1302.0, 636.0),
		"cabinet_politics_jiafa": Vector2(1302.0, 826.0),
		"west_workshop": Vector2(195.0, 255.0),
		"west_atelier": Vector2(390.0, 255.0),
		"west_plot_a": Vector2(210.0, 380.0),
		"west_math_hall": Vector2(192.0, 656.0),
		"west_infirmary": Vector2(444.0, 385.0),
		"courtyard_stage": Vector2(540.0, 620.0),
		"courtyard_table": Vector2(650.0, 775.0),
		"courtyard_pond": Vector2(860.0, 690.0),
		"courtyard_pavilion": Vector2(195.0, 842.0),
		"palace_corridor": Vector2(800.0, 455.0),
		"south_gate_patrol": Vector2(800.0, 945.0),
	}


func _build_interactables() -> void:
	var sandbox := InteractableSpot.new()
	sandbox.spot_id = "sandbox_table"
	sandbox.display_title = "正殿舆图沙盘"
	sandbox.prompt_hint = "按 [E] 召集内阁短议"
	sandbox.accent_color = Color(0.92, 0.76, 0.36)
	sandbox.is_council_sandbox = true
	sandbox.position = Vector2(800.0, 270.0)
	add_child(sandbox)

	var plot_a := InteractableSpot.new()
	plot_a.spot_id = "west_plot_a"
	plot_a.display_title = "西偏院 · 预留地块 A"
	plot_a.prompt_hint = "按 [E] 勘察扩建地块"
	plot_a.accent_color = Color(0.38, 0.80, 0.90)
	plot_a.info_lines = PackedStringArray([
		"【预留地块 A · 拟建：墨家工坊 / 司天监】",
		"Bit 已经量好尺寸，达文西坚持屋檐必须用青瓦飞檐。",
		"后续进入「皇城细尺度建设」阶段后，可直接在此落成新宫署。",
	])
	plot_a.position = Vector2(175.0, 385.0)
	add_child(plot_a)

	var plot_b := InteractableSpot.new()
	plot_b.spot_id = "west_plot_b"
	plot_b.display_title = "西偏院 · 预留地块 B"
	plot_b.prompt_hint = "按 [E] 勘察扩建地块"
	plot_b.accent_color = Color(0.66, 0.84, 0.56)
	plot_b.info_lines = PackedStringArray([
		"【预留地块 B · 拟建：太医院 / 御苑药圃】",
		"等第二批内阁成员「千金 (Qianjin)」入驻后，这里会种满草药并负责调理陛下体力。",
	])
	plot_b.position = Vector2(365.0, 385.0)
	add_child(plot_b)


func _bake_navigation() -> void:
	var nav_poly := NavigationPolygon.new()
	nav_poly.agent_radius = 16.0
	nav_poly.parsed_geometry_type = NavigationPolygon.PARSED_GEOMETRY_STATIC_COLLIDERS
	nav_poly.source_geometry_mode = NavigationPolygon.SOURCE_GEOMETRY_ROOT_NODE_CHILDREN
	var outline := PackedVector2Array([
		Vector2(68.0, 68.0),
		Vector2(1532.0, 68.0),
		Vector2(1532.0, 1024.0),
		Vector2(68.0, 1024.0),
	])
	nav_poly.add_outline(outline)
	_nav_region.navigation_polygon = nav_poly
	_nav_region.bake_navigation_polygon(false)


func _build_night_lamps() -> void:
	var lamp_positions: Array[Vector2] = [
		Vector2(640.0, 180.0),
		Vector2(960.0, 180.0),
		Vector2(540.0, 560.0),
		Vector2(860.0, 600.0),
		Vector2(1280.0, 290.0),
		Vector2(280.0, 290.0),
		Vector2(720.0, 960.0),
		Vector2(880.0, 960.0),
	]
	for pos in lamp_positions:
		var glow := Polygon2D.new()
		glow.position = pos
		var pts := PackedVector2Array()
		for i in range(16):
			var angle: float = TAU * float(i) / 16.0
			pts.append(Vector2(cos(angle), sin(angle)) * 78.0)
		glow.polygon = pts
		glow.color = Color(1.0, 0.78, 0.42, 0.22)
		_night_lamps_layer.add_child(glow)


func _on_time_slot_changed(slot_id: String, _slot_label: String) -> void:
	_apply_slot_lighting(slot_id)


func _apply_slot_lighting(slot_id: String) -> void:
	var target_color: Color = Color.WHITE
	var show_lamps: bool = false
	match slot_id:
		GameClock.SLOT_MORNING:
			target_color = Color(1.0, 0.96, 0.90)
		GameClock.SLOT_FOCUS:
			target_color = Color(1.0, 1.0, 1.0)
		GameClock.SLOT_REFUEL:
			target_color = Color(1.0, 0.98, 0.92)
		GameClock.SLOT_FREE_SOUL:
			target_color = Color(0.84, 0.78, 0.92)
			show_lamps = true
		GameClock.SLOT_SHUTDOWN:
			target_color = Color(0.56, 0.60, 0.76)
			show_lamps = true
	_ambient_modulate.color = target_color
	_night_lamps_layer.visible = show_lamps


func _draw() -> void:
	# 背景底色（宫城外草地）
	draw_rect(Rect2(Vector2.ZERO, WORLD_SIZE), Color(0.14, 0.17, 0.16), true)
	# 宫城内石板大院
	draw_rect(Rect2(68.0, 68.0, 1464.0, 956.0), Color(0.24, 0.25, 0.27), true)

	# 四个功能区地坪
	# 1. 议事正殿地砖 + 中轴红毯
	draw_rect(Rect2(542.0, 68.0, 516.0, 322.0), Color(0.32, 0.27, 0.25), true)
	draw_rect(Rect2(752.0, 110.0, 96.0, 300.0), Color(0.58, 0.18, 0.20), true)
	draw_rect(Rect2(752.0, 110.0, 96.0, 300.0), Color(0.84, 0.68, 0.30), false, 2.0)

	# 2. 东偏殿内阁值房（木地板）
	draw_rect(Rect2(1080.0, 68.0, 452.0, 372.0), Color(0.33, 0.28, 0.22), true)

	# 3. 西偏院匠造与画坊（浅石地）
	draw_rect(Rect2(68.0, 68.0, 452.0, 412.0), Color(0.27, 0.28, 0.30), true)
	# 预留地块虚线框
	draw_rect(Rect2(125.0, 345.0, 100.0, 80.0), Color(0.38, 0.80, 0.90, 0.14), true)
	draw_rect(Rect2(125.0, 345.0, 100.0, 80.0), Color(0.38, 0.80, 0.90, 0.70), false, 2.0)
	draw_rect(Rect2(315.0, 345.0, 100.0, 80.0), Color(0.66, 0.84, 0.56, 0.14), true)
	draw_rect(Rect2(315.0, 345.0, 100.0, 80.0), Color(0.66, 0.84, 0.56, 0.70), false, 2.0)

	# 4. 中心御苑草坪与广场通道
	draw_rect(Rect2(340.0, 500.0, 920.0, 400.0), Color(0.23, 0.34, 0.25), true)
	draw_rect(Rect2(745.0, 412.0, 110.0, 612.0), Color(0.30, 0.30, 0.32), true)
	# 御苑小戏台地面
	draw_rect(Rect2(475.0, 555.0, 130.0, 110.0), Color(0.42, 0.31, 0.24), true)
	draw_rect(Rect2(475.0, 555.0, 130.0, 110.0), Color(0.86, 0.70, 0.42), false, 2.0)

	# 装饰网格线（增强俯视角空间尺度感）
	for x in range(80, 1520, 80):
		draw_line(Vector2(float(x), 68.0), Vector2(float(x), 1024.0), Color(1.0, 1.0, 1.0, 0.03), 1.0)
	for y in range(80, 1024, 80):
		draw_line(Vector2(68.0, float(y)), Vector2(1532.0, float(y)), Color(1.0, 1.0, 1.0, 0.03), 1.0)

	# 宫墙渲染
	for wall in _wall_rects:
		draw_rect(wall, Color(0.42, 0.39, 0.38), true)
		draw_rect(wall, Color(0.64, 0.58, 0.52), false, 2.0)

	# 家具渲染
	for item in _furniture_rects:
		var rect: Rect2 = item["rect"]
		var col: Color = item["color"]
		draw_rect(rect, col, true)
		draw_rect(rect, col.lightened(0.25), false, 2.0)

	# 区域名牌
	var font: Font = ThemeDB.fallback_font
	for entry in _zone_labels:
		var pos: Vector2 = entry["pos"]
		var txt: String = entry["text"]
		draw_string(font, pos + Vector2(-95.0, 0.0), txt, HORIZONTAL_ALIGNMENT_CENTER, 190.0, 14, Color(0.96, 0.92, 0.78, 0.85))
