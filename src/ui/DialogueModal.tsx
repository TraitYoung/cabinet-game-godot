import { useCallback, useEffect, useState } from 'react';
import { getProfile } from '../data/cabinetDatabase';
import type { DialogueRequest } from '../data/types';

interface DialogueModalProps {
  request: DialogueRequest | null;
  onClose: () => void;
}

export function DialogueModal({ request, onClose }: DialogueModalProps) {
  const [lines, setLines] = useState<readonly string[]>([]);
  const [lineIndex, setLineIndex] = useState(0);
  const [councilIndex, setCouncilIndex] = useState(0);
  const [imgError, setImgError] = useState(false);

  useEffect(() => {
    setLineIndex(0);
    setCouncilIndex(0);
    setImgError(false);
    if (!request) {
      setLines([]);
      return;
    }
    if (request.mode === 'character') {
      const slotLines = request.profile.greetingsBySlot[request.slotId];
      setLines(slotLines && slotLines.length > 0 ? slotLines : ['陛下安好。']);
    } else if (request.mode === 'info') {
      setLines(request.lines);
    } else {
      setLines([]);
    }
  }, [request]);

  const advanceDialogue = useCallback(() => {
    if (!request) {
      return;
    }
    if (request.mode === 'council') {
      if (councilIndex + 1 < request.entries.length) {
        setCouncilIndex((i) => i + 1);
        setImgError(false);
      } else {
        onClose();
      }
      return;
    }
    if (lineIndex + 1 < lines.length) {
      setLineIndex((i) => i + 1);
    } else if (request.mode === 'info') {
      onClose();
    }
  }, [request, councilIndex, lineIndex, lines.length, onClose]);

  useEffect(() => {
    if (!request) {
      return;
    }
    const onKeyDown = (e: KeyboardEvent): void => {
      if (e.repeat) {
        return;
      }
      if (e.code === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.code === 'KeyE' || e.code === 'Space') {
        e.preventDefault();
        advanceDialogue();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [request, advanceDialogue, onClose]);

  if (!request) {
    return null;
  }

  let speakerName = '';
  let speakerRole = '';
  let badgeText = '议';
  let accentColor = '#d6b261';
  let portraitPath = '';
  let bodyText = '';
  let showNext = false;
  let nextLabel = '继续 [E]';

  if (request.mode === 'character') {
    const p = request.profile;
    const tierLabel = p.tier <= 1 ? '一等' : p.tier === 2 ? '二等' : '三等';
    speakerName = p.displayName;
    speakerRole = `${tierLabel} · ${p.roleTitle}`;
    badgeText = p.badgeText;
    accentColor = p.accentColor;
    portraitPath = p.portraitPath;
    bodyText = lines[Math.min(lineIndex, Math.max(0, lines.length - 1))] ?? '';
    showNext = lineIndex + 1 < lines.length;
    nextLabel = '继续 [E]';
  } else if (request.mode === 'council') {
    const entry = request.entries[councilIndex];
    if (!entry) {
      return null;
    }
    const prof = getProfile(entry.id);
    speakerName = entry.name;
    speakerRole = entry.role;
    badgeText = prof?.badgeText ?? '议';
    accentColor = entry.color;
    portraitPath = prof?.portraitPath ?? '';
    bodyText = entry.text;
    showNext = true;
    nextLabel = councilIndex + 1 < request.entries.length ? '下一位 [E]' : '散朝 [E]';
  } else {
    speakerName = request.speakerName;
    speakerRole = request.speakerRole;
    badgeText = request.badgeText;
    accentColor = request.accentColor;
    bodyText = lines[Math.min(lineIndex, Math.max(0, lines.length - 1))] ?? '';
    showNext = true;
    nextLabel = lineIndex + 1 < lines.length ? '继续 [E]' : '明白 [E]';
  }

  const showPortrait = Boolean(portraitPath) && !imgError;

  return (
    <div className="dialogue-panel panel-imperial" role="dialog" aria-label={speakerName}>
      <div className="dialogue-layout">
        <div className="avatar-frame" style={{ borderColor: accentColor }}>
          {showPortrait ? (
            <img
              key={portraitPath}
              className="avatar-portrait"
              src={portraitPath}
              alt={speakerName}
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="avatar-badge" style={{ backgroundColor: accentColor }}>
              {badgeText}
            </div>
          )}
        </div>

        <div className="dialogue-content">
          <div className="dialogue-header">
            <span className="speaker-name" style={{ color: accentColor }}>
              {speakerName}
            </span>
            <span className="speaker-role">{speakerRole}</span>
          </div>

          <div className="dialogue-text">{bodyText}</div>

          <div className="dialogue-footer">
            <div className="topic-row">
              {request.mode === 'character' &&
                Object.entries(request.profile.topicReplies).map(([topicName, replies]) => (
                  <button
                    key={topicName}
                    type="button"
                    className="hud-btn"
                    onClick={() => {
                      setLines(replies);
                      setLineIndex(0);
                    }}
                  >
                    💬 {topicName}
                  </button>
                ))}
            </div>

            <div className="dialogue-actions">
              {showNext && (
                <button type="button" className="hud-btn hud-btn-primary" onClick={advanceDialogue}>
                  {nextLabel}
                </button>
              )}
              <button type="button" className="hud-btn" onClick={onClose}>
                告退 [Esc]
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
