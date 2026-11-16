extends Node2D

## 「一轴四区」皇城宫城场景：
## 中轴议事正殿、东偏殿内阁值房、中心御苑广场、西偏院匠造与画坊、南宫门。
## 优先加载 assets/palace/ 32x32 唐风像素底图、前景屋檐遮挡层与透明底像素家具/景观精灵，并保留白模回退绘制。

const InteractableSpot = preload("res://scripts/world/interactable_spot.gd")

const WORLD_SIZE: Vector2 = Vector2(1600.0, 1120.0)
const BASE_MAP_PATH: String = "res://assets/palace/palace_base.png"
const FRONT_MAP_PATH: String = "res://assets/palace/palace_front.png"
const PROPS_DIR: String = "res://assets/palace/props/"

var waypoints: Dictionary = {}
var actors_container: Node2D
var _nav_region: NavigationRegion2D
var _obstacles_root: Node2D
var _ground_decor_layer: Node2D
var _plaques_layer: Node2D
var _ambient_modulate: CanvasModulate
var _night_lamps_layer: Node2D
var _base_map_sprite: Sprite2D
var _front_map_sprite: Sprite2D
var _has_base_map: bool = false
var _zone_labels: Array[Dictionary] = []
var _furniture_rects: Array[Dictionary] = []
var _wall_rects: Array[Rect2] = []


func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_build_structure()
	_build_waypoints()
	_build_interactables()
	_bake_navigation()
	GameClock.time_slot_changed.connect(_on_time_slot_changed)
	_apply_slot_lighting(GameClock.current_slot)
	queue_redraw()


