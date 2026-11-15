extends Resource

## 通用内阁大臣数据配置。后续新增内阁成员只需补充本资源数据，无需复制脚本。

@export var id: String = ""
@export var display_name: String = ""
@export var full_name: String = ""
@export var role_title: String = ""
@export var tier: int = 1
@export var personality_summary: String = ""
@export var badge_text: String = ""

@export var accent_color: Color = Color.WHITE
@export var hair_color: Color = Color.GRAY
@export var outfit_color: Color = Color.SLATE_GRAY

@export var portrait_path: String = ""
@export var chibi_sprite_path: String = ""

## 时段 -> 宫城 Marker2D 名称映射
@export var schedule_waypoints: Dictionary = {}

## 时段 -> 初始问候语（PackedStringArray）
@export var greetings_by_slot: Dictionary = {}

## 话题按钮 -> 回复列表（topic_label -> PackedStringArray）
@export var topic_replies: Dictionary = {}

## 独自待机时的头顶随机气泡
@export var idle_thoughts: PackedStringArray = PackedStringArray()
