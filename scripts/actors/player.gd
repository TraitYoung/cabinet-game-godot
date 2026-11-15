extends CharacterBody2D

## 玩家控制的「陛下」：支持 WASD 移动、相机跟随与按 [E] 交互。

const CharacterProfile = preload("res://scripts/data/character_profile.gd")
const CabinetMember = preload("res://scripts/actors/cabinet_member.gd")
const InteractableSpot = preload("res://scripts/world/interactable_spot.gd")

const MONARCH_SPRITE_PATH: String = "res://assets/characters/chibi/monarch.png"
const BASE_SPRITE_SCALE: Vector2 = Vector2(0.30, 0.30)
const BASE_SPRITE_Y: float = 8.0

@export var move_speed: float = 225.0

var facing_dir: Vector2 = Vector2.DOWN
var _nearby_ministers: Array[CabinetMember] = []
var _nearby_spots: Array[InteractableSpot] = []
var _active_target: Node = null
var _sprite: Sprite2D
var _prompt_label: Label
var _is_dialogue_locked: bool = false
var _anim_time: float = 0.0


func _ready() -> void:
	collision_layer = 2
	collision_mask = 1

	var body_shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 12.0
	body_shape.shape = circle
	add_child(body_shape)

	var cam := Camera2D.new()
	cam.enabled = true
	cam.zoom = Vector2(1.15, 1.15)
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 8.0
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = 1600
	cam.limit_bottom = 1120
	add_child(cam)

	var sensor := Area2D.new()
	sensor.name = "InteractSensor"
	sensor.collision_layer = 0
	sensor.collision_mask = 2 | 4
	var sensor_shape := CollisionShape2D.new()
	var sensor_circle := CircleShape2D.new()
	sensor_circle.radius = 64.0
	sensor_shape.shape = sensor_circle
	sensor.add_child(sensor_shape)
	sensor.body_entered.connect(_on_sensor_body_entered)
	sensor.body_exited.connect(_on_sensor_body_exited)
	sensor.area_entered.connect(_on_sensor_area_entered)
	sensor.area_exited.connect(_on_sensor_area_exited)
	add_child(sensor)

	_build_chibi_sprite()

	_prompt_label = Label.new()
	_prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt_label.position = Vector2(-95.0, -82.0)
	_prompt_label.size = Vector2(190.0, 22.0)
	_prompt_label.add_theme_font_size_override("font_size", 13)
	_prompt_label.add_theme_color_override("font_color", Color(1.0, 0.94, 0.65))
	_prompt_label.add_theme_color_override("font_outline_color", Color(0.06, 0.06, 0.10))
	_prompt_label.add_theme_constant_override("outline_size", 4)
	_prompt_label.visible = false
	add_child(_prompt_label)

	DialogueBus.character_dialogue_requested.connect(_on_dialogue_opened)
	DialogueBus.council_meeting_requested.connect(_on_council_opened)
	DialogueBus.info_dialogue_requested.connect(_on_info_opened)
	DialogueBus.dialogue_closed.connect(_on_dialogue_closed)


func _physics_process(delta: float) -> void:
	if _is_dialogue_locked:
		velocity = Vector2.ZERO
		_update_sprite_animation(delta, false)
		return

	var input_vec := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	var is_moving: bool = input_vec.length() > 0.01
	if is_moving:
		facing_dir = input_vec.normalized()
		velocity = facing_dir * move_speed
		if _sprite != null:
			if facing_dir.x < -0.1:
				_sprite.flip_h = true
			elif facing_dir.x > 0.1:
				_sprite.flip_h = false
		else:
			queue_redraw()
	else:
		velocity = Vector2.ZERO

	_update_sprite_animation(delta, is_moving)
	move_and_slide()
	_refresh_active_target()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("toggle_speed"):
		GameClock.cycle_speed()
		return
	if _is_dialogue_locked:
		return
	if event.is_action_pressed("interact") and _active_target != null:
		if _active_target is CabinetMember:
			(_active_target as CabinetMember).start_conversation(global_position)
		elif _active_target is InteractableSpot:
			(_active_target as InteractableSpot).interact()
		get_viewport().set_input_as_handled()