func get_waypoint_position(waypoint_name: String) -> Vector2:
	if waypoints.has(waypoint_name):
		return waypoints[waypoint_name] as Vector2
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
	_load_base_map()

	_ground_decor_layer = Node2D.new()
	_ground_decor_layer.name = "GroundDecorLayer"
	_ground_decor_layer.z_index = -2
	add_child(_ground_decor_layer)

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

	_plaques_layer = Node2D.new()
	_plaques_layer.name = "PlaquesLayer"
	_plaques_layer.z_index = 6
	add_child(_plaques_layer)

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
	_add_furniture(Rect2(745.0, 110.0, 110.0, 48.0), Color(0.72, 0.56, 0.24), "御坐", PROPS_DIR + "throne_dais.png", Vector2(160.0, 110.0))
	# 2. 正殿舆图沙盘桌
	_add_furniture(Rect2(730.0, 232.0, 140.0, 76.0), Color(0.32, 0.44, 0.38), "舆图沙盘", PROPS_DIR + "sandbox_table.png", Vector2(180.0, 110.0))
	# 3. 东偏殿办公书桌 & 卷宗架
	_add_furniture(Rect2(1150.0, 160.0, 120.0, 50.0), Color(0.45, 0.30, 0.20), "考成案牍", PROPS_DIR + "desk_chizheng.png", Vector2(150.0, 84.0), false, true)
	_add_furniture(Rect2(1350.0, 160.0, 120.0, 50.0), Color(0.45, 0.30, 0.20), "秘文案桌", PROPS_DIR + "desk_bina.png", Vector2(150.0, 84.0), false, true)
	_add_furniture(Rect2(1240.0, 100.0, 150.0, 28.0), Color(0.38, 0.26, 0.18), "卷宗架", PROPS_DIR + "shelf_archives.png", Vector2(176.0, 86.0))
	_add_furniture(Rect2(1105.0, 318.0, 104.0, 44.0), Color(0.42, 0.30, 0.24), "书记案", PROPS_DIR + "desk_taki.png", Vector2(136.0, 76.0), false, true, Vector2(0.0, 12.0))
	_add_furniture(Rect2(1386.0, 318.0, 110.0, 44.0), Color(0.34, 0.44, 0.46), "兰台书架", PROPS_DIR + "shelf_lantai.png", Vector2(140.0, 88.0), false, true, Vector2(0.0, 18.0))
	# 4. 西偏院工坊台、画架与太医药架
	_add_furniture(Rect2(130.0, 165.0, 125.0, 54.0), Color(0.34, 0.40, 0.48), "工学锻台", PROPS_DIR + "workbench_bit.png", Vector2(156.0, 90.0), false, true)
	_add_furniture(Rect2(345.0, 170.0, 95.0, 48.0), Color(0.56, 0.46, 0.34), "画坊长案", PROPS_DIR + "atelier_vinci.png", Vector2(130.0, 84.0), false, true)
	_add_furniture(Rect2(476.0, 330.0, 36.0, 84.0), Color(0.36, 0.50, 0.38), "太医药架", PROPS_DIR + "shelf_qianjin.png", Vector2(72.0, 116.0), false, true)
	# 5. 御苑莲池、石桌与东西外廊案台（莲池已直接绘入底图）
	_add_furniture(Rect2(920.0, 620.0, 200.0, 130.0), Color(0.24, 0.52, 0.64), "御苑莲池", "", Vector2(240.0, 160.0), true)
	_add_furniture(Rect2(675.0, 690.0, 96.0, 64.0), Color(0.62, 0.60, 0.56), "石桌", PROPS_DIR + "stone_table.png", Vector2(128.0, 88.0), false, true)
	_add_furniture(Rect2(1245.0, 555.0, 115.0, 48.0), Color(0.38, 0.46, 0.44), "军机沙案", PROPS_DIR + "desk_boming.png", Vector2(146.0, 80.0), false, true)
	_add_furniture(Rect2(1245.0, 745.0, 115.0, 48.0), Color(0.42, 0.34, 0.44), "政宣刊案", PROPS_DIR + "desk_jiafa.png", Vector2(146.0, 80.0), false, true)
	_add_furniture(Rect2(135.0, 575.0, 115.0, 48.0), Color(0.34, 0.38, 0.48), "格物算席", PROPS_DIR + "desk_planck.png", Vector2(146.0, 80.0), false, true)
	_add_furniture(Rect2(140.0, 755.0, 110.0, 54.0), Color(0.50, 0.36, 0.26), "御苑茶亭", PROPS_DIR + "tea_pavilion.png", Vector2(168.0, 136.0), false, true, Vector2(0.0, 60.0))

	# 地面扁平建筑与庭院装饰（戏台、预留地块已绘入底图；此处放置立体园林树木）
	_build_scenery_props()

	# 区域匾额（落在屋脊/院门/宫门处，避免遮挡角色）
	_zone_labels = [
		{"pos": Vector2(800.0, 26.0), "text": "【中轴 · 议事正殿】"},
		{"pos": Vector2(1300.0, 28.0), "text": "【东偏殿 · 内阁值房】"},
		{"pos": Vector2(290.0, 28.0), "text": "【西偏院 · 匠造与画坊】"},
		{"pos": Vector2(800.0, 492.0), "text": "【中心 · 御苑广场】"},
		{"pos": Vector2(800.0, 1072.0), "text": "【南宫门】"},
	]
	for entry: Dictionary in _zone_labels:
		var pos: Vector2 = entry["pos"] as Vector2
		var txt: String = str(entry["text"])
		_create_plaque_label(txt, pos, _plaques_layer, 13, Color(0.88, 0.74, 0.38, 0.92), Color(0.08, 0.06, 0.05, 0.90), 2, 14)

	_build_night_lamps()


