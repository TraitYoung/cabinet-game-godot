import type { TimeSlotId } from '../data/types';

export const SLOT_LABELS: Record<TimeSlotId, string> = {
  morning: '晨启 · 宫门初开',
  focus: '政务 · 内阁当值',
  refuel: '午憩 · 御苑闲话',
  free_soul: '夜游 · 宫灯华彩',
  shutdown: '宵禁 · 巡夜安寝',
};

const SLOT_START_HOURS: readonly number[] = [8, 10, 12, 14, 18, 23];

export class GameClock {
  day = 1;
  totalMinutes = 8 * 60 + 30;
  speedMultiplier = 1;
  minutesPerRealSecond = 6;
  isDialoguePaused = false;
  currentSlot: TimeSlotId = 'morning';

  private lastEmittedMinute = -1;
  private slotListeners = new Set<(slotId: TimeSlotId, slotLabel: string) => void>();
  private changeListeners = new Set<() => void>();

  constructor() {
    this.currentSlot = this.computeSlot(this.getHour());
    this.lastEmittedMinute = this.getMinute();
  }

  onSlotChanged(cb: (slotId: TimeSlotId, slotLabel: string) => void): () => void {
    this.slotListeners.add(cb);
    return () => this.slotListeners.delete(cb);
  }

  onChanged(cb: () => void): () => void {
    this.changeListeners.add(cb);
    return () => this.changeListeners.delete(cb);
  }

  getHour(): number {
    return Math.floor(this.totalMinutes / 60) % 24;
  }

  getMinute(): number {
    return Math.floor(this.totalMinutes) % 60;
  }

  getFormattedTime(): string {
    const h = String(this.getHour()).padStart(2, '0');
    const m = String(this.getMinute()).padStart(2, '0');
    return `${h}:${m}`;
  }

  getSlotLabel(slotId: TimeSlotId = this.currentSlot): string {
    return SLOT_LABELS[slotId] ?? '日常';
  }

  computeSlot(hour: number): TimeSlotId {
    if (hour >= 8 && hour < 10) {
      return 'morning';
    }
    if (hour >= 12 && hour < 14) {
      return 'refuel';
    }
    if ((hour >= 10 && hour < 12) || (hour >= 14 && hour < 18)) {
      return 'focus';
    }
    if (hour >= 18 && hour < 23) {
      return 'free_soul';
    }
    return 'shutdown';
  }

  tick(dtSeconds: number): void {
    if (this.isDialoguePaused || this.speedMultiplier <= 0) {
      return;
    }
    this.totalMinutes += dtSeconds * this.minutesPerRealSecond * this.speedMultiplier;
    while (this.totalMinutes >= 1440) {
      this.totalMinutes -= 1440;
      this.day += 1;
    }

    const hour = this.getHour();
    const minute = this.getMinute();
    let changed = false;

    if (minute !== this.lastEmittedMinute) {
      this.lastEmittedMinute = minute;
      changed = true;
    }

    const nextSlot = this.computeSlot(hour);
    if (nextSlot !== this.currentSlot) {
      this.currentSlot = nextSlot;
      this.emitSlotChanged();
      changed = true;
    }

    if (changed) {
      this.emitChanged();
    }
  }

  setSpeed(multiplier: number): void {
    this.speedMultiplier = multiplier;
    this.emitChanged();
  }

  cycleSpeed(): void {
    if (this.speedMultiplier <= 0) {
      this.setSpeed(1);
    } else if (this.speedMultiplier < 2.5) {
      this.setSpeed(3);
    } else {
      this.setSpeed(0);
    }
  }

  skipToNextSlot(): void {
    const hour = this.getHour();
    let targetHour = -1;
    for (const startHour of SLOT_START_HOURS) {
      if (startHour > hour) {
        targetHour = startHour;
        break;
      }
    }
    if (targetHour === -1) {
      this.day += 1;
      targetHour = 8;
    }

    this.totalMinutes = targetHour * 60 + 5;
    this.lastEmittedMinute = this.getMinute();
    this.currentSlot = this.computeSlot(this.getHour());
    this.emitSlotChanged();
    this.emitChanged();
  }

  private emitSlotChanged(): void {
    const label = this.getSlotLabel();
    for (const cb of this.slotListeners) {
      cb(this.currentSlot, label);
    }
  }

  private emitChanged(): void {
    for (const cb of this.changeListeners) {
      cb();
    }
  }
}
