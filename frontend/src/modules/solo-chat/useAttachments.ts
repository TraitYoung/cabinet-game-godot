"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { ingestAttachment } from "@/matrix/client";
import type { PendingAttachment } from "./composePayload";

export function useAttachments(sessionId: string, onError: (message: string) => void) {
  const [attachments, setAttachments] = useState<PendingAttachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const urls = useRef(new Set<string>());
  const fileInputRef = useRef<HTMLInputElement>(null);
  const reset = useCallback(() => {
    controllerRef.current?.abort(); controllerRef.current = null;
    setUploading(false); setAttachments([]);
    for (const url of urls.current) URL.revokeObjectURL(url);
    urls.current.clear();
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, []);
  useEffect(() => {
    const previews = urls.current;
    return () => {
      controllerRef.current?.abort();
      for (const url of previews) URL.revokeObjectURL(url);
      previews.clear();
    };
  }, [sessionId]);

  const pick = async (files: FileList | null) => {
    if (!files?.length || !sessionId) return;
    controllerRef.current?.abort();
    const controller = new AbortController(); controllerRef.current = controller;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        const result = await ingestAttachment(file, sessionId, controller.signal);
        if (controller.signal.aborted || controllerRef.current !== controller) return;
        const previewUrl = result.kind === "image" ? URL.createObjectURL(file) : undefined;
        if (previewUrl) urls.current.add(previewUrl);
        setAttachments((current) => [...current, { ...result, id: crypto.randomUUID(), previewUrl }]);
      }
    } catch (error) {
      if (!controller.signal.aborted && controllerRef.current === controller) onError(error instanceof Error ? error.message : String(error));
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null; setUploading(false);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    }
  };
  return { attachments, uploading, fileInputRef, reset, pick,
    take: () => { const sent = attachments; setAttachments([]); return sent; },
    restore: (sent: PendingAttachment[]) => setAttachments((current) => current.length ? current : sent),
    remove: (id: string) => setAttachments((current) => {
      const target = current.find((item) => item.id === id);
      if (target?.previewUrl) { URL.revokeObjectURL(target.previewUrl); urls.current.delete(target.previewUrl); }
      return current.filter((item) => item.id !== id);
    }) };
}
