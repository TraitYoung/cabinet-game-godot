"use client";

import Script from "next/script";
import { useEffect, useImperativeHandle, useRef, useState, type Ref } from "react";
import type { Application } from "pixi.js";
import type { Live2DModel, CubismInternalModel } from "untitled-pixi-live2d-engine/cubism";
import { stabilizeBinaRig } from "./binaRig";

export type AvatarStatus = {
  phase: "loading" | "ready" | "error";
  message: string;
  motions: string[];
  expressions: string[];
};

export type AvatarControls = {
  motion: (group: string) => Promise<unknown> | undefined;
  expression: (name: string) => Promise<unknown> | undefined;
};

export function Live2DAvatar({ modelUrl, controlsRef, onStatus }: {
  modelUrl: string;
  controlsRef: Ref<AvatarControls>;
  onStatus: (status: AvatarStatus) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const modelRef = useRef<Live2DModel | null>(null);
  const [coreReady, setCoreReady] = useState(false);

  useImperativeHandle(controlsRef, () => ({
    motion: (group) => modelRef.current?.motion(group),
    expression: (name) => modelRef.current?.expression(name),
  }), []);

  useEffect(() => {
    if (!coreReady) return;
    const host = hostRef.current!;
    let cancelled = false;
    let app: Application | undefined;
    let model: Live2DModel | undefined;
    let observer: ResizeObserver | undefined;
    let release: (() => void) | undefined;

    async function load() {
      onStatus({ phase: "loading", message: "正在加载 Live2D 模型…", motions: [], expressions: [] });
      try {
        const [pixi, engine] = await Promise.all([
          import("pixi.js"),
          import("untitled-pixi-live2d-engine/cubism"),
        ]);
        if (cancelled) return;
        pixi.extensions.add(engine.Live2DPlugin);
        app = new pixi.Application();
        await app.init({
          width: host.clientWidth,
          height: host.clientHeight,
          preference: ["webgl"],
          failIfMajorPerformanceCaveat: false,
          backgroundAlpha: 0,
          autoDensity: true,
          resolution: Math.min(window.devicePixelRatio || 1, 2),
        });
        release = () => {
          // Detach the model from its ticker before Application destroys it.
          model?.destroy();
          model = undefined;
          app?.destroy(true, { children: true });
          app = undefined;
        };
        if (cancelled) { release(); return; }
        host.appendChild(app.canvas);
        model = await engine.Live2DModel.from(modelUrl, { autoFocus: true, autoHitTest: true, ticker: app.ticker, anchorMode: "drawable" });
        if (cancelled) { release(); return; }
        if (new URL(modelUrl, window.location.href).pathname === "/live2d/bina/bina.model3.json") {
          stabilizeBinaRig(model.internalModel as CubismInternalModel);
        }
        app.stage.addChild(model);
        modelRef.current = model;
        const modelWidth = model.width;
        const modelHeight = model.height;
        model.anchor.set(0.5, 1);
        const fit = () => {
          if (!app || !model) return;
          const width = host.clientWidth;
          const height = host.clientHeight;
          if (!width || !height) return;
          app.renderer.resize(width, height);
          model.scale.set(Math.min(width * 0.9 / modelWidth, height * 0.9 / modelHeight));
          model.position.set(width / 2, height * 0.98);
        };
        observer = new ResizeObserver(fit);
        observer.observe(host);
        fit();
        const motions = (model.internalModel as CubismInternalModel).motionManager;
        onStatus({
          phase: "ready", message: "Live2D 已就绪",
          motions: Object.keys(motions.definitions).filter((group) => motions.definitions[group]?.length),
          expressions: motions.expressionManager?.definitions.map((item) => item.Name) ?? [],
        });
      } catch (error) {
        observer?.disconnect();
        release?.();
        release = undefined;
        modelRef.current = null;
        if (!cancelled) onStatus({
          phase: "error",
          message: `Live2D 加载失败：${error instanceof Error ? error.message : String(error)}`,
          motions: [], expressions: [],
        });
      }
    }
    void load();
    return () => {
      cancelled = true;
      observer?.disconnect();
      modelRef.current = null;
      // Loading owns cleanup until the model has finished arriving.
      if (model) { release?.(); release = undefined; }
    };
  }, [coreReady, modelUrl, onStatus]);

  return <>
    <Script src="/live2d/core/live2dcubismcore.min.js" strategy="afterInteractive"
      onReady={() => setCoreReady(true)}
      onError={() => onStatus({ phase: "error", message: "缺少 Live2D Core，请先按项目说明放入运行库。", motions: [], expressions: [] })} />
    <div ref={hostRef} className="bina-live2d" role="img" aria-label="Bina 的 Live2D 形象" />
  </>;
}