func _load_base_map() -> void:
	if ResourceLoader.exists(BASE_MAP_PATH):
		var tex: Texture2D = load(BASE_MAP_PATH) as Texture2D
		if tex != null:
			_base_map_sprite = Sprite2D.new()
			_base_map_sprite.name = "PalaceBaseMap"
			_base_map_sprite.texture = tex
			_base_map_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			_base_map_sprite.centered = false
			_base_map_sprite.z_index = -10
			var tex_size: Vector2 = tex.get_size()
			if tex_size.x > 0.0 and tex_size.y > 0.0:
				_base_map_sprite.scale = Vector2(WORLD_SIZE.x / tex_size.x, WORLD_SIZE.y / tex_size.y)
			add_child(_base_map_sprite)
			_has_base_map = true

	if ResourceLoader.exists(FRONT_MAP_PATH):
		var front_tex: Texture2D = load(FRONT_MAP_PATH) as Texture2D
		if front_tex != null:
			_front_map_sprite = Sprite2D.new()
			_front_map_sprite.name = "PalaceFrontMap"
			_front_map_sprite.texture = front_tex
			_front_map_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			_front_map_sprite.centered = false
			_front_map_sprite.z_index = 4
			var front_size: Vector2 = front_tex.get_size()
			if front_size.x > 0.0 and front_size.y > 0.0:
				_front_map_sprite.scale = Vector2(WORLD_SIZE.x / front_size.x, WORLD_SIZE.y / front_size.y)
			add_child(_front_map_sprite)


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


func _add_furniture(
	rect: Rect2,
	color: Color,
	label_text: String,
	prop_tex_path: String = "",
	visual_size: Vector2 = Vector2.ZERO,
	is_ground_flat: bool = false,
	label_above: bool = false,
	plaque_offset: Vector2 = Vector2.ZERO
) -> void:
	var body := StaticBody2D.new()
	body.position = rect.get_center()
	body.collision_layer = 1
	var shape := CollisionShape2D.new()
	var box := RectangleShape2D.new()
	box.size = rect.size
	shape.shape = box
	body.add_child(shape)
	_obstacles_root.add_child(body)

	var placed_sprite: bool = false
	if not prop_tex_path.is_empty():
		var target_parent: Node2D = _ground_decor_layer if is_ground_flat else actors_container
		if is_ground_flat:
			placed_sprite = _spawn_ground_sprite(prop_tex_path, rect.get_center(), visual_size, target_parent) != null
		else:
			placed_sprite = _spawn_ysort_sprite(prop_tex_path, Vector2(rect.get_center().x, rect.end.y - 4.0), visual_size, target_parent, 2.0) != null

	if not placed_sprite and not _has_base_map:
		_furniture_rects.append({"rect": rect, "color": color, "label": label_text})

	var plaque_y: float = rect.end.y + 10.0
	if label_above:
		if visual_size.y > 0.0:
			plaque_y = rect.end.y - 4.0 - visual_size.y - 8.0
		else:
			plaque_y = rect.position.y - 12.0
	var plaque_pos := Vector2(rect.get_center().x, plaque_y) + plaque_offset
	_create_plaque_label(label_text, plaque_pos, _plaques_layer, 11, Color(0.74, 0.62, 0.36, 0.62), Color(0.09, 0.08, 0.07, 0.78))


func _spawn_ground_sprite(tex_path: String, center_pos: Vector2, target_size: Vector2, parent: Node2D) -> Sprite2D:
	if not ResourceLoader.exists(tex_path):
		return null
	var tex: Texture2D = load(tex_path) as Texture2D
	if tex == null:
		return null
	var spr := Sprite2D.new()
	spr.texture = tex
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.centered = true
	spr.position = center_pos.snapped(Vector2(2.0, 2.0))
	var tex_size: Vector2 = tex.get_size()
	if target_size != Vector2.ZERO and tex_size.x > 0.0 and tex_size.y > 0.0:
		spr.scale = Vector2(target_size.x / tex_size.x, target_size.y / tex_size.y)
	parent.add_child(spr)
	return spr


