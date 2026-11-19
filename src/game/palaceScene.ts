import { Container, Graphics, Sprite, Text, Texture } from 'pixi.js';
import { getAllProfiles, getCouncilMeetingEntries } from '../data/cabinetDatabase';
import {
  MONARCH_SPRITE_PATH,
  PALACE_BASE_MAP,
  PALACE_FRONT_MAP,
  PALACE_FURNITURE,
  PALACE_INTERACTABLES,
  PALACE_LANTERNS,
  PALACE_LANTERN_SPRITE,
  PALACE_LOTUS_POND,
  PALACE_PLAYABLE_BOUNDS,
  PALACE_TREES,
  PALACE_WALLS,
  PALACE_WORLD_SIZE,
  PALACE_ZONE_LABELS,
  getWaypointPosition,
  getZoneNameForPosition,
} from '../data/palaceLayout';
import type {
  CharacterProfile,
  DialogueRequest,
  InteractableSpec,
  Rect,
  RosterEntry,
  TimeSlotId,
  Vec2,
} from '../data/types';
import { BanterDirector, type BanterParticipant } from './banterDirector';
import type { GameClock } from './clock';
import { resolveCircleVsRects } from './collision';
import type { InputManager } from './input';
import { NavGrid } from './pathfinding';
import {
  createChibiActorVisual,
  createPromptPill,
  loadTextures,
  snap2,
  updateChibiBob,
  updateSmoothCamera,
  type PromptPill,
} from './pixiHelpers';

type MinisterState = 'WORKING' | 'MOVING' | 'CHATTING';

function randomRange(min: number, max: number): number {
  return min + Math.random() * (max - min);
}

function rgbToHexNumber(r: number, g: number, b: number): number {
  const ri = Math.max(0, Math.min(255, Math.round(r * 255)));
  const gi = Math.max(0, Math.min(255, Math.round(g * 255)));
  const bi = Math.max(0, Math.min(255, Math.round(b * 255)));
  return (ri << 16) | (gi << 8) | bi;
}

function getTargetAmbientRgb(slotId: TimeSlotId): readonly [number, number, number] {
  switch (slotId) {
    case 'morning':
      return [1.0, 0.96, 0.9];
    case 'focus':
      return [1.0, 1.0, 1.0];
    case 'refuel':
      return [1.0, 0.98, 0.92];
    case 'free_soul':
      return [0.84, 0.78, 0.92];
    case 'shutdown':
      return [0.56, 0.6, 0.76];
  }
}

class MinisterActor implements BanterParticipant {
  readonly id: string;
  readonly profile: CharacterProfile;
  readonly idleThoughts: readonly string[];
  readonly root: Container;
  readonly sprite: Sprite;
  readonly bubbleContainer: Container;

  private readonly bubbleBg: Graphics;
  private readonly bubbleText: Text;
  private readonly navGrid: NavGrid;

  pos: Vec2;
  private homeTarget: Vec2;
  private path: Vec2[] = [];
  private state: MinisterState = 'WORKING';
  private facingDir: Vec2 = { x: 0, y: 1 };
  private wanderTimer: number;
  private isBantering = false;
  private animTime: number;
  private bubbleTimer = 0;

