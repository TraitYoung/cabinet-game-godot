"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { fetchHistory } from "@/matrix/client";
import type { ChatTurn } from "@/matrix/types";

export function useConversationHistory(isSending: () => boolean, onLoaded: (turns: ChatTurn[], greeting?: string) => void) {
  const controllerRef = useRef<AbortController | null>(null);
  const [loading, setLoading] = useState(false);
  const current = useRef({ isSending, onLoaded });
  useEffect(() => { current.current = { isSending, onLoaded }; }, [isSending, onLoaded]);
  const cancel = useCallback(() => { controllerRef.current?.abort(); controllerRef.current = null; setLoading(false); }, []);
  useEffect(() => () => controllerRef.current?.abort(), []);
  const reload = useCallback(async (sessionId: string, greeting?: string) => {
    if (current.current.isSending()) return;
    controllerRef.current?.abort();
    const controller = new AbortController(); controllerRef.current = controller;
    setLoading(true);
    try {
      const turns = await fetchHistory(sessionId, 50, controller.signal);
      if (!controller.signal.aborted && !current.current.isSending()) current.current.onLoaded(turns, greeting);
    } catch {
      if (!controller.signal.aborted) throw new Error("历史记录暂时读不到，先聊着；可点「重新接通」再试。");
    } finally {
      if (controllerRef.current === controller) { controllerRef.current = null; setLoading(false); }
    }
  }, []);
  return { loading, reload, cancel };
}
