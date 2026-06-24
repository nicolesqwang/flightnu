import { clsx } from "clsx";
import type { Recommendation } from "@/lib/types";
import { RECOMMENDATION_LABEL } from "@/lib/format";

const STYLES: Record<Recommendation, string> = {
  BUY_NOW: "bg-accent-green/12 text-accent-green border-accent-green/40 shadow-[0_0_18px_-2px_rgba(44,255,184,0.55)]",
  WAIT: "bg-accent-red/12 text-accent-red border-accent-red/40 shadow-[0_0_18px_-2px_rgba(255,93,143,0.55)]",
  MONITOR: "bg-accent-yellow/12 text-accent-yellow border-accent-yellow/40 shadow-[0_0_18px_-2px_rgba(255,200,87,0.55)]",
};

export function RecommendationBadge({
  recommendation,
  size = "md",
}: {
  recommendation: Recommendation | null | undefined;
  size?: "sm" | "md" | "lg";
}) {
  if (!recommendation) {
    return (
      <span className="inline-flex items-center rounded-full border border-border px-3 py-1 text-xs font-semibold text-muted">
        PENDING
      </span>
    );
  }

  const sizeClass =
    size === "lg" ? "px-4 py-1.5 text-sm" : size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-3 py-1 text-xs";

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border font-semibold tracking-wide backdrop-blur-sm",
        STYLES[recommendation],
        sizeClass
      )}
    >
      <span className="neon-dot h-1.5 w-1.5 animate-pulse-glow rounded-full bg-current" />
      {RECOMMENDATION_LABEL[recommendation]}
    </span>
  );
}
