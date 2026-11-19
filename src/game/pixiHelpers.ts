import { Assets, Container, Graphics, Sprite, Text, Texture } from 'pixi.js';
import type { Vec2 } from '../data/types';

export function snap2(v: number): number {
  return Math.floor(v / 2 + 0.5) * 2;
}

export async function loadTextures(
  paths: readonly string[],
  scaleMode: 'nearest' | 'linear',
): Promise<Map<string, Texture>> {
  const unique = Array.from(new Set(paths.filter((p) => p.length > 0)));
  const loaded = await Promise.all(
    unique.map(async (url) => {
      const tex = await Assets.load<Texture>(url);
      tex.source.scaleMode = scaleMode;
      return [url, tex] as const;
    }),
  );
  return new Map<string, Texture>(loaded);
}

export interface ChibiVisual {
  root: Container;
  sprite: Sprite;
  nameLabel: Text | null;
}

export function createChibiActorVisual(
  texture: Texture,
  nameText?: string,
  nameColorHex?: string,
): ChibiVisual {
  const root = new Container();

  const shadow = new Graphics();
  shadow.rect(-14, 4, 28, 6).fill({ color: 0x140f14, alpha: 0.34 });
  shadow.rect(-10, 2, 20, 10).fill({ color: 0x140f14, alpha: 0.24 });
  root.addChild(shadow);

  const sprite = new Sprite({ texture });
  sprite.anchor.set(38 / texture.width, 82 / texture.height);
  sprite.position.set(0, 8);
  root.addChild(sprite);

  let nameLabel: Text | null = null;
  if (nameText) {
    nameLabel = new Text({
      text: nameText,
      resolution: 2,
      style: {
        fontFamily: 'system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif',
        fontSize: 12,
        fill: nameColorHex ?? '#f5efd8',
        stroke: { color: '#0d0d14', width: 3 },
        align: 'center',
      },
    });
    nameLabel.anchor.set(0.5, 0);
    nameLabel.position.set(0, 14);
    root.addChild(nameLabel);
  }

  return { root, sprite, nameLabel };
}

export function updateChibiBob(sprite: Sprite, animTime: number, isMoving: boolean): void {
  const baseSpriteY = 8;
  if (isMoving) {
    const bobStep = Math.floor(Math.abs(Math.sin(animTime)) * 2.5) * 2;
    sprite.position.y = baseSpriteY - bobStep;
  } else {
    const idleStep = Math.sin(animTime) > 0.35 ? 2 : 0;
    sprite.position.y = baseSpriteY - idleStep;
  }
}

export interface PromptPill {
  root: Container;
  setText(message: string): void;
}

export function createPromptPill(): PromptPill {
  const root = new Container();
  root.visible = false;

  const bg = new Graphics();
  const label = new Text({
    text: '',
    resolution: 2,
    style: {
      fontFamily: 'system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif',
      fontSize: 13,
      fill: '#fff5cc',
      stroke: { color: '#14141f', width: 4 },
      align: 'center',
    },
  });
  label.anchor.set(0.5, 0.5);
  root.addChild(bg, label);

  let lastMessage = '';
  const setText = (message: string): void => {
    if (message === lastMessage) {
      return;
    }
    lastMessage = message;
    label.text = message;
    const padX = 10;
    const padY = 4;
    const w = Math.max(80, Math.ceil(label.width + padX * 2));
    const h = Math.ceil(label.height + padY * 2);
    bg.clear();
    bg.roundRect(-w * 0.5, -h * 0.5, w, h, 6)
      .fill({ color: 0x141620, alpha: 0.9 })
      .stroke({ color: 0xe6c25c, width: 1.5, alpha: 0.95 });
  };

  return { root, setText };
}

export function updateSmoothCamera(
  worldContainer: Container,
  targetPos: Vec2,
  worldSize: Vec2,
  viewportSize: Vec2,
  zoom: number,
  dt: number,
  snapImmediate = false,
): void {
  const scaledW = worldSize.x * zoom;
  const scaledH = worldSize.y * zoom;

  let desiredX = viewportSize.x * 0.5 - targetPos.x * zoom;
  let desiredY = viewportSize.y * 0.5 - targetPos.y * zoom;

  if (scaledW <= viewportSize.x) {
    desiredX = (viewportSize.x - scaledW) * 0.5;
  } else {
    desiredX = Math.max(viewportSize.x - scaledW, Math.min(0, desiredX));
  }

  if (scaledH <= viewportSize.y) {
    desiredY = (viewportSize.y - scaledH) * 0.5;
  } else {
    desiredY = Math.max(viewportSize.y - scaledH, Math.min(0, desiredY));
  }

  worldContainer.scale.set(zoom);
  if (snapImmediate) {
    worldContainer.position.set(desiredX, desiredY);
    return;
  }
  const alpha = 1 - Math.exp(-8 * dt);
  worldContainer.x += (desiredX - worldContainer.x) * alpha;
  worldContainer.y += (desiredY - worldContainer.y) * alpha;
}
