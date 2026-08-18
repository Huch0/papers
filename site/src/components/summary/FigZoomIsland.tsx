import { useRef, useState, type ReactNode } from "react";

// Per-figure zoom + pan. Zoom scales the inner width (SVG text scales with it);
// while zoomed, the viewport keeps its 100% height and the figure is panned by
// dragging (pointer events → works for mouse and touch) or native scrollbars.
export default function FigZoomIsland({ children }: { children: ReactNode }) {
  const [z, setZ] = useState(1);
  const [baseH, setBaseH] = useState<number | null>(null);
  const view = useRef<HTMLDivElement>(null);
  const drag = useRef<{ x: number; y: number; sl: number; st: number } | null>(null);

  const clamp = (v: number) => Math.min(3, Math.max(0.6, v));
  const zoomTo = (nz: number) => {
    nz = clamp(nz);
    if (z <= 1 && nz > 1 && view.current) setBaseH(view.current.clientHeight);
    if (nz <= 1) { setBaseH(null); view.current?.scrollTo(0, 0); }
    setZ(nz);
  };

  const down = (e: React.PointerEvent<HTMLDivElement>) => {
    if (z <= 1 || !view.current) return;
    drag.current = { x: e.clientX, y: e.clientY, sl: view.current.scrollLeft, st: view.current.scrollTop };
    (e.target as Element).setPointerCapture?.(e.pointerId);
  };
  const move = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!drag.current || !view.current) return;
    view.current.scrollLeft = drag.current.sl - (e.clientX - drag.current.x);
    view.current.scrollTop = drag.current.st - (e.clientY - drag.current.y);
  };
  const up = () => { drag.current = null; };

  return (
    <div className="figzoom">
      <div className="figzoom-bar">
        {z > 1 && <span style={{ marginRight: "auto" }}>drag to pan</span>}
        <button onClick={() => zoomTo(z / 1.25)} aria-label="shrink figure">−</button>
        <span>{Math.round(z * 100)}%</span>
        <button onClick={() => zoomTo(z * 1.25)} aria-label="enlarge figure">+</button>
        {z !== 1 && <button onClick={() => zoomTo(1)} aria-label="reset figure size">reset</button>}
      </div>
      <div
        ref={view}
        className="figzoom-viewport"
        onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up}
        style={{
          overflow: z > 1 ? "auto" : "visible",
          maxHeight: z > 1 && baseH ? baseH : undefined,
          cursor: z > 1 ? (drag.current ? "grabbing" : "grab") : undefined,
          touchAction: z > 1 ? "none" : undefined,
          userSelect: z > 1 ? "none" : undefined,
        }}
      >
        <div style={{ width: (z * 100) + "%" }}>{children}</div>
      </div>
    </div>
  );
}
