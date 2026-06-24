import { clsx } from "clsx";
import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
}

const VARIANTS: Record<string, string> = {
  primary:
    "bg-accent-blue text-black font-semibold hover:bg-accent-blue/90 shadow-[0_0_0_1px_rgba(106,227,255,0.5),0_0_24px_-4px_rgba(106,227,255,0.7)] hover:shadow-[0_0_0_1px_rgba(106,227,255,0.7),0_0_40px_-2px_rgba(106,227,255,0.9)]",
  secondary:
    "bg-surface-2 text-foreground border border-border hover:border-accent-purple/50 hover:shadow-[0_0_24px_-6px_rgba(180,109,255,0.6)]",
  ghost: "bg-transparent text-muted hover:text-foreground hover:bg-white/5",
  danger:
    "bg-accent-red/15 text-accent-red border border-accent-red/30 hover:bg-accent-red/25 hover:shadow-[0_0_24px_-6px_rgba(255,93,143,0.6)]",
};

export function Button({ variant = "primary", className, ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all disabled:cursor-not-allowed disabled:opacity-50",
        VARIANTS[variant],
        className
      )}
      {...props}
    />
  );
}
