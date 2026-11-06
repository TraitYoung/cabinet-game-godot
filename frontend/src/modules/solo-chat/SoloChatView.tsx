"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "@/host/AppShell";
import { useUserLocalId } from "@/infra/session";
import {
  fetchHistory,
  fetchChatOptions,
  getPersona,
  ingestAttachment,
  parsePersonaFromReply,
  reportPresence,
  sendChat,
} from "@/matrix/client";
import type { ChatTurn, PersonaCard, ChatOptions, ReasoningEffort } from "@/matrix/types";
import Image from "next/image";
import { Live2DAvatar, type AvatarControls, type AvatarStatus } from "@/modules/embodiment/Live2DAvatar";
import { MessageList, renderContentWithImages, type BubbleMessage } from "@/modules/solo-chat/MessageList";
import { THINK_LINES, useRotatingLine } from "@/modules/solo-chat/CuteWait";
import { ConversationMenu } from "@/modules/solo-chat/ConversationMenu";
import {
  canSendChat,
  composeChatPayload,
  type PendingAttachment,
} from "@/modules/solo-chat/composePayload";
import { useSpeechInput } from "@/modules/solo-chat/useSpeechInput";
import {
  createConversation,
  ensureCatalog,
  getActiveConversation,
  listConversations,
  memoryPoolId,
  removeConversation,
  renameConversation,
  selectConversation,
  touchConversation,
  type SoloConversation,
} from "@/modules/solo-chat/conversationStore";

const FILE_ACCEPT =
  ".txt,.md,.markdown,.json,.csv,.log,image/png,image/jpeg,image/webp,image/gif";

const BINA_ID = "bina";
const BINA_MODEL_URL = "/live2d/bina/bina.model3.json";
const PROACTIVE_MARKER = "[proactive]";

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function turnsToBubbles(turns: ChatTurn[], greeting?: string): BubbleMessage[] {
  const bubbles: BubbleMessage[] = [];
  for (const t of turns) {
    const isProactive = (t.user || "").trim() === PROACTIVE_MARKER;
    if (t.user && !isProactive) {
      bubbles.push({ id: uid(), role: "user", content: t.user });
    }
    if (t.assistant) {
      bubbles.push({
        id: uid(),
        role: "assistant",
        content: t.assistant,
        personaId: BINA_ID,
        hint: isProactive ? "Bina 先开口" : undefined,
      });
    }
  }
  if (bubbles.length === 0 && greeting) {
    bubbles.push({
      id: uid(),
      role: "assistant",
      content: greeting,
      personaId: BINA_ID,
    });
  }
  return bubbles;
}

