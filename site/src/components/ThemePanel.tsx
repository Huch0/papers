import { useEffect, useRef, useState, type ReactNode } from "react";

const PRESETS = [
  { id: "reading-room", label: "Reading Room" },
  { id: "lab-notes", label: "Lab Notes" },
  { id: "terminal", label: "Terminal" },
  { id: "pastel", label: "Pastel" },
];
const FONTS = [
  { id: "", label: "Preset" },
  { id: "serif", label: "Serif" },
  { id: "sans", label: "Sans" },
  { id: "mono", label: "Mono" },
];
const ACCENTS = [
  { id: "", label: "Preset", color: "transparent" },
  { id: "#8a2f2a", label: "Oxblood", color: "#8a2f2a" },
  { id: "#1d6f6f", label: "Teal", color: "#1d6f6f" },
  { id: "#3a4f9a", label: "Indigo", color: "#3a4f9a" },
  { id: "#2f6b3a", label: "Forest", color: "#2f6b3a" },
  { id: "#7a3f72", label: "Plum", color: "#7a3f72" },
  { id: "#b5791f", label: "Amber", color: "#b5791f" },
];
const DENSITY = [
  { id: "compact", label: "Compact" },
  { id: "comfortable", label: "Comfortable" },
  { id: "spacious", label: "Spacious" },
];

const get = (k: string) => { try { return localStorage.getItem(k) || ""; } catch { return ""; } };
const save = (k: string, v: string) => { try { v ? localStorage.setItem(k, v) : localStorage.removeItem(k); } catch { /* ignore */ } };
const root = () => document.documentElement;

export default function ThemePanel() {
  const [open, setOpen] = useState(false);
  const [preset, setPreset] = useState("reading-room");
  const [font, setFont] = useState("");
  const [accent, setAccent] = useState("");
  const [density, setDensity] = useState("comfortable");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setPreset(get("theme-preset") || "reading-room");
    setFont(get("theme-font"));
    setAccent(get("theme-accent"));
    setDensity(get("theme-density") || "comfortable");
  }, []);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    const onEsc = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onEsc);
    return () => { document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onEsc); };
  }, [open]);

  const applyPreset = (id: string) => {
    setPreset(id); save("theme-preset", id === "reading-room" ? "" : id);
    if (id === "reading-room") root().removeAttribute("data-theme");
    else root().setAttribute("data-theme", id);
  };
  const applyFont = (id: string) => {
    setFont(id); save("theme-font", id);
    if (id) root().setAttribute("data-font", id); else root().removeAttribute("data-font");
  };
  const applyAccent = (id: string) => {
    setAccent(id); save("theme-accent", id);
    if (id) { root().style.setProperty("--accent", id); root().style.setProperty("--tldr-bd", id); }
    else { root().style.removeProperty("--accent"); root().style.removeProperty("--tldr-bd"); }
  };
  const applyDensity = (id: string) => {
    setDensity(id); save("theme-density", id === "comfortable" ? "" : id);
    root().setAttribute("data-density", id);
    root().style.setProperty("--ui-scale", id === "compact" ? "94%" : id === "spacious" ? "112%" : "100%");
  };
  const reset = () => { applyPreset("reading-room"); applyFont(""); applyAccent(""); applyDensity("comfortable"); };

  return (
    <div className="relative inline-block align-middle" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Customize theme" title="Customize theme"
        className="border rounded px-2 py-1 leading-none text-sm hover:text-[var(--accent)]"
        style={{ fontFamily: "var(--font-display)" }}
      >Aa</button>
      {open && (
        <div
          className="absolute right-0 mt-2 w-64 z-50 rounded-lg border bg-card text-card-foreground shadow-xl p-3"
          style={{ fontFamily: "var(--font-body)" }}
        >
          <Group label="Theme">
            {PRESETS.map((p) => <Chip key={p.id} on={preset === p.id} onClick={() => applyPreset(p.id)}>{p.label}</Chip>)}
          </Group>
          <Group label="Typeface">
            {FONTS.map((f) => <Chip key={f.id || "preset"} on={font === f.id} onClick={() => applyFont(f.id)}>{f.label}</Chip>)}
          </Group>
          <Group label="Accent">
            {ACCENTS.map((a) => (
              <button
                key={a.id || "preset"} title={a.label} onClick={() => applyAccent(a.id)}
                aria-label={a.label}
                className={"w-6 h-6 rounded-full border " + (accent === a.id ? "ring-2 ring-[var(--ring)] ring-offset-1 ring-offset-[var(--card)]" : "")}
                style={{ background: a.color === "transparent" ? "var(--soft)" : a.color }}
              />
            ))}
          </Group>
          <Group label="Density">
            {DENSITY.map((x) => <Chip key={x.id} on={density === x.id} onClick={() => applyDensity(x.id)}>{x.label}</Chip>)}
          </Group>
          <button onClick={reset} className="mt-1 w-full text-xs underline text-muted-foreground hover:text-foreground">
            Reset to default
          </button>
        </div>
      )}
    </div>
  );
}

function Group({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="mb-3">
      <div className="text-[0.62rem] uppercase tracking-wider text-muted-foreground mb-1.5">{label}</div>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}
function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={"px-2 py-1 rounded border text-xs transition-colors " +
        (on ? "bg-primary text-primary-foreground border-transparent" : "bg-secondary text-secondary-foreground hover:border-[var(--accent)]")}
    >{children}</button>
  );
}
