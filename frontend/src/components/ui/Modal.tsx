"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";

export function Modal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/75 backdrop-blur-sm animate-fade-in-up" onClick={onClose} />
      <div
        className="glass-card relative z-10 w-full max-w-lg rounded-2xl bg-surface p-6 animate-fade-in-up"
        style={{
          boxShadow:
            "0 1px 0 rgba(255,255,255,0.06) inset, 0 0 0 1px rgba(106,227,255,0.18), 0 0 60px -8px rgba(106,227,255,0.35), 0 0 120px -20px rgba(180,109,255,0.3)",
        }}
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-muted hover:bg-white/5 hover:text-foreground"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
