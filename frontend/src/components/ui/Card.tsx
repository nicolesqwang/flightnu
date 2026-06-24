import { clsx } from "clsx";
import type { ReactNode } from "react";

export function Card({
  children,
  className,
  as: Component = "div",
}: {
  children: ReactNode;
  className?: string;
  as?: "div" | "section";
}) {
  return (
    <Component className={clsx("glass-card rounded-2xl p-5", className)}>{children}</Component>
  );
}

export function CardLabel({ children }: { children: ReactNode }) {
  return <p className="text-xs font-medium uppercase tracking-wider text-muted">{children}</p>;
}

export function CardValue({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <p className={clsx("font-numeric mt-2 text-2xl font-bold tracking-tight text-foreground", className)}>
      {children}
    </p>
  );
}
