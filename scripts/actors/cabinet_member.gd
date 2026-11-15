extends CharacterBody2D

## 通用内阁大臣控制器：基于 CharacterProfile 驱动日程巡游、玩家对话与头顶气泡演出。

const CharacterProfile = preload("res://scripts/data/character_profile.gd")
const PalaceWorld = preload("res://scripts/world/palace.gd")

const BASE_SPRITE_SCALE: Vector2 = Vector2(0.28, 0.28)
const BASE_SPRITE_Y: float = 8.0

enum State {
	WORKING,
	MOVING,
	CHATTING,
}

@export var move_speed: float = 115.0

var profile: CharacterProfile
var palace: PalaceWorld
var state: State = State.WORKING
var facing_dir: Vector2 = Vector2.DOWN

var _nav_agent: NavigationAgent2D
var _sprite: Sprite2D
var _name_label: Label
var _bubble_panel: PanelContainer
var _bubble_label: Label
var _bubble_timer: Timer
var _home_target: Vector2 = Vector2.ZERO
var _wander_timer: float = 0.0
var _is_bantering: bool = false
var _anim_time: float = 0.0


func setup(p_profile: CharacterProfile, p_palace: PalaceWorld) -> void:
	profile = p_profile
	palace = p_palace
	name = "Minister_%s" % profile.id


func _ready() -> void:
	collision_layer = 2
	collision_mask = 1

	var col := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 12.0
	col.shape = circle
	add_child(col)

	_nav_agent = NavigationAgent2D.new()
	_nav_agent.path_desired_distance = 14.0
	_nav_agent.target_desired_distance = 18.0
	_nav_agent.avoidance_enabled = false
	add_child(_nav_agent)

	_build_chibi_sprite()
	_build_visual_labels()

	GameClock.time_slot_changed.connect(_on_time_slot_changed)
	DialogueBus.dialogue_closed.connect(_on_dialogue_closed)

	if profile != null and palace != null:
		var slot_wp: String = str(profile.schedule_waypoints.get(GameClock.current_slot, "courtyard_table"))
		global_position = palace.get_waypoint_position(slot_wp) + _get_personal_offset()
		_home_target = global_position
		_name_label.text = profile.display_name
		_name_label.add_theme_color_override("font_color", profile.accent_color.lightened(0.25))
		_wander_timer = randf_range(4.0, 9.0)
	_anim_time = randf_range(0.0, TAU)
	queue_redraw()


func _physics_process(delta: float) -> void:
	if state == State.CHATTING:
		velocity = Vector2.ZERO
		_update_sprite_animation(delta, false)
		return

	if state == State.MOVING:
		if _nav_agent.is_navigation_finished():
			velocity = Vector2.ZERO
			state = State.WORKING
			_wander_timer = randf_range(5.0, 11.0)
			_update_sprite_animation(delta, false)
		else:
			var next_pos: Vector2 = _nav_agent.get_next_path_position()
			var dir: Vector2 = next_pos - global_position
			if dir.length() > 1.0:
				facing_dir = dir.normalized()
				velocity = facing_dir * move_speed
				_update_sprite_facing()
				if _sprite == null:
					queue_redraw()
			else:
				velocity = Vector2.ZERO
			_update_sprite_animation(delta, velocity.length() > 2.0)
		move_and_slide()
		return

	_update_sprite_animation(delta, false)

	# WORKING 状态下在工位周边小幅度活动，显得更自然
	if not _is_bantering:
		_wander_timer -= delta
		if _wander_timer <= 0.0:
			_wander_timer = randf_range(6.0, 13.0)
			var offset := Vector2(randf_range(-28.0, 28.0), randf_range(-22.0, 22.0))
			_move_to(_home_target + offset)


func is_available_for_banter() -> bool:
	return state != State.CHATTING and not _is_bantering


