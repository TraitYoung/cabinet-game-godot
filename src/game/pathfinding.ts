import type { Rect, Vec2 } from '../data/types';

const CELL_SIZE = 16;

interface AStarNode {
  idx: number;
  g: number;
  f: number;
}

class MinHeap {
  private items: AStarNode[] = [];

  get size(): number {
    return this.items.length;
  }

  push(node: AStarNode): void {
    this.items.push(node);
    this.bubbleUp(this.items.length - 1);
  }

  pop(): AStarNode | undefined {
    const top = this.items[0];
    const last = this.items.pop();
    if (this.items.length > 0 && last) {
      this.items[0] = last;
      this.sinkDown(0);
    }
    return top;
  }

  private bubbleUp(i: number): void {
    let idx = i;
    while (idx > 0) {
      const parent = (idx - 1) >> 1;
      if (this.items[idx]!.f >= this.items[parent]!.f) {
        break;
      }
      const tmp = this.items[idx]!;
      this.items[idx] = this.items[parent]!;
      this.items[parent] = tmp;
      idx = parent;
    }
  }

  private sinkDown(i: number): void {
    let idx = i;
    const len = this.items.length;
    while (true) {
      const left = idx * 2 + 1;
      const right = left + 1;
      let smallest = idx;
      if (left < len && this.items[left]!.f < this.items[smallest]!.f) {
        smallest = left;
      }
      if (right < len && this.items[right]!.f < this.items[smallest]!.f) {
        smallest = right;
      }
      if (smallest === idx) {
        break;
      }
      const tmp = this.items[idx]!;
      this.items[idx] = this.items[smallest]!;
      this.items[smallest] = tmp;
      idx = smallest;
    }
  }
}

export class NavGrid {
  readonly cols: number;
  readonly rows: number;
  readonly cellSize = CELL_SIZE;
  private readonly walkable: Uint8Array;
  private readonly playableBounds: Rect;
  private readonly obstacles: readonly Rect[];
  private readonly agentRadius: number;

  constructor(
    worldSize: Vec2,
    playableBounds: Rect,
    obstacles: readonly Rect[],
    agentRadius = 14,
  ) {
    this.cols = Math.ceil(worldSize.x / CELL_SIZE);
    this.rows = Math.ceil(worldSize.y / CELL_SIZE);
    this.walkable = new Uint8Array(this.cols * this.rows);
    this.playableBounds = playableBounds;
    this.obstacles = obstacles;
    this.agentRadius = agentRadius;
    this.bake();
  }

  private bake(): void {
    for (let r = 0; r < this.rows; r += 1) {
      for (let c = 0; c < this.cols; c += 1) {
        const wx = c * CELL_SIZE + CELL_SIZE * 0.5;
        const wy = r * CELL_SIZE + CELL_SIZE * 0.5;
        this.walkable[r * this.cols + c] = this.isPointClear(wx, wy) ? 1 : 0;
      }
    }
  }

  isPointClear(x: number, y: number): boolean {
    const b = this.playableBounds;
    if (
      x < b.x + this.agentRadius ||
      x > b.x + b.w - this.agentRadius ||
      y < b.y + this.agentRadius ||
      y > b.y + b.h - this.agentRadius
    ) {
      return false;
    }
    for (const rect of this.obstacles) {
      if (
        x >= rect.x - this.agentRadius &&
        x <= rect.x + rect.w + this.agentRadius &&
        y >= rect.y - this.agentRadius &&
        y <= rect.y + rect.h + this.agentRadius
      ) {
        return false;
      }
    }
    return true;
  }

  isWalkableCell(col: number, row: number): boolean {
    if (col < 0 || col >= this.cols || row < 0 || row >= this.rows) {
      return false;
    }
    return this.walkable[row * this.cols + col] === 1;
  }

  worldToCell(pos: Vec2): { col: number; row: number } {
    const col = Math.max(0, Math.min(this.cols - 1, Math.floor(pos.x / CELL_SIZE)));
    const row = Math.max(0, Math.min(this.rows - 1, Math.floor(pos.y / CELL_SIZE)));
    return { col, row };
  }

  cellToWorld(col: number, row: number): Vec2 {
    return {
      x: col * CELL_SIZE + CELL_SIZE * 0.5,
      y: row * CELL_SIZE + CELL_SIZE * 0.5,
    };
  }

  findNearestWalkableCell(col: number, row: number, maxRadius = 10): { col: number; row: number } | null {
    if (this.isWalkableCell(col, row)) {
      return { col, row };
    }
    let best: { col: number; row: number } | null = null;
    let bestDistSq = Infinity;
    for (let rad = 1; rad <= maxRadius; rad += 1) {
      for (let dy = -rad; dy <= rad; dy += 1) {
        for (let dx = -rad; dx <= rad; dx += 1) {
          const nc = col + dx;
          const nr = row + dy;
          if (!this.isWalkableCell(nc, nr)) {
            continue;
          }
          const dSq = dx * dx + dy * dy;
          if (dSq < bestDistSq) {
            bestDistSq = dSq;
            best = { col: nc, row: nr };
          }
        }
      }
      if (best) {
        return best;
      }
    }
    return null;
  }

