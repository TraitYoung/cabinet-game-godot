import type { Vec2 } from '../data/types';

export interface InputCallbacks {
  onInteract: () => void;
  onToggleSpeed: () => void;
  onCancel: () => void;
}

export class InputManager {
  private pressedKeys = new Set<string>();
  private callbacks: InputCallbacks;

  private readonly handleKeyDown = (e: KeyboardEvent): void => {
    const active = document.activeElement;
    if (
      active instanceof HTMLInputElement ||
      active instanceof HTMLTextAreaElement ||
      active instanceof HTMLSelectElement
    ) {
      return;
    }

    const code = e.code;
    if (
      code === 'Space' ||
      code === 'ArrowUp' ||
      code === 'ArrowDown' ||
      code === 'ArrowLeft' ||
      code === 'ArrowRight' ||
      code === 'Tab'
    ) {
      e.preventDefault();
    }

    if (!e.repeat) {
      if (code === 'KeyE' || code === 'Space') {
        this.callbacks.onInteract();
      } else if (code === 'Tab') {
        this.callbacks.onToggleSpeed();
      } else if (code === 'Escape') {
        this.callbacks.onCancel();
      }
    }

    this.pressedKeys.add(code);
  };

  private readonly handleKeyUp = (e: KeyboardEvent): void => {
    this.pressedKeys.delete(e.code);
  };

  private readonly handleBlur = (): void => {
    this.pressedKeys.clear();
  };

  constructor(callbacks: InputCallbacks) {
    this.callbacks = callbacks;
    window.addEventListener('keydown', this.handleKeyDown);
    window.addEventListener('keyup', this.handleKeyUp);
    window.addEventListener('blur', this.handleBlur);
  }

  getMovementVector(): Vec2 {
    let x = 0;
    let y = 0;
    if (this.pressedKeys.has('KeyA') || this.pressedKeys.has('ArrowLeft')) {
      x -= 1;
    }
    if (this.pressedKeys.has('KeyD') || this.pressedKeys.has('ArrowRight')) {
      x += 1;
    }
    if (this.pressedKeys.has('KeyW') || this.pressedKeys.has('ArrowUp')) {
      y -= 1;
    }
    if (this.pressedKeys.has('KeyS') || this.pressedKeys.has('ArrowDown')) {
      y += 1;
    }
    if (x === 0 && y === 0) {
      return { x: 0, y: 0 };
    }
    const len = Math.hypot(x, y);
    return { x: x / len, y: y / len };
  }

  destroy(): void {
    window.removeEventListener('keydown', this.handleKeyDown);
    window.removeEventListener('keyup', this.handleKeyUp);
    window.removeEventListener('blur', this.handleBlur);
    this.pressedKeys.clear();
  }
}