  constructor(
    profile: CharacterProfile,
    texture: Texture,
    initialSlot: TimeSlotId,
    navGrid: NavGrid,
    onSelect: (minister: MinisterActor) => void,
  ) {
    this.id = profile.id;
    this.profile = profile;
    this.idleThoughts = profile.idleThoughts;
    this.navGrid = navGrid;

    const slotWp = profile.scheduleWaypoints[initialSlot] ?? 'courtyard_table';
    const base = getWaypointPosition(slotWp);
    this.pos = {
      x: base.x + profile.personalOffset.x,
      y: base.y + profile.personalOffset.y,
    };
    this.homeTarget = { x: this.pos.x, y: this.pos.y };
    this.wanderTimer = randomRange(4, 9);
    this.animTime = randomRange(0, Math.PI * 2);

    const visual = createChibiActorVisual(
      texture,
      profile.displayName,
      profile.accentColor,
    );
    this.root = visual.root;
    this.sprite = visual.sprite;
    this.root.position.set(this.pos.x, this.pos.y);
    this.root.zIndex = Math.round(this.pos.y);
    this.root.eventMode = 'static';
    this.root.cursor = 'pointer';
    this.root.on('pointertap', () => onSelect(this));

    this.bubbleContainer = new Container();
    this.bubbleContainer.visible = false;
    this.bubbleBg = new Graphics();
    this.bubbleText = new Text({
      text: '',
      resolution: 2,
      style: {
        fontFamily: 'system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif',
        fontSize: 12,
        fill: '#f5f5f0',
        wordWrap: true,
        wordWrapWidth: 210,
        breakWords: true,
      },
    });
    this.bubbleContainer.addChild(this.bubbleBg, this.bubbleText);
  }

  getPosition(): Vec2 {
    return { x: this.pos.x, y: this.pos.y };
  }

  isAvailableForBanter(): boolean {
    return this.state !== 'CHATTING' && !this.isBantering;
  }

  isChatting(): boolean {
    return this.state === 'CHATTING';
  }

  setBantering(active: boolean, lookAt?: Vec2): void {
    this.isBantering = active;
    if (active && lookAt) {
      const dx = lookAt.x - this.pos.x;
      const dy = lookAt.y - this.pos.y;
      const len = Math.hypot(dx, dy);
      if (len > 0.01) {
        this.facingDir = { x: dx / len, y: dy / len };
        this.updateFacing();
      }
      this.state = 'WORKING';
      this.path = [];
    }
  }

  startConversation(playerPos: Vec2): CharacterProfile {
    this.state = 'CHATTING';
    this.isBantering = false;
    this.path = [];
    this.hideOverheadBubble();
    const dx = playerPos.x - this.pos.x;
    const dy = playerPos.y - this.pos.y;
    const len = Math.hypot(dx, dy);
    if (len > 0.01) {
      this.facingDir = { x: dx / len, y: dy / len };
      this.updateFacing();
    }
    return this.profile;
  }

  endConversation(): void {
    if (this.state === 'CHATTING') {
      this.state = 'WORKING';
      this.wanderTimer = randomRange(4, 8);
    }
  }

  onSlotChanged(slotId: TimeSlotId): void {
    const wpName = this.profile.scheduleWaypoints[slotId] ?? 'courtyard_table';
    const base = getWaypointPosition(wpName);
    this.homeTarget = {
      x: base.x + this.profile.personalOffset.x,
      y: base.y + this.profile.personalOffset.y,
    };
    if (this.state !== 'CHATTING') {
      this.moveTo(this.homeTarget);
    }
  }

  showOverheadBubble(text: string, duration = 3.2): void {
    this.bubbleText.text = text;
    const padX = 8;
    const padY = 5;
    const w = Math.max(60, Math.ceil(this.bubbleText.width + padX * 2));
    const h = Math.max(24, Math.ceil(this.bubbleText.height + padY * 2));
    this.bubbleText.position.set(padX, padY);

    this.bubbleBg.clear();
    this.bubbleBg
      .roundRect(0, 0, w, h, 6)
      .fill({ color: 0x1c1e29, alpha: 0.92 })
      .stroke({ color: this.profile.accentColor, width: 1 });

    this.bubbleContainer.position.set(this.pos.x - w * 0.5, this.pos.y - 76 - h);
    this.bubbleContainer.visible = true;
    this.bubbleTimer = duration;
  }

  hideOverheadBubble(): void {
    this.bubbleContainer.visible = false;
    this.bubbleTimer = 0;
  }

  getStatusLabel(): string {
    if (this.state === 'CHATTING') {
      return '侍驾中';
    }
    if (this.isBantering) {
      return '同僚闲谈';
    }
    if (this.state === 'MOVING') {
      return '巡走换岗';
    }
    return '当值';
  }

