export function Footer() {
  return (
    <footer className="mt-auto border-t border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-6 py-6 text-xs text-muted sm:flex-row">
        <div className="flex items-center gap-2">
          <span
            className="flex h-6 w-6 items-center justify-center rounded-full bg-accent-blue/15 text-[11px] font-bold text-accent-blue"
            style={{ boxShadow: "0 0 12px -1px rgba(106,227,255,0.6), inset 0 0 0 1px rgba(106,227,255,0.3)" }}
          >
            N
          </span>
          <span>
            Flight<span className="text-accent-blue">Nu</span>
          </span>
        </div>

        <p>&copy; {new Date().getFullYear()} FlightNu. All rights reserved.</p>

        <a
          href="https://nicoleswang.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent-blue transition-colors hover:text-accent-blue/80 hover:underline"
        >
          Built by nicoleswang.com
        </a>
      </div>
    </footer>
  );
}
