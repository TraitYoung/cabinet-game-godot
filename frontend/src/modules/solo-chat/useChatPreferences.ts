"use client";
import { useCallback, useEffect, useState } from "react";
import { fetchChatOptions } from "@/matrix/client";
import type { ChatOptions, ReasoningEffort } from "@/matrix/types";
export function useChatPreferences() {
  const [chatOptions, setChatOptions] = useState<ChatOptions | null>(null);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [model, setModel] = useState("");
  const [reasoningEffort, setReasoningEffort] = useState<ReasoningEffort | "">("");
  const loadChatOptions = useCallback(async () => {
    try {
      const options = await fetchChatOptions();
      setChatOptions(options);
      setOptionsError(null);
      const saved = JSON.parse(localStorage.getItem("bina-chat-preferences") || "{}");
      setModel(options.models.includes(saved.model) ? saved.model : "");
      setReasoningEffort(options.reasoning_levels.includes(saved.reasoningEffort) ? saved.reasoningEffort : "");
    } catch (exception) {
      setOptionsError(exception instanceof Error ? exception.message : "无法加载模型设置");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    void Promise.resolve().then(() => {
      if (!cancelled) void loadChatOptions();
    });
    return () => { cancelled = true; };
  }, [loadChatOptions]);

  const changeChatPreferences = (nextModel: string, nextEffort: ReasoningEffort | "") => {
    setModel(nextModel);
    setReasoningEffort(nextEffort);
    localStorage.setItem("bina-chat-preferences", JSON.stringify({ model: nextModel, reasoningEffort: nextEffort }));
  };

  return { chatOptions, optionsError, model, reasoningEffort, changeChatPreferences, loadChatOptions };
}
