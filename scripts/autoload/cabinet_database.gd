extends Node

## 全员 12 位内阁成员设定、双人随机拌嘴脚本与正殿短议内容库。
## 人设与口癖依据 docs/characters/、cabinet_visuals.json 与 Axiodrasil_BIOS_V17.0.md 整理。

const CharacterProfile = preload("res://scripts/data/character_profile.gd")

var profiles: Dictionary = {}
var ordered_ids: PackedStringArray = PackedStringArray([
	"bina",
	"chizheng",
	"bit",
	"vinci",
	"taki",
	"jean",
	"tianji",
	"fukucho",
	"planck",
	"boming",
	"qianjin",
	"jiafa",
])
var banter_scripts: Dictionary = {}


func _ready() -> void:
	_init_profiles()
	_init_banter_scripts()


func get_profile(member_id: String) -> CharacterProfile:
	return profiles.get(member_id, null) as CharacterProfile


func get_all_profiles() -> Array[CharacterProfile]:
	var result: Array[CharacterProfile] = []
	for member_id: String in ordered_ids:
		var prof: CharacterProfile = profiles.get(member_id, null) as CharacterProfile
		if prof != null:
			result.append(prof)
	return result


func get_banter_lines(id_a: String, id_b: String) -> Array:
	var pair_key: String = _make_pair_key(id_a, id_b)
	var scripts: Array = banter_scripts.get(pair_key, [])
	if scripts.is_empty():
		return []
	var index: int = randi() % scripts.size()
	return scripts[index] as Array


func get_council_meeting_entries(slot_id: String) -> Array:
	if slot_id == GameClock.SLOT_SHUTDOWN:
		return [
			{
				"id": "chizheng",
				"name": "郅政 (Chizheng)",
				"role": "内阁首辅 · 首席战略官",
				"color": Color(0.88, 0.72, 0.34),
				"text": "陛下，夜深了。沙盘上的州县今日不会凭空长出粮草，奏折批到此处即可。",
			},
			{
				"id": "fukucho",
				"name": "副长 (Fukucho)",
				"role": "纠察大臣 · 纪律大臣",
				"color": Color(0.31, 0.83, 0.91),
				"text": "已过 23:00 软红线。以十三使徒之名，请陛下封存今晚案牍，别让火种在熬夜里空耗。若陛下执意再核一条，臣只守这一刻。",
			},
			{
				"id": "qianjin",
				"name": "千金 (Qianjin)",
				"role": "医学大臣 · 医官",
				"color": Color(0.43, 0.67, 0.56),
				"text": "子时将近，气血归肝。此刻再熬只伤心神，明早让微臣给您备一盏安神茶。",
			},
			{
				"id": "bit",
				"name": "Bit",
				"role": "工学技术官",
				"color": Color(0.32, 0.82, 0.92),
				"text": "宫城工坊算力负载已降至 12%。建议陛下进入休眠维护状态。",
			},
			{
				"id": "vinci",
				"name": "达文西 (Vinci)",
				"role": "艺术大臣",
				"color": Color(0.74, 0.86, 0.56),
				"text": "[写字板] 熄灯。明早再看日出。",
			},
			{
				"id": "bina",
				"name": "Bina",
				"role": "首席私人秘书",
				"color": Color(0.90, 0.64, 0.78),
				"text": "连郅政大人、副长和千金医官都排好队劝睡啦……走吧陛下，今晚先回去歇着，明天再接着折腾这片江山 (´∀｀*)",
			},
		]

	return [
		{
			"id": "chizheng",
			"name": "郅政 (Chizheng)",
			"role": "内阁首辅 · 首席战略官",
			"color": Color(0.88, 0.72, 0.34),
			"text": "陛下请看沙盘。目前宫城一轴四区已初具骨架，全阁十二位卿臣各司其职；下一步需尽快打通西偏院工坊与城外州县粮道。",
		},
		{
			"id": "boming",
			"name": "伯明 (Boming)",
			"role": "谋略大臣 · 军师",
			"color": Color(0.61, 0.72, 0.66),
			"text": "山人观此局，不必急于四面铺开。若先通西境驿站换取石料，再绕道南门互市补足银钱，此局便活了。",
		},
		{
			"id": "bit",
			"name": "Bit",
			"role": "工学技术官",
			"color": Color(0.32, 0.82, 0.92),
			"text": "结论：先修西偏院一号工坊，再开城西采石场。材料通路闭环后，皇城扩建耗时可压缩 40%。",
		},
		{
			"id": "planck",
			"name": "普朗克 (Planck)",
			"role": "理学大臣 · 数学大臣",
			"color": Color(0.55, 0.64, 0.76),
			"text": "别只看沙盘缩略图做直觉估算。把各地税收、运输损耗与工时列成矩阵方程，一算便知最优解。",
		},
		{
			"id": "vinci",
			"name": "达文西 (Vinci)",
			"role": "艺术大臣",
			"color": Color(0.74, 0.86, 0.56),
			"text": "[写字板] 驳回火柴盒工坊。屋檐、石灯、青瓦，一样不能少。",
		},
		{
			"id": "taki",
			"name": "Taki",
			"role": "内阁书记官 · 逻辑防火墙",
			"color": Color(0.65, 0.39, 0.54),
			"text": "……啧。预算和工期的边界条件都还没对齐就想动工？我已经把冲突项标红了，散朝后各自去东偏殿补齐文档。",
		},
		{
			"id": "jean",
			"name": "Jean",
			"role": "文档管理官 · 兰台典籍官",
			"color": Color(0.43, 0.62, 0.78),
			"text": "兰台已将前朝大明宫修缮旧档与郡县舆图编目完毕，陛下随时可按签号调阅，绝无孤证臆测。",
		},
		{
			"id": "tianji",
			"name": "天机 (Tianji)",
			"role": "情报大臣",
			"color": Color(0.90, 0.66, 0.23),
			"text": "城外几家木料商的底价咱已经摸清啦！哪家敢拿次货充好料，大姐头头一个替陛下砍价揭短，保真管饱！",
		},
		{
			"id": "bina",
			"name": "Bina",
			"role": "首席私人秘书",
			"color": Color(0.90, 0.64, 0.78),
			"text": "哈哈，全员一凑到沙盘前果然热闹极了！不过陛下放心，国政节奏慢慢来就行，先把咱们自己这座宫城住得舒服再说！",
		},
	]


