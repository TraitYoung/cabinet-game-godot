import { Container, Graphics, Rectangle, Sprite, Texture } from 'pixi.js';
import { MONARCH_SPRITE_PATH } from '../data/palaceLayout';
import {
  COURTYARD_BASE_MAP,
  COURTYARD_CANVAS_SIZE,
  COURTYARD_ENTRANCE_ROAD,
  COURTYARD_FRONT_MAP,
  COURTYARD_FRONT_STRIPS,
  COURTYARD_INTERACTABLES,
  COURTYARD_ORIGIN,
  COURTYARD_WALL_POLYGONS,
  COURTYARD_WAYPOINTS,
  COURTYARD_WORLD_SIZE,
} from '../data/smallCourtyardLayout';
import type { DialogueRequest, InteractableSpec, Vec2 } from '../data/types';
import type { GameClock } from './clock';
import { resolveCircleVsPolygons } from './collision';
import type { InputManager } from './input';
import {
  createChibiActorVisual,
  createPromptPill,
  loadTextures,
  updateChibiBob,
  updateSmoothCamera,
  type PromptPill,
} from './pixiHelpers';

export class CourtyardScene {
  readonly worldContainer = new Container();

  private readonly ysortLayer = new Container();
  private readonly overlayLayer = new Container();
  private readonly worldWallPolygons: readonly (readonly Vec2[])[];
  private readonly spotIndicators = new Map<string, Graphics>();

  private playerPos: Vec2;
  private playerRoot!: Container;
  private playerSprite!: Sprite;
  private playerAnimTime = 0;
  private promptPill!: PromptPill;
  private activeSpot: InteractableSpec | null = null;
  private hasSnappedCamera = false;

  private readonly clock: GameClock;
  private readonly onDialogueRequest: (req: DialogueRequest) => void;

  constructor(clock: GameClock, onDialogueRequest: (req: DialogueRequest) => void) {
    this.clock = clock;
    this.onDialogueRequest = onDialogueRequest;

    this.worldWallPolygons = COURTYARD_WALL_POLYGONS.map((poly) =>
      poly.map((p) => ({
        x: p.x + COURTYARD_ORIGIN.x,
        y: p.y + COURTYARD_ORIGIN.y,
      })),
    );

    const spawn = COURTYARD_WAYPOINTS.gate_outside!;
    this.playerPos = {
      x: COURTYARD_ORIGIN.x + spawn.x,
      y: COURTYARD_ORIGIN.y + spawn.y,
    };

    this.ysortLayer.sortableChildren = true;
  }

  async init(): Promise<void> {
    const [linearTextures, nearestTextures] = await Promise.all([
      loadTextures([COURTYARD_BASE_MAP, COURTYARD_FRONT_MAP], 'linear'),
      loadTextures([MONARCH_SPRITE_PATH], 'nearest'),
    ]);

    const ground = new Graphics();
    ground
      .rect(0, 0, COURTYARD_WORLD_SIZE.x, COURTYARD_WORLD_SIZE.y)
      .fill({ color: 0x2e3630 });
    const roadFlat = COURTYARD_ENTRANCE_ROAD.flatMap((p) => [p.x, p.y]);
    ground.poly(roadFlat).fill({ color: 0x615e57 });
    this.worldContainer.addChild(ground);

    const baseTex = linearTextures.get(COURTYARD_BASE_MAP);
    if (baseTex) {
      const baseSprite = new Sprite({ texture: baseTex });
      baseSprite.position.set(COURTYARD_ORIGIN.x, COURTYARD_ORIGIN.y);
      this.worldContainer.addChild(baseSprite);
    }

    this.worldContainer.addChild(this.ysortLayer, this.overlayLayer);

    const frontTex = linearTextures.get(COURTYARD_FRONT_MAP);
    if (frontTex) {
      for (const strip of COURTYARD_FRONT_STRIPS) {
        const frame = new Rectangle(strip.x, 0, strip.w, COURTYARD_CANVAS_SIZE.y);
        const stripTex = new Texture({ source: frontTex.source, frame });
        const spr = new Sprite({ texture: stripTex });
        const footWorldY = COURTYARD_ORIGIN.y + strip.footY;
        spr.position.set(COURTYARD_ORIGIN.x + strip.x, COURTYARD_ORIGIN.y);
        spr.zIndex = Math.round(footWorldY);
        this.ysortLayer.addChild(spr);
      }
    }

    for (const spec of COURTYARD_INTERACTABLES) {
      const marker = new Graphics();
      marker
        .roundRect(
          -spec.indicatorSize.x * 0.5,
          -spec.indicatorSize.y * 0.5,
          spec.indicatorSize.x,
          spec.indicatorSize.y,
          6,
        )
        .stroke({ color: spec.accentColor, width: 2, alpha: 0.75 });
      marker.position.set(spec.x, spec.y);
      marker.visible = false;
      marker.eventMode = 'static';
      marker.cursor = 'pointer';
      marker.on('pointertap', () => {
        if (Math.hypot(this.playerPos.x - spec.x, this.playerPos.y - spec.y) <= 90) {
          this.triggerSpot(spec);
        }
      });
      this.overlayLayer.addChild(marker);
      this.spotIndicators.set(spec.id, marker);
    }

    const monarchTex = nearestTextures.get(MONARCH_SPRITE_PATH);
    if (monarchTex) {
      const visual = createChibiActorVisual(monarchTex);
      this.playerRoot = visual.root;
      this.playerSprite = visual.sprite;
      this.playerRoot.position.set(this.playerPos.x, this.playerPos.y);
      this.playerRoot.zIndex = Math.round(this.playerPos.y);
      this.ysortLayer.addChild(this.playerRoot);
    }

    this.promptPill = createPromptPill();
    this.overlayLayer.addChild(this.promptPill.root);
  }