  update(dt: number, isPaused: boolean): void {
    if (this.bubbleTimer > 0) {
      this.bubbleTimer -= dt;
      if (this.bubbleTimer <= 0) {
        this.hideOverheadBubble();
      } else {
        const bw = this.bubbleBg.width;
        const bh = this.bubbleBg.height;
        this.bubbleContainer.position.set(this.pos.x - bw * 0.5, this.pos.y - 76 - bh);
      }
    }

    if (this.state === 'CHATTING') {
      this.animTime += dt * 2.4;
      updateChibiBob(this.sprite, this.animTime, false);
      return;
    }

    if (isPaused) {
      this.animTime += dt * 2.4;
      updateChibiBob(this.sprite, this.animTime, false);
      return;
    }

    const moveSpeed = 115;
    if (this.state === 'MOVING') {
      const target = this.path[0];
      if (!target) {
        this.state = 'WORKING';
        this.wanderTimer = randomRange(5, 11);
        this.animTime += dt * 2.4;
        updateChibiBob(this.sprite, this.animTime, false);
        return;
      }

      const dx = target.x - this.pos.x;
      const dy = target.y - this.pos.y;
      const dist = Math.hypot(dx, dy);
      const step = moveSpeed * dt;

      if (dist <= Math.max(4, step)) {
        this.pos.x = target.x;
        this.pos.y = target.y;
        this.path.shift();
        if (this.path.length === 0) {
          this.state = 'WORKING';
          this.wanderTimer = randomRange(5, 11);
        }
      } else {
        this.facingDir = { x: dx / dist, y: dy / dist };
        this.pos.x += this.facingDir.x * step;
        this.pos.y += this.facingDir.y * step;
        this.updateFacing();
      }

      this.root.position.set(this.pos.x, this.pos.y);
      this.root.zIndex = Math.round(this.pos.y);
      this.animTime += dt * 11;
      updateChibiBob(this.sprite, this.animTime, true);
      return;
    }

    this.animTime += dt * 2.4;
    updateChibiBob(this.sprite, this.animTime, false);

    if (!this.isBantering) {
      this.wanderTimer -= dt;
      if (this.wanderTimer <= 0) {
        this.wanderTimer = randomRange(6, 13);
        const target = {
          x: this.homeTarget.x + randomRange(-28, 28),
          y: this.homeTarget.y + randomRange(-22, 22),
        };
        this.moveTo(target);
      }
    }
  }

  private moveTo(targetPos: Vec2): void {
    const nextPath = this.navGrid.findPath(this.pos, targetPos);
    if (nextPath.length > 0) {
      this.path = nextPath;
      this.state = 'MOVING';
    } else {
      this.path = [];
      this.state = 'WORKING';
    }
  }

  private updateFacing(): void {
    if (this.facingDir.x < -0.1) {
      this.sprite.scale.x = -1;
    } else if (this.facingDir.x > 0.1) {
      this.sprite.scale.x = 1;
    }
  }
}

export class PalaceScene {
  readonly worldContainer = new Container();

  private readonly litWorldLayer = new Container();
  private readonly ysortLayer = new Container();
  private readonly nightLampsLayer = new Container();
  private readonly plaquesLayer = new Container();
  private readonly bubblesLayer = new Container();

  private readonly obstacles: Rect[] = [];
  private readonly navGrid: NavGrid;
  private readonly banterDirector = new BanterDirector();
  private readonly ministers: MinisterActor[] = [];
  private readonly spotIndicators = new Map<string, Graphics>();

  private playerPos: Vec2;
  private playerRoot!: Container;
  private playerSprite!: Sprite;
  private playerAnimTime = 0;
  private promptPill!: PromptPill;

  private activeTarget:
    | { kind: 'minister'; actor: MinisterActor }
    | { kind: 'spot'; spec: InteractableSpec }
    | null = null;

