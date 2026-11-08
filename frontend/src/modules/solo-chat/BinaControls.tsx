"use client";
import type { Dispatch, SetStateAction } from "react";
import type { ReasoningEffort } from "@/matrix/types";
import { BINA_MODEL_URL, BINA_WORK_MODEL_URL, type useAppearance } from "./useAppearance";
import type { useChatPreferences } from "./useChatPreferences";
type Props = {
  avatar: ReturnType<typeof useAppearance>; preferences: ReturnType<typeof useChatPreferences>;
  tab: string; setTab: Dispatch<SetStateAction<string>>;
  interaction: string; busy: boolean; connected: boolean; conversationTitle: string; messageCount: number;
  speechActive: boolean; reconnecting: boolean; onReconnect: () => Promise<void>;
  showSubtitle: boolean; setShowSubtitle: Dispatch<SetStateAction<boolean>>;
  enterToSend: boolean; setEnterToSend: Dispatch<SetStateAction<boolean>>;
};
export function BinaControls({ avatar, preferences, tab, setTab, interaction, busy, connected, conversationTitle,
  messageCount, speechActive, reconnecting, onReconnect, showSubtitle, setShowSubtitle, enterToSend, setEnterToSend }: Props) {
  const { scale, setScale, background, setBackground, avatarModelUrl, avatarModelDraft, setAvatarModelDraft,
    avatarStatus, avatarActionError, applyAvatarModel, previewAvatar, isWorkAvatar } = avatar;
  const { chatOptions, optionsError, model, reasoningEffort, changeChatPreferences, loadChatOptions } = preferences;
  return (
        <aside className="bina-controls" id="bina-controls" aria-label="Bina 状态与设置">
          <div className="bina-controls-heading"><span className="bina-eyebrow">陪伴空间</span><h2>此刻的 Bina</h2><p>形象、互动，以及我们的日常。</p></div>
          <div className="bina-tabs" role="tablist" aria-label="侧栏分类">{["状态", "形象", "设置"].map((name) => <button key={name} id={`tab-${name}`} type="button" role="tab" aria-selected={tab === name} aria-controls="bina-tab-panel" tabIndex={tab === name ? 0 : -1} onKeyDown={(event) => {
            const names = ["状态", "形象", "设置"];
            const direction = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
            if (direction) { const next = names[(names.indexOf(tab) + direction + 3) % 3]; setTab(next); document.getElementById(`tab-${next}`)?.focus(); }
          }} onClick={() => setTab(name)}>{name}</button>)}</div>
          <div className="bina-tab-content" role="tabpanel" id="bina-tab-panel" aria-labelledby={`tab-${tab}`}>
            {tab === "状态" ? <>
              <div className="bina-info-card"><span className="bina-eyebrow">INTERACTION</span><h3>{interaction}</h3><p>{busy ? "Bina 正在准备回复，稍等片刻。" : "可以打字，也可以用麦克风说话。"}</p></div>
              <dl className="bina-facts"><div><dt>人物连接</dt><dd>{connected ? "已加载" : "未连接"}</dd></div><div><dt>当前谈话</dt><dd>{conversationTitle}</dd></div><div><dt>往来消息</dt><dd>{messageCount} 条</dd></div><div><dt>语音输入</dt><dd>{speechActive ? "进行中" : "未开启"}</dd></div></dl>
              <div className="bina-note"><h3>记忆会随交谈延续</h3><p>新建谈话后，仍沿用同一份长期记忆。</p></div>
            </> : tab === "形象" ? <>
              <div className="bina-info-card"><span className="bina-eyebrow">APPEARANCE</span><h3>{avatarModelUrl && avatarStatus?.phase === "ready" ? isWorkAvatar ? "工装 · Live2D 形象" : "日常 · Live2D 形象" : isWorkAvatar ? "工装 · 夹克与工装裤" : "日常 · 针织外套"}</h3><p>{avatarModelUrl ? avatarStatus?.message || "正在准备 Live2D…" : "当前显示定妆图，可加载已绑定的 Live2D 模型。"}</p></div>
              <div className="bina-avatar-buttons" role="group" aria-label="Bina 服装">
                <button type="button" className="ax-btn-ghost" aria-pressed={avatarModelUrl === BINA_MODEL_URL} onClick={() => applyAvatarModel(BINA_MODEL_URL)}>日常装</button>
                <button type="button" className="ax-btn-ghost" aria-pressed={isWorkAvatar} onClick={() => applyAvatarModel(BINA_WORK_MODEL_URL)}>工装</button>
              </div>
              <form className="bina-avatar-settings" onSubmit={(event) => { event.preventDefault(); applyAvatarModel(avatarModelDraft); }}>
                <label className="bina-setting">Live2D 模型路径<input className="ax-input" aria-label="Live2D 模型路径" placeholder={BINA_MODEL_URL} value={avatarModelDraft} onChange={(event) => setAvatarModelDraft(event.target.value)} /></label>
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
              <button type="button" className="ax-btn-ghost" disabled={reconnecting || busy} onClick={() => void onReconnect()}>{reconnecting ? "连接中…" : "重新连接 Bina"}</button>
            </>}
          </div>
          <div className="bina-controls-footer">AXIODRASIL <span>与你在这里</span></div>
        </aside>
  );
}