export function SoloChatView() {
  const userLocalId = useUserLocalId();
  const [card, setCard] = useState<PersonaCard | null>(null);
  const [messages, setMessages] = useState<BubbleMessage[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [convos, setConvos] = useState<SoloConversation[]>([]);
  const [activeConvoId, setActiveConvoId] = useState("");
  const [attachments, setAttachments] = useState<PendingAttachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [interimSpeech, setInterimSpeech] = useState("");
  const [chatOptions, setChatOptions] = useState<ChatOptions | null>(null);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [model, setModel] = useState("");
  const [reasoningEffort, setReasoningEffort] = useState<ReasoningEffort | "">("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [tab, setTab] = useState("状态");
  const [scale, setScale] = useState(100);
  const [background, setBackground] = useState("暖光");
  const [showSubtitle, setShowSubtitle] = useState(true);
  const [enterToSend, setEnterToSend] = useState(true);
  const [avatarModelUrl, setAvatarModelUrl] = useState(BINA_MODEL_URL);
  const [avatarModelDraft, setAvatarModelDraft] = useState(BINA_MODEL_URL);
  const [avatarStatus, setAvatarStatus] = useState<AvatarStatus | null>(null);
  const [avatarReload, setAvatarReload] = useState(0);
  const [avatarActionError, setAvatarActionError] = useState<string | null>(null);
  const avatarRef = useRef<AvatarControls>(null);
  const abortRef = useRef<AbortController | null>(null);
  const historyAbortRef = useRef<AbortController | null>(null);
  const chatInFlightRef = useRef(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pendingLabel = useRotatingLine(THINK_LINES, 2400);

  useEffect(() => {
    void Promise.resolve().then(() => {
      const saved = localStorage.getItem("bina-live2d-model") ?? BINA_MODEL_URL;
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

  const speech = useSpeechInput({
    sessionId: activeConvoId || undefined,
    onTranscript: (chunk, opts) => {
      if (opts?.replaceInterim) {
        setInterimSpeech(chunk);
        return;
      }
      setInterimSpeech("");
      setText((prev) => {
        const base = prev.trimEnd();
        const piece = chunk.trim();
        if (!piece) return prev;
        return base ? `${base}${/[。！？…]$/.test(base) ? "" : " "}${piece}` : piece;
      });
    },
    onError: (msg) => setError(msg),
  });

  const memoryThreadId = useMemo(() => {
    if (!userLocalId) return "";
    return memoryPoolId(userLocalId);
  }, [userLocalId]);

  /** 当前谈话气泡 session（可新建多条） */
  const sessionId = activeConvoId;

  const personaMap = useMemo(() => {
    if (!card) return {};
    return { [card.id]: card };
  }, [card]);

  const refreshCatalog = useCallback(() => {
    if (!userLocalId) return;
    ensureCatalog(userLocalId);
    setConvos(listConversations(userLocalId));
    setActiveConvoId(getActiveConversation(userLocalId).id);
  }, [userLocalId]);

  useEffect(() => {
    if (!userLocalId) return;
    let cancelled = false;
    void Promise.resolve().then(() => {
      if (!cancelled) refreshCatalog();
    });
    return () => { cancelled = true; };
  }, [userLocalId, refreshCatalog]);

  const syncPresence = useCallback(
    async (sid: string) => {
      if (!memoryThreadId) return;
      try {
        await reportPresence(sid, memoryThreadId);
      } catch {
        // 后端未起时不阻断聊天
      }
    },
    [memoryThreadId],
  );

  const reloadHistory = useCallback(async (sid: string, greeting?: string) => {
    if (chatInFlightRef.current) return;
    historyAbortRef.current?.abort();
    const controller = new AbortController();
    historyAbortRef.current = controller;
    try {
      const turns = await fetchHistory(sid, 50, controller.signal);
      if (controller.signal.aborted || chatInFlightRef.current) return;
      setMessages(turnsToBubbles(turns, greeting));
    } catch {
      if (controller.signal.aborted) return;
      setMessages((prev) => (prev.length ? prev : turnsToBubbles([], greeting)));
      throw new Error("历史记录暂时读不到，先聊着；可点「重新接通」再试。");
    } finally {
      if (historyAbortRef.current === controller) historyAbortRef.current = null;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setError(null);
        const bina = await getPersona(BINA_ID);
        if (!cancelled) setCard(bina);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    void Promise.resolve().then(async () => {
      if (cancelled) return;
      if (!sessionId || !card) {
        setMessages([]);
        setHistoryLoading(false);
        return;
      }
      setHistoryLoading(true);
      try {
        await syncPresence(sessionId);
        if (cancelled) return;
        await reloadHistory(sessionId, card.greeting);
        if (!cancelled) setError(null);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    });
    return () => {
      cancelled = true;
      historyAbortRef.current?.abort();
    };
  }, [sessionId, card, syncPresence, reloadHistory]);

  useEffect(() => {
    if (!sessionId || !card) return;
    const onFocus = () => {
      void syncPresence(sessionId);
      void reloadHistory(sessionId).catch(() => {});
    };
    window.addEventListener("focus", onFocus);
    return () => {
      window.removeEventListener("focus", onFocus);
    };
  }, [sessionId, card, syncPresence, reloadHistory]);

  useEffect(() => {
    if (!historyOpen) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setHistoryOpen(false);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [historyOpen]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      historyAbortRef.current?.abort();
    };
  }, []);

  const reconnect = useCallback(async () => {
    if (reconnecting || busy) return;
    setReconnecting(true);
    setError(null);
    setHistoryLoading(true);
    try {
      const bina = await getPersona(BINA_ID);
      setCard(bina);
      if (sessionId) {
        await syncPresence(sessionId);
        await reloadHistory(sessionId, bina.greeting);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setHistoryLoading(false);
      setReconnecting(false);
    }
  }, [reconnecting, busy, sessionId, syncPresence, reloadHistory]);

  const onCreateConvo = () => {
    if (!userLocalId || busy) return;
    historyAbortRef.current?.abort();
    clearAttachments(attachments);
    setAttachments([]);
    createConversation(userLocalId, "新的谈话");
    refreshCatalog();
    setMessages([]);
    setError(null);
  };

  const onSelectConvo = (id: string) => {
    if (!userLocalId || busy || id === activeConvoId) return;
    historyAbortRef.current?.abort();
    clearAttachments(attachments);
    setAttachments([]);
    selectConversation(userLocalId, id);
    refreshCatalog();
    setError(null);
  };

  const onRenameConvo = (id: string, title: string) => {
    if (!userLocalId) return;
    renameConversation(userLocalId, id, title);
    refreshCatalog();
  };

  const onRemoveConvo = (id: string) => {
    if (!userLocalId || busy) return;
    historyAbortRef.current?.abort();
    removeConversation(userLocalId, id);
    refreshCatalog();
    setError(null);
  };

  const onStop = () => {
    abortRef.current?.abort();
    speech.stop();
  };

  const clearAttachments = useCallback((list: PendingAttachment[]) => {
    for (const a of list) {
      if (a.previewUrl) URL.revokeObjectURL(a.previewUrl);
    }
  }, []);

  useEffect(() => {
    return () => clearAttachments(attachments);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only revoke on unmount
  }, []);

  const removeAttachment = (id: string) => {
    setAttachments((prev) => {
      const target = prev.find((x) => x.id === id);
      if (target?.previewUrl) URL.revokeObjectURL(target.previewUrl);
      return prev.filter((x) => x.id !== id);
    });
  };

  const onPickFiles = async (files: FileList | null) => {
    if (!files?.length || !sessionId) return;
    setUploading(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        const result = await ingestAttachment(file, sessionId);
        const previewUrl =
          result.kind === "image" ? URL.createObjectURL(file) : undefined;
        setAttachments((prev) => [
          ...prev,
          {
            id: uid(),
            name: result.name,
            kind: result.kind,
            text: result.text,
            truncated: result.truncated,
            previewUrl,
          },
        ]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const onSend = async () => {
    if (busy || uploading || !sessionId || !memoryThreadId || !userLocalId) return;
    const typed = [text.trim(), interimSpeech.trim()].filter(Boolean).join(" ");
    if (!canSendChat(typed, attachments)) return;
    speech.stop();
    setInterimSpeech("");
    const payload = composeChatPayload(typed, attachments);
    if (!payload) return;
    const bubbleAttachments = attachments.map((a) => ({
      name: a.name,
      kind: a.kind,
      previewUrl: a.previewUrl,
    }));
    const displayText =
      typed || (attachments.length ? `（${attachments.length} 个附件）` : "");

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const timeoutId = window.setTimeout(() => controller.abort(), 120_000);

    chatInFlightRef.current = true;
    historyAbortRef.current?.abort();
    setBusy(true);
    setError(null);
    setText("");
    const sentAtt = attachments;
    setAttachments([]);
    void syncPresence(sessionId);
    const pendingId = uid();
    setMessages((prev) => [
      ...prev,
      {
        id: uid(),
        role: "user",
        content: displayText,
        attachments: bubbleAttachments,
      },
      { id: pendingId, role: "assistant", content: "", personaId: BINA_ID, pending: true },
    ]);
    try {
      const { reply, meta } = await sendChat({
        text: payload,
        model: model || undefined,
        reasoningEffort: reasoningEffort || undefined,
        sessionId,
        memoryThreadId,
        forcedPersona: BINA_ID,
        stripPersonaPrefix: true,
        signal: controller.signal,
      });
      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingId
            ? {
                ...m,
                content: reply,
                personaId: meta?.active_persona || BINA_ID || parsePersonaFromReply(reply),
                pending: false,
              }
            : m,
        ),
      );
      touchConversation(userLocalId, sessionId, typed || sentAtt[0]?.name || "附件", {
        suggestTitleFromPreview: true,
      });
      refreshCatalog();
    } catch (e) {
      const aborted =
        (e instanceof DOMException && e.name === "AbortError") ||
        (e instanceof Error && e.name === "AbortError");
      if (aborted) {
        setError("已停止这一轮。想说什么再说一句就好。");
      } else {
        setError(e instanceof Error ? e.message : String(e));
      }
      setMessages((prev) => prev.filter((m) => m.id !== pendingId));
      // 失败时尽量把附件还回去（预览 URL 仍有效）
      setAttachments((prev) => (prev.length ? prev : sentAtt));
    } finally {
      window.clearTimeout(timeoutId);
      if (abortRef.current === controller) abortRef.current = null;
      chatInFlightRef.current = false;
      setBusy(false);
    }
  };

  const statusHint = reconnecting
    ? "内线重拨中…"
    : historyLoading
      ? "翻找往来记录…"
      : null;

  const latestReply = [...messages].reverse().find((message) => message.role === "assistant");
  const interaction = reconnecting || historyLoading ? "连接中" : busy ? "思考中" : speech.active ? "正在聆听" : card ? "等待交谈" : error ? "连接未就绪" : "连接中";

  return (
    <AppShell
      subtitle="虚拟具身 · 互动与记忆"
      actions={
        <>
          {userLocalId ? (
            <ConversationMenu
              items={convos}
              activeId={activeConvoId}
              disabled={busy || reconnecting}
              onCreate={onCreateConvo}
              onSelect={onSelectConvo}
              onRename={onRenameConvo}
              onRemove={onRemoveConvo}
            />
          ) : null}
          <button type="button" className="ax-btn-ghost" aria-expanded={sidebarOpen} aria-controls="bina-controls" onClick={() => setSidebarOpen((value) => !value)}>
            {sidebarOpen ? "收起侧栏" : "展开侧栏"}
          </button>
        </>
      }
    >
      <div className={`bina-workspace ${sidebarOpen ? "" : "bina-workspace--wide"}`}>
        <section className="bina-room" aria-label="Bina 的房间">
          <div className={`bina-scene bina-scene--${background === "暖光" ? "warm" : "night"}`}>
            <div className="bina-room-heading">
              <div><span className="bina-eyebrow">AXIODRASIL / PERSONAL SPACE</span><h1>Bina 的房间</h1></div>
              <span className="bina-status"><i className={card && !error ? "is-connected" : ""} />{interaction}</span>
            </div>
            <div className="bina-room-caption" aria-hidden="true"><span>Stay a little.</span><p>片刻相伴，慢慢说。</p></div>
            <div className={`bina-portrait ${avatarModelUrl && avatarStatus?.phase === "ready" ? "bina-portrait--hidden" : ""}`} style={{ transform: `translateX(-50%) scale(${scale / 100})` }}>
              <Image src="/bina/casual.jpeg" alt="Bina，浅灰紫短发、琥珀色眼睛，穿着灰色针织外套向你挥手" fill sizes="(max-width: 700px) 70vw, 35vw" priority />
            </div>
            {avatarModelUrl ? <div className="bina-avatar-stage" style={{ transform: `scale(${scale / 100})`, visibility: avatarStatus?.phase === "ready" ? "visible" : "hidden" }}>
              <Live2DAvatar key={`${avatarModelUrl}-${avatarReload}`} modelUrl={avatarModelUrl} controlsRef={avatarRef} onStatus={setAvatarStatus} />
            </div> : null}
            <div className="bina-scene-footer"><span>BINA · 日常形象</span><span>{avatarModelUrl ? avatarStatus?.phase === "ready" ? "Live2D" : avatarStatus?.phase === "error" ? "模型未就绪 · 显示立绘" : "Live2D 加载中…" : "静态立绘"}</span></div>
          </div>
          <div className="bina-dialogue-area">
            <div className="bina-dialogue-heading"><span>Bina <small>比娜</small></span><button type="button" className="ax-btn-ghost" aria-expanded={historyOpen} aria-controls="bina-history" onClick={() => setHistoryOpen(true)}>聊天记录 ↗</button></div>
            {showSubtitle ? <div className="bina-subtitle" aria-live="polite" aria-busy={busy}>
              {latestReply?.pending ? pendingLabel : latestReply?.content ? renderContentWithImages(latestReply.content) : historyLoading ? "正在读取我们的聊天记录…" : card ? "想说什么，直接告诉我。" : error ? "连接未就绪，可在设置中重新连接。" : "正在连接 Bina…"}
            </div> : null}
            {error ? <p className="bina-error" role="alert">{error}</p> : null}
            <div className="bina-composer">
                <div className="flex flex-col gap-2">
                  {attachments.length ? (
                    <ul className="flex flex-wrap gap-2">
                      {attachments.map((a) => (
                        <li
                          key={a.id}
                          className="flex max-w-full items-center gap-2 rounded-lg border border-[var(--ax-line)] bg-[var(--ax-panel)] px-2 py-1 text-xs"
                        >
                          {a.kind === "image" && a.previewUrl ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                              src={a.previewUrl}
                              alt=""
                              className="h-8 w-8 rounded object-cover"
                            />
                          ) : null}
                          <span className="truncate">
                            {a.kind === "image" ? "图片" : "附件"} · {a.name}
                            {a.truncated ? "（已截断）" : ""}
                          </span>
                          <button
                            type="button"
                            className="text-[var(--ax-muted)] hover:text-[var(--ax-fg)]"
                            disabled={busy}
                            onClick={() => removeAttachment(a.id)}
                          >
                            移除
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  <textarea
                    className="ax-input min-h-[64px] w-full resize-y"
                    aria-label="对 Bina 说"
                    placeholder="对 Bina 说… 也可上传文件/图片，或点麦克风说话"
                    value={interimSpeech ? `${text}${text && !/\s$/.test(text) ? " " : ""}${interimSpeech}` : text}
                    disabled={busy || !card || !sessionId || speech.busy}
                    onChange={(e) => {
                      setInterimSpeech("");
                      setText(e.target.value);
                    }}
                    onKeyDown={(e) => {
                      if (enterToSend && e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                        e.preventDefault();
                        void onSend();
                      }
                    }}
                  />
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      ref={fileInputRef}
                      type="file"
                      className="hidden"
                      accept={FILE_ACCEPT}
                      multiple
                      onChange={(e) => void onPickFiles(e.target.files)}
                    />
                    <button
                      type="button"
                      className="ax-btn-ghost"
                      disabled={busy || uploading || !sessionId}
                      title="上传文本或图片"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      {uploading ? "处理中…" : "附件"}
                    </button>
                    <button
                      type="button"
                      className="ax-btn-ghost"
                      disabled={busy || uploading || !sessionId || speech.busy}
                      title={
                        speech.webSpeechSupported
                          ? "浏览器听写（再点停止）"
                          : "录音后走服务端识别"
                      }
                      onClick={() => speech.toggle()}
                    >
                      {speech.mode === "listening"
                        ? "听写中…"
                        : speech.mode === "recording"
                          ? "录音中…"
                          : speech.mode === "transcribing"
                            ? "识别中…"
                            : "麦克风"}
                    </button>
                    {!speech.webSpeechSupported || speech.mode === "idle" ? (
                      <button
                        type="button"
                        className="ax-btn-ghost text-xs"
                        disabled={busy || uploading || !sessionId || speech.busy}
                        title="强制服务端 STT"
                        onClick={() => speech.toggleServer()}
                      >
                        {speech.mode === "recording" ? "结束录音" : "服务端识别"}
                      </button>
                    ) : null}
                    <button
                      type="button"
                      className="ax-btn-primary self-start"
                      disabled={
                        busy ||
                        uploading ||
                        !sessionId ||
                        !card ||
                        !canSendChat([text, interimSpeech].filter(Boolean).join(" "), attachments)
                      }
                      onClick={() => void onSend()}
                    >
                      发送
                    </button>
                    {busy || speech.active || speech.busy ? (
                      <button type="button" className="ax-btn-ghost" onClick={onStop}>
                        停止
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>
          </div>
        </section>
        {sidebarOpen ? <aside className="bina-controls" id="bina-controls" aria-label="Bina 状态与设置">
          <div className="bina-controls-heading"><span className="bina-eyebrow">陪伴空间</span><h2>此刻的 Bina</h2><p>形象、互动，以及我们的日常。</p></div>
          <div className="bina-tabs" role="tablist" aria-label="侧栏分类">{["状态", "形象", "设置"].map((name) => <button key={name} id={`tab-${name}`} type="button" role="tab" aria-selected={tab === name} aria-controls="bina-tab-panel" tabIndex={tab === name ? 0 : -1} onKeyDown={(event) => {
            const names = ["状态", "形象", "设置"];
            const direction = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
            if (direction) { const next = names[(names.indexOf(tab) + direction + 3) % 3]; setTab(next); document.getElementById(`tab-${next}`)?.focus(); }
          }} onClick={() => setTab(name)}>{name}</button>)}</div>
          <div className="bina-tab-content" role="tabpanel" id="bina-tab-panel" aria-labelledby={`tab-${tab}`}>
            {tab === "状态" ? <>
              <div className="bina-info-card"><span className="bina-eyebrow">INTERACTION</span><h3>{interaction}</h3><p>{busy ? "Bina 正在准备回复，稍等片刻。" : "可以打字，也可以用麦克风说话。"}</p></div>
              <dl className="bina-facts"><div><dt>人物连接</dt><dd>{card ? "已加载" : "未连接"}</dd></div><div><dt>当前谈话</dt><dd>{convos.find((convo) => convo.id === activeConvoId)?.title || "准备中"}</dd></div><div><dt>往来消息</dt><dd>{messages.filter((message) => !message.pending).length} 条</dd></div><div><dt>语音输入</dt><dd>{speech.active ? "进行中" : "未开启"}</dd></div></dl>
              <div className="bina-note"><h3>记忆会随交谈延续</h3><p>新建谈话后，仍沿用同一份长期记忆。</p></div>
            </> : tab === "形象" ? <>
              <div className="bina-info-card"><span className="bina-eyebrow">APPEARANCE</span><h3>{avatarModelUrl && avatarStatus?.phase === "ready" ? "Live2D 形象" : "日常 · 针织外套"}</h3><p>{avatarModelUrl ? avatarStatus?.message || "正在准备 Live2D…" : "当前显示定妆图，可加载已绑定的 Live2D 模型。"}</p></div>
              <form className="bina-avatar-settings" onSubmit={(event) => { event.preventDefault(); applyAvatarModel(avatarModelDraft); }}>
                <label className="bina-setting">Live2D 模型路径<input className="ax-input" aria-label="Live2D 模型路径" placeholder="/live2d/bina/bina.model3.json" value={avatarModelDraft} onChange={(event) => setAvatarModelDraft(event.target.value)} /></label>
                <div className="bina-avatar-buttons"><button type="submit" className="ax-btn-ghost" disabled={!avatarModelDraft.trim()}>加载模型</button><button type="button" className="ax-btn-ghost" onClick={() => applyAvatarModel("")}>使用立绘</button></div>
              </form>
              {avatarStatus?.phase === "error" && avatarModelUrl ? <p className="bina-error" role="alert">{avatarStatus.message}</p> : null}
              {avatarStatus?.phase === "ready" && avatarModelUrl ? <div className="bina-avatar-previews">
                <p className="bina-model-hint">移动鼠标可引导视线，以下动作与表情由模型提供。</p>
                {avatarStatus.motions.length > 0 ? <fieldset><legend>动作预览</legend><div className="bina-avatar-buttons">{avatarStatus.motions.map((name) => <button type="button" className="ax-btn-ghost" key={name} onClick={() => void previewAvatar("motion", name)}>{name || "默认"}</button>)}</div></fieldset> : null}
                {avatarStatus.expressions.length > 0 ? <fieldset><legend>表情预览</legend><div className="bina-avatar-buttons">{avatarStatus.expressions.map((name) => <button type="button" className="ax-btn-ghost" key={name} onClick={() => void previewAvatar("expression", name)}>{name}</button>)}</div></fieldset> : null}
                {avatarActionError ? <p className="bina-error" role="alert">{avatarActionError}</p> : null}
              </div> : null}
              <label className="bina-setting">人物缩放 <output>{scale}%</output><input type="range" min="80" max="130" value={scale} onChange={(event) => setScale(Number(event.target.value))} /></label>
              <label className="bina-setting">房间氛围<select value={background} onChange={(event) => setBackground(event.target.value)}><option>暖光</option><option>夜色</option></select></label>
              <button type="button" className="ax-btn-ghost" onClick={() => { setScale(100); setBackground("暖光"); applyAvatarModel(BINA_MODEL_URL); }}>恢复默认形象</button>
            </> : <>
              <div className="bina-model-settings">
                <span className="bina-eyebrow">回复模型</span>
                <label className="bina-setting">模型<select aria-label="模型" value={model} disabled={busy || !chatOptions} onChange={(event) => changeChatPreferences(event.target.value, reasoningEffort)}>
                  <option value="">跟随默认{chatOptions ? ` · ${chatOptions.default_model}` : ""}</option>
                  {chatOptions?.models.map((name) => <option key={name} value={name}>{name}</option>)}
                </select></label>
                <label className="bina-setting">思考档位<select aria-label="思考档位" value={reasoningEffort} disabled={busy || !chatOptions?.reasoning_levels.length} onChange={(event) => changeChatPreferences(model, event.target.value as ReasoningEffort | "")}>
                  <option value="">跟随默认</option>
                  {chatOptions?.reasoning_levels.map((level) => <option key={level} value={level}>{{ off: "关闭思考 · 快速回复", low: "低 · 轻量思考", high: "高 · 深入思考", max: "最高 · 充分推理" }[level]}</option>)}
                </select></label>
                <p className="bina-model-hint">{busy ? "回复结束后可切换，下次发送生效。" : chatOptions && !chatOptions.reasoning_levels.length ? "当前模型服务未提供思考档位。" : "下次发送生效，较高档位可能需要更久。"}</p>
                {optionsError ? <div className="bina-error" role="alert">{optionsError}<button type="button" className="ax-btn-ghost" onClick={() => void loadChatOptions()}>重新加载模型</button></div> : null}
              </div>
              <label className="bina-toggle"><span>显示对白字幕<small>在人物画面下方显示最近的回复</small></span><input type="checkbox" checked={showSubtitle} onChange={(event) => setShowSubtitle(event.target.checked)} /></label>
              <label className="bina-toggle"><span>Enter 发送<small>{enterToSend ? "Shift + Enter 换行" : "Enter 换行，点击按钮发送"}</small></span><input type="checkbox" checked={enterToSend} onChange={(event) => setEnterToSend(event.target.checked)} /></label>
              <div className="bina-note"><h3>摄像头 · 尚未接入</h3><p>当前仅支持文字、附件和语音输入。</p></div>
              <button type="button" className="ax-btn-ghost" disabled={reconnecting || busy} onClick={() => void reconnect()}>{reconnecting ? "连接中…" : "重新连接 Bina"}</button>
            </>}
          </div>
          <div className="bina-controls-footer">AXIODRASIL <span>与你在这里</span></div>
        </aside> : null}
      </div>
      {historyOpen ? <div className="bina-history-layer">
        <button type="button" className="bina-history-backdrop" aria-label="关闭聊天记录" onClick={() => setHistoryOpen(false)} />
        <section className="bina-history ax-drawer" id="bina-history" aria-label="聊天记录">
          <header><div><span className="bina-eyebrow">CONVERSATION</span><h2>我们的谈话</h2></div><button autoFocus type="button" className="ax-btn-ghost" onClick={() => setHistoryOpen(false)}>关闭 ×</button></header>
          <MessageList messages={messages} personaMap={personaMap} emptyTitle="还没有聊天记录" emptyHint="从一句问候开始。" pendingLabel={pendingLabel} statusHint={statusHint} />
        </section>
      </div> : null}
    </AppShell>
  );
}
