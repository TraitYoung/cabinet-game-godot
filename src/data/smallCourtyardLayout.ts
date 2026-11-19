import type { FrontStripSpec, InteractableSpec, Vec2 } from './types';

export const COURTYARD_WORLD_SIZE: Vec2 = { x: 1600, y: 1120 };
export const COURTYARD_ORIGIN: Vec2 = { x: 74, y: 56 };
export const COURTYARD_CANVAS_SIZE: Vec2 = { x: 1452, y: 1008 };

export const COURTYARD_BASE_MAP = '/game-assets/palace/small_courtyard_base.png';
export const COURTYARD_FRONT_MAP = '/game-assets/palace/small_courtyard_front.png';

export const COURTYARD_FRONT_STRIPS: readonly FrontStripSpec[] = [
  { x: 0, w: 100, footY: 642.9 },
  { x: 100, w: 100, footY: 680.9 },
  { x: 200, w: 100, footY: 718.9 },
  { x: 300, w: 96, footY: 756.1 },
  { x: 396, w: 49, footY: 795.8 },
  { x: 445, w: 58, footY: 795.8 },
  { x: 503, w: 65, footY: 795.8 },
  { x: 568, w: 102, footY: 852.8 },
  { x: 670, w: 105, footY: 892.4 },
  { x: 775, w: 105, footY: 932.6 },
  { x: 880, w: 106, footY: 972.9 },
  { x: 986, w: 109, footY: 942.4 },
  { x: 1095, w: 110, footY: 841.6 },
  { x: 1205, w: 115, footY: 738.0 },
  { x: 1320, w: 132, footY: 624.3 },
];

export const COURTYARD_WALL_POLYGONS: readonly (readonly Vec2[])[] = [
  [
    { x: 15, y: 600.8 },
    { x: 441, y: 759 },
    { x: 429, y: 788.2 },
    { x: 15, y: 633 },
  ],
  [
    { x: 501, y: 780 },
    { x: 985.5, y: 963 },
    { x: 985.5, y: 996 },
    { x: 490.5, y: 807 },
  ],
  [
    { x: 985.5, y: 963 },
    { x: 1432.5, y: 559.5 },
    { x: 1445.2, y: 582 },
    { x: 985.5, y: 996 },
  ],
  [
    { x: 15, y: 600.8 },
    { x: 552.8, y: 113.2 },
    { x: 594, y: 135.8 },
    { x: 222.8, y: 544.5 },
    { x: 54, y: 608.2 },
  ],
  [
    { x: 1005, y: 413.2 },
    { x: 1092.8, y: 338.2 },
    { x: 1430.2, y: 465.8 },
    { x: 1430.2, y: 559.5 },
    { x: 982.5, y: 818.2 },
    { x: 972.8, y: 709.5 },
    { x: 850.5, y: 660.8 },
  ],
  [
    { x: 552.8, y: 113.2 },
    { x: 755.2, y: 188.2 },
    { x: 723, y: 370.5 },
    { x: 552.8, y: 308.2 },
  ],
  [
    { x: 755.2, y: 188.2 },
    { x: 1092.8, y: 338.2 },
    { x: 1005, y: 413.2 },
    { x: 822.8, y: 406.5 },
  ],
  [
    { x: 710.2, y: 289.5 },
    { x: 852.8, y: 342 },
    { x: 822.8, y: 383.2 },
    { x: 723, y: 348 },
  ],
];

export const COURTYARD_WAYPOINTS: Record<string, Vec2> = {
  gate_outside: { x: 440.2, y: 844.5 },
  gate_threshold: { x: 472.5, y: 768.0 },
  courtyard_center: { x: 627.8, y: 544.5 },
  hall_stairs: { x: 770.2, y: 394.5 },
  west_corridor_steps: { x: 399.0, y: 454.5 },
};

export const COURTYARD_ENTRANCE_ROAD: readonly Vec2[] = [
  { x: COURTYARD_ORIGIN.x + 440 - 42, y: COURTYARD_ORIGIN.y + 844 - 35 },
  { x: COURTYARD_ORIGIN.x + 440 + 58, y: COURTYARD_ORIGIN.y + 844 + 4 },
  { x: COURTYARD_ORIGIN.x + 440 - 120, y: COURTYARD_ORIGIN.y + 844 + 190 },
  { x: COURTYARD_ORIGIN.x + 440 - 220, y: COURTYARD_ORIGIN.y + 844 + 150 },
];

export const COURTYARD_INTERACTABLES: readonly InteractableSpec[] = [
  {
    id: 'small_courtyard_hall',
    x: COURTYARD_ORIGIN.x + COURTYARD_WAYPOINTS.hall_stairs.x,
    y: COURTYARD_ORIGIN.y + COURTYARD_WAYPOINTS.hall_stairs.y,
    displayTitle: '内阁值房小院 · 值房正厅',
    promptHint: '按 [E] 检视 值房正厅',
    accentColor: '#e6b85c',
    indicatorSize: { x: 104, y: 76 },
    infoLines: [
      '【最小宫廷建筑单元 · 一进值房小院】',
      '参照唐大明宫门下省 / 东西朝堂侧院制式：北三间单檐正厅、东西廊庑、南向小门与石板天井。',
      '可作为独立官署模块在宫城中拼接复用。',
    ],
  },
  {
    id: 'small_courtyard_west_corridor',
    x: COURTYARD_ORIGIN.x + COURTYARD_WAYPOINTS.west_corridor_steps.x,
    y: COURTYARD_ORIGIN.y + COURTYARD_WAYPOINTS.west_corridor_steps.y,
    displayTitle: '西厢廊庑',
    promptHint: '按 [E] 检视 西厢廊庑',
    accentColor: '#8ad1c7',
    indicatorSize: { x: 104, y: 76 },
    infoLines: [
      '【西厢廊庑 · 考成与卷宗抄录处】',
      '单檐灰瓦连廊连接南院门与北正厅，供值房书吏暂存文书与避雨通廊。',
    ],
  },
];
