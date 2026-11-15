extends CanvasLayer

## 顶部时钟/在岗一览 + 底部多模式对话框（一对一话题对话 / 内阁短议 / 设施勘察）。

const CharacterProfile = preload("res://scripts/data/character_profile.gd")

var _time_label: Label
var _slot_label: Label
var _speed_label: Label
var _roster_label: Label
var _toast_panel: PanelContainer
var _toast_label: Label
var _toast_timer: Timer

var _dialogue_panel: PanelContainer
var _avatar_frame: PanelContainer
var _avatar_frame_style: StyleBoxFlat
var _avatar_portrait: TextureRect
var _avatar_badge: ColorRect
var _avatar_char: Label
var _speaker_name_label: Label
var _speaker_role_label: Label
var _dialogue_text_label: Label
var _topic_row: HBoxContainer
var _next_btn: Button
var _close_btn: Button

var _mode: String = ""
var _current_profile: CharacterProfile = null
var _lines: PackedStringArray = PackedStringArray()
var _line_index: int = 0
var _council_entries: Array = []
var _council_index: int = 0


func _ready() -> void:
	_build_ui()
	GameClock.time_updated.connect(_on_time_updated)
	GameClock.time_slot_changed.connect(_on_time_slot_changed)
	GameClock.speed_changed.connect(_on_speed_changed)
	DialogueBus.character_dialogue_requested.connect(_on_character_dialogue_requested)
	DialogueBus.council_meeting_requested.connect(_on_council_meeting_requested)
	DialogueBus.info_dialogue_requested.connect(_on_info_dialogue_requested)
	DialogueBus.world_toast_requested.connect(_show_toast)
	DialogueBus.minister_roster_updated.connect(_on_roster_updated)

	_on_time_updated(GameClock.day, GameClock.get_hour(), GameClock.get_minute())
	_on_time_slot_changed(GameClock.current_slot, GameClock.get_slot_label())
	_on_speed_changed(GameClock.speed_multiplier)


func _unhandled_input(event: InputEvent) -> void:
	if not _dialogue_panel.visible:
		return
	if event.is_action_pressed("cancel"):
		_close_dialogue()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("interact"):
		_advance_dialogue()
		get_viewport().set_input_as_handled()