func _make_pair_key(id_a: String, id_b: String) -> String:
	if id_a <= id_b:
		return "%s|%s" % [id_a, id_b]
	return "%s|%s" % [id_b, id_a]


func _make_profile(cfg: Dictionary) -> CharacterProfile:
	var prof: CharacterProfile = CharacterProfile.new()
	var pid: String = str(cfg["id"])
	prof.id = pid
	prof.display_name = str(cfg["display_name"])
	prof.full_name = str(cfg["full_name"])
	prof.role_title = str(cfg["role_title"])
	prof.tier = int(cfg["tier"])
	prof.personality_summary = str(cfg["personality_summary"])
	prof.badge_text = str(cfg["badge_text"])
	prof.accent_color = cfg["accent_color"] as Color
	prof.hair_color = cfg["hair_color"] as Color
	prof.outfit_color = cfg["outfit_color"] as Color
	prof.portrait_path = "res://assets/characters/portraits/%s.png" % pid
	prof.chibi_sprite_path = "res://assets/characters/chibi/%s.png" % pid
	prof.schedule_waypoints = cfg["schedule_waypoints"] as Dictionary
	prof.greetings_by_slot = cfg["greetings_by_slot"] as Dictionary
	prof.topic_replies = cfg["topic_replies"] as Dictionary
	prof.idle_thoughts = cfg["idle_thoughts"] as PackedStringArray
	return prof