func _spawn_ysort_sprite(
	tex_path: String,
	foot_pos: Vector2,
	target_size: Vector2,
	parent: Node2D,
	bottom_pad: float = 2.0
) -> Sprite2D:
	if not ResourceLoader.exists(tex_path):
		return null
	var tex: Texture2D = load(tex_path) as Texture2D
	if tex == null:
		return null
	var spr := Sprite2D.new()
	spr.texture = tex
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.centered = false
	var tex_size: Vector2 = tex.get_size()
	spr.offset = Vector2(-tex_size.x * 0.5, -tex_size.y + bottom_pad).snapped(Vector2(2.0, 2.0))
	spr.position = foot_pos.snapped(Vector2(2.0, 2.0))
	if target_size != Vector2.ZERO and tex_size.x > 0.0 and tex_size.y > 0.0:
		spr.scale = Vector2(target_size.x / tex_size.x, target_size.y / tex_size.y)
	parent.add_child(spr)
	return spr


func _build_scenery_props() -> void:
	# 戏台与西偏院预留地块已直接绘入底图，此处放置垂直 Y-Sort 树木
	# 池畔垂柳（避开寻路主通道，保持 1:1 整数像素比例）
	var willow_positions: Array[Vector2] = [
		Vector2(1176.0, 680.0),
		Vector2(1136.0, 566.0),
	]
	for pos: Vector2 in willow_positions:
		_spawn_ysort_sprite(PROPS_DIR + "tree_willow.png", pos, Vector2(150.0, 160.0), actors_container, 4.0)

	# 御苑与宫城庭院银杏树
	var ginkgo_positions: Array[Vector2] = [
		Vector2(406.0, 576.0),
		Vector2(410.0, 846.0),
		Vector2(1186.0, 846.0),
		Vector2(146.0, 966.0),
		Vector2(1456.0, 966.0),
	]
	for pos: Vector2 in ginkgo_positions:
		_spawn_ysort_sprite(PROPS_DIR + "tree_ginkgo.png", pos, Vector2(140.0, 150.0), actors_container, 4.0)


