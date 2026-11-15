extends Node

## 全局对话与提示信号总线。

const CharacterProfile = preload("res://scripts/data/character_profile.gd")

signal character_dialogue_requested(profile: CharacterProfile)
signal council_meeting_requested(title: String, entries: Array)
signal info_dialogue_requested(speaker_name: String, speaker_role: String, accent_color: Color, lines: PackedStringArray)
signal dialogue_closed()
signal world_toast_requested(message: String)
signal minister_roster_updated(entries: Array)