  private ambientRgb: [number, number, number] = [1.0, 0.96, 0.9];
  private targetAmbientRgb: readonly [number, number, number] = [1.0, 0.96, 0.9];
  private hasSnappedCamera = false;

  private readonly clock: GameClock;
  private readonly onDialogueRequest: (req: DialogueRequest) => void;

  constructor(clock: GameClock, onDialogueRequest: (req: DialogueRequest) => void) {
    this.clock = clock;
    this.onDialogueRequest = onDialogueRequest;

    for (const w of PALACE_WALLS) {
      this.obstacles.push(w.rect);
    }
    this.obstacles.push(PALACE_LOTUS_POND.rect);
    for (const f of PALACE_FURNITURE) {
      this.obstacles.push(f.rect);
    }

    this.navGrid = new NavGrid(
      PALACE_WORLD_SIZE,
      PALACE_PLAYABLE_BOUNDS,
      this.obstacles,
      14,
    );

    const spawn = getWaypointPosition('player_spawn');
    this.playerPos = { x: spawn.x, y: spawn.y };

    this.ysortLayer.sortableChildren = true;
    this.worldContainer.addChild(
      this.litWorldLayer,
      this.nightLampsLayer,
      this.plaquesLayer,
      this.bubblesLayer,
    );
  }

