export type TimeSlotId = 'morning' | 'focus' | 'refuel' | 'free_soul' | 'shutdown';

export type SceneMode = 'palace' | 'courtyard';

export interface Vec2 {
  x: number;
  y: number;
}

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface CharacterProfile {
  id: string;
  displayName: string;
  fullName: string;
  roleTitle: string;
  tier: number;
  personalitySummary: string;
  badgeText: string;
  accentColor: string;
  hairColor: string;
  outfitColor: string;
  portraitPath: string;
  chibiSpritePath: string;
  personalOffset: Vec2;
  scheduleWaypoints: Record<TimeSlotId, string>;
  greetingsBySlot: Record<TimeSlotId, readonly string[]>;
  topicReplies: Record<string, readonly string[]>;
  idleThoughts: readonly string[];
}

export interface BanterLine {
  id: string;
  text: string;
}

export interface CouncilEntry {
  id: string;
  name: string;
  role: string;
  color: string;
  text: string;
}

export interface InteractableSpec {
  id: string;
  x: number;
  y: number;
  displayTitle: string;
  promptHint: string;
  accentColor: string;
  isCouncilSandbox?: boolean;
  infoLines: readonly string[];
  indicatorSize: Vec2;
}

export interface RosterEntry {
  id: string;
  name: string;
  zone: string;
  status: string;
}

export type DialogueRequest =
  | {
      mode: 'character';
      profile: CharacterProfile;
      slotId: TimeSlotId;
    }
  | {
      mode: 'council';
      title: string;
      entries: readonly CouncilEntry[];
    }
  | {
      mode: 'info';
      speakerName: string;
      speakerRole: string;
      badgeText: string;
      accentColor: string;
      lines: readonly string[];
    };

export interface HudSnapshot {
  day: number;
  formattedTime: string;
  slotId: TimeSlotId;
  slotLabel: string;
  speedMultiplier: number;
  sceneMode: SceneMode;
  roster: readonly RosterEntry[];
  zoom: number;
}

export interface WallSpec {
  name: string;
  rect: Rect;
}

export interface FurnitureSpec {
  id: string;
  rect: Rect;
  label: string;
  spritePath: string;
  visualSize: Vec2;
  labelAbove: boolean;
  plaqueOffset: Vec2;
}

export interface TreeSpec {
  id: string;
  pos: Vec2;
  spritePath: string;
  visualSize: Vec2;
  bottomPad: number;
}

export interface ZoneLabelSpec {
  pos: Vec2;
  text: string;
}

export interface FrontStripSpec {
  x: number;
  w: number;
  footY: number;
}