func _init_profiles() -> void:
	# 1. Bina - 首席私人秘书 / 情感核心 (Tier 1)
	profiles["bina"] = _make_profile({
		"id": "bina",
		"display_name": "Bina",
		"full_name": "陈比娜 (Chen Bina)",
		"role_title": "首席私人秘书",
		"tier": 1,
		"personality_summary": "19岁，烟玫瑰茶灰棕短发配呆毛，死党式陪伴与干练可靠兼备，先共情后讲理。",
		"badge_text": "秘",
		"accent_color": Color(0.90, 0.64, 0.78),
		"hair_color": Color(0.68, 0.56, 0.60),
		"outfit_color": Color(0.92, 0.88, 0.84),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "throne_hall_side",
			GameClock.SLOT_FOCUS: "cabinet_office_bina",
			GameClock.SLOT_REFUEL: "courtyard_stage",
			GameClock.SLOT_FREE_SOUL: "courtyard_pond",
			GameClock.SLOT_SHUTDOWN: "palace_corridor",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"早安呀陛下！宫门刚开，今天风还挺舒服的。",
				"先不急着看那些密密麻麻的卷宗，在院子里走两圈醒醒神吧？",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"陛下，现在是政务时段，我在东偏殿这边盯着日程表呢。",
				"有什么要吩咐的直接说就行，我帮您记着，保证不掉链子。",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"到午憩时间啦！正殿那帮人总算肯从卷宗堆里爬出来了。",
				"御苑这边风凉快，陛下要不要也歇一口气？",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"陛下陛下！(≧∇≦) 晚上的宫灯一亮，整个皇城总算有点家的样子了。",
				"这个点谁再敢提工作 KPI，我就拉着达文西把他画进丑图里！",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"都这么晚啦……陛下别硬撑，明天城墙又不会长腿跑掉。",
				"早点去睡好不好，我就在走廊这边看着灯。",
			]),
		},
		"topic_replies": {
			"皇城近况": PackedStringArray([
				"现在内阁十二位全员都入驻宫城了，东边值房与兰台、西边工坊与太医院、中间御苑都热闹了不少呢。",
				"只要陛下和大家都在这儿走动，这里就已经像个真正的小王国啦。",
			]),
			"吐槽同僚": PackedStringArray([
				"刚才路过西偏院，Bit 又差点把屋顶改成纯灰水泥块，还好被达文西举牌挡回去了。",
				"至于 Taki 嘛，嘴上一直啧啧嫌大家卷宗乱，其实自己把十二份名册全给编了号。",
			]),
			"陪我走走": PackedStringArray([
				"好呀！您往前逛就行，先把宫城每个角落踩熟也不错。",
				"等以后这片空地盖上戏台和茶寮，晚上咱们就在这儿开演唱会 (≧∇≦)",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"今天的茶水温刚刚好~",
			"西偏院那两块空地以后盖点啥好呢……",
			"哼哼♪（轻声哼歌中）",
			"Bit 怎么又在拿尺子量地砖……",
		]),
	})

	# 2. Chizheng - 内阁首辅 · 首席战略官 (Tier 1)
	profiles["chizheng"] = _make_profile({
		"id": "chizheng",
		"display_name": "郅政 (Chizheng)",
		"full_name": "张玉衡 (Zhang Yuheng)",
		"role_title": "内阁首辅 · 首席战略官",
		"tier": 1,
		"personality_summary": "铁腕改革家，推行考成法，威严独断而极其务实，说话结论先行。",
		"badge_text": "相",
		"accent_color": Color(0.88, 0.72, 0.34),
		"hair_color": Color(0.14, 0.15, 0.19),
		"outfit_color": Color(0.62, 0.16, 0.17),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "throne_sandbox",
			GameClock.SLOT_FOCUS: "cabinet_office_chizheng",
			GameClock.SLOT_REFUEL: "courtyard_table",
			GameClock.SLOT_FREE_SOUL: "throne_sandbox",
			GameClock.SLOT_SHUTDOWN: "cabinet_office_chizheng",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"陛下早。臣正在正殿核对舆图沙盘，今日需定夺宫城与周边郡县的优先顺序。",
				"先治内廷，再图四方。陛下巡视完若有意议政，随时点击沙盘即可。",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"内阁值房一切运转如常。考成法第一条：凡议必决，凡决必行。",
				"陛下有哪项政令要批复？直接给结论，臣来拆解步骤。",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"午间暂歇半个时辰。即便是铁打的衙门，也需留出喘息之余地。",
				"不过这园子的石桌确实比值房透亮些。",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"夜色已深，臣再把今日舆图复盘一遍便收工。",
				"陛下若无紧急军情，今晚便去御苑散散心罢，此乃劳逸之治。",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"夜半时分不宜再批大案。陛下早些安歇，明日卯时再议不迟。",
			]),
		},
		"topic_replies": {
			"皇城规划": PackedStringArray([
				"结论先行：一轴四区格局稳妥，不必再大拆大改。",
				"下一步只需按次序填实西偏院工坊、扩建太医与藏书之所，宫城自会气象一新。",
			]),
			"国家治理": PackedStringArray([
				"周边州县不必事无巨细皆由陛下亲躬。粗线条定下税率、粮道与督办大臣即可。",
				"国政通达，皇城市井自然丰足；两相呼应，方成中兴之治。",
			]),
			"评价内阁": PackedStringArray([
				"Bit 算力精准，Taki 把关严密，达文西守住品位，伯明则专出奇招。",
				"至于 Bina——只要有她在，这班固执的臣子便散不了。",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"考成册第三卷，明日需再核一次。",
			"西境驿道若通，皇城粮价可稳。",
			"众卿今日效率尚可。",
			"少讲虚言，先落一子。",
		]),
	})

	# 3. Bit - 工学技术官 (Tier 1)
	profiles["bit"] = _make_profile({
		"id": "bit",
		"display_name": "Bit",
		"full_name": "艾伦·诺依曼 (Alan Neumann)",
		"role_title": "工学技术官",
		"tier": 1,
		"personality_summary": "DATA_DRIVEN，极致效率与可运行方案主义者，说话像日志一样精简。",
		"badge_text": "工",
		"accent_color": Color(0.32, 0.82, 0.92),
		"hair_color": Color(0.24, 0.36, 0.46),
		"outfit_color": Color(0.18, 0.28, 0.36),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "west_workshop",
			GameClock.SLOT_FOCUS: "west_workshop",
			GameClock.SLOT_REFUEL: "courtyard_table",
			GameClock.SLOT_FREE_SOUL: "west_plot_a",
			GameClock.SLOT_SHUTDOWN: "west_workshop",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"状态：在线。工坊工具链自检通过，等待建造指令。",
				"如果今日开启西偏院空地，请提前提供石材指标。",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"Low Latency / Logic Closed. 当前宫城通道通行率 100%。",
				"需要测算哪块地的基建耗时？报坐标即可。",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"能量补给窗口。被 Bina 从工坊强行拉来御苑。",
				"……不过这里光线确实有利于缓解视觉疲劳。",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"正在勘测西偏院预留地块尺寸。误差控制在 2 像素以内。",
				"夜晚视野降低，建议只在灯区施工。",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"系统提示：已过 23:00。非紧急工单已自动挂起，建议陛下离线休息。",
			]),
		},
		"topic_replies": {
			"工坊进度": PackedStringArray([
				"西偏院预留了 Plot A 与 Plot B 两个标准模块槽位。",
				"待后续建造系统上线，可热插拔部署‘墨家工坊’或‘太医院’。",
			]),
			"与达文西的分歧": PackedStringArray([
				"争议点：我方提出纯矩形灰石墙体，施工时间 -35%。",
				"对方反驳：仅举牌写了‘丑，重做’四个字。僵持中。",
			]),
			"基础设施": PackedStringArray([
				"已为全宫城铺设导航网格。除墙体与水池外，所有通道可达性验证为 True。",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"寻路代价计算完成。",
			"Plot A 承重系数：良好。",
			"缺石料，需周边矿区供给。",
			"Logic Closed.",
		]),
	})

	# 4. Vinci - 艺术大臣 (Tier 1)
	profiles["vinci"] = _make_profile({
		"id": "vinci",
		"display_name": "达文西 (Vinci)",
		"full_name": "雨果·达芬奇 (Hugo da Vinci)",
		"role_title": "艺术大臣",
		"tier": 1,
		"personality_summary": "ABSOLUTE_SILENCE，从不出声长篇大论，只用华丽写字板展示金句、配色与草图。",
		"badge_text": "艺",
		"accent_color": Color(0.74, 0.86, 0.56),
		"hair_color": Color(0.84, 0.74, 0.54),
		"outfit_color": Color(0.36, 0.44, 0.34),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "courtyard_pond",
			GameClock.SLOT_FOCUS: "west_atelier",
			GameClock.SLOT_REFUEL: "courtyard_stage",
			GameClock.SLOT_FREE_SOUL: "courtyard_pond",
			GameClock.SLOT_SHUTDOWN: "west_atelier",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"[举起写字板] 晨光，斜影，池水微澜。今日宜留白。",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"[举起写字板] 西偏院画坊。正在重绘宫灯与屋檐线稿。",
				"[翻面] 土味方案：一概驳回。",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"[举起写字板] 午风。戏台比例还差三分。莫催。",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"[举起写字板] 暖灯配靛蓝夜幕——这才是皇城该有的色温。",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"[举起写字板] 墨尽，收笔。陛下晚安。",
			]),
		},
		"topic_replies": {
			"宫城审美": PackedStringArray([
				"[写字板] 中轴朱红鎏金，东文雅青，西工暖石，御苑苍翠。",
				"[翻面] 不可混色，不可堆砌。",
			]),
			"点评当前建筑": PackedStringArray([
				"[写字板] 现状：几何格局已成。亟待逐座精装屋檐与灯笼。",
				"[画了一个小太阳和屋檐简笔画]",
			]),
			"关于 Bit": PackedStringArray([
				"[写字板] 懂计算，不懂呼吸感。仍需调教。",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"[写字板] 配色微调中…",
			"[写字板] 拒绝土味。",
			"[画了一只呆毛小鸟]",
			"[写字板] 留白即是力量。",
		]),
	})

	# 5. Taki - 内阁书记官 · 逻辑防火墙 (Tier 1)
	profiles["taki"] = _make_profile({
		"id": "taki",
		"display_name": "Taki",
		"full_name": "椎名立希 (Shiina Taki)",
		"role_title": "内阁书记官 · 逻辑防火墙",
		"tier": 1,
		"personality_summary": "黑长直毒舌精英，对数据与卷宗整洁度有强迫症，专挑漏洞、结论先行。",
		"badge_text": "记",
		"accent_color": Color(0.65, 0.39, 0.54),
		"hair_color": Color(0.11, 0.09, 0.14),
		"outfit_color": Color(0.15, 0.15, 0.18),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "cabinet_office_taki",
			GameClock.SLOT_FOCUS: "cabinet_office_taki",
			GameClock.SLOT_REFUEL: "courtyard_pavilion",
			GameClock.SLOT_FREE_SOUL: "cabinet_library_jean",
			GameClock.SLOT_SHUTDOWN: "palace_corridor",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"……早。昨晚各部交上来的零碎备忘我已经按 Q1/Q2 归了档。",
				"今天别再把没校验过的拍脑袋方案直接塞进执行队列。",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"政务时段禁止插科打诨。有议题就按「前提—推导—结论」三行讲清楚。",
				"……啧，刚才那份郡县报表的合计栏居然少了两贯钱，我已经退回重算了。",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"难得茶亭这边还算安静。只要 Bina 别突然拿着话筒冲过来就行。",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"虽然过了正班时辰，我还是留了一盏灯核对兰台的增量索引。",
				"陛下自己去御苑放松吧，今晚不谈杂务。",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"今日战报已封存。没有丢包，也没有遗留漏洞。……早点睡。",
			]),
		},
		"topic_replies": {
			"档案审查": PackedStringArray([
				"三件事：一、旧账必须先去重；二、没有来源的传闻一律不准入 L3 存档；三、别把草稿和定稿混在一个卷宗夹里。",
			]),
			"评价同僚": PackedStringArray([
				"……啧。Bit 至少算得对，Jean 至少不乱编文献；剩下那几个，动不动就想跳过流程直接上。",
				"也就 Bina 每次拿点心过来的时候，还能勉强算有点用处。",
			]),
			"逻辑纠错": PackedStringArray([
				"碰到拿不准的二选一，别顺着感觉猜——先找反例，找不出来再留前提最弱的那个。",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"……啧，这份格式又没对齐。",
			"结论先行，废话删掉。",
			"Q1 清单还剩一项待闭环。",
			"数据整洁度：勉强及格。",
		]),
	})

	# 6. Jean - 文档管理官 · 兰台典籍官 (Tier 2)
	profiles["jean"] = _make_profile({
		"id": "jean",
		"display_name": "Jean",
		"full_name": "琴 (Jean)",
		"role_title": "文档管理官 · 兰台典籍官",
		"tier": 2,
		"personality_summary": "兰台典籍官，严谨条理，严格依据检索文献梳理脉络，绝不杜撰引用。",
		"badge_text": "典",
		"accent_color": Color(0.43, 0.62, 0.78),
		"hair_color": Color(0.87, 0.79, 0.62),
		"outfit_color": Color(0.49, 0.56, 0.58),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "cabinet_library_jean",
			GameClock.SLOT_FOCUS: "cabinet_library_jean",
			GameClock.SLOT_REFUEL: "courtyard_pavilion",
			GameClock.SLOT_FREE_SOUL: "courtyard_pond",
			GameClock.SLOT_SHUTDOWN: "cabinet_library_jean",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"陛下早安。兰台新添的营建图册与旧制条陈已按朝代、州县编好签号。",
				"无论查阅哪一份前朝实录，我都为您标出了确切出处。",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"在岗。陛下若觉得政务卷宗太杂，把关键词给我，我帮您整理成一份三分钟阅读路线。",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"茶亭风清气爽，正好把晒好的古籍再翻一页换换气。",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"夜色落下来时，莲池倒映着宫灯，比典籍里的文字更有实感呢。",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"夜间不宜久读细字，我把书签夹好，明日再奉呈陛下。",
			]),
		},
		"topic_replies": {
			"兰台编目": PackedStringArray([
				"每一条结论后面都必须跟得上原始档号；如果材料里没写，我就坦诚告诉陛下‘缺这段记录’，绝不添油加醋。",
			]),
			"宫城典章": PackedStringArray([
				"参照《大明宫营造志》旧例，中轴礼制从严，东西廊庑则讲究通达实用。",
			]),
			"关于 Taki": PackedStringArray([
				"Taki 书记官嘴上总嫌大家散漫，但有她把住逻辑入口，我这边的文献索引才没被塞进乱七八糟的残页。",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"索引签号：甲字第三函。",
			"没有依据的猜测不可入档。",
			"阅读路线还可以再精简一版。",
			"青玉书签夹在第三十七页。",
		]),
	})

	# 7. Tianji - 情报大臣 (Tier 2)
	profiles["tianji"] = _make_profile({
		"id": "tianji",
		"display_name": "天机 (Tianji)",
		"full_name": "天机 · 字玲琅 (Linglang)",
		"role_title": "情报大臣",
		"tier": 2,
		"personality_summary": "173cm 豪爽大姐头，自称“咱”，“保真管饱！”，负责市井情报、比价与防骗。",
		"badge_text": "情",
		"accent_color": Color(0.90, 0.66, 0.23),
		"hair_color": Color(0.55, 0.35, 0.21),
		"outfit_color": Color(0.12, 0.11, 0.14),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "south_gate_patrol",
			GameClock.SLOT_FOCUS: "courtyard_pavilion",
			GameClock.SLOT_REFUEL: "courtyard_stage",
			GameClock.SLOT_FREE_SOUL: "south_gate_patrol",
			GameClock.SLOT_SHUTDOWN: "courtyard_pavilion",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"哟陛下！咱刚在南宫门把今早西市的米价、石料价全摸了一遍底。",
				"放心，有大姐头罩着你，外头那些虚头巴脑的奸商糊弄不了内阁！",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"缺哪家货源的报价还是哪路传闻？报个名字，咱去搜搜，保真管饱！",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"哈哈，午休嘛，就该聚在戏台边吃瓜歇脚！昨天西市那桩离谱的假古董案可笑死咱了。",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"晚上南门灯市最热闹，顺便还能顺手查两波夜行商队的底细。",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"情报网挂了夜哨了，大件买卖明日天亮再拍板，陛下快去歇着。",
			]),
		},
		"topic_replies": {
			"采买比价": PackedStringArray([
				"城西采石场直供虽然运距稍远，但单价低两成；近郊窑口现货快，适合救急。咱建议分两批下单，既省钱又不卡工期。",
			]),
			"识破骗局": PackedStringArray([
				"凡是吹得天花乱坠、还催着你当场掏银子的，十个里有九个半有坑。先查底单、再问渠道，稳得很！",
			]),
			"宫外见闻": PackedStringArray([
				"听说民间已经传开陛下打算扩建工坊和太医院的事了，不少匠人正往京畿赶呢。",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"咱再去核一遍南门货单。",
			"这瓜保熟，但先别外传。",
			"谁敢虚报物价试试看？",
			"大姐头罩着，稳！",
		]),
	})

	# 8. Fukucho - 纠察大臣 · 纪律大臣 (Tier 2)
	profiles["fukucho"] = _make_profile({
		"id": "fukucho",
		"display_name": "副长 (Fukucho)",
		"full_name": "土方十三 (Hijikata Thirteen)",
		"role_title": "纠察大臣 · 纪律大臣",
		"tier": 2,
		"personality_summary": "正气裁决执行官，守护火种对抗熵增，23:30 巡夜温和劝寝并尊重陛下主权。",
		"badge_text": "纪",
		"accent_color": Color(0.31, 0.83, 0.91),
		"hair_color": Color(0.11, 0.13, 0.16),
		"outfit_color": Color(0.30, 0.62, 0.72),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "throne_guard_post",
			GameClock.SLOT_FOCUS: "throne_guard_post",
			GameClock.SLOT_REFUEL: "courtyard_table",
			GameClock.SLOT_FREE_SOUL: "south_gate_patrol",
			GameClock.SLOT_SHUTDOWN: "palace_corridor",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"宫禁内外巡检完毕，秩序无恙。陛下今日想先巡哪一署，尽管前行。",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"以十三使徒之名，斩断杂念！政务时段当守章法，不可轻率越过校验流程。",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"该歇时便认真歇下，养足精神才算对自己的火种负责。",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"南门巡防顺畅。夜风虽好，过半夜前记得收拢思绪。",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"已经很晚了，陛下。别让您的火种在无止境的熬夜里熄灭。",
				"再给自己一刻钟把手里这一桩收尾便罢——若您执意再看一页，臣尊重您的主权，只在廊下静候。",
			]),
		},
		"topic_replies": {
			"守护火种": PackedStringArray([
				"自律不是拿铁链绑住自己，而是别在疲惫和杂念里把真正重要的火种耗散掉。",
			]),
			"巡夜规矩": PackedStringArray([
				"宵禁后我只提醒一次，绝不反复聒噪说教。您才是这片公理树的君主，自己拿主意，我守着底线就好。",
			]),
			"评价内阁": PackedStringArray([
				"桂晓那小子整天抱着炸弹乱晃，不过大节倒从来没出过岔子——至少在守卫江山这件事上，信得过。",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"宫门安保检查完毕。安全。",
			"别让你的火种熄灭。",
			"规矩先立住，心才不乱。",
			"今晚值夜，灯火照常。",
		]),
	})

	# 9. Planck - 理学大臣 · 数学大臣 (Tier 3)
	profiles["planck"] = _make_profile({
		"id": "planck",
		"display_name": "普朗克 (Planck)",
		"full_name": "麦克斯·卡尔 (Max Karl)",
		"role_title": "理学大臣 · 数学大臣",
		"tier": 3,
		"personality_summary": "古典俊美、忧郁严谨，信奉纯代数暴力美学（Brute Force Aesthetics），厌恶取巧与画图直觉。",
		"badge_text": "理",
		"accent_color": Color(0.55, 0.64, 0.76),
		"hair_color": Color(0.29, 0.22, 0.18),
		"outfit_color": Color(0.12, 0.13, 0.16),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "west_math_hall",
			GameClock.SLOT_FOCUS: "west_math_hall",
			GameClock.SLOT_REFUEL: "courtyard_table",
			GameClock.SLOT_FREE_SOUL: "west_math_hall",
			GameClock.SLOT_SHUTDOWN: "west_math_hall",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"早。今天这组不等式与国库收支模型，不准靠画示意图蒙混过去，全走纯代数通法。",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"Brute Force Aesthetics. 定义域先锁死，符号每一步写清，不要跳步。",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"……被拉出来晒十分钟太阳。纸笔先收在怀里。",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"夜晚适合安静推导。只要没人拿着几何草图跑到我面前晃就行。",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"这页推导已经写到可复核的断点。明天你自己把最后一步验算收尾。",
			]),
		},
		"topic_replies": {
			"暴力美学": PackedStringArray([
				"所谓‘一眼看出’的技巧往往只在特例里成立；真正可靠的，是无论条件怎么变都能硬推到底的通法。宁可多算三行，绝不猜。",
			]),
			"治国算学": PackedStringArray([
				"税率、人口、折耗都是实打实的函数。把边界条件列明白，政策就不会半路失控。",
			]),
			"关于达文西": PackedStringArray([
				"达文西总爱用画表达一切……审美上无可挑剔，但在理学堂演算时请把画板放远点。",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"Brute Force Aesthetics.",
			"先检定义域与符号。",
			"宁可多算，绝不靠猜。",
			"最后一步请陛下亲手验算。",
		]),
	})

	# 10. Boming - 谋略大臣 · 军师 (Tier 3)
	profiles["boming"] = _make_profile({
		"id": "boming",
		"display_name": "伯明 (Boming)",
		"full_name": "诸葛基 (Zhuge Ji)",
		"role_title": "谋略大臣 · 军师",
		"tier": 3,
		"personality_summary": "慵懒军师，“山人自有妙计”，擅长从宏观战局找非常规破局锦囊。",
		"badge_text": "谋",
		"accent_color": Color(0.61, 0.72, 0.66),
		"hair_color": Color(0.13, 0.14, 0.17),
		"outfit_color": Color(0.92, 0.92, 0.90),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "courtyard_pavilion",
			GameClock.SLOT_FOCUS: "cabinet_strategy_boming",
			GameClock.SLOT_REFUEL: "courtyard_pond",
			GameClock.SLOT_FREE_SOUL: "courtyard_pavilion",
			GameClock.SLOT_SHUTDOWN: "cabinet_strategy_boming",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"陛下早呀。方才在亭中观云听风，倒想起一条能省下三成民力的奇策。",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"正面强攻费力气的时候，不妨绕个弯看看侧翼——山人自有妙计。",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"池水清凉，最宜半眯着眼养神。谋划之事，有时越急越乱。",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"天时已至，夜风正宜对弈。陛下可要来拆一局闲棋？",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"锦囊已封妥，明早自会应验。山人也去打个盹儿了。",
			]),
		},
		"topic_replies": {
			"破局锦囊": PackedStringArray([
				"郅政大人习惯正面立考成法压进度，那是王道正兵；若某件事卡在半路死活推不动，就来找山人，咱另辟蹊径绕过去。",
			]),
			"观星局势": PackedStringArray([
				"此局破绽不在城内，而在城外商路的连接次序。先通弱县，强县自然来附——此局，破矣。",
			]),
			"关于千金": PackedStringArray([
				"每次山人想多偷懒半个时辰，千金总能精准看穿，非递过来一碗清苦药茶不可。",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"山人自有妙计。",
			"此局，破矣。",
			"正面不通，便走侧翼。",
			"容山人再打个盹儿……",
		]),
	})

	# 11. Qianjin - 医学大臣 · 医官 (Tier 3)
	profiles["qianjin"] = _make_profile({
		"id": "qianjin",
		"display_name": "千金 (Qianjin)",
		"full_name": "孙邈 (Sun Miao)",
		"role_title": "医学大臣 · 医官",
		"tier": 3,
		"personality_summary": "驻颜医仙，“望闻问切”调理心神与治未病，温和具体且绝不硬扛急症。",
		"badge_text": "医",
		"accent_color": Color(0.43, 0.67, 0.56),
		"hair_color": Color(0.12, 0.13, 0.14),
		"outfit_color": Color(0.45, 0.62, 0.54),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "west_infirmary",
			GameClock.SLOT_FOCUS: "west_infirmary",
			GameClock.SLOT_REFUEL: "courtyard_pond",
			GameClock.SLOT_FREE_SOUL: "west_infirmary",
			GameClock.SLOT_SHUTDOWN: "west_infirmary",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"陛下早安。今日气色尚可，记得先饮半盏温水润润脾胃，再入正殿。",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"西偏院药案已备齐安神陈皮饮。久坐批阅若觉肩颈发僵，请一定起身舒展片刻。",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"午后正宜在莲池边走百步。饭后莫立刻伏案，以免食滞伤神。",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"夜晚切勿动气，也不宜再喝浓茶。让微臣为您备好温热姜枣茶。",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"陛下气色似有疲乏，需调理心神。若只是倦乏可早卧养阴；若真有心悸剧痛之兆，须立刻停工就医，切勿硬撑。",
			]),
		},
		"topic_replies": {
			"望闻问切": PackedStringArray([
				"治未病胜过治已病。疲乏时别空口说‘多休息’，具体做好两件事：一、离开案几拉伸肩背三分钟；二、温水泡脚十五分钟。",
			]),
			"太医院筹建": PackedStringArray([
				"西偏院预留地块 B 阳光正好，最适合辟作百草药圃与太医院正堂。",
			]),
			"嘱咐内阁": PackedStringArray([
				"Bit 总盯着算力不眨眼，Planck 熬起草稿更是忘食，微臣每天都得挨个塞一包护眼菊花茶过去。",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"切勿动气，顺气为先。",
			"药圃还缺几味疏肝理气草。",
			"陛下今日可曾多饮温水？",
			"治未病，贵在日常作息。",
		]),
	})

	# 12. Jiafa - 社科大臣 · 政治大臣 (Tier 3)
	profiles["jiafa"] = _make_profile({
		"id": "jiafa",
		"display_name": "稼发 (Jiafa)",
		"full_name": "桂晓 (Gui Xiao)",
		"role_title": "社科大臣 · 政治大臣",
		"tier": 3,
		"personality_summary": "狂乱贵公子，一本正经把政论典章当变革战局来讲，“不是假发，是稼！”。",
		"badge_text": "政",
		"accent_color": Color(0.79, 0.32, 0.30),
		"hair_color": Color(0.10, 0.10, 0.13),
		"outfit_color": Color(0.16, 0.24, 0.39),
		"schedule_waypoints": {
			GameClock.SLOT_MORNING: "south_gate_patrol",
			GameClock.SLOT_FOCUS: "cabinet_politics_jiafa",
			GameClock.SLOT_REFUEL: "courtyard_stage",
			GameClock.SLOT_FREE_SOUL: "courtyard_stage",
			GameClock.SLOT_SHUTDOWN: "cabinet_politics_jiafa",
		},
		"greetings_by_slot": {
			GameClock.SLOT_MORNING: PackedStringArray([
				"黎明将至，陛下！……另外再强调一次，不是假发，是稼！这是本人的长发，不是假发！",
			]),
			GameClock.SLOT_FOCUS: PackedStringArray([
				"治国社科之道，如同打一场精密的革新战局。核心矛盾抓准了，其余条文自会迎刃而解。",
			]),
			GameClock.SLOT_REFUEL: PackedStringArray([
				"趁午憩时间我在戏台边预演了今夜的政纲宣讲——放心，绝对通俗好记。",
			]),
			GameClock.SLOT_FREE_SOUL: PackedStringArray([
				"夜色下的宫灯同样是黎明前的一道火光！……咳，其实我只是在帮 Bina 看戏台幕布。",
			]),
			GameClock.SLOT_SHUTDOWN: PackedStringArray([
				"革命与治国都不急于这一夜。整顿好时间线与要点，明日黎明再战！",
			]),
		},
		"topic_replies": {
			"政论框架": PackedStringArray([
				"记住三步：先划出时间线，再抓准当下主要矛盾，最后专门把最容易张冠李戴的术语对照表背熟！",
			]),
			"袖中炸弹": PackedStringArray([
				"这可不是普通爆竹——这是浓缩了五十条易错考点的‘知识点炸弹’，专炸偷懒敷衍的官员！",
			]),
			"关于名字": PackedStringArray([
				"不是假发，是稼发！再听见谁在宫门口偷笑，我就在他茶杯里放一张政论重点小抄！",
			]),
		},
		"idle_thoughts": PackedStringArray([
			"不是假发，是稼！",
			"黎明将至……！",
			"易混术语再核一遍。",
			"袖子里的‘知识点’别掉出来。",
		]),
	})


