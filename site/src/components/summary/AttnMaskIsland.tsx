import { useState } from "react";

// Interactive attention-mask explorer for chunked/causal (video-)DiTs.
// Defaults mirror Fig.14 of arXiv 2602.15922 (DreamZero): clean context frames
// C0-C2, then the current window's noisy video tokens Z1-Z3 and action tokens
// Y1-Y3. Hover (or tap) a query row to read its receptive field.

type Tok = { id: string; kind: "ctx" | "vid" | "act" };
const WINDOW: Tok[] = [
  { id: "C0", kind: "ctx" }, { id: "C1", kind: "ctx" }, { id: "C2", kind: "ctx" },
  { id: "Z1", kind: "vid" }, { id: "Y1", kind: "act" },
  { id: "Z2", kind: "vid" }, { id: "Y2", kind: "act" },
  { id: "Z3", kind: "vid" }, { id: "Y3", kind: "act" },
];
const CHUNKS = ["chunk 1", "chunk 2", "chunk 3", "chunk 4"];

const btn: React.CSSProperties = {
  border: "1px solid var(--line)", borderRadius: 6, padding: "0.15rem 0.55rem",
  background: "var(--soft)", color: "inherit", fontSize: "0.78rem", cursor: "pointer",
};
const btnOn: React.CSSProperties = { ...btn, borderColor: "var(--accent)", color: "var(--accent)", fontWeight: 600 };
const REAL = "#2f6b3a";   // cache holds real observations (forest, readable both themes)
const PRED = "#b5791f";   // cache holds the model's own predictions (amber)

