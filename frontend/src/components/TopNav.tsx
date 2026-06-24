import Link from "next/link";

export function TopNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-blue/15 text-accent-blue"
            style={{ boxShadow: "0 0 18px -2px rgba(106,227,255,0.7), inset 0 0 0 1px rgba(106,227,255,0.3)" }}
          >
            ✈
          </span>
          <span className="text-lg font-bold tracking-tight text-foreground">
            Flight<span className="text-accent-blue neon-text-blue">Nu</span>
          </span>
        </Link>
        <div className="flex items-center gap-2 text-xs text-muted">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent-green opacity-60" />
            <span className="neon-dot relative inline-flex h-2 w-2 rounded-full bg-accent-green text-accent-green" />
          </span>
          Live tracking
        </div>
      </div>
    </header>
  );
}