func _build_ui() -> void:
	# 左上：日历与时辰面板
	var top_left := _make_panel(Color(0.08, 0.09, 0.13, 0.88), Color(0.76, 0.64, 0.34))
	top_left.position = Vector2(18.0, 16.0)
	add_child(top_left)

	var tl_vbox := VBoxContainer.new()
	tl_vbox.add_theme_constant_override("separation", 6)
	top_left.add_child(tl_vbox)

	var row1 := HBoxContainer.new()
	row1.add_theme_constant_override("separation", 12)
	tl_vbox.add_child(row1)

	_time_label = Label.new()
	_time_label.add_theme_font_size_override("font_size", 18)
	_time_label.add_theme_color_override("font_color", Color(1.0, 0.94, 0.78))
	row1.add_child(_time_label)

	_slot_label = Label.new()
	_slot_label.add_theme_font_size_override("font_size", 14)
	_slot_label.add_theme_color_override("font_color", Color(0.84, 0.88, 0.94))
	row1.add_child(_slot_label)

	var row2 := HBoxContainer.new()
	row2.add_theme_constant_override("separation", 6)
	tl_vbox.add_child(row2)

	var btn_pause := _make_small_btn("暂停", func() -> void: GameClock.set_speed(0.0))
	var btn_1x := _make_small_btn("1x", func() -> void: GameClock.set_speed(1.0))
	var btn_3x := _make_small_btn("3x", func() -> void: GameClock.set_speed(3.0))
	var btn_next_slot := _make_small_btn("跳至下一时段 ⏭", func() -> void: GameClock.skip_to_next_slot())
	row2.add_child(btn_pause)
	row2.add_child(btn_1x)
	row2.add_child(btn_3x)
	row2.add_child(btn_next_slot)

	_speed_label = Label.new()
	_speed_label.add_theme_font_size_override("font_size", 12)
	_speed_label.add_theme_color_override("font_color", Color(0.72, 0.76, 0.82))
	row2.add_child(_speed_label)

	# 右上：内阁在岗一览
	var top_right := _make_panel(Color(0.08, 0.09, 0.13, 0.86), Color(0.45, 0.50, 0.62))
	top_right.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	top_right.offset_left = -335.0
	top_right.offset_top = 16.0
	top_right.offset_right = -18.0
	top_right.offset_bottom = 330.0
	add_child(top_right)

	var tr_vbox := VBoxContainer.new()
	tr_vbox.add_theme_constant_override("separation", 4)
	top_right.add_child(tr_vbox)

	var roster_title := Label.new()
	roster_title.text = "内阁诸卿在岗动态"
	roster_title.add_theme_font_size_override("font_size", 14)
	roster_title.add_theme_color_override("font_color", Color(0.95, 0.84, 0.52))
	tr_vbox.add_child(roster_title)

	var roster_scroll := ScrollContainer.new()
	roster_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	roster_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	tr_vbox.add_child(roster_scroll)

	_roster_label = Label.new()
	_roster_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_roster_label.add_theme_font_size_override("font_size", 12)
	_roster_label.add_theme_color_override("font_color", Color(0.88, 0.90, 0.94))
	roster_scroll.add_child(_roster_label)

	var hint_lbl := Label.new()
	hint_lbl.text = "操作：WASD 移动 · E 互动 · Tab 调速"
	hint_lbl.add_theme_font_size_override("font_size", 11)
	hint_lbl.add_theme_color_override("font_color", Color(0.66, 0.70, 0.78))
	tr_vbox.add_child(hint_lbl)

	# 顶部中央：时段切换提示条
	_toast_panel = _make_panel(Color(0.10, 0.11, 0.16, 0.92), Color(0.88, 0.72, 0.36))
	_toast_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_toast_panel.offset_left = -220.0
	_toast_panel.offset_top = 20.0
	_toast_panel.offset_right = 220.0
	_toast_panel.offset_bottom = 58.0
	_toast_panel.visible = false
	add_child(_toast_panel)

	_toast_label = Label.new()
	_toast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast_label.add_theme_font_size_override("font_size", 13)
	_toast_label.add_theme_color_override("font_color", Color(1.0, 0.95, 0.80))
	_toast_panel.add_child(_toast_label)

	_toast_timer = Timer.new()
	_toast_timer.one_shot = true
	_toast_timer.timeout.connect(func() -> void: _toast_panel.visible = false)
	add_child(_toast_timer)

	# 底部中央：对话框
	_dialogue_panel = _make_panel(Color(0.08, 0.09, 0.13, 0.95), Color(0.84, 0.70, 0.38))
	_dialogue_panel.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_dialogue_panel.offset_left = 120.0
	_dialogue_panel.offset_top = -238.0
	_dialogue_panel.offset_right = -120.0
	_dialogue_panel.offset_bottom = -20.0
	_dialogue_panel.visible = false
	add_child(_dialogue_panel)

	var dlg_hbox := HBoxContainer.new()
	dlg_hbox.add_theme_constant_override("separation", 18)
	_dialogue_panel.add_child(dlg_hbox)

	_avatar_frame = PanelContainer.new()
	_avatar_frame.custom_minimum_size = Vector2(138.0, 138.0)
	_avatar_frame.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_avatar_frame_style = StyleBoxFlat.new()
	_avatar_frame_style.bg_color = Color(0.11, 0.12, 0.17, 0.96)
	_avatar_frame_style.border_width_left = 2
	_avatar_frame_style.border_width_top = 2
	_avatar_frame_style.border_width_right = 2
	_avatar_frame_style.border_width_bottom = 2
	_avatar_frame_style.border_color = Color(0.84, 0.70, 0.38)
	_avatar_frame_style.corner_radius_top_left = 10
	_avatar_frame_style.corner_radius_top_right = 10
	_avatar_frame_style.corner_radius_bottom_left = 10
	_avatar_frame_style.corner_radius_bottom_right = 10
	_avatar_frame_style.content_margin_left = 3
	_avatar_frame_style.content_margin_right = 3
	_avatar_frame_style.content_margin_top = 3
	_avatar_frame_style.content_margin_bottom = 3
	_avatar_frame.add_theme_stylebox_override("panel", _avatar_frame_style)
	dlg_hbox.add_child(_avatar_frame)

	var avatar_holder := Control.new()
	avatar_holder.set_anchors_preset(Control.PRESET_FULL_RECT)
	avatar_holder.clip_contents = true
	_avatar_frame.add_child(avatar_holder)

	_avatar_portrait = TextureRect.new()
	_avatar_portrait.set_anchors_preset(Control.PRESET_FULL_RECT)
	_avatar_portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_avatar_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_avatar_portrait.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_avatar_portrait.visible = false
	avatar_holder.add_child(_avatar_portrait)

	_avatar_badge = ColorRect.new()
	_avatar_badge.set_anchors_preset(Control.PRESET_FULL_RECT)
	avatar_holder.add_child(_avatar_badge)

	_avatar_char = Label.new()
	_avatar_char.set_anchors_preset(Control.PRESET_FULL_RECT)
	_avatar_char.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_avatar_char.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_avatar_char.add_theme_font_size_override("font_size", 36)
	_avatar_char.add_theme_color_override("font_color", Color(0.08, 0.08, 0.12))
	_avatar_badge.add_child(_avatar_char)

	var dlg_vbox := VBoxContainer.new()
	dlg_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	dlg_vbox.add_theme_constant_override("separation", 8)
	dlg_hbox.add_child(dlg_vbox)

	var header_row := HBoxContainer.new()
	header_row.add_theme_constant_override("separation", 10)
	dlg_vbox.add_child(header_row)

	_speaker_name_label = Label.new()
	_speaker_name_label.add_theme_font_size_override("font_size", 18)
	header_row.add_child(_speaker_name_label)

	_speaker_role_label = Label.new()
	_speaker_role_label.add_theme_font_size_override("font_size", 13)
	_speaker_role_label.add_theme_color_override("font_color", Color(0.72, 0.76, 0.84))
	header_row.add_child(_speaker_role_label)

	_dialogue_text_label = Label.new()
	_dialogue_text_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_dialogue_text_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_dialogue_text_label.add_theme_font_size_override("font_size", 16)
	_dialogue_text_label.add_theme_color_override("font_color", Color(0.95, 0.95, 0.92))
	dlg_vbox.add_child(_dialogue_text_label)

	var footer_row := HBoxContainer.new()
	footer_row.add_theme_constant_override("separation", 8)
	dlg_vbox.add_child(footer_row)

	_topic_row = HBoxContainer.new()
	_topic_row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_topic_row.add_theme_constant_override("separation", 8)
	footer_row.add_child(_topic_row)

	_next_btn = _make_small_btn("继续 [E]", _advance_dialogue)
	_close_btn = _make_small_btn("告退 [Esc]", _close_dialogue)
	footer_row.add_child(_next_btn)
	footer_row.add_child(_close_btn)


