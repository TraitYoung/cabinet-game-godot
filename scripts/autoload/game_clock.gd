extends Node

## 全局日夜节律与操作映射初始化。
## 依据 Axiodrasil BIOS 时段切分：晨启 / 政务 / 午憩 / 夜游 / 宵禁。

signal time_updated(day: int, hour: int, minute: int)
signal time_slot_changed(slot_id: String, slot_label: String)
signal speed_changed(speed_multiplier: float)

const SLOT_MORNING: String = "morning"
const SLOT_FOCUS: String = "focus"
const SLOT_REFUEL: String = "refuel"
const SLOT_FREE_SOUL: String = "free_soul"
const SLOT_SHUTDOWN: String = "shutdown"

const SLOT_LABELS: Dictionary = {
	SLOT_MORNING: "晨启 · 宫门初开",
	SLOT_FOCUS: "政务 · 内阁当值",
	SLOT_REFUEL: "午憩 · 御苑闲话",
	SLOT_FREE_SOUL: "夜游 · 宫灯华彩",
	SLOT_SHUTDOWN: "宵禁 · 巡夜安寝",
}

const SLOT_START_HOURS: Array[int] = [8, 10, 12, 14, 18, 23]

var day: int = 1
var total_minutes: float = 8.0 * 60.0 + 30.0
var speed_multiplier: float = 1.0
var minutes_per_real_second: float = 6.0
var is_dialogue_paused: bool = false

var current_slot: String = SLOT_MORNING
var _last_emitted_minute: int = -1


func _enter_tree() -> void:
	_ensure_input_actions()


func _ready() -> void:
	current_slot = compute_slot(get_hour())
	time_slot_changed.emit(current_slot, get_slot_label())
	time_updated.emit(day, get_hour(), get_minute())


func _process(delta: float) -> void:
	if is_dialogue_paused or speed_multiplier <= 0.0:
		return
	total_minutes += delta * minutes_per_real_second * speed_multiplier
	if total_minutes >= 1440.0:
		total_minutes -= 1440.0
		day += 1

	var hour: int = get_hour()
	var minute: int = get_minute()
	if minute != _last_emitted_minute:
		_last_emitted_minute = minute
		time_updated.emit(day, hour, minute)

	var next_slot: String = compute_slot(hour)
	if next_slot != current_slot:
		current_slot = next_slot
		time_slot_changed.emit(current_slot, get_slot_label())


func get_hour() -> int:
	return int(floor(total_minutes / 60.0)) % 24


func get_minute() -> int:
	return int(floor(total_minutes)) % 60


func get_formatted_time() -> String:
	return "%02d:%02d" % [get_hour(), get_minute()]


func get_slot_label() -> String:
	return str(SLOT_LABELS.get(current_slot, "日常"))


func compute_slot(hour: int) -> String:
	if hour >= 8 and hour < 10:
		return SLOT_MORNING
	if hour >= 12 and hour < 14:
		return SLOT_REFUEL
	if (hour >= 10 and hour < 12) or (hour >= 14 and hour < 18):
		return SLOT_FOCUS
	if hour >= 18 and hour < 23:
		return SLOT_FREE_SOUL
	return SLOT_SHUTDOWN


func set_speed(multiplier: float) -> void:
	speed_multiplier = multiplier
	speed_changed.emit(speed_multiplier)


func cycle_speed() -> void:
	if speed_multiplier <= 0.0:
		set_speed(1.0)
	elif speed_multiplier < 2.5:
		set_speed(3.0)
	else:
		set_speed(0.0)


func skip_to_next_slot() -> void:
	var hour: int = get_hour()
	var target_hour: int = -1
	for start_hour in SLOT_START_HOURS:
		if start_hour > hour:
			target_hour = start_hour
			break
	if target_hour == -1:
		day += 1
		target_hour = 8

	total_minutes = float(target_hour * 60) + 5.0
	_last_emitted_minute = -1
	var next_slot: String = compute_slot(get_hour())
	current_slot = next_slot
	time_updated.emit(day, get_hour(), get_minute())
	time_slot_changed.emit(current_slot, get_slot_label())


func _ensure_input_actions() -> void:
	_bind_keys("move_up", [KEY_W, KEY_UP])
	_bind_keys("move_down", [KEY_S, KEY_DOWN])
	_bind_keys("move_left", [KEY_A, KEY_LEFT])
	_bind_keys("move_right", [KEY_D, KEY_RIGHT])
	_bind_keys("interact", [KEY_E, KEY_SPACE])
	_bind_keys("toggle_speed", [KEY_TAB])
	_bind_keys("cancel", [KEY_ESCAPE])


func _bind_keys(action_name: String, keycodes: Array) -> void:
	if not InputMap.has_action(action_name):
		Input.set_use_accumulated_input(true)
		InputMap.add_action(action_name)
	for code in keycodes:
		var ev: InputEventKey = InputEventKey.new()
		ev.physical_keycode = int(code) as Key
		if not InputMap.action_has_event(action_name, ev):
			InputMap.action_add_event(action_name, ev)
