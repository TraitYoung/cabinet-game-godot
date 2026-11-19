import type { Rect, Vec2 } from '../data/types';

function clamp(v: number, min: number, max: number): number {
  return v < min ? min : v > max ? max : v;
}

export function pointInPolygon(point: Vec2, polygon: readonly Vec2[]): boolean {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i]!.x;
    const yi = polygon[i]!.y;
    const xj = polygon[j]!.x;
    const yj = polygon[j]!.y;

    const intersect =
      yi > point.y !== yj > point.y &&
      point.x < ((xj - xi) * (point.y - yi)) / (yj - yi + 1e-12) + xi;
    if (intersect) {
      inside = !inside;
    }
  }
  return inside;
}

function closestPointOnSegment(p: Vec2, a: Vec2, b: Vec2): Vec2 {
  const abx = b.x - a.x;
  const aby = b.y - a.y;
  const lenSq = abx * abx + aby * aby;
  if (lenSq <= 1e-9) {
    return { x: a.x, y: a.y };
  }
  const t = clamp(((p.x - a.x) * abx + (p.y - a.y) * aby) / lenSq, 0, 1);
  return { x: a.x + abx * t, y: a.y + aby * t };
}

export function resolveCircleVsRects(
  pos: Vec2,
  radius: number,
  rects: readonly Rect[],
  bounds?: Rect,
): Vec2 {
  let x = pos.x;
  let y = pos.y;

  for (let iter = 0; iter < 3; iter += 1) {
    if (bounds) {
      x = clamp(x, bounds.x + radius, bounds.x + bounds.w - radius);
      y = clamp(y, bounds.y + radius, bounds.y + bounds.h - radius);
    }

    for (const rect of rects) {
      const cx = clamp(x, rect.x, rect.x + rect.w);
      const cy = clamp(y, rect.y, rect.y + rect.h);
      const dx = x - cx;
      const dy = y - cy;
      const distSq = dx * dx + dy * dy;

      if (distSq < 1e-8) {
        const toLeft = x - rect.x;
        const toRight = rect.x + rect.w - x;
        const toTop = y - rect.y;
        const toBottom = rect.y + rect.h - y;
        const minPen = Math.min(toLeft, toRight, toTop, toBottom);
        if (minPen === toLeft) {
          x = rect.x - radius;
        } else if (minPen === toRight) {
          x = rect.x + rect.w + radius;
        } else if (minPen === toTop) {
          y = rect.y - radius;
        } else {
          y = rect.y + rect.h + radius;
        }
      } else if (distSq < radius * radius) {
        const dist = Math.sqrt(distSq);
        const push = radius - dist;
        x += (dx / dist) * push;
        y += (dy / dist) * push;
      }
    }
  }

  return { x, y };
}

export function resolveCircleVsPolygons(
  pos: Vec2,
  radius: number,
  polygons: readonly (readonly Vec2[])[],
  bounds?: Rect,
): Vec2 {
  let x = pos.x;
  let y = pos.y;

  for (let iter = 0; iter < 3; iter += 1) {
    if (bounds) {
      x = clamp(x, bounds.x + radius, bounds.x + bounds.w - radius);
      y = clamp(y, bounds.y + radius, bounds.y + bounds.h - radius);
    }

    for (const poly of polygons) {
      if (poly.length < 3) {
        continue;
      }

      let bestPoint: Vec2 = { x, y };
      let bestDistSq = Infinity;
      let bestEdgeIndex = 0;

      for (let i = 0; i < poly.length; i += 1) {
        const a = poly[i]!;
        const b = poly[(i + 1) % poly.length]!;
        const cp = closestPointOnSegment({ x, y }, a, b);
        const dSq = (x - cp.x) * (x - cp.x) + (y - cp.y) * (y - cp.y);
        if (dSq < bestDistSq) {
          bestDistSq = dSq;
          bestPoint = cp;
          bestEdgeIndex = i;
        }
      }

      const inside = pointInPolygon({ x, y }, poly);
      const dist = Math.sqrt(bestDistSq);

      if (inside) {
        if (dist > 1e-6) {
          const nx = (bestPoint.x - x) / dist;
          const ny = (bestPoint.y - y) / dist;
          x = bestPoint.x + nx * radius;
          y = bestPoint.y + ny * radius;
        } else {
          const a = poly[bestEdgeIndex]!;
          const b = poly[(bestEdgeIndex + 1) % poly.length]!;
          const ex = b.x - a.x;
          const ey = b.y - a.y;
          const elen = Math.hypot(ex, ey) || 1;
          const nx1 = -ey / elen;
          const ny1 = ex / elen;
          const probe = { x: x + nx1 * 2, y: y + ny1 * 2 };
          const sign = pointInPolygon(probe, poly) ? -1 : 1;
          x += nx1 * sign * radius;
          y += ny1 * sign * radius;
        }
      } else if (dist < radius && dist > 1e-6) {
        const push = radius - dist;
        x += ((x - bestPoint.x) / dist) * push;
        y += ((y - bestPoint.y) / dist) * push;
      }
    }
  }

  return { x, y };
}