export default function AttnMaskIsland() {
  const [tab, setTab] = useState<0 | 1 | 2>(0);
  const [row, setRow] = useState<number | null>(null);
  const [overwrite, setOverwrite] = useState(true);

  const cell = 26, pad = 44, n = WINDOW.length;
  const attends = (q: Tok, k: Tok) => q.kind !== "ctx" && (k.kind === "ctx" || true); // window: noisy tokens see everything
  const caption = (i: number) => {
    const q = WINDOW[i];
    if (q.kind === "ctx") return q.id + " is clean context - it is only read (KV), never a query here.";
    const what = q.kind === "act" ? "action tokens " : "video-latent tokens ";
    const cache = tab === 2
      ? (overwrite ? "C0-C2 = real camera frames (KV cache, overwritten after execution)" : "C0-C2 = the model's own earlier predictions (drift accumulates)")
      : "C0-C2 = clean past frames (teacher forcing)";
    return what + q.id + " see: " + cache + " + every noisy token of the current window (all share one t).";
  };

  const grid = (
    <svg viewBox={"0 0 " + (pad + n * cell + 8) + " " + (pad + n * cell + 8)}
      style={{ width: "100%", maxWidth: 380, height: "auto", display: "block" }} role="img"
      aria-label="Attention mask grid: noisy video and action tokens attend to clean context frames and to each other.">
      {WINDOW.map((k, j) => (
        <text key={"c" + j} x={pad + j * cell + cell / 2} y={pad - 10} textAnchor="middle" fontSize="11"
          fill={k.kind === "ctx" ? (tab === 2 ? (overwrite ? REAL : PRED) : "currentColor") : "currentColor"}
          opacity={k.kind === "ctx" ? 0.95 : 0.65} fontWeight={k.kind === "ctx" ? 600 : 400}>{k.id}</text>
      ))}
      {WINDOW.map((q, i) => (
        <g key={"r" + i} onMouseEnter={() => setRow(i)} onClick={() => setRow(i)} style={{ cursor: "pointer" }}>
          <text x={pad - 8} y={pad + i * cell + cell / 2 + 4} textAnchor="end" fontSize="11"
            fill="currentColor" opacity={q.kind === "ctx" ? 0.4 : 0.85}
            fontWeight={row === i ? 700 : 400}>{q.id}</text>
          {WINDOW.map((k, j) => {
            const on = attends(q, k);
            const isCtxCol = k.kind === "ctx";
            const fill = !on ? "var(--soft)"
              : isCtxCol && tab === 2 ? (overwrite ? REAL : PRED)
              : "var(--accent)";
            return (
              <rect key={j} x={pad + j * cell + 1.5} y={pad + i * cell + 1.5} width={cell - 3} height={cell - 3}
                rx="3" fill={fill} opacity={!on ? 0.55 : row === null || row === i ? (isCtxCol ? 0.85 : 0.75) : 0.18}
                stroke="var(--line)" strokeWidth="0.5" />
            );
          })}
        </g>
      ))}
      <text x={pad - 34} y={pad + (n * cell) / 2} fontSize="10" fill="currentColor" opacity="0.5"
        transform={"rotate(-90 " + (pad - 34) + " " + (pad + (n * cell) / 2) + ")"} textAnchor="middle">query</text>
      <text x={pad + (n * cell) / 2} y={16} fontSize="10" fill="currentColor" opacity="0.5" textAnchor="middle">key / value</text>
    </svg>
  );

  const chunkGrid = (
    <svg viewBox="0 0 360 220" style={{ width: "100%", maxWidth: 380, height: "auto", display: "block" }} role="img"
      aria-label="Block-causal mask over four chunks: each chunk attends to all earlier clean chunks and to itself.">
      {CHUNKS.map((c, j) => (
        <text key={"h" + j} x={110 + j * 60 + 26} y={40} textAnchor="middle" fontSize="11" fill="currentColor" opacity="0.7">{c}</text>
      ))}
      {CHUNKS.map((rq, i) => (
        <g key={i}>
          <text x={100} y={58 + i * 42 + 20} textAnchor="end" fontSize="11" fill="currentColor" opacity="0.85">{rq} (noisy)</text>
          {CHUNKS.map((_, j) => (
            <rect key={j} x={110 + j * 60} y={58 + i * 42} width="52" height="32" rx="4"
              fill={j < i ? "var(--accent)" : j === i ? "none" : "var(--soft)"}
              stroke={j === i ? "var(--accent)" : "var(--line)"}
              strokeDasharray={j === i ? "4 3" : "0"}
              opacity={j <= i ? 0.85 : 0.5} strokeWidth={j === i ? 1.6 : 0.6} />
          ))}
        </g>
      ))}
      <text x={330} y={210} textAnchor="end" fontSize="10" fill="currentColor" opacity="0.55">solid = reads clean chunk · dashed = its own noisy tokens</text>
    </svg>
  );

  return (
    <div style={{ border: "1px solid var(--line)", borderRadius: 8, padding: "0.6rem 0.7rem", margin: "0.8rem 0" }}>
      <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", marginBottom: "0.5rem" }}>
        <button style={tab === 0 ? btnOn : btn} onClick={() => { setTab(0); setRow(null); }}>Training: one window</button>
        <button style={tab === 1 ? btnOn : btn} onClick={() => { setTab(1); setRow(null); }}>Chunk-causal over time</button>
        <button style={tab === 2 ? btnOn : btn} onClick={() => { setTab(2); setRow(null); }}>Inference: KV cache</button>
        {tab === 2 && (
          <button style={{ ...btn, marginLeft: "auto", borderColor: overwrite ? REAL : PRED, color: overwrite ? REAL : PRED }}
            onClick={() => setOverwrite((o) => !o)}>
            {overwrite ? "cache = real frames ✓" : "cache = own predictions ⚠"}
          </button>
        )}
      </div>
      {tab === 1 ? chunkGrid : grid}
      <p style={{ margin: "0.45rem 0 0", fontSize: "0.78rem", color: "var(--mut)", minHeight: "2.2em" }}>
        {tab === 1
          ? "Across chunks the mask is block-triangular, like an LLM over sentences: chunk k denoises while reading the finished chunks before it, never the future. Within a chunk, attention is bidirectional."
          : row !== null ? caption(row)
          : tab === 2
            ? (overwrite
              ? "Hover a row. After each 1.6 s chunk executes, DreamZero throws away its predicted frames and writes the real camera frames into the KV cache - autoregressive drift is erased every chunk."
              : "Hover a row. A pure video generator must condition on its own imperfect predictions; small errors feed back and compound. Toggle the button to see DreamZero's fix.")
            : "Hover a row to read its receptive field. Text and proprioception tokens also join the sequence; this grid shows the frame/action structure of Fig. 14."}
      </p>
    </div>
  );
}