func set_bantering(active: bool, look_at_pos: Vector2 = Vector2.ZERO) -> void:
	_is_bantering = active
	if active and look_at_pos != Vector2.ZERO:
		facing_dir = (look_at_pos - global_position).normalized()
		velocity = Vector2.ZERO
		state = State.WORKING
		_update_sprite_facing()
		if _sprite == null:
			queue_redraw()


func start_conversation(player_pos: Vector2) -> void:
	state = State.CHATTING
	_is_bantering = false
	_hide_overhead_bubble()
	facing_dir = (player_pos - global_position).normalized()
	_update_sprite_facing()
	if _sprite == null:
		queue_redraw()
	DialogueBus.character_dialogue_requested.emit(profile)


func show_overhead_bubble(text: String, duration: float = 3.2) -> void:
	if _bubble_panel == null or _bubble_label == null:
		return
	_bubble_label.text = text
	_bubble_panel.visible = true
	_bubble_panel.reset_size()
	_bubble_panel.position = Vector2(-_bubble_panel.size.x * 0.5, -76.0 - _bubble_panel.size.y)
	_bubble_timer.start(duration)


func get_status_label() -> String:
	if state == State.CHATTING:
		return "侍驾中"
	if _is_bantering:
		return "同僚闲谈"
	if state == State.MOVING:
		return "巡走换岗"
	return "当值"


func _move_to(target_pos: Vector2) -> void:
	_nav_agent.target_position = target_pos
	state = State.MOVING


func _on_time_slot_changed(slot_id: String, _slot_label: String) -> void:
	if profile == null or palace == null:
		return
	var wp_name: String = str(profile.schedule_waypoints.get(slot_id, "courtyard_table"))
	_home_target = palace.get_waypoint_position(wp_name) + _get_personal_offset()
	if state != State.CHATTING:
		_move_to(_home_target)


func _on_dialogue_closed() -> void:
	if state == State.CHATTING:
		state = State.WORKING
		_wander_timer = randf_range(4.0, 8.0)


func _hide_overhead_bubble() -> void:
	if _bubble_panel != null:
		_bubble_panel.visible = false


func _get_personal_offset() -> Vector2:
	if profile == null:
		return Vector2.ZERO
	match profile.id:
		"bina":
			return Vector2(-24.0, 12.0)
		"chizheng":
			return Vector2(24.0, -10.0)
		"bit":
			return Vector2(-22.0, -16.0)
		"vinci":
			return Vector2(26.0, 16.0)
		"taki":
			return Vector2(-34.0, -6.0)
		"jean":
			return Vector2(34.0, 8.0)
		"tianji":
			return Vector2(-10.0, 26.0)
		"fukucho":
			return Vector2(14.0, -26.0)
		"planck":
			return Vector2(-38.0, 20.0)
		"boming":
			return Vector2(38.0, -18.0)
		"qianjin":
			return Vector2(0.0, 30.0)
		"jiafa":
			return Vector2(42.0, 24.0)
	return Vector2.ZERO


func _build_chibi_sprite() -> void:
	if profile == null or profile.chibi_sprite_path.is_empty():
		return
	if not ResourceLoader.exists(profile.chibi_sprite_path):
		return
	var tex: Texture2D = load(profile.chibi_sprite_path) as Texture2D
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


func _update_sprite_facing() -> void:
	if _sprite == null:
		return
	if facing_dir.x < -0.1:
		_sprite.flip_h = true
	elif facing_dir.x > 0.1:
		_sprite.flip_h = false


func _update_sprite_animation(delta: float, is_moving: bool) -> void:
	if _sprite == null:
		return
	if is_moving:
		_anim_time += delta * 11.0
		_sprite.position.y = BASE_SPRITE_Y - absf(sin(_anim_time)) * 3.5
		_sprite.rotation = sin(_anim_time) * 0.045
		_sprite.scale = BASE_SPRITE_SCALE
	else:
		_anim_time += delta * 2.4
		_sprite.position.y = BASE_SPRITE_Y
		_sprite.rotation = 0.0
		var breath: float = 1.0 + sin(_anim_time) * 0.015
		_sprite.scale = Vector2(BASE_SPRITE_SCALE.x, BASE_SPRITE_SCALE.y * breath)


