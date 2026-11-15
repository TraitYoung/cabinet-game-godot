extends Node2D

## 主场景装配器：初始化宫城、陛下、首批 4 位内阁成员、自主互动导演与 HUD。

const PalaceWorld = preload("res://scripts/world/palace.gd")
const PlayerRoyal = preload("res://scripts/actors/player.gd")
const CabinetMember = preload("res://scripts/actors/cabinet_member.gd")
const BanterDirector = preload("res://scripts/systems/banter_director.gd")
const GameHUD = preload("res://scripts/ui/hud.gd")

var _palace: PalaceWorld
var _player: PlayerRoyal
var _banter_director: BanterDirector
var _members: Array[CabinetMember] = []
var _roster_timer: float = 0.0


func _ready() -> void:
	_palace = PalaceWorld.new()
	_palace.name = "PalaceWorld"
	add_child(_palace)

	_player = PlayerRoyal.new()
	_player.name = "PlayerRoyal"
	_player.position = _palace.get_waypoint_position("player_spawn")
	_palace.actors_container.add_child(_player)

	for prof in CabinetDatabase.get_all_profiles():
		var member := CabinetMember.new()
		member.setup(prof, _palace)
		_palace.actors_container.add_child(member)
		_members.append(member)

	_banter_director = BanterDirector.new()
	_banter_director.name = "BanterDirector"
	add_child(_banter_director)
	_banter_director.register_members(_members)

	var hud := GameHUD.new()
	hud.name = "GameHUD"
	add_child(hud)

	_push_roster_update()


func _process(delta: float) -> void:
	_roster_timer += delta
	if _roster_timer >= 0.4:
		_roster_timer = 0.0
		_push_roster_update()


func _push_roster_update() -> void:
	var entries: Array = []
	for m in _members:
		if not is_instance_valid(m):
			continue
		entries.append({
			"name": m.profile.display_name,
			"zone": _palace.get_zone_name_for_position(m.global_position),
			"status": m.get_status_label(),
		})
	DialogueBus.minister_roster_updated.emit(entries)