func _create_plaque_label(
	text: String,
	center_pos: Vector2,
	parent: Node,
	font_size: int,
	border_color: Color,
	bg_color: Color,
	border_width: int = 1,
	pad_x: int = 8
) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var style := StyleBoxFlat.new()
	style.bg_color = bg_color
	style.border_width_left = border_width
	style.border_width_top = border_width
	style.border_width_right = border_width
	style.border_width_bottom = border_width
	style.border_color = border_color
	style.corner_radius_top_left = 0
	style.corner_radius_top_right = 0
	style.corner_radius_bottom_left = 0
	style.corner_radius_bottom_right = 0
	style.shadow_color = Color(0.05, 0.04, 0.04, 0.58)
	style.shadow_size = 1
	style.shadow_offset = Vector2(2.0, 2.0)
	style.content_margin_left = pad_x
	style.content_margin_right = pad_x
	style.content_margin_top = 3 if border_width > 1 else 2
	style.content_margin_bottom = 3 if border_width > 1 else 2
	panel.add_theme_stylebox_override("panel", style)

	var lbl := Label.new()
	lbl.text = text
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	lbl.add_theme_font_size_override("font_size", font_size)
	lbl.add_theme_color_override("font_color", Color(0.98, 0.94, 0.82))
	lbl.add_theme_color_override("font_outline_color", Color(0.05, 0.04, 0.04))
	lbl.add_theme_constant_override("outline_size", 2)
	panel.add_child(lbl)

	parent.add_child(panel)
	panel.reset_size()
	panel.position = (center_pos - panel.size * 0.5).snapped(Vector2(2.0, 2.0))
	return panel


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
	sandbox.indicator_size = Vector2(150.0, 86.0)
	sandbox.is_council_sandbox = true
	sandbox.position = Vector2(800.0, 270.0)
	add_child(sandbox)

	var plot_a := InteractableSpot.new()
	plot_a.spot_id = "west_plot_a"
	plot_a.display_title = "西偏院 · 预留地块 A"
	plot_a.prompt_hint = "按 [E] 勘察扩建地块"
	plot_a.accent_color = Color(0.38, 0.80, 0.90)
	plot_a.indicator_size = Vector2(114.0, 92.0)
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
	plot_b.indicator_size = Vector2(114.0, 92.0)
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
		Vector2(456.0, 548.0),
		Vector2(860.0, 600.0),
		Vector2(1280.0, 290.0),
		Vector2(280.0, 290.0),
		Vector2(720.0, 960.0),
		Vector2(880.0, 960.0),
	]
	var glow_layers: Array[Dictionary] = [
		{"radius": 96.0, "color": Color(1.0, 0.72, 0.34, 0.08)},
		{"radius": 62.0, "color": Color(1.0, 0.78, 0.42, 0.14)},
		{"radius": 32.0, "color": Color(1.0, 0.86, 0.56, 0.22)},
		{"radius": 10.0, "color": Color(1.0, 0.95, 0.78, 0.50)},
	]
	for pos: Vector2 in lamp_positions:
		var snapped_pos: Vector2 = pos.snapped(Vector2(2.0, 2.0))
		_spawn_ysort_sprite(PROPS_DIR + "palace_lantern.png", snapped_pos, Vector2(56.0, 96.0), actors_container, 4.0)
		var glow_center: Vector2 = snapped_pos + Vector2(0.0, -56.0)
		for spec: Dictionary in glow_layers:
			var radius: float = float(spec["radius"])
			var col: Color = spec["color"] as Color
			var glow := Polygon2D.new()
			glow.position = glow_center
			var pts := PackedVector2Array()
			for i: int in range(8):
				var angle: float = (TAU * float(i) / 8.0) + (PI / 8.0)
				var raw_pt := Vector2(cos(angle), sin(angle)) * radius
				pts.append(raw_pt.snapped(Vector2(2.0, 2.0)))
			glow.polygon = pts
			glow.color = col
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
	if not _has_base_map:
		# 白模回退背景底色（宫城外草地与石板大院）
		draw_rect(Rect2(Vector2.ZERO, WORLD_SIZE), Color(0.14, 0.17, 0.16), true)
		draw_rect(Rect2(68.0, 68.0, 1464.0, 956.0), Color(0.24, 0.25, 0.27), true)
		draw_rect(Rect2(542.0, 68.0, 516.0, 322.0), Color(0.32, 0.27, 0.25), true)
		draw_rect(Rect2(752.0, 110.0, 96.0, 300.0), Color(0.58, 0.18, 0.20), true)
		draw_rect(Rect2(752.0, 110.0, 96.0, 300.0), Color(0.84, 0.68, 0.30), false, 2.0)
		draw_rect(Rect2(1080.0, 68.0, 452.0, 372.0), Color(0.33, 0.28, 0.22), true)
		draw_rect(Rect2(68.0, 68.0, 452.0, 412.0), Color(0.27, 0.28, 0.30), true)
		draw_rect(Rect2(340.0, 500.0, 920.0, 400.0), Color(0.23, 0.34, 0.25), true)
		draw_rect(Rect2(745.0, 412.0, 110.0, 612.0), Color(0.30, 0.30, 0.32), true)
		draw_rect(Rect2(475.0, 555.0, 130.0, 110.0), Color(0.42, 0.31, 0.24), true)
		draw_rect(Rect2(475.0, 555.0, 130.0, 110.0), Color(0.86, 0.70, 0.42), false, 2.0)
		for wall: Rect2 in _wall_rects:
			draw_rect(wall, Color(0.42, 0.39, 0.38), true)
			draw_rect(wall, Color(0.64, 0.58, 0.52), false, 2.0)

	# 仅针对未加载到精灵贴图的家具绘制回退色块
	for item: Dictionary in _furniture_rects:
		var rect: Rect2 = item["rect"] as Rect2
		var col: Color = item["color"] as Color
		draw_rect(rect, col, true)
		draw_rect(rect, col.lightened(0.25), false, 2.0)