  handleInteract(): boolean {
    if (!this.activeSpot) {
      return false;
    }
    this.triggerSpot(this.activeSpot);
    return true;
  }

  update(dt: number, input: InputManager, viewportSize: Vec2, zoom: number): void {
    const isPaused = this.clock.isDialoguePaused;

    if (!isPaused && this.playerRoot) {
      const move = input.getMovementVector();
      const moving = move.x !== 0 || move.y !== 0;
      if (moving) {
        const speed = 225;
        const candidate = {
          x: this.playerPos.x + move.x * speed * dt,
          y: this.playerPos.y + move.y * speed * dt,
        };
        this.playerPos = resolveCircleVsPolygons(candidate, 12, this.worldWallPolygons, {
          x: 0,
          y: 0,
          w: COURTYARD_WORLD_SIZE.x,
          h: COURTYARD_WORLD_SIZE.y,
        });
        this.playerRoot.position.set(this.playerPos.x, this.playerPos.y);
        this.playerRoot.zIndex = Math.round(this.playerPos.y);

        if (move.x < -0.1) {
          this.playerSprite.scale.x = -1;
        } else if (move.x > 0.1) {
          this.playerSprite.scale.x = 1;
        }
        this.playerAnimTime += dt * 12;
        updateChibiBob(this.playerSprite, this.playerAnimTime, true);
      } else {
        this.playerAnimTime += dt * 2.6;
        updateChibiBob(this.playerSprite, this.playerAnimTime, false);
      }
      this.refreshActiveSpot();
    } else if (this.playerSprite) {
      this.playerAnimTime += dt * 2.6;
      updateChibiBob(this.playerSprite, this.playerAnimTime, false);
    }

    updateSmoothCamera(
      this.worldContainer,
      this.playerPos,
      COURTYARD_WORLD_SIZE,
      viewportSize,
      zoom,
      dt,
      !this.hasSnappedCamera,
    );
    this.hasSnappedCamera = true;
  }

  private refreshActiveSpot(): void {
    const sensorRadiusSq = 64 * 64;
    let best: InteractableSpec | null = null;
    let bestDistSq = Infinity;

    for (const spec of COURTYARD_INTERACTABLES) {
      const dSq = (this.playerPos.x - spec.x) ** 2 + (this.playerPos.y - spec.y) ** 2;
      if (dSq <= sensorRadiusSq && dSq < bestDistSq) {
        bestDistSq = dSq;
        best = spec;
      }
    }

    this.activeSpot = best;
    for (const [id, marker] of this.spotIndicators) {
      marker.visible = best?.id === id;
    }

    if (!best) {
      this.promptPill.root.visible = false;
      return;
    }
    this.promptPill.setText(best.promptHint);
    this.promptPill.root.position.set(best.x, best.y - best.indicatorSize.y * 0.5 - 18);
    this.promptPill.root.visible = true;
  }

  private triggerSpot(spec: InteractableSpec): void {
    this.onDialogueRequest({
      mode: 'info',
      speakerName: spec.displayTitle,
      speakerRole: '宫城设施',
      badgeText: '建',
      accentColor: spec.accentColor,
      lines: spec.infoLines,
    });
  }

  destroy(): void {
    this.worldContainer.destroy({ children: true });
  }
}