func _on_character_dialogue_requested(profile: CharacterProfile) -> void:
	_mode = "character"
	_current_profile = profile
	GameClock.is_dialogue_paused = true

	var slot_lines: PackedStringArray = profile.greetings_by_slot.get(
		GameClock.current_slot,
		PackedStringArray(["陛下安好。"])
	)
	_lines = slot_lines
	_line_index = 0
	var tier_label: String = "一等" if profile.tier <= 1 else ("二等" if profile.tier == 2 else "三等")
	var role_text: String = "%s · %s" % [tier_label, profile.role_title]
	_apply_speaker_header(
		profile.display_name,
		role_text,
		profile.badge_text,
		profile.accent_color,
		profile.portrait_path
	)
	_rebuild_topic_buttons(profile)
	_refresh_dialogue_text()
	_dialogue_panel.visible = true


func _on_council_meeting_requested(_title: String, entries: Array) -> void:
	_mode = "council"
	_current_profile = null
	_council_entries = entries
	_council_index = 0
	GameClock.is_dialogue_paused = true
	_clear_topic_buttons()
	_refresh_council_entry()
	_dialogue_panel.visible = true


func _on_info_dialogue_requested(speaker_name: String, speaker_role: String, accent_color: Color, lines: PackedStringArray) -> void:
	_mode = "info"
	_current_profile = null
	_lines = lines
	_line_index = 0
	GameClock.is_dialogue_paused = true
	_clear_topic_buttons()
	_apply_speaker_header(speaker_name, speaker_role, "建", accent_color)
	_refresh_dialogue_text()
	_dialogue_panel.visible = true


func _advance_dialogue() -> void:
	if _mode == "council":
		if _council_index + 1 < _council_entries.size():
			_council_index += 1
			_refresh_council_entry()
		else:
			_close_dialogue()
		return

	if _line_index + 1 < _lines.size():
		_line_index += 1
		_refresh_dialogue_text()
	elif _mode == "info":
		_close_dialogue()


