import { useCallback, useEffect, useRef, useState } from 'react';
import type { DialogueRequest, HudSnapshot, SceneMode } from './data/types';
import { GameController } from './game/gameController';
import { HudOverlay } from './ui/HudOverlay';

function getInitialSceneMode(): SceneMode {
  const params = new URLSearchParams(window.location.search);
  return params.get('scene') === 'courtyard' ? 'courtyard' : 'palace';
}

const INITIAL_SNAPSHOT: HudSnapshot = {
  day: 1,
  formattedTime: '08:30',
  slotId: 'morning',
  slotLabel: '晨启 · 宫门初开',
  speedMultiplier: 1,
  sceneMode: getInitialSceneMode(),
  roster: [],
  zoom: 1,
};

export function App() {
  const canvasHostRef = useRef<HTMLDivElement | null>(null);
  const controllerRef = useRef<GameController | null>(null);
  const toastTimerRef = useRef<number | null>(null);

  const [snapshot, setSnapshot] = useState<HudSnapshot>(INITIAL_SNAPSHOT);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [dialogueRequest, setDialogueRequest] = useState<DialogueRequest | null>(null);

  useEffect(() => {
    const host = canvasHostRef.current;
    if (!host) {
      return;
    }

    const initialMode = getInitialSceneMode();
    const controller = new GameController(host, initialMode, {
      onSnapshot: (next) => {
        setSnapshot(next);
      },
      onDialogueRequest: (req) => {
        setDialogueRequest(req);
      },
      onToast: (message) => {
        setToastMessage(message);
        if (toastTimerRef.current !== null) {
          window.clearTimeout(toastTimerRef.current);
        }
        toastTimerRef.current = window.setTimeout(() => {
          setToastMessage(null);
          toastTimerRef.current = null;
        }, 3200);
      },
    });
    controllerRef.current = controller;
    void controller.init();

    return () => {
      if (toastTimerRef.current !== null) {
        window.clearTimeout(toastTimerRef.current);
        toastTimerRef.current = null;
      }
      controller.destroy();
      controllerRef.current = null;
    };
  }, []);

  const handleSetSpeed = useCallback((mult: number) => {
    controllerRef.current?.setSpeed(mult);
  }, []);

  const handleSkipNextSlot = useCallback(() => {
    controllerRef.current?.skipToNextSlot();
  }, []);

  const handleSwitchScene = useCallback((mode: SceneMode) => {
    setDialogueRequest(null);
    void controllerRef.current?.switchScene(mode);
  }, []);

  const handleResetZoom = useCallback(() => {
    controllerRef.current?.resetZoom();
  }, []);

  const handleCloseDialogue = useCallback(() => {
    setDialogueRequest(null);
    controllerRef.current?.closeDialogue();
  }, []);

  return (
    <div className="app-viewport">
      <div ref={canvasHostRef} className="game-canvas-host" />
      <HudOverlay
        snapshot={snapshot}
        toastMessage={toastMessage}
        dialogueRequest={dialogueRequest}
        onSetSpeed={handleSetSpeed}
        onSkipNextSlot={handleSkipNextSlot}
        onSwitchScene={handleSwitchScene}
        onResetZoom={handleResetZoom}
        onCloseDialogue={handleCloseDialogue}
      />
    </div>
  );
}
