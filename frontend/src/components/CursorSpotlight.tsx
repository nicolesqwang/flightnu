"use client";

import { useEffect, useRef } from "react";

/**
 * Flashlight-style cursor halo. Writes raw CSS vars on every pointer move
 * (rAF-throttled) instead of React state, since this fires far too often
 * for a render cycle.
 */
export function CursorSpotlight() {
  const coreRef = useRef<HTMLDivElement>(null);
  const haloRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let frame = 0;
    let pending = false;
    let x = window.innerWidth / 2;
    let y = window.innerHeight / 2;

    function apply() {
      pending = false;
      const root = document.documentElement;
      root.style.setProperty("--cursor-x", `${x}px`);
      root.style.setProperty("--cursor-y", `${y}px`);
      if (coreRef.current) coreRef.current.style.opacity = "1";
      if (haloRef.current) haloRef.current.style.opacity = "1";
    }

    function onMove(e: PointerEvent) {
      x = e.clientX;
      y = e.clientY;
      if (!pending) {
        pending = true;
        frame = requestAnimationFrame(apply);
      }
    }

    function onLeave() {
      if (coreRef.current) coreRef.current.style.opacity = "0";
      if (haloRef.current) haloRef.current.style.opacity = "0";
    }

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerleave", onLeave);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
      cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <>
      <div ref={haloRef} className="cursor-halo" aria-hidden="true" />
      <div ref={coreRef} className="cursor-core" aria-hidden="true" />
    </>
  );
}