func _refresh_dialogue_text() -> void:
	if _lines.is_empty():
		_dialogue_text_label.text = ""
	else:
		_dialogue_text_label.text = _lines[clampi(_line_index, 0, _lines.size() - 1)]
	_next_btn.visible = (_line_index + 1 < _lines.size()) or (_mode == "info")
	_next_btn.text = "继续 [E]" if _line_index + 1 < _lines.size() else "明白 [E]"


func _refresh_council_entry() -> void:
	if _council_entries.is_empty():
		_close_dialogue()
		return
	var entry: Dictionary = _council_entries[_council_index]
	var speaker_id: String = str(entry.get("id", ""))
	var prof: CharacterProfile = CabinetDatabase.get_profile(speaker_id)
	var badge: String = prof.badge_text if prof != null else "议"
	var p_path: String = prof.portrait_path if prof != null else ""
	_apply_speaker_header(
		str(entry.get("name", "内阁")),
		str(entry.get("role", "")),
		badge,
		entry.get("color", Color.GOLD) as Color,
		p_path
	)
	_dialogue_text_label.text = str(entry.get("text", ""))
	_next_btn.visible = true
	_next_btn.text = "下一位 [E]" if _council_index + 1 < _council_entries.size() else "散朝 [E]"


func _apply_speaker_header(s_name: String, s_role: String, badge: String, color: Color, portrait_path: String = "") -> void:
	_speaker_name_label.text = s_name
	_speaker_name_label.add_theme_color_override("font_color", color.lightened(0.2))
	_speaker_role_label.text = s_role
	_avatar_frame_style.border_color = color

	var portrait_tex: Texture2D = null
	if not portrait_path.is_empty() and ResourceLoader.exists(portrait_path):
		portrait_tex = load(portrait_path) as Texture2D

	if portrait_tex != null:
		_avatar_portrait.texture = portrait_tex
		_avatar_portrait.visible = true
		_avatar_badge.visible = false
	else:
		_avatar_portrait.texture = null
		_avatar_portrait.visible = false
		_avatar_badge.visible = true
		_avatar_badge.color = color
		_avatar_char.text = badge


func _rebuild_topic_buttons(profile: CharacterProfile) -> void:
	_clear_topic_buttons()
	for topic_key in profile.topic_replies.keys():
		var topic_name: String = str(topic_key)
		var btn := _make_small_btn("💬 " + topic_name, func() -> void:
			_lines = profile.topic_replies[topic_name]
			_line_index = 0
			_refresh_dialogue_text()
		)
		_topic_row.add_child(btn)


func _clear_topic_buttons() -> void:
	for child in _topic_row.get_children():
		child.queue_free()


func _close_dialogue() -> void:
	_dialogue_panel.visible = false
	GameClock.is_dialogue_paused = false
	DialogueBus.dialogue_closed.emit()


func _on_time_updated(day: int, _hour: int, _minute: int) -> void:
	_time_label.text = "第 %d 天  %s" % [day, GameClock.get_formatted_time()]


func _on_time_slot_changed(_slot_id: String, slot_label: String) -> void:
	_slot_label.text = slot_label
	_show_toast("时辰流转：%s" % slot_label)


func _on_speed_changed(mult: float) -> void:
	if mult <= 0.0:
		_speed_label.text = "[已暂停]"
	else:
		_speed_label.text = "[%dx]" % int(mult)


func _on_roster_updated(entries: Array) -> void:
	var lines: PackedStringArray = PackedStringArray()
	for item in entries:
		lines.append("• %s — %s（%s）" % [str(item["name"]), str(item["zone"]), str(item["status"])])
	_roster_label.text = "\n".join(lines)


func _show_toast(message: String) -> void:
	if _toast_panel == null:
		return
	_toast_label.text = message
	_toast_panel.visible = true
	_toast_timer.start(3.2)


func _make_panel(bg: Color, border: Color) -> PanelContainer:
	var panel := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.border_width_left = 2
	style.border_width_top = 2
	style.border_width_right = 2
	style.border_width_bottom = 2
	style.corner_radius_top_left = 8
	style.corner_radius_top_right = 8
	style.corner_radius_bottom_left = 8
	style.corner_radius_bottom_right = 8
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 10
	style.content_margin_bottom = 10
	panel.add_theme_stylebox_override("panel", style)
	return panel


func _make_small_btn(label_text: String, on_click: Callable) -> Button:
	var btn := Button.new()
	btn.text = label_text
	btn.focus_mode = Control.FOCUS_NONE
	btn.add_theme_font_size_override("font_size", 12)
	btn.pressed.connect(on_click)
	return btn