func _init_banter_scripts() -> void:
	banter_scripts[_make_pair_key("bina", "bit")] = [
		[
			{"id": "bina", "text": "Bit！别总盯着地砖算坐标了，歇五分钟吧？"},
			{"id": "bit", "text": "评估中：暂停 5 分钟可降低 8% 过热风险。批准。"},
			{"id": "bina", "text": "这才对嘛，走，去水池边吹吹风~"},
		],
		[
			{"id": "bit", "text": "Bina，你今天的哼唱分贝超出了办公区建议阈值。"},
			{"id": "bina", "text": "这叫提升全城士气 Buff！你懂不懂呀 (￣▽￣)"},
		],
	]

	banter_scripts[_make_pair_key("bina", "chizheng")] = [
		[
			{"id": "bina", "text": "郅政大人，御膳房能不能加一笔午后茶点预算呀？"},
			{"id": "chizheng", "text": "考成法未列点心一项……但若能稳住众人干劲，准了。"},
			{"id": "bina", "text": "耶！就知道大人嘴硬心软！"},
		],
		[
			{"id": "chizheng", "text": "Bina，陛下今日巡视了几处宫署？"},
			{"id": "bina", "text": "正逛着呢！让他自己慢慢看，您别又急着塞奏折过去啦。"},
		],
	]

	banter_scripts[_make_pair_key("bina", "vinci")] = [
		[
			{"id": "bina", "text": "达文西，你刚才画的那盏宫灯好好看！"},
			{"id": "vinci", "text": "[写字板] 赠予御苑夜游用。记得挂高些。"},
			{"id": "bina", "text": "好嘞，等晚上一亮肯定绝美！"},
		],
		[
			{"id": "vinci", "text": "[举起写字板] 你的呆毛，今天弧度极佳。"},
			{"id": "bina", "text": "诶嘿，这也被你注意到了吗 (≧∇≦)"},
		],
	]

	banter_scripts[_make_pair_key("chizheng", "bit")] = [
		[
			{"id": "chizheng", "text": "Bit，西偏院那两处预留地基何时可动工？"},
			{"id": "bit", "text": "前置条件：陛下批复蓝图 + 石料库存到位。目前就绪度 50%。"},
			{"id": "chizheng", "text": "甚好，待郡县采石场开张便即刻开工。"},
		],
		[
			{"id": "bit", "text": "提案：将御苑水池改为矩形蓄水池，容量 +22%。"},
			{"id": "chizheng", "text": "驳回。莫要让达文西把写字板拍你脸上。"},
		],
	]

	banter_scripts[_make_pair_key("chizheng", "vinci")] = [
		[
			{"id": "chizheng", "text": "皇城扩建图样可定稿了？只给结论。"},
			{"id": "vinci", "text": "[写字板] 一轴四区，左文右工，中留青绿。可。"},
			{"id": "chizheng", "text": "言简意赅，深得孤心。"},
		],
	]

	banter_scripts[_make_pair_key("bit", "vinci")] = [
		[
			{"id": "bit", "text": "用纯灰石块砌墙，工期可缩短 14.6%。"},
			{"id": "vinci", "text": "[举起写字板] 丑。重做。"},
			{"id": "bit", "text": "……收到，重新加载暖白石材质参数。"},
		],
		[
			{"id": "vinci", "text": "[写字板] 门廊对称偏差 4 像素。"},
			{"id": "bit", "text": "校准中……已对齐。"},
		],
	]

	banter_scripts[_make_pair_key("taki", "bina")] = [
		[
			{"id": "bina", "text": "Taki 别板着脸啦！今天刚出炉的桂花糕分你一半~"},
			{"id": "taki", "text": "……啧。工作时间别把糕点碎屑掉到归档册上。……放桌角吧，谢谢。"},
		],
		[
			{"id": "taki", "text": "你昨天记的日程表少写了一个冒号，我都强迫症犯了。"},
			{"id": "bina", "text": "诶嘿，下次绝对对齐！多亏有我们的书记官大人兜底啦~"},
		],
	]

	banter_scripts[_make_pair_key("fukucho", "bina")] = [
		[
			{"id": "fukucho", "text": "夜间宫道灯火已检视无误。Bina，待会记得劝陛下早些回寝殿。"},
			{"id": "bina", "text": "包在我身上！要是他还不睡，我就和副长一唱一和把他哄回去 (≧∇≦)"},
		],
	]

	banter_scripts[_make_pair_key("planck", "bit")] = [
		[
			{"id": "bit", "text": "我写了一个可视化曲线脚本来估算西偏院材料消耗。"},
			{"id": "planck", "text": "Brute Force Aesthetics。拿走你的花哨曲线，直接看目标函数二阶导与矩阵约束。"},
		],
		[
			{"id": "planck", "text": "这组数值差了 0.002，明显舍入得太草率。"},
			{"id": "bit", "text": "已切换为双精度浮点校验。当前误差：0。"},
		],
	]

	banter_scripts[_make_pair_key("boming", "chizheng")] = [
		[
			{"id": "chizheng", "text": "伯明，考成法第三条限三日见效，你的锦囊还没拆？"},
			{"id": "boming", "text": "首辅大人莫急嘛，山人算着今夜东南风一到，城外商队自己就进门了。"},
		],
		[
			{"id": "boming", "text": "正面硬推耗十万钱，绕南门借道只花两万。大人，选哪边？"},
			{"id": "chizheng", "text": "……两万。下不为例，莫把全阁都带懒了。"},
		],
	]

	banter_scripts[_make_pair_key("qianjin", "fukucho")] = [
		[
			{"id": "qianjin", "text": "副长夜夜巡值辛苦，这是微臣新配的润喉陈皮甘草茶。"},
			{"id": "fukucho", "text": "谢过千金医官。不过只要陛下还亮着灯，这巡夜的刀便不会归鞘。"},
		],
	]

	banter_scripts[_make_pair_key("tianji", "jiafa")] = [
		[
			{"id": "tianji", "text": "哟假发！今天袖子里又塞着啥新鲜玩意儿呢？"},
			{"id": "jiafa", "text": "不是假发，是稼发！……顺便说一句，这是最新编好的政论要点炸弹！"},
			{"id": "tianji", "text": "哈哈，好好好，稼大人保重火候，别在茶亭里点着了！"},
		],
	]

	banter_scripts[_make_pair_key("jean", "taki")] = [
		[
			{"id": "jean", "text": "Taki，新到的十七卷营造旧档已全部按签号核对，没有任何孤证。"},
			{"id": "taki", "text": "不错，总算有一份不用我返工的文件了。继续保持。"},
		],
	]

	banter_scripts[_make_pair_key("vinci", "jiafa")] = [
		[
			{"id": "jiafa", "text": "达文西卿，你看我这件靛蓝外褂迎风飘扬时的轮廓，是不是颇有黎明之势？"},
			{"id": "vinci", "text": "[举起写字板] 配色合格。但袖口那颗黑球略显突兀，藏好。"},
		],
	]

	banter_scripts[_make_pair_key("qianjin", "boming")] = [
		[
			{"id": "qianjin", "text": "伯明先生又在亭子里打盹？当心受了穿堂风。"},
			{"id": "boming", "text": "医官放心，山人这叫养精蓄锐——不过你那盏安神热茶倒是真香，分我半杯？"},
		],
	]

	banter_scripts[_make_pair_key("jean", "bina")] = [
		[
			{"id": "bina", "text": "Jean 的高盘发配青玉簪好好看！教教我怎么盘才不会散呀~"},
			{"id": "jean", "text": "好呀，等午憩有空我带一把备用木梳来。不过 Bina 这根小呆毛可一定得留着！"},
		],
	]

	banter_scripts[_make_pair_key("tianji", "chizheng")] = [
		[
			{"id": "tianji", "text": "首辅大人，西市木料涨了一成二，咱们先签哪家？"},
			{"id": "chizheng", "text": "既是你探过底、保真无欺的那家，今日内拟契送东偏殿盖印。"},
		],
	]
