import type { DialogueRequest, HudSnapshot, SceneMode } from '../data/types';
import { DialogueModal } from './DialogueModal';

interface HudOverlayProps {
  snapshot: HudSnapshot;
  toastMessage: string | null;
  dialogueRequest: DialogueRequest | null;
  onSetSpeed: (multiplier: number) => void;
  onSkipNextSlot: () => void;
  onSwitchScene: (mode: SceneMode) => void;
  onResetZoom: () => void;
  onCloseDialogue: () => void;
}

export function HudOverlay({
  snapshot,
  toastMessage,
  dialogueRequest,
  onSetSpeed,
  onSkipNextSlot,
  onSwitchScene,
  onResetZoom,
  onCloseDialogue,
}: HudOverlayProps) {
  const speedText =
    snapshot.speedMultiplier <= 0 ? '[已暂停]' : `[${Math.round(snapshot.speedMultiplier)}x]`;

  return (
    <div className="hud-root">
      {/* Top-Left: Imperial Calendar & Time Controls */}
      <div className="panel-imperial top-left-panel">
        <div className="time-row">
          <span className="time-display">
            第 {snapshot.day} 天 &nbsp;{snapshot.formattedTime}
          </span>
          <span className="slot-display">{snapshot.slotLabel}</span>
        </div>
        <div className="speed-row">
          <button
            type="button"
            className={`hud-btn ${snapshot.speedMultiplier <= 0 ? 'is-active' : ''}`}
            onClick={() => onSetSpeed(0)}
          >
            暂停
          </button>
          <button
            type="button"
            className={`hud-btn ${snapshot.speedMultiplier === 1 ? 'is-active' : ''}`}
            onClick={() => onSetSpeed(1)}
          >
            1x
          </button>
          <button
            type="button"
            className={`hud-btn ${snapshot.speedMultiplier === 3 ? 'is-active' : ''}`}
            onClick={() => onSetSpeed(3)}
          >
            3x
          </button>
          <button type="button" className="hud-btn" onClick={onSkipNextSlot}>
            跳至下一时段 ⏭
          </button>
          <span className="speed-badge">{speedText}</span>
        </div>
      </div>

      {/* Top-Right: Scene Switcher & Cabinet Roster */}
      <div className="panel-slate top-right-panel">
        <div className="roster-header">
          <span className="roster-title">
            {snapshot.sceneMode === 'palace' ? '内阁诸卿在岗动态' : '院落单元沙盒'}
          </span>
          <div className="scene-switch">
            <button
              type="button"
              className={`hud-btn hud-btn-compact ${snapshot.sceneMode === 'palace' ? 'is-active' : ''}`}
              onClick={() => onSwitchScene('palace')}
            >
              皇城宫城
            </button>
            <button
              type="button"
              className={`hud-btn hud-btn-compact ${snapshot.sceneMode === 'courtyard' ? 'is-active' : ''}`}
              onClick={() => onSwitchScene('courtyard')}
            >
              值房小院
            </button>
          </div>
        </div>

        {snapshot.sceneMode === 'palace' ? (
          <div className="roster-scroll">
            {snapshot.roster.map((entry) => (
              <div key={entry.id} className="roster-item">
                • {entry.name} — {entry.zone}（{entry.status}）
              </div>
            ))}
          </div>
        ) : (
          <div className="courtyard-note">
            当前为「一进值房小院」等距遮挡验证沙盒：支持穿过南院门、走进石板天井与正厅，按 [E] 检视西厢廊庑与正厅。
          </div>
        )}

        <div className="controls-footer">
          <span className="controls-hint">WASD 移动 · E 互动 · Tab 调速 · 滚轮缩放</span>
          {Math.abs(snapshot.zoom - 1) > 0.01 && (
            <button type="button" className="hud-btn hud-btn-compact" onClick={onResetZoom}>
              {Math.round(snapshot.zoom * 100)}% ↺
            </button>
          )}
        </div>
      </div>

      {/* Top-Center: Slot Transition Toast */}
      {toastMessage && (
        <div className="panel-imperial toast-panel" role="status">
          {toastMessage}
        </div>
      )}

      {/* Bottom: Dialogue Modal */}
      <DialogueModal request={dialogueRequest} onClose={onCloseDialogue} />
    </div>
  );
}
