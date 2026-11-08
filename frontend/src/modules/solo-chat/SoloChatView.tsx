"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/host/AppShell";
import { useUserLocalId } from "@/infra/session";
import {
  getPersona,
  reportPresence,
} from "@/matrix/client";
import type { ChatTurn, PersonaCard } from "@/matrix/types";
import Image from "next/image";
import { Live2DAvatar } from "@/modules/embodiment/Live2DAvatar";
import { MessageList, renderContentWithImages, type BubbleMessage } from "@/modules/solo-chat/MessageList";
import { THINK_LINES, useRotatingLine } from "@/modules/solo-chat/CuteWait";
import { ConversationMenu } from "@/modules/solo-chat/ConversationMenu";
import {
  canSendChat,
  composeChatPayload,
} from "@/modules/solo-chat/composePayload";
import { useAppearance } from "./useAppearance";
import { useChatPreferences } from "./useChatPreferences";
import { BinaControls } from "./BinaControls";
import { useChatTurn } from "./useChatTurn";
import { useAttachments } from "./useAttachments";
import { useConversationHistory } from "./useConversationHistory";
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
  const [reconnecting, setReconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [convos, setConvos] = useState<SoloConversation[]>([]);
  const [activeConvoId, setActiveConvoId] = useState("");
  const [interimSpeech, setInterimSpeech] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [tab, setTab] = useState("状态");
  const [showSubtitle, setShowSubtitle] = useState(true);
  const [enterToSend, setEnterToSend] = useState(true);
  const avatar = useAppearance();
  const { scale, background, avatarModelUrl, avatarStatus, setAvatarStatus, avatarReload, avatarRef, isWorkAvatar } = avatar;
  const preferences = useChatPreferences();
  const { model, reasoningEffort } = preferences;
  const turn = useChatTurn();
  const busy = turn.busy;
  const uploads = useAttachments(activeConvoId, setError);
  const { attachments, uploading, fileInputRef } = uploads;
  const receiveHistory = useCallback((turns: ChatTurn[], greeting?: string) => setMessages(turnsToBubbles(turns, greeting)), []);
  const history = useConversationHistory(turn.isSending, receiveHistory);
  const { loading: historyLoading, reload: reloadHistory, cancel: cancelHistory } = history;
  const pendingLabel = useRotatingLine(THINK_LINES, 2400);

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
        return;
      }
      try {
        await syncPresence(sessionId);
        if (cancelled) return;
        await reloadHistory(sessionId, card.greeting);
        if (!cancelled) setError(null);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
      }
    });
    return () => {
      cancelled = true;
      cancelHistory();
    };
  }, [sessionId, card, syncPresence, reloadHistory, cancelHistory]);

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
  }, [sessionId, card, syncPresence, reloadHistory, cancelHistory]);

  useEffect(() => {
    if (!historyOpen) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setHistoryOpen(false);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [historyOpen]);

  const reconnect = useCallback(async () => {
    if (reconnecting || busy) return;
    setReconnecting(true);
    setError(null);
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
      setReconnecting(false);
    }
  }, [reconnecting, busy, sessionId, syncPresence, reloadHistory]);

  const onCreateConvo = () => {
    if (!userLocalId || busy) return;
    cancelHistory();
    uploads.reset();
    createConversation(userLocalId, "新的谈话");
    refreshCatalog();
    setMessages([]);
    setError(null);
  };

  const onSelectConvo = (id: string) => {
    if (!userLocalId || busy || id === activeConvoId) return;
    cancelHistory();
    uploads.reset();
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
    cancelHistory();
    uploads.reset();
    removeConversation(userLocalId, id);
    refreshCatalog();
    setError(null);
  };

  const onStop = () => { turn.stop(); speech.stop(); };
  const removeAttachment = uploads.remove;
  const onPickFiles = (files: FileList | null) => { setError(null); return uploads.pick(files); };

  const onSend = async () => {
    if (turn.isSending() || uploading || !sessionId || !memoryThreadId || !userLocalId) return;
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

    cancelHistory();
    setError(null);
    setText("");
    const sentAtt = uploads.take();
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
    const outcome = await turn.send({
      text: payload, model: model || undefined, reasoningEffort: reasoningEffort || undefined,
      sessionId, memoryThreadId, forcedPersona: BINA_ID, stripPersonaPrefix: true,
    });
    if (!outcome) return;
    if (outcome.reply) {
      setMessages((prev) => prev.map((message) => message.id === pendingId
        ? { ...message, content: outcome.reply!, personaId: outcome.persona || BINA_ID, pending: false } : message));
      touchConversation(userLocalId, sessionId, typed || sentAtt[0]?.name || "附件", { suggestTitleFromPreview: true });
      refreshCatalog();
    } else {
      setError(outcome.error || "回合未完成");
      setMessages((prev) => prev.filter((message) => message.id !== pendingId));
      setText(typed);
      uploads.restore(sentAtt);
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
            <div className={`bina-portrait ${isWorkAvatar ? "bina-portrait--work" : ""} ${avatarModelUrl && avatarStatus?.phase === "ready" ? "bina-portrait--hidden" : ""}`} style={{ transform: `translateX(-50%) scale(${scale / 100})` }}>
              <Image src={isWorkAvatar ? "/bina/work.png" : "/bina/casual.jpeg"} alt={isWorkAvatar ? "Bina，穿着灰色短夹克、领带和橙色织带工装裤自然站立" : "Bina，浅灰紫短发、琥珀色眼睛，穿着灰色针织外套向你挥手"} fill sizes="(max-width: 700px) 70vw, 35vw" priority />
            </div>
            {avatarModelUrl ? <div className="bina-avatar-stage" style={{ transform: `scale(${scale / 100})`, visibility: avatarStatus?.phase === "ready" ? "visible" : "hidden" }}>
              <Live2DAvatar key={`${avatarModelUrl}-${avatarReload}`} modelUrl={avatarModelUrl} controlsRef={avatarRef} onStatus={setAvatarStatus} />
            </div> : null}
            <div className="bina-scene-footer"><span>BINA · {isWorkAvatar ? "工装形象" : "日常形象"}</span><span>{avatarModelUrl ? avatarStatus?.phase === "ready" ? "Live2D" : avatarStatus?.phase === "error" ? "模型未就绪 · 显示立绘" : "Live2D 加载中…" : "静态立绘"}</span></div>
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
        {sidebarOpen ? <BinaControls avatar={avatar} preferences={preferences} tab={tab} setTab={setTab}
          interaction={interaction} busy={busy} connected={Boolean(card)} conversationTitle={convos.find((convo) => convo.id === activeConvoId)?.title || "准备中"}
          messageCount={messages.filter((message) => !message.pending).length} speechActive={speech.active}
          reconnecting={reconnecting} onReconnect={reconnect} showSubtitle={showSubtitle} setShowSubtitle={setShowSubtitle}
          enterToSend={enterToSend} setEnterToSend={setEnterToSend} /> : null}
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
