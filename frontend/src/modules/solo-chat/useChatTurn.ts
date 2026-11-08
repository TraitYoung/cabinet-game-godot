"use client";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { cancelChat, sendChat } from "@/matrix/client";
import type { StreamChatInput } from "@/matrix/types";
import { TurnLifecycle } from "./turnLifecycle";

export function useChatTurn() {
  const [turn] = useState(() => new TurnLifecycle(sendChat, cancelChat));
  const mounted = useRef(true);
  const phase = useSyncExternalStore(turn.subscribe, turn.snapshot, turn.snapshot);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; turn.stop(); };
  }, [turn]);
  return { phase, busy: phase === "generating" || phase === "confirming", stop: turn.stop,
    isSending: () => turn.busy,
    send: async (input: StreamChatInput) => {
      const outcome = await turn.send(input);
      return mounted.current ? outcome : undefined;
    } };
}
