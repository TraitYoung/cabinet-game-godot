extends Node

## 内阁自主互动导演：当两位大臣走近时触发非阻塞式头顶气泡互怼小剧场，
## 并在空档期随机触发单人自言自语，让宫城时刻保持“活人感”。

const CabinetMember = preload("res://scripts/actors/cabinet_member.gd")

var members: Array[CabinetMember] = []
var _check_timer: float = 4.5
var _solo_timer: float = 7.0
var _active_banter: bool = false


func register_members(p_members: Array[CabinetMember]) -> void:
	members = p_members


func _process(delta: float) -> void:
	if GameClock.is_dialogue_paused or members.is_empty():
		return

	if not _active_banter:
		_check_timer -= delta
		if _check_timer <= 0.0:
			_check_timer = randf_range(6.5, 10.5)
			_try_trigger_pair_banter()

	_solo_timer -= delta
	if _solo_timer <= 0.0:
		_solo_timer = randf_range(8.0, 14.0)
		_try_trigger_solo_thought()


func _try_trigger_pair_banter() -> void:
	var candidates: Array[Array] = []
	for i in range(members.size()):
		for j in range(i + 1, members.size()):
			var a: CabinetMember = members[i]
			var b: CabinetMember = members[j]
			if not is_instance_valid(a) or not is_instance_valid(b):
				continue
			if not a.is_available_for_banter() or not b.is_available_for_banter():
				continue
			if a.global_position.distance_to(b.global_position) <= 230.0:
				candidates.append([a, b])

	if candidates.is_empty():
		return

	var pair: Array = candidates[randi() % candidates.size()]
	var first: CabinetMember = pair[0] as CabinetMember
	var second: CabinetMember = pair[1] as CabinetMember
	var script_lines: Array = CabinetDatabase.get_banter_lines(first.profile.id, second.profile.id)
	if script_lines.is_empty():
		return

	_play_banter_sequence(first, second, script_lines)


func _play_banter_sequence(a: CabinetMember, b: CabinetMember, script_lines: Array) -> void:
	_active_banter = true
	a.set_bantering(true, b.global_position)
	b.set_bantering(true, a.global_position)

	var lookup: Dictionary = {
		a.profile.id: a,
		b.profile.id: b,
	}

	for line_data in script_lines:
		if not is_instance_valid(a) or not is_instance_valid(b):
			break
		if a.state == CabinetMember.State.CHATTING or b.state == CabinetMember.State.CHATTING:
			break
		var speaker_id: String = str(line_data.get("id", ""))
		var text: String = str(line_data.get("text", ""))
		var speaker: CabinetMember = lookup.get(speaker_id, null) as CabinetMember
		if speaker != null:
			speaker.show_overhead_bubble(text, 3.2)
		await get_tree().create_timer(2.8).timeout

	if is_instance_valid(a):
		a.set_bantering(false)
	if is_instance_valid(b):
		b.set_bantering(false)
	_active_banter = false


func _try_trigger_solo_thought() -> void:
	var free_members: Array[CabinetMember] = []
	for m in members:
		if is_instance_valid(m) and m.is_available_for_banter():
			free_members.append(m)
	if free_members.is_empty():
		return
	var picked: CabinetMember = free_members[randi() % free_members.size()]
	if picked.profile.idle_thoughts.is_empty():
		return
	var thought: String = picked.profile.idle_thoughts[randi() % picked.profile.idle_thoughts.size()]
	picked.show_overhead_bubble(thought, 2.8)
