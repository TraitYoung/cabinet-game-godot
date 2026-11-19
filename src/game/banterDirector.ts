import { getBanterLines } from '../data/cabinetDatabase';
import type { BanterLine, Vec2 } from '../data/types';

export interface BanterParticipant {
  readonly id: string;
  readonly idleThoughts: readonly string[];
  getPosition(): Vec2;
  isAvailableForBanter(): boolean;
  isChatting(): boolean;
  setBantering(active: boolean, lookAt?: Vec2): void;
  showOverheadBubble(text: string, duration: number): void;
}

interface ActiveBanter {
  a: BanterParticipant;
  b: BanterParticipant;
  lines: readonly BanterLine[];
  index: number;
  stepTimer: number;
}

function randomRange(min: number, max: number): number {
  return min + Math.random() * (max - min);
}

export class BanterDirector {
  private members: BanterParticipant[] = [];
  private checkTimer = 4.5;
  private soloTimer = 7.0;
  private activeBanter: ActiveBanter | null = null;

  registerMembers(members: BanterParticipant[]): void {
    this.members = members;
  }

  tick(dt: number, isDialoguePaused: boolean): void {
    if (isDialoguePaused || this.members.length === 0) {
      return;
    }

    if (this.activeBanter) {
      this.tickActiveBanter(dt);
    } else {
      this.checkTimer -= dt;
      if (this.checkTimer <= 0) {
        this.checkTimer = randomRange(6.5, 10.5);
        this.tryTriggerPairBanter();
      }
    }

    this.soloTimer -= dt;
    if (this.soloTimer <= 0) {
      this.soloTimer = randomRange(8.0, 14.0);
      this.tryTriggerSoloThought();
    }
  }

  private tickActiveBanter(dt: number): void {
    const active = this.activeBanter;
    if (!active) {
      return;
    }
    if (active.a.isChatting() || active.b.isChatting()) {
      this.finishActiveBanter();
      return;
    }
    active.stepTimer -= dt;
    if (active.stepTimer <= 0) {
      active.index += 1;
      if (active.index >= active.lines.length) {
        this.finishActiveBanter();
        return;
      }
      this.showCurrentLine(active);
      active.stepTimer = 2.8;
    }
  }

  private showCurrentLine(active: ActiveBanter): void {
    const line = active.lines[active.index];
    if (!line) {
      return;
    }
    if (line.id === active.a.id) {
      active.a.showOverheadBubble(line.text, 3.2);
    } else if (line.id === active.b.id) {
      active.b.showOverheadBubble(line.text, 3.2);
    }
  }

  private finishActiveBanter(): void {
    if (!this.activeBanter) {
      return;
    }
    this.activeBanter.a.setBantering(false);
    this.activeBanter.b.setBantering(false);
    this.activeBanter = null;
  }

  private tryTriggerPairBanter(): void {
    const candidates: Array<[BanterParticipant, BanterParticipant]> = [];
    for (let i = 0; i < this.members.length; i += 1) {
      for (let j = i + 1; j < this.members.length; j += 1) {
        const a = this.members[i]!;
        const b = this.members[j]!;
        if (!a.isAvailableForBanter() || !b.isAvailableForBanter()) {
          continue;
        }
        const pa = a.getPosition();
        const pb = b.getPosition();
        if (Math.hypot(pa.x - pb.x, pa.y - pb.y) <= 230) {
          candidates.push([a, b]);
        }
      }
    }

    if (candidates.length === 0) {
      return;
    }

    const pair = candidates[Math.floor(Math.random() * candidates.length)]!;
    const [first, second] = pair;
    const lines = getBanterLines(first.id, second.id);
    if (lines.length === 0) {
      return;
    }

    first.setBantering(true, second.getPosition());
    second.setBantering(true, first.getPosition());
    this.activeBanter = {
      a: first,
      b: second,
      lines,
      index: 0,
      stepTimer: 2.8,
    };
    this.showCurrentLine(this.activeBanter);
  }

  private tryTriggerSoloThought(): void {
    const free = this.members.filter((m) => m.isAvailableForBanter());
    if (free.length === 0) {
      return;
    }
    const picked = free[Math.floor(Math.random() * free.length)]!;
    if (picked.idleThoughts.length === 0) {
      return;
    }
    const thought = picked.idleThoughts[Math.floor(Math.random() * picked.idleThoughts.length)]!;
    picked.showOverheadBubble(thought, 2.8);
  }
}
