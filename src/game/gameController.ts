import { Application } from 'pixi.js';
import type { DialogueRequest, HudSnapshot, SceneMode, TimeSlotId } from '../data/types';
import { GameClock } from './clock';
import { CourtyardScene } from './courtyardScene';
import { InputManager } from './input';
import { PalaceScene } from './palaceScene';

export interface GameControllerCallbacks {
  onSnapshot: (snapshot: HudSnapshot) => void;
  onDialogueRequest: (req: DialogueRequest) => void;
  onToast: (message: string) => void;
}

export class GameController {
  private readonly hostEl: HTMLElement;
  private readonly callbacks: GameControllerCallbacks;
  private readonly clock = new GameClock();

  private app: Application | null = null;
  private input: InputManager | null = null;
  private palaceScene: PalaceScene | null = null;
  private courtyardScene: CourtyardScene | null = null;
  private sceneMode: SceneMode;
  private zoom = 1;
  private rosterTimer = 0;
  private disposed = false;
  private switchingScene = false;
  private unsubs: Array<() => void> = [];

  private readonly handleWheel = (e: WheelEvent): void => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 0.12 : -0.12;
    const nextZoom = Math.max(0.75, Math.min(1.8, Math.round((this.zoom + delta) * 100) / 100));
    if (nextZoom !== this.zoom) {
      this.zoom = nextZoom;
      this.emitSnapshot();
    }
  };

  constructor(
    hostEl: HTMLElement,
    initialSceneMode: SceneMode,
    callbacks: GameControllerCallbacks,
  ) {
    this.hostEl = hostEl;
    this.sceneMode = initialSceneMode;
    this.callbacks = callbacks;
  }

  async init(): Promise<void> {
    const app = new Application();
    await app.init({
      resizeTo: this.hostEl,
      background: '#161b1c',
      antialias: false,
      resolution: Math.min(window.devicePixelRatio || 1, 2),
      autoDensity: true,
    });

    if (this.disposed) {
      app.destroy(true, { children: true });
      return;
    }

    this.app = app;
    this.hostEl.appendChild(app.canvas);
    app.canvas.style.display = 'block';
    app.canvas.addEventListener('wheel', this.handleWheel, { passive: false });

    this.input = new InputManager({
      onInteract: () => {
        if (this.clock.isDialoguePaused) {
          return;
        }
        if (this.sceneMode === 'palace') {
          this.palaceScene?.handleInteract();
        } else {
          this.courtyardScene?.handleInteract();
        }
      },
      onToggleSpeed: () => {
        this.clock.cycleSpeed();
      },
      onCancel: () => {
        // DialogueModal handles Escape while open; no-op here.
      },
    });

    this.unsubs.push(
      this.clock.onSlotChanged((slotId: TimeSlotId, slotLabel: string) => {
        this.palaceScene?.onSlotChanged(slotId);
        this.callbacks.onToast(`时辰流转：${slotLabel}`);
        this.emitSnapshot();
      }),
      this.clock.onChanged(() => {
        this.emitSnapshot();
      }),
    );

    await this.loadActiveScene();
    if (this.disposed) {
      return;
    }

    this.emitSnapshot();
    app.ticker.add(this.tick);
  }

  private readonly tick = (): void => {
    if (this.disposed || !this.app || !this.input) {
      return;
    }
    const dt = Math.min(this.app.ticker.deltaMS / 1000, 0.05);
    this.clock.tick(dt);

    const viewport = {
      x: this.app.screen.width,
      y: this.app.screen.height,
    };

    if (this.sceneMode === 'palace') {
      this.palaceScene?.update(dt, this.input, viewport, this.zoom);
      this.rosterTimer += dt;
      if (this.rosterTimer >= 0.4) {
        this.rosterTimer = 0;
        this.emitSnapshot();
      }
    } else {
      this.courtyardScene?.update(dt, this.input, viewport, this.zoom);
    }
  };

  setSpeed(multiplier: number): void {
    this.clock.setSpeed(multiplier);
  }

  skipToNextSlot(): void {
    this.clock.skipToNextSlot();
  }

  resetZoom(): void {
    this.zoom = 1;
    this.emitSnapshot();
  }

  closeDialogue(): void {
    this.clock.isDialoguePaused = false;
    this.palaceScene?.onDialogueClosed();
    this.emitSnapshot();
  }

  async switchScene(nextMode: SceneMode): Promise<void> {
    if (nextMode === this.sceneMode || this.switchingScene || this.disposed) {
      return;
    }
    this.switchingScene = true;
    try {
      this.clock.isDialoguePaused = false;
      this.sceneMode = nextMode;
      await this.loadActiveScene();
      if (!this.disposed) {
        this.emitSnapshot();
      }
    } finally {
      this.switchingScene = false;
    }
  }

  private async loadActiveScene(): Promise<void> {
    if (!this.app) {
      return;
    }

    if (this.palaceScene) {
      this.app.stage.removeChild(this.palaceScene.worldContainer);
      this.palaceScene.destroy();
      this.palaceScene = null;
    }
    if (this.courtyardScene) {
      this.app.stage.removeChild(this.courtyardScene.worldContainer);
      this.courtyardScene.destroy();
      this.courtyardScene = null;
    }

    const requestDialogue = (req: DialogueRequest): void => {
      this.clock.isDialoguePaused = true;
      this.callbacks.onDialogueRequest(req);
      this.emitSnapshot();
    };

    if (this.sceneMode === 'palace') {
      const scene = new PalaceScene(this.clock, requestDialogue);
      await scene.init();
      if (this.disposed || this.sceneMode !== 'palace') {
        scene.destroy();
        return;
      }
      this.palaceScene = scene;
      this.app.stage.addChild(scene.worldContainer);
    } else {
      const scene = new CourtyardScene(this.clock, requestDialogue);
      await scene.init();
      if (this.disposed || this.sceneMode !== 'courtyard') {
        scene.destroy();
        return;
      }
      this.courtyardScene = scene;
      this.app.stage.addChild(scene.worldContainer);
    }
  }

  private emitSnapshot(): void {
    this.callbacks.onSnapshot({
      day: this.clock.day,
      formattedTime: this.clock.getFormattedTime(),
      slotId: this.clock.currentSlot,
      slotLabel: this.clock.getSlotLabel(),
      speedMultiplier: this.clock.speedMultiplier,
      sceneMode: this.sceneMode,
      roster: this.sceneMode === 'palace' && this.palaceScene ? this.palaceScene.getRoster() : [],
      zoom: this.zoom,
    });
  }

  destroy(): void {
    this.disposed = true;
    for (const unsub of this.unsubs) {
      unsub();
    }
    this.unsubs = [];

    this.input?.destroy();
    this.input = null;

    if (this.app) {
      this.app.ticker.remove(this.tick);
      this.app.canvas.removeEventListener('wheel', this.handleWheel);
      this.palaceScene?.destroy();
      this.courtyardScene?.destroy();
      this.palaceScene = null;
      this.courtyardScene = null;
      this.app.destroy(true, { children: true });
      this.app = null;
    }
  }
}