func _build_visual_labels() -> void:
	_name_label = Label.new()
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name_label.position = Vector2(-75.0, 14.0)
	_name_label.size = Vector2(150.0, 20.0)
	_name_label.add_theme_font_size_override("font_size", 12)
	_name_label.add_theme_color_override("font_outline_color", Color(0.05, 0.05, 0.08))
	_name_label.add_theme_constant_override("outline_size", 3)
	add_child(_name_label)

	_bubble_panel = PanelContainer.new()
	_bubble_panel.visible = false
	_bubble_panel.z_index = 20
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.11, 0.12, 0.16, 0.92)
	style.border_width_left = 1
	style.border_width_top = 1
	style.border_width_right = 1
	style.border_width_bottom = 1
	style.border_color = profile.accent_color if profile != null else Color.WHITE
	style.corner_radius_top_left = 6
	style.corner_radius_top_right = 6
	style.corner_radius_bottom_left = 6
	style.corner_radius_bottom_right = 6
	style.content_margin_left = 8
	style.content_margin_right = 8
	style.content_margin_top = 5
	style.content_margin_bottom = 5
	_bubble_panel.add_theme_stylebox_override("panel", style)
	add_child(_bubble_panel)

	_bubble_label = Label.new()
	_bubble_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_bubble_label.custom_minimum_size = Vector2(60.0, 18.0)
	_bubble_label.add_theme_font_size_override("font_size", 12)
	_bubble_label.add_theme_color_override("font_color", Color(0.96, 0.96, 0.94))
	_bubble_panel.add_child(_bubble_label)

	_bubble_timer = Timer.new()
	_bubble_timer.one_shot = true
	_bubble_timer.timeout.connect(_hide_overhead_bubble)
	add_child(_bubble_timer)


func _draw() -> void:
	if profile == null:
		return
	if _sprite != null:
		# 二头身立绘脚底椭圆投影
		draw_set_transform(Vector2(0.0, 8.0), 0.0, Vector2(1.35, 0.55))
		draw_circle(Vector2.ZERO, 12.0, Color(0.0, 0.0, 0.0, 0.28))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		return
	# 脚下阴影
	draw_circle(Vector2(0.0, 12.0), 12.0, Color(0.0, 0.0, 0.0, 0.28))
	# 服装身体
	draw_circle(Vector2(0.0, 2.0), 11.5, profile.outfit_color)
	draw_arc(Vector2(0.0, 2.0), 11.5, 0.0, TAU, 20, profile.accent_color, 1.8)
	# 头部与发色
	draw_circle(Vector2(0.0, -9.0), 9.5, profile.hair_color)
	draw_circle(Vector2(0.0, -7.5) + facing_dir.normalized() * 2.0, 6.5, Color(0.96, 0.88, 0.82))

	# 角色专属特征标识
	match profile.id:
		"bina":
			# 呆毛
			draw_line(Vector2(0.0, -18.0), Vector2(4.0, -24.0), profile.hair_color, 2.0)
		"chizheng":
			# 辅政金纹高领
			draw_rect(Rect2(-6.0, -3.0, 12.0, 4.0), profile.accent_color, true)
		"bit":
			# 科技青色目镜条
			draw_line(Vector2(-5.0, -8.0), Vector2(5.0, -8.0), Color(0.20, 0.92, 1.0), 2.5)
		"vinci":
			# 画家贝雷帽 + 手持小画板
			draw_circle(Vector2(-2.0, -16.0), 6.0, Color(0.92, 0.90, 0.84))
			draw_rect(Rect2(9.0, -4.0, 8.0, 10.0), Color(0.98, 0.97, 0.92), true)
			draw_rect(Rect2(9.0, -4.0, 8.0, 10.0), Color(0.45, 0.32, 0.22), false, 1.2)
