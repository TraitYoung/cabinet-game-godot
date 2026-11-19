import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  ORDERED_MINISTER_IDS,
  getAllBanterPairs,
  getAllProfiles,
  getCouncilMeetingEntries,
} from '../../data/cabinetDatabase';
import {
  MONARCH_SPRITE_PATH,
  PALACE_BASE_MAP,
  PALACE_FRONT_MAP,
  PALACE_FURNITURE,
  PALACE_LANTERN_SPRITE,
  PALACE_LOTUS_POND,
  PALACE_PLAYABLE_BOUNDS,
  PALACE_TREES,
  PALACE_WALLS,
  PALACE_WAYPOINTS,
  PALACE_WORLD_SIZE,
} from '../../data/palaceLayout';
import {
  COURTYARD_BASE_MAP,
  COURTYARD_FRONT_MAP,
  COURTYARD_ORIGIN,
  COURTYARD_WALL_POLYGONS,
  COURTYARD_WAYPOINTS,
  COURTYARD_WORLD_SIZE,
} from '../../data/smallCourtyardLayout';
import type { Rect, TimeSlotId } from '../../data/types';
import { GameClock } from '../clock';
import { resolveCircleVsPolygons, resolveCircleVsRects } from '../collision';
import { NavGrid } from '../pathfinding';

const REPO_ROOT = path.resolve(import.meta.dirname, '../../..');

function resolveGameAssetPath(publicPath: string): string {
  const prefix = '/game-assets/';
  expect(publicPath.startsWith(prefix)).toBe(true);
  return path.join(REPO_ROOT, 'assets', publicPath.slice(prefix.length));
}

describe('cabinetDatabase', () => {
  it('contains all 12 ministers with valid schedules, banter pairs, and existing PNG assets', () => {
    const profiles = getAllProfiles();
    expect(ORDERED_MINISTER_IDS).toHaveLength(12);
    expect(profiles).toHaveLength(12);

    const slots: readonly TimeSlotId[] = ['morning', 'focus', 'refuel', 'free_soul', 'shutdown'];
    const idSet = new Set(ORDERED_MINISTER_IDS);

    for (const prof of profiles) {
      for (const slot of slots) {
        const wpName = prof.scheduleWaypoints[slot];
        expect(PALACE_WAYPOINTS[wpName]).toBeDefined();
      }
      expect(fs.existsSync(resolveGameAssetPath(prof.portraitPath))).toBe(true);
      expect(fs.existsSync(resolveGameAssetPath(prof.chibiSpritePath))).toBe(true);
    }

    const banterPairs = getAllBanterPairs();
    const pairKeys = Object.keys(banterPairs);
    expect(pairKeys).toHaveLength(17);
    for (const key of pairKeys) {
      const [idA, idB] = key.split('|');
      expect(idSet.has(idA!)).toBe(true);
      expect(idSet.has(idB!)).toBe(true);
      const scripts = banterPairs[key]!;
      expect(scripts.length).toBeGreaterThan(0);
      for (const script of scripts) {
        for (const line of script) {
          expect(line.id === idA || line.id === idB).toBe(true);
          expect(line.text.length).toBeGreaterThan(0);
        }
      }
    }

    expect(getCouncilMeetingEntries('focus').length).toBe(9);
    expect(getCouncilMeetingEntries('shutdown').length).toBe(6);
  });

  it('references existing PNG files for monarch, palace, props, and courtyard maps', () => {
    const assetPaths = [
      MONARCH_SPRITE_PATH,
      PALACE_BASE_MAP,
      PALACE_FRONT_MAP,
      PALACE_LANTERN_SPRITE,
      COURTYARD_BASE_MAP,
      COURTYARD_FRONT_MAP,
      ...PALACE_FURNITURE.map((f) => f.spritePath),
      ...PALACE_TREES.map((t) => t.spritePath),
    ];

    for (const assetUrl of assetPaths) {
      expect(fs.existsSync(resolveGameAssetPath(assetUrl))).toBe(true);
    }
  });
});