  async init(): Promise<void> {
    const profiles = getAllProfiles();
    const paths: string[] = [
      PALACE_BASE_MAP,
      PALACE_FRONT_MAP,
      PALACE_LANTERN_SPRITE,
      MONARCH_SPRITE_PATH,
      ...PALACE_FURNITURE.map((f) => f.spritePath),
      ...PALACE_TREES.map((t) => t.spritePath),
      ...profiles.map((p) => p.chibiSpritePath),
    ];
    const textures = await loadTextures(paths, 'nearest');

    const baseTex = textures.get(PALACE_BASE_MAP);
    if (baseTex) {
      const baseSprite = new Sprite({ texture: baseTex });
      this.litWorldLayer.addChild(baseSprite);
    }

    this.litWorldLayer.addChild(this.ysortLayer);

    // 15 furniture props + plaques
    for (const f of PALACE_FURNITURE) {
      const tex = textures.get(f.spritePath);
      const cx = f.rect.x + f.rect.w * 0.5;
      const endY = f.rect.y + f.rect.h;
      const footX = snap2(cx);
      const footY = snap2(endY - 4);

      if (tex) {
        const spr = new Sprite({ texture: tex });
        spr.position.set(footX + snap2(-tex.width * 0.5), footY + snap2(-tex.height + 2));
        spr.zIndex = Math.round(footY);
        this.ysortLayer.addChild(spr);
      }

      const plaqueY = f.labelAbove
        ? endY - 4 - f.visualSize.y - 8
        : endY + 10;
      this.addPlaque(f.label, { x: cx + f.plaqueOffset.x, y: plaqueY + f.plaqueOffset.y }, false);
    }

    // Lotus pond plaque
    const pond = PALACE_LOTUS_POND.rect;
    this.addPlaque(
      PALACE_LOTUS_POND.label,
      { x: pond.x + pond.w * 0.5, y: pond.y + pond.h + 10 },
      false,
    );

    // Trees
    for (const t of PALACE_TREES) {
      const tex = textures.get(t.spritePath);
      if (!tex) {
        continue;
      }
      const fx = snap2(t.pos.x);
      const fy = snap2(t.pos.y);
      const spr = new Sprite({ texture: tex });
      spr.position.set(fx + snap2(-tex.width * 0.5), fy + snap2(-tex.height + t.bottomPad));
      spr.zIndex = Math.round(fy);
      this.ysortLayer.addChild(spr);
    }

    // Lanterns + night lamp glow rings
    const lanternTex = textures.get(PALACE_LANTERN_SPRITE);
    for (const lp of PALACE_LANTERNS) {
      const sx = snap2(lp.x);
      const sy = snap2(lp.y);
      if (lanternTex) {
        const spr = new Sprite({ texture: lanternTex });
        spr.position.set(
          sx + snap2(-lanternTex.width * 0.5),
          sy + snap2(-lanternTex.height + 4),
        );
        spr.zIndex = Math.round(sy);
        this.ysortLayer.addChild(spr);
      }
      this.addLanternGlow({ x: sx, y: sy - 56 });
    }

    // Front eaves overlay
    const frontTex = textures.get(PALACE_FRONT_MAP);
    if (frontTex) {
      const frontSprite = new Sprite({ texture: frontTex });
      this.litWorldLayer.addChild(frontSprite);
    }

    // Zone header plaques
    for (const z of PALACE_ZONE_LABELS) {
      this.addPlaque(z.text, z.pos, true);
    }

    // Interactable floor markers (click-to-inspect when close + subtle highlight)
    for (const spec of PALACE_INTERACTABLES) {
      const ring = new Graphics();
      ring
        .roundRect(
          -spec.indicatorSize.x * 0.5,
          -spec.indicatorSize.y * 0.5,
          spec.indicatorSize.x,
          spec.indicatorSize.y,
          6,
        )
        .stroke({ color: spec.accentColor, width: 2, alpha: 0.75 });
      ring.position.set(spec.x, spec.y);
      ring.visible = false;
      ring.eventMode = 'static';
      ring.cursor = 'pointer';
      ring.on('pointertap', () => {
        if (Math.hypot(this.playerPos.x - spec.x, this.playerPos.y - spec.y) <= 90) {
          this.triggerSpot(spec);
        }
      });
      this.plaquesLayer.addChild(ring);
      this.spotIndicators.set(spec.id, ring);
    }

    // Player Royal
    const monarchTex = textures.get(MONARCH_SPRITE_PATH);
    if (monarchTex) {
      const visual = createChibiActorVisual(monarchTex);
      this.playerRoot = visual.root;
      this.playerSprite = visual.sprite;
      this.playerRoot.position.set(this.playerPos.x, this.playerPos.y);
      this.playerRoot.zIndex = Math.round(this.playerPos.y);
      this.ysortLayer.addChild(this.playerRoot);
    }

    // 12 Ministers
    for (const prof of profiles) {
      const chibiTex = textures.get(prof.chibiSpritePath);
      if (!chibiTex) {
        continue;
      }
      const actor = new MinisterActor(
        prof,
        chibiTex,
        this.clock.currentSlot,
        this.navGrid,
        (clicked) => {
          const p = clicked.getPosition();
          if (Math.hypot(this.playerPos.x - p.x, this.playerPos.y - p.y) <= 90) {
            this.triggerMinister(clicked);
          }
        },
      );
      this.ministers.push(actor);
      this.ysortLayer.addChild(actor.root);
      this.bubblesLayer.addChild(actor.bubbleContainer);
    }
    this.banterDirector.registerMembers(this.ministers);

    this.promptPill = createPromptPill();
    this.bubblesLayer.addChild(this.promptPill.root);

    this.applySlotLighting(this.clock.currentSlot, true);
  }

  onSlotChanged(slotId: TimeSlotId): void {
    this.applySlotLighting(slotId, false);
    for (const m of this.ministers) {
      m.onSlotChanged(slotId);
    }
  }

  onDialogueClosed(): void {
    for (const m of this.ministers) {
      m.endConversation();
    }
  }

  handleInteract(): boolean {
    if (!this.activeTarget) {
      return false;
    }
    if (this.activeTarget.kind === 'minister') {
      this.triggerMinister(this.activeTarget.actor);
      return true;
    }
    this.triggerSpot(this.activeTarget.spec);
    return true;
  }

