"use client";
import { useEffect, useRef, useState } from "react";
import type { AvatarControls, AvatarStatus } from "@/modules/embodiment/Live2DAvatar";
export const BINA_MODEL_URL = "/live2d/bina-registered/bina.model3.json";
export const BINA_WORK_MODEL_URL = "/live2d/bina-work/bina.model3.json";
export function useAppearance() {
  const [scale, setScale] = useState(100);
  const [background, setBackground] = useState("暖光");
  const [avatarModelUrl, setAvatarModelUrl] = useState(BINA_MODEL_URL);
  const [avatarModelDraft, setAvatarModelDraft] = useState(BINA_MODEL_URL);
  const [avatarStatus, setAvatarStatus] = useState<AvatarStatus | null>(null);
  const [avatarReload, setAvatarReload] = useState(0);
  const [avatarActionError, setAvatarActionError] = useState<string | null>(null);
  const avatarRef = useRef<AvatarControls>(null);
  useEffect(() => {
    void Promise.resolve().then(() => {
      const previous = localStorage.getItem("bina-live2d-model");
      const saved = previous == null || previous === "/live2d/bina/bina.model3.json" ? BINA_MODEL_URL : previous;
      if (saved !== previous) localStorage.setItem("bina-live2d-model", saved);
      setAvatarModelUrl(saved);
      setAvatarModelDraft(saved);
    });
  }, []);

  const applyAvatarModel = (url: string) => {
    const next = url.trim();
    localStorage.setItem("bina-live2d-model", next);
    setAvatarModelUrl(next);
    setAvatarModelDraft(next);
    setAvatarStatus(null);
    setAvatarActionError(null);
    setAvatarReload((value) => value + 1);
  };

  const previewAvatar = async (kind: "motion" | "expression", name: string) => {
    setAvatarActionError(null);
    try {
      await avatarRef.current?.[kind](name);
    } catch (exception) {
      setAvatarActionError(exception instanceof Error ? exception.message : String(exception));
    }
  };

  return { scale, setScale, background, setBackground, avatarModelUrl, avatarModelDraft, setAvatarModelDraft,
    avatarStatus, setAvatarStatus, avatarReload, avatarActionError, avatarRef, applyAvatarModel, previewAvatar,
    isWorkAvatar: avatarModelUrl === BINA_WORK_MODEL_URL };
}