describe('NavGrid', () => {
  const obstacles: Rect[] = [
    ...PALACE_WALLS.map((w) => w.rect),
    PALACE_LOTUS_POND.rect,
    ...PALACE_FURNITURE.map((f) => f.rect),
  ];
  const navGrid = new NavGrid(PALACE_WORLD_SIZE, PALACE_PLAYABLE_BOUNDS, obstacles, 14);

  it('keeps all 21 palace waypoints walkable', () => {
    for (const [name, wp] of Object.entries(PALACE_WAYPOINTS)) {
      expect(navGrid.isPointClear(wp.x, wp.y), `Waypoint ${name} should be clear`).toBe(true);
    }
  });

  it('finds valid A* paths across palace zones without intersecting obstacles', () => {
    const routes: Array<[string, string]> = [
      ['cabinet_office_bina', 'west_workshop'],
      ['throne_sandbox', 'south_gate_patrol'],
      ['west_infirmary', 'courtyard_pond'],
    ];

    for (const [fromKey, toKey] of routes) {
      const from = PALACE_WAYPOINTS[fromKey]!;
      const to = PALACE_WAYPOINTS[toKey]!;
      const pathPts = navGrid.findPath(from, to);
      expect(pathPts.length).toBeGreaterThan(0);
      const last = pathPts[pathPts.length - 1]!;
      expect(Math.hypot(last.x - to.x, last.y - to.y)).toBeLessThan(24);
      for (const pt of pathPts) {
        expect(navGrid.isPointClear(pt.x, pt.y)).toBe(true);
      }
    }
  });
});

describe('collision', () => {
  it('blocks wall entry and preserves lateral sliding for circle-vs-rect', () => {
    const wall: Rect = { x: 520, y: 390, w: 200, h: 22 };
    const pushed = resolveCircleVsRects({ x: 600, y: 386 }, 12, [wall]);
    expect(pushed.y).toBeLessThanOrEqual(390 - 12 + 0.001);
    expect(pushed.x).toBeCloseTo(600, 3);
  });

  it('blocks courtyard walls while allowing passage through gate_threshold', () => {
    const worldPolys = COURTYARD_WALL_POLYGONS.map((poly) =>
      poly.map((p) => ({ x: p.x + COURTYARD_ORIGIN.x, y: p.y + COURTYARD_ORIGIN.y })),
    );
    const bounds: Rect = {
      x: 0,
      y: 0,
      w: COURTYARD_WORLD_SIZE.x,
      h: COURTYARD_WORLD_SIZE.y,
    };

    const gateThreshold = {
      x: COURTYARD_ORIGIN.x + COURTYARD_WAYPOINTS.gate_threshold!.x,
      y: COURTYARD_ORIGIN.y + COURTYARD_WAYPOINTS.gate_threshold!.y,
    };
    const resolvedGate = resolveCircleVsPolygons(gateThreshold, 12, worldPolys, bounds);
    expect(Math.hypot(resolvedGate.x - gateThreshold.x, resolvedGate.y - gateThreshold.y)).toBeLessThan(
      0.5,
    );

    // Inside wall polygon 0 (south-west courtyard wall)
    const insideWall = {
      x: COURTYARD_ORIGIN.x + 200,
      y: COURTYARD_ORIGIN.y + 685,
    };
    const pushedOut = resolveCircleVsPolygons(insideWall, 12, worldPolys, bounds);
    expect(Math.hypot(pushedOut.x - insideWall.x, pushedOut.y - insideWall.y)).toBeGreaterThan(5);
  });
});

describe('GameClock', () => {
  it('computes all 5 time slots and handles day rollover via skipToNextSlot', () => {
    const clock = new GameClock();
    expect(clock.computeSlot(8)).toBe('morning');
    expect(clock.computeSlot(10)).toBe('focus');
    expect(clock.computeSlot(12)).toBe('refuel');
    expect(clock.computeSlot(14)).toBe('focus');
    expect(clock.computeSlot(18)).toBe('free_soul');
    expect(clock.computeSlot(23)).toBe('shutdown');
    expect(clock.computeSlot(2)).toBe('shutdown');

    expect(clock.day).toBe(1);
    expect(clock.currentSlot).toBe('morning');

    clock.skipToNextSlot(); // 10:05 focus
    expect(clock.currentSlot).toBe('focus');
    expect(clock.getFormattedTime()).toBe('10:05');

    clock.skipToNextSlot(); // 12:05 refuel
    expect(clock.currentSlot).toBe('refuel');

    clock.skipToNextSlot(); // 14:05 focus
    expect(clock.currentSlot).toBe('focus');

    clock.skipToNextSlot(); // 18:05 free_soul
    expect(clock.currentSlot).toBe('free_soul');

    clock.skipToNextSlot(); // 23:05 shutdown
    expect(clock.currentSlot).toBe('shutdown');

    clock.skipToNextSlot(); // Day 2 08:05 morning
    expect(clock.day).toBe(2);
    expect(clock.currentSlot).toBe('morning');
    expect(clock.getFormattedTime()).toBe('08:05');
  });
});
