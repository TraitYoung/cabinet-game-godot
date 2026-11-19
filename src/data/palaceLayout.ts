import type {
  FurnitureSpec,
  InteractableSpec,
  Rect,
  TreeSpec,
  Vec2,
  WallSpec,
  ZoneLabelSpec,
} from './types';

export const PALACE_WORLD_SIZE: Vec2 = { x: 1600, y: 1120 };
export const PALACE_PLAYABLE_BOUNDS: Rect = { x: 68, y: 68, w: 1464, h: 956 };

export const PALACE_BASE_MAP = '/game-assets/palace/palace_base.png';
export const PALACE_FRONT_MAP = '/game-assets/palace/palace_front.png';
export const PALACE_LANTERN_SPRITE = '/game-assets/palace/props/palace_lantern.png';
export const MONARCH_SPRITE_PATH = '/game-assets/characters/chibi/monarch.png';

export const PALACE_WALLS: readonly WallSpec[] = [
  { name: 'OuterWallNorth', rect: { x: 40, y: 40, w: 1520, h: 28 } },
  { name: 'OuterWallWest', rect: { x: 40, y: 68, w: 28, h: 984 } },
  { name: 'OuterWallEast', rect: { x: 1532, y: 68, w: 28, h: 984 } },
  { name: 'OuterWallSouthLeft', rect: { x: 68, y: 1024, w: 632, h: 28 } },
  { name: 'OuterWallSouthRight', rect: { x: 900, y: 1024, w: 632, h: 28 } },
  { name: 'ThroneSouthLeft', rect: { x: 520, y: 390, w: 200, h: 22 } },
  { name: 'ThroneSouthRight', rect: { x: 880, y: 390, w: 200, h: 22 } },
  { name: 'ThroneWestUpper', rect: { x: 520, y: 68, w: 22, h: 140 } },
  { name: 'ThroneWestLower', rect: { x: 520, y: 300, w: 22, h: 90 } },
  { name: 'ThroneEastUpper', rect: { x: 1058, y: 68, w: 22, h: 140 } },
  { name: 'ThroneEastLower', rect: { x: 1058, y: 300, w: 22, h: 90 } },
  { name: 'EastWingSouthLeft', rect: { x: 1080, y: 440, w: 150, h: 20 } },
  { name: 'EastWingSouthRight', rect: { x: 1340, y: 440, w: 192, h: 20 } },
  { name: 'WestWingSouthLeft', rect: { x: 68, y: 480, w: 170, h: 20 } },
  { name: 'WestWingSouthRight', rect: { x: 350, y: 480, w: 170, h: 20 } },
];

export const PALACE_LOTUS_POND: { rect: Rect; label: string } = {
  rect: { x: 920, y: 620, w: 200, h: 130 },
  label: '御苑莲池',
};