func _refresh_active_target() -> void:
	var best: Node = null
	var best_dist: float = INF

	for member in _nearby_ministers:
		if not is_instance_valid(member):
			continue
		var d: float = global_position.distance_squared_to(member.global_position)
		if d < best_dist:
			best_dist = d
			best = member

	for spot in _nearby_spots:
		if not is_instance_valid(spot):
			continue
		var d: float = global_position.distance_squared_to(spot.global_position)
		if d < best_dist:
			best_dist = d
			best = spot

	if best != _active_target:
		if _active_target is InteractableSpot and is_instance_valid(_active_target):
			(_active_target as InteractableSpot).set_highlighted(false)
		_active_target = best
		if _active_target is InteractableSpot:
			(_active_target as InteractableSpot).set_highlighted(true)

	if _active_target is CabinetMember:
		var prof: CharacterProfile = (_active_target as CabinetMember).profile
		_prompt_label.text = "按 [E] 与 %s 对话" % prof.display_name
		_prompt_label.visible = true
	elif _active_target is InteractableSpot:
		_prompt_label.visible = false
	else:
		_prompt_label.visible = false


func _on_sensor_body_entered(body: Node2D) -> void:
	if body is CabinetMember and not _nearby_ministers.has(body):
		_nearby_ministers.append(body as CabinetMember)


func _on_sensor_body_exited(body: Node2D) -> void:
	if body is CabinetMember:
		_nearby_ministers.erase(body as CabinetMember)


func _on_sensor_area_entered(area: Area2D) -> void:
	if area is InteractableSpot and not _nearby_spots.has(area):
		_nearby_spots.append(area as InteractableSpot)


func _on_sensor_area_exited(area: Area2D) -> void:
	if area is InteractableSpot:
		(area as InteractableSpot).set_highlighted(false)
		_nearby_spots.erase(area as InteractableSpot)


func _on_dialogue_opened(_profile: CharacterProfile) -> void:
	_is_dialogue_locked = true


func _on_council_opened(_title: String, _entries: Array) -> void:
	_is_dialogue_locked = true


func _on_info_opened(_n: String, _r: String, _c: Color, _l: PackedStringArray) -> void:
	_is_dialogue_locked = true


func _on_dialogue_closed() -> void:
	_is_dialogue_locked = false


func _build_chibi_sprite() -> void:
	if not ResourceLoader.exists(MONARCH_SPRITE_PATH):
		return
	var tex: Texture2D = load(MONARCH_SPRITE_PATH) as Texture2D
	if tex == null:
		return
	_sprite = Sprite2D.new()
	_sprite.texture = tex
	_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_sprite.centered = false
	_sprite.offset = Vector2(-100.0, -226.0)
	_sprite.position = Vector2(0.0, BASE_SPRITE_Y)
	_sprite.scale = BASE_SPRITE_SCALE
	add_child(_sprite)


func _update_sprite_animation(delta: float, is_moving: bool) -> void:
	if _sprite == null:
		return
	if is_moving:
		_anim_time += delta * 12.5
		_sprite.position.y = BASE_SPRITE_Y - absf(sin(_anim_time)) * 4.0
		_sprite.rotation = sin(_anim_time) * 0.05
		_sprite.scale = BASE_SPRITE_SCALE
	else:
		_anim_time += delta * 2.4
		_sprite.position.y = BASE_SPRITE_Y
		_sprite.rotation = 0.0
		var breath: float = 1.0 + sin(_anim_time) * 0.015
		_sprite.scale = Vector2(BASE_SPRITE_SCALE.x, BASE_SPRITE_SCALE.y * breath)


func _draw() -> void:
	if _sprite != null:
		draw_set_transform(Vector2(0.0, 8.0), 0.0, Vector2(1.4, 0.58))
		draw_circle(Vector2.ZERO, 12.5, Color(0.0, 0.0, 0.0, 0.30))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		return
	# 脚下投影
	draw_circle(Vector2(0.0, 12.0), 13.0, Color(0.0, 0.0, 0.0, 0.30))
	# 皇室玄金常服
	draw_circle(Vector2(0.0, 2.0), 13.0, Color(0.16, 0.22, 0.38))
	draw_arc(Vector2(0.0, 2.0), 13.0, 0.0, TAU, 24, Color(0.92, 0.76, 0.34), 2.2)
	# 头部与小金冠
	draw_circle(Vector2(0.0, -10.0), 10.0, Color(0.96, 0.87, 0.78))
	draw_rect(Rect2(-6.0, -21.0, 12.0, 4.0), Color(0.95, 0.80, 0.28), true)
	# 朝向高光点
	var look_offset: Vector2 = facing_dir.normalized() * 5.0
	draw_circle(Vector2(0.0, -9.0) + look_offset * 0.6, 2.0, Color(0.18, 0.20, 0.28))
