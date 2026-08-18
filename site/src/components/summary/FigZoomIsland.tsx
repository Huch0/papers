import { useState, type ReactNode } from "react";

// Per-figure zoom control. Children are the (static) figure; zooming scales the
// inner width, and the viewport scrolls horizontally instead of the page.
export default function FigZoomIsland({ children }: { children: ReactNode }) {
  const [z, setZ] = useState(1);
  const clamp = (v: number) => Math.min(3, Math.max(0.6, v));
  return (
    <div className="figzoom">
      <div className="figzoom-bar">
        <button onClick={() => setZ(v => clamp(v / 1.25))} aria-label="shrink figure">−</button>
        <span>{Math.round(z * 100)}%</span>
        <button onClick={() => setZ(v => clamp(v * 1.25))} aria-label="enlarge figure">+</button>
        {z !== 1 && <button onClick={() => setZ(1)} aria-label="reset figure size">reset</button>}
      </div>
      <div className="figzoom-viewport" style={{ overflowX: z > 1 ? "auto" : "visible" }}>
        <div style={{ width: (z * 100) + "%" }}>{children}</div>
      </div>
    </div>
  );
}