export const PALACE_FURNITURE: readonly FurnitureSpec[] = [
  {
    id: 'throne_dais',
    rect: { x: 745, y: 110, w: 110, h: 48 },
    label: '御坐',
    spritePath: '/game-assets/palace/props/throne_dais.png',
    visualSize: { x: 160, y: 110 },
    labelAbove: false,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'sandbox_table',
    rect: { x: 730, y: 232, w: 140, h: 76 },
    label: '舆图沙盘',
    spritePath: '/game-assets/palace/props/sandbox_table.png',
    visualSize: { x: 180, y: 110 },
    labelAbove: false,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'desk_chizheng',
    rect: { x: 1150, y: 160, w: 120, h: 50 },
    label: '考成案牍',
    spritePath: '/game-assets/palace/props/desk_chizheng.png',
    visualSize: { x: 150, y: 84 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'desk_bina',
    rect: { x: 1350, y: 160, w: 120, h: 50 },
    label: '秘文案桌',
    spritePath: '/game-assets/palace/props/desk_bina.png',
    visualSize: { x: 150, y: 84 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'shelf_archives',
    rect: { x: 1240, y: 100, w: 150, h: 28 },
    label: '卷宗架',
    spritePath: '/game-assets/palace/props/shelf_archives.png',
    visualSize: { x: 176, y: 86 },
    labelAbove: false,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'desk_taki',
    rect: { x: 1105, y: 318, w: 104, h: 44 },
    label: '书记案',
    spritePath: '/game-assets/palace/props/desk_taki.png',
    visualSize: { x: 136, y: 76 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 12 },
  },
  {
    id: 'shelf_lantai',
    rect: { x: 1386, y: 318, w: 110, h: 44 },
    label: '兰台书架',
    spritePath: '/game-assets/palace/props/shelf_lantai.png',
    visualSize: { x: 140, y: 88 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 18 },
  },
  {
    id: 'workbench_bit',
    rect: { x: 130, y: 165, w: 125, h: 54 },
    label: '工学锻台',
    spritePath: '/game-assets/palace/props/workbench_bit.png',
    visualSize: { x: 156, y: 90 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'atelier_vinci',
    rect: { x: 345, y: 170, w: 95, h: 48 },
    label: '画坊长案',
    spritePath: '/game-assets/palace/props/atelier_vinci.png',
    visualSize: { x: 130, y: 84 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'shelf_qianjin',
    rect: { x: 476, y: 330, w: 36, h: 84 },
    label: '太医药架',
    spritePath: '/game-assets/palace/props/shelf_qianjin.png',
    visualSize: { x: 72, y: 116 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'stone_table',
    rect: { x: 675, y: 690, w: 96, h: 64 },
    label: '石桌',
    spritePath: '/game-assets/palace/props/stone_table.png',
    visualSize: { x: 128, y: 88 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'desk_boming',
    rect: { x: 1245, y: 555, w: 115, h: 48 },
    label: '军机沙案',
    spritePath: '/game-assets/palace/props/desk_boming.png',
    visualSize: { x: 146, y: 80 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'desk_jiafa',
    rect: { x: 1245, y: 745, w: 115, h: 48 },
    label: '政宣刊案',
    spritePath: '/game-assets/palace/props/desk_jiafa.png',
    visualSize: { x: 146, y: 80 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'desk_planck',
    rect: { x: 135, y: 575, w: 115, h: 48 },
    label: '格物算席',
    spritePath: '/game-assets/palace/props/desk_planck.png',
    visualSize: { x: 146, y: 80 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 0 },
  },
  {
    id: 'tea_pavilion',
    rect: { x: 140, y: 755, w: 110, h: 54 },
    label: '御苑茶亭',
    spritePath: '/game-assets/palace/props/tea_pavilion.png',
    visualSize: { x: 168, y: 136 },
    labelAbove: true,
    plaqueOffset: { x: 0, y: 60 },
  },
];

export const PALACE_TREES: readonly TreeSpec[] = [
  {
    id: 'willow_01',
    pos: { x: 1176, y: 680 },
    spritePath: '/game-assets/palace/props/tree_willow.png',
    visualSize: { x: 150, y: 160 },
    bottomPad: 4,
  },
  {
    id: 'willow_02',
    pos: { x: 1136, y: 566 },
    spritePath: '/game-assets/palace/props/tree_willow.png',
    visualSize: { x: 150, y: 160 },
    bottomPad: 4,
  },
  {
    id: 'ginkgo_01',
    pos: { x: 406, y: 576 },
    spritePath: '/game-assets/palace/props/tree_ginkgo.png',
    visualSize: { x: 140, y: 150 },
    bottomPad: 4,
  },
  {
    id: 'ginkgo_02',
    pos: { x: 410, y: 846 },
    spritePath: '/game-assets/palace/props/tree_ginkgo.png',
    visualSize: { x: 140, y: 150 },
    bottomPad: 4,
  },
  {
    id: 'ginkgo_03',
    pos: { x: 1186, y: 846 },
    spritePath: '/game-assets/palace/props/tree_ginkgo.png',
    visualSize: { x: 140, y: 150 },
    bottomPad: 4,
  },
  {
    id: 'ginkgo_04',
    pos: { x: 146, y: 966 },
    spritePath: '/game-assets/palace/props/tree_ginkgo.png',
    visualSize: { x: 140, y: 150 },
    bottomPad: 4,
  },
  {
    id: 'ginkgo_05',
    pos: { x: 1456, y: 966 },
    spritePath: '/game-assets/palace/props/tree_ginkgo.png',
    visualSize: { x: 140, y: 150 },
    bottomPad: 4,
  },
];

export const PALACE_LANTERNS: readonly Vec2[] = [
  { x: 640, y: 180 },
  { x: 960, y: 180 },
  { x: 456, y: 548 },
  { x: 860, y: 600 },
  { x: 1280, y: 290 },
  { x: 280, y: 290 },
  { x: 720, y: 960 },
  { x: 880, y: 960 },
];

export const PALACE_ZONE_LABELS: readonly ZoneLabelSpec[] = [
  { pos: { x: 800, y: 26 }, text: '【中轴 · 议事正殿】' },
  { pos: { x: 1300, y: 28 }, text: '【东偏殿 · 内阁值房】' },
  { pos: { x: 290, y: 28 }, text: '【西偏院 · 匠造与画坊】' },
  { pos: { x: 800, y: 492 }, text: '【中心 · 御苑广场】' },
  { pos: { x: 800, y: 1072 }, text: '【南宫门】' },
];

export const PALACE_WAYPOINTS: Record<string, Vec2> = {
  player_spawn: { x: 800, y: 860 },
  throne_sandbox: { x: 695, y: 270 },
  throne_hall_side: { x: 895, y: 270 },
  throne_guard_post: { x: 635, y: 340 },
  cabinet_office_chizheng: { x: 1210, y: 250 },
  cabinet_office_bina: { x: 1410, y: 250 },
  cabinet_office_taki: { x: 1157, y: 394 },
  cabinet_library_jean: { x: 1440, y: 394 },
  cabinet_strategy_boming: { x: 1302, y: 636 },
  cabinet_politics_jiafa: { x: 1302, y: 826 },
  west_workshop: { x: 195, y: 255 },
  west_atelier: { x: 390, y: 255 },
  west_plot_a: { x: 210, y: 380 },
  west_math_hall: { x: 192, y: 656 },
  west_infirmary: { x: 444, y: 385 },
  courtyard_stage: { x: 540, y: 620 },
  courtyard_table: { x: 650, y: 775 },
  courtyard_pond: { x: 860, y: 690 },
  courtyard_pavilion: { x: 195, y: 842 },
  palace_corridor: { x: 800, y: 455 },
  south_gate_patrol: { x: 800, y: 945 },
};

export const PALACE_INTERACTABLES: readonly InteractableSpec[] = [
  {
    id: 'sandbox_table',
    x: 800,
    y: 270,
    displayTitle: '正殿舆图沙盘',
    promptHint: '按 [E] 召集内阁短议',
    accentColor: '#ebc25c',
    isCouncilSandbox: true,
    indicatorSize: { x: 150, y: 86 },
    infoLines: [],
  },
  {
    id: 'west_plot_a',
    x: 175,
    y: 385,
    displayTitle: '西偏院 · 预留地块 A',
    promptHint: '按 [E] 勘察扩建地块',
    accentColor: '#61cce6',
    indicatorSize: { x: 114, y: 92 },
    infoLines: [
      '【预留地块 A · 拟建：墨家工坊 / 司天监】',
      'Bit 已经量好尺寸，达文西坚持屋檐必须用青瓦飞檐。',
      '后续进入「皇城细尺度建设」阶段后，可直接在此落成新宫署。',
    ],
  },
  {
    id: 'west_plot_b',
    x: 365,
    y: 385,
    displayTitle: '西偏院 · 预留地块 B',
    promptHint: '按 [E] 勘察扩建地块',
    accentColor: '#a8d68f',
    indicatorSize: { x: 114, y: 92 },
    infoLines: [
      '【预留地块 B · 拟建：太医院 / 御苑药圃】',
      '等第二批内阁成员「千金 (Qianjin)」入驻后，这里会种满草药并负责调理陛下体力。',
    ],
  },
];

export function getWaypointPosition(waypointName: string): Vec2 {
  const wp = PALACE_WAYPOINTS[waypointName];
  if (wp) {
    return { x: wp.x, y: wp.y };
  }
  return { x: 800, y: 620 };
}

export function getZoneNameForPosition(pos: Vec2): string {
  if (pos.y < 410 && pos.x >= 520 && pos.x <= 1080) {
    return '议事正殿';
  }
  if (pos.x > 1080 && pos.y < 520) {
    return '东偏殿值房';
  }
  if (pos.x < 520 && pos.y < 520) {
    return '西偏院工坊';
  }
  if (pos.y > 920) {
    return '南宫门';
  }
  return '中心御苑';
}