  update(dt: number, input: InputManager, viewportSize: Vec2, zoom: number): void {
    const isPaused = this.clock.isDialoguePaused;

    // Player movement
    if (!isPaused && this.playerRoot) {
      const move = input.getMovementVector();
      const moving = move.x !== 0 || move.y !== 0;
      if (moving) {
        const speed = 225;
        const candidate = {
          x: this.playerPos.x + move.x * speed * dt,
          y: this.playerPos.y + move.y * speed * dt,
        };
        this.playerPos = resolveCircleVsRects(candidate, 12, this.obstacles, {
          x: 0,
          y: 0,
          w: PALACE_WORLD_SIZE.x,
          h: PALACE_WORLD_SIZE.y,
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
      this.refreshActiveTarget();
    } else if (this.playerSprite) {
      this.playerAnimTime += dt * 2.6;
      updateChibiBob(this.playerSprite, this.playerAnimTime, false);
    }

    // Ministers & banter
    const simPaused = isPaused || this.clock.speedMultiplier <= 0;
    for (const m of this.ministers) {
      m.update(dt, simPaused);
    }
    this.banterDirector.tick(dt, isPaused || this.clock.speedMultiplier <= 0);

    // Ambient tint transition
    const lerpFactor = 1 - Math.exp(-4 * dt);
    this.ambientRgb[0] += (this.targetAmbientRgb[0] - this.ambientRgb[0]) * lerpFactor;
    this.ambientRgb[1] += (this.targetAmbientRgb[1] - this.ambientRgb[1]) * lerpFactor;
    this.ambientRgb[2] += (this.targetAmbientRgb[2] - this.ambientRgb[2]) * lerpFactor;
    this.litWorldLayer.tint = rgbToHexNumber(
      this.ambientRgb[0],
      this.ambientRgb[1],
      this.ambientRgb[2],
    );

    updateSmoothCamera(
      this.worldContainer,
      this.playerPos,
      PALACE_WORLD_SIZE,
      viewportSize,
      zoom,
      dt,
      !this.hasSnappedCamera,
    );
    this.hasSnappedCamera = true;
  }

  getRoster(): RosterEntry[] {
    return this.ministers.map((m) => ({
      id: m.id,
      name: m.profile.displayName,
      zone: getZoneNameForPosition(m.getPosition()),
      status: m.getStatusLabel(),
    }));
  }

  private triggerMinister(actor: MinisterActor): void {
    const profile = actor.startConversation(this.playerPos);
    this.onDialogueRequest({
      mode: 'character',
      profile,
      slotId: this.clock.currentSlot,
    });
  }

  private triggerSpot(spec: InteractableSpec): void {
    if (spec.isCouncilSandbox) {
      const entries = getCouncilMeetingEntries(this.clock.currentSlot);
      this.onDialogueRequest({
        mode: 'council',
        title: '正殿舆图沙盘 · 内阁短议',
        entries,
      });
      return;
    }
    this.onDialogueRequest({
      mode: 'info',
      speakerName: spec.displayTitle,
      speakerRole: '宫城设施',
      badgeText: '建',
      accentColor: spec.accentColor,
      lines: spec.infoLines,
    });
  }

  private refreshActiveTarget(): void {
    const sensorRadiusSq = 64 * 64;
    let best:
      | { kind: 'minister'; actor: MinisterActor }
      | { kind: 'spot'; spec: InteractableSpec }
      | null = null;
    let bestDistSq = Infinity;

    for (const m of this.ministers) {
      const mp = m.getPosition();
      const dSq = (this.playerPos.x - mp.x) ** 2 + (this.playerPos.y - mp.y) ** 2;
      if (dSq <= sensorRadiusSq && dSq < bestDistSq) {
        bestDistSq = dSq;
        best = { kind: 'minister', actor: m };
      }
    }

    for (const spec of PALACE_INTERACTABLES) {
      const dSq = (this.playerPos.x - spec.x) ** 2 + (this.playerPos.y - spec.y) ** 2;
      if (dSq <= sensorRadiusSq && dSq < bestDistSq) {
        bestDistSq = dSq;
        best = { kind: 'spot', spec };
      }
    }

    this.activeTarget = best;

    for (const [id, ring] of this.spotIndicators) {
      ring.visible = best?.kind === 'spot' && best.spec.id === id;
    }

    if (!best) {
      this.promptPill.root.visible = false;
      return;
    }

    if (best.kind === 'minister') {
      this.promptPill.setText(`按 [E] 与 ${best.actor.profile.displayName} 对话`);
      this.promptPill.root.position.set(this.playerPos.x, this.playerPos.y - 78);
      this.promptPill.root.visible = true;
    } else {
      this.promptPill.setText(best.spec.promptHint);
      this.promptPill.root.position.set(
        best.spec.x,
        best.spec.y - best.spec.indicatorSize.y * 0.5 - 18,
      );
      this.promptPill.root.visible = true;
    }
  }

  private applySlotLighting(slotId: TimeSlotId, immediate: boolean): void {
    this.targetAmbientRgb = getTargetAmbientRgb(slotId);
    if (immediate) {
      this.ambientRgb = [
        this.targetAmbientRgb[0],
        this.targetAmbientRgb[1],
        this.targetAmbientRgb[2],
      ];
      this.litWorldLayer.tint = rgbToHexNumber(
        this.ambientRgb[0],
        this.ambientRgb[1],
        this.ambientRgb[2],
      );
    }
    this.nightLampsLayer.visible = slotId === 'free_soul' || slotId === 'shutdown';
  }

  private addPlaque(text: string, centerPos: Vec2, isZoneHeader: boolean): void {
    const fontSize = isZoneHeader ? 13 : 11;
    const borderWidth = isZoneHeader ? 2 : 1;
    const borderColor = isZoneHeader ? '#e0bd61' : '#bd9e5c';
    const borderAlpha = isZoneHeader ? 0.92 : 0.62;
    const bgColor = isZoneHeader ? 0x140f0d : 0x171412;
    const bgAlpha = isZoneHeader ? 0.9 : 0.78;
    const padX = isZoneHeader ? 14 : 8;
    const padY = isZoneHeader ? 3 : 2;

    const lbl = new Text({
      text,
      resolution: 2,
      style: {
        fontFamily: 'system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif',
        fontSize,
        fill: '#faf0d1',
        stroke: { color: '#0d0a0a', width: 2 },
        align: 'center',
      },
    });
    lbl.anchor.set(0.5, 0.5);

    const w = Math.ceil(lbl.width + padX * 2);
    const h = Math.ceil(lbl.height + padY * 2);

    const box = new Graphics();
    box.rect(-w * 0.5 + 2, -h * 0.5 + 2, w, h).fill({ color: 0x0d0a0a, alpha: 0.58 });
    box
      .rect(-w * 0.5, -h * 0.5, w, h)
      .fill({ color: bgColor, alpha: bgAlpha })
      .stroke({ color: borderColor, width: borderWidth, alpha: borderAlpha });

    const container = new Container();
    container.position.set(snap2(centerPos.x), snap2(centerPos.y));
    container.addChild(box, lbl);
    this.plaquesLayer.addChild(container);
  }

  private addLanternGlow(centerPos: Vec2): void {
    const layers: ReadonlyArray<{ radius: number; color: number; alpha: number }> = [
      { radius: 96, color: 0xffb857, alpha: 0.08 },
      { radius: 62, color: 0xffc76b, alpha: 0.14 },
      { radius: 32, color: 0xffdb8f, alpha: 0.22 },
      { radius: 10, color: 0xfff2c7, alpha: 0.5 },
    ];
    const glow = new Graphics();
    glow.position.set(centerPos.x, centerPos.y);
    for (const layer of layers) {
      const pts: number[] = [];
      for (let i = 0; i < 8; i += 1) {
        const a = (Math.PI * 2 * i) / 8 + Math.PI / 8;
        pts.push(snap2(Math.cos(a) * layer.radius), snap2(Math.sin(a) * layer.radius));
      }
      glow.poly(pts).fill({ color: layer.color, alpha: layer.alpha });
    }
    this.nightLampsLayer.addChild(glow);
  }

  destroy(): void {
    this.worldContainer.destroy({ children: true });
  }
}