  hasLineOfSight(a: Vec2, b: Vec2): boolean {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const dist = Math.hypot(dx, dy);
    if (dist < 1) {
      return true;
    }
    const steps = Math.ceil(dist / 6);
    for (let i = 1; i < steps; i += 1) {
      const t = i / steps;
      if (!this.isPointClear(a.x + dx * t, a.y + dy * t)) {
        return false;
      }
    }
    return true;
  }

  findPath(from: Vec2, to: Vec2): Vec2[] {
    const rawStart = this.worldToCell(from);
    const rawGoal = this.worldToCell(to);
    const start = this.findNearestWalkableCell(rawStart.col, rawStart.row);
    const goal = this.findNearestWalkableCell(rawGoal.col, rawGoal.row);

    if (!start || !goal) {
      return [];
    }

    const startWorld = this.cellToWorld(start.col, start.row);
    const goalWorld = this.isPointClear(to.x, to.y)
      ? { x: to.x, y: to.y }
      : this.cellToWorld(goal.col, goal.row);

    if (this.hasLineOfSight(from, goalWorld)) {
      return [goalWorld];
    }

    const total = this.cols * this.rows;
    const gScore = new Float32Array(total);
    gScore.fill(Infinity);
    const cameFrom = new Int32Array(total);
    cameFrom.fill(-1);
    const closed = new Uint8Array(total);

    const startIdx = start.row * this.cols + start.col;
    const goalIdx = goal.row * this.cols + goal.col;

    gScore[startIdx] = 0;
    const open = new MinHeap();
    open.push({
      idx: startIdx,
      g: 0,
      f: Math.hypot(goal.col - start.col, goal.row - start.row),
    });

    const dirs = [
      [1, 0, 1],
      [-1, 0, 1],
      [0, 1, 1],
      [0, -1, 1],
      [1, 1, Math.SQRT2],
      [1, -1, Math.SQRT2],
      [-1, 1, Math.SQRT2],
      [-1, -1, Math.SQRT2],
    ] as const;

    let found = false;
    while (open.size > 0) {
      const curr = open.pop();
      if (!curr) {
        break;
      }
      if (curr.idx === goalIdx) {
        found = true;
        break;
      }
      if (closed[curr.idx] === 1) {
        continue;
      }
      closed[curr.idx] = 1;

      const cc = curr.idx % this.cols;
      const cr = Math.floor(curr.idx / this.cols);

      for (const [dx, dy, cost] of dirs) {
        const nc = cc + dx;
        const nr = cr + dy;
        if (!this.isWalkableCell(nc, nr)) {
          continue;
        }
        if (dx !== 0 && dy !== 0) {
          if (!this.isWalkableCell(cc + dx, cr) || !this.isWalkableCell(cc, cr + dy)) {
            continue;
          }
        }
        const nIdx = nr * this.cols + nc;
        if (closed[nIdx] === 1) {
          continue;
        }
        const tentativeG = curr.g + cost;
        if (tentativeG < gScore[nIdx]!) {
          gScore[nIdx] = tentativeG;
          cameFrom[nIdx] = curr.idx;
          const h = Math.hypot(goal.col - nc, goal.row - nr);
          open.push({ idx: nIdx, g: tentativeG, f: tentativeG + h });
        }
      }
    }

    if (!found) {
      return [];
    }

    const rawPoints: Vec2[] = [];
    let trace = goalIdx;
    while (trace !== -1 && trace !== startIdx) {
      const c = trace % this.cols;
      const r = Math.floor(trace / this.cols);
      rawPoints.push(this.cellToWorld(c, r));
      trace = cameFrom[trace]!;
    }
    rawPoints.reverse();
    if (rawPoints.length > 0) {
      rawPoints[rawPoints.length - 1] = goalWorld;
    } else {
      rawPoints.push(goalWorld);
    }

    // String-pulling / line-of-sight smoothing
    const smoothed: Vec2[] = [];
    let anchor = this.isPointClear(from.x, from.y) ? from : startWorld;
    let i = 0;
    while (i < rawPoints.length) {
      let furthest = i;
      for (let j = rawPoints.length - 1; j > i; j -= 1) {
        if (this.hasLineOfSight(anchor, rawPoints[j]!)) {
          furthest = j;
          break;
        }
      }
      const picked = rawPoints[furthest]!;
      smoothed.push(picked);
      anchor = picked;
      i = furthest + 1;
    }

    return smoothed;
  }
}
