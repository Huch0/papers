import { useEffect, useRef, useState } from "react";

// Interactive flow-matching explainer (toy 2-D transport).
// Convention matches DreamZero/Wan (Eq.2 of arXiv 2602.15922): t=0 is pure noise,
// t=1 is clean data, x_t = t*x1 + (1-t)*x0, constant velocity v = x1 - x0.
// Deterministic PRNG so the server render and the hydrated client render agree.

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function gauss(rnd: () => number) {
  const u = Math.max(rnd(), 1e-9), v = rnd();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

const W = 480, H = 300;
const DATA_C = [352, 152], NOISE_C = [118, 152];

function makeData(): [number, number][] {
  const pts: [number, number][] = [];
  const [cx, cy] = DATA_C, R = 74;
  for (let i = 0; i < 18; i++) { // face ring
    const a = (i / 18) * 2 * Math.PI;
    pts.push([cx + R * Math.cos(a), cy + R * Math.sin(a)]);
  }
  for (const ex of [-27, 27]) // eyes
    for (const [dx, dy] of [[0, 0], [-7, 6], [7, 6]] as [number, number][])
      pts.push([cx + ex + dx, cy - 22 + dy]);
  for (let i = 0; i < 7; i++) { // mouth arc
    const a = Math.PI * (0.2 + 0.6 * (i / 6));
    pts.push([cx + 38 * Math.cos(a), cy + 12 + 26 * Math.sin(a)]);
  }
  return pts;
}
function makeNoise(seed: number, n: number): [number, number][] {
  const rnd = mulberry32(seed);
  return Array.from({ length: n }, () => [
    NOISE_C[0] + gauss(rnd) * 40,
    NOISE_C[1] + gauss(rnd) * 40,
  ] as [number, number]);
}

const btn: React.CSSProperties = {
  border: "1px solid var(--line)", borderRadius: 6, padding: "0.15rem 0.55rem",
  background: "var(--soft)", color: "inherit", fontSize: "0.78rem", cursor: "pointer",
};
const btnOn: React.CSSProperties = { ...btn, borderColor: "var(--accent)", color: "var(--accent)", fontWeight: 600 };

export default function FlowMatchIsland() {
  const [t, setT] = useState(0);
  const [tab, setTab] = useState<"gen" | "train">("gen");
  const [seed, setSeed] = useState(7);
  const [trainT, setTrainT] = useState(0.45);
  const [anim, setAnim] = useState(false);
  const [sameSpace, setSameSpace] = useState(false);
  const raf = useRef(0);

  const data = useRef(makeData()).current;
  const noiseRaw = makeNoise(seed, data.length);
  const noise = sameSpace
    ? noiseRaw.map(([x, y]) => [x - NOISE_C[0] + DATA_C[0], y - NOISE_C[1] + DATA_C[1]] as [number, number])
    : noiseRaw;
  const tt = tab === "gen" ? t : trainT;
  const pos = data.map((d, i) => [
    tt * d[0] + (1 - tt) * noise[i][0],
    tt * d[1] + (1 - tt) * noise[i][1],
  ] as [number, number]);

  useEffect(() => {
    if (!anim) return;
    let cur = 0;
    const t0 = performance.now();
    const step = (now: number) => {
      cur = Math.min((now - t0) / 2600, 1);
      setT(cur);
      if (cur < 1) raf.current = requestAnimationFrame(step);
      else setAnim(false);
    };
    raf.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf.current);
  }, [anim]);

  const nextTrainT = () => setTrainT((p) => { const v = (p * 9301 + 49297) % 233280 / 233280; return 0.12 + 0.72 * v; });

  return (
    <div style={{ border: "1px solid var(--line)", borderRadius: 8, padding: "0.6rem 0.7rem", margin: "0.8rem 0" }}>
      <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.45rem" }}>
        <button style={tab === "gen" ? btnOn : btn} onClick={() => setTab("gen")}>Generate: ride the field</button>
        <button style={tab === "train" ? btnOn : btn} onClick={() => { setAnim(false); setTab("train"); }}>Train: regress the arrows</button>
        <span style={{ flex: 1 }} />
        {tab === "gen" && (
          <button style={btn} onClick={() => { setT(0); setAnim(true); }}>▶ animate t: 0 → 1</button>
        )}
        {tab === "train" && <button style={btn} onClick={nextTrainT}>sample a new t</button>}
        <button style={btn} onClick={() => setSeed((s) => s + 1)}>re-draw the noise</button>
        <button style={sameSpace ? btnOn : btn} onClick={() => setSameSpace(v => !v)}>{sameSpace ? "same-space view ✓" : "separated for legibility"}</button>
      </div>

      <svg viewBox={"0 0 " + W + " " + H} style={{ width: "100%", height: "auto", display: "block" }} role="img"
        aria-label="Toy flow matching: points travel straight lines from a Gaussian noise cloud at t equals 0 to a smiley-shaped data distribution at t equals 1; arrows show the constant velocity the network must predict. A toggle overlays the two distributions in the same space, showing that transport directions point every way.">
        {sameSpace ? (
          <text x={DATA_C[0]} y={26} textAnchor="middle" fill="currentColor" opacity="0.65" fontSize="12">noise and data share one space — arrows point every direction</text>
        ) : (<>
          <text x={NOISE_C[0]} y={26} textAnchor="middle" fill="currentColor" opacity="0.65" fontSize="12">noise&nbsp; x₀ ~ N(0, I) &nbsp;(t = 0)</text>
          <text x={DATA_C[0]} y={26} textAnchor="middle" fill="currentColor" opacity="0.65" fontSize="12">data&nbsp; x₁ &nbsp;(t = 1)</text>
        </>)}
        {pos.map((p, i) => (
          <g key={i}>
            <line x1={noise[i][0]} y1={noise[i][1]} x2={data[i][0]} y2={data[i][1]}
              stroke="currentColor" strokeWidth="0.6" opacity="0.10" />
            <circle cx={noise[i][0]} cy={noise[i][1]} r="1.6" fill="currentColor" opacity="0.22" />
            <circle cx={data[i][0]} cy={data[i][1]} r="1.6" fill="currentColor" opacity="0.22" />
          </g>
        ))}
        {pos.map((p, i) => {
          if (i % (tab === "train" ? 2 : 3) !== 0) return null;
          const dx = data[i][0] - noise[i][0], dy = data[i][1] - noise[i][1];
          const n = Math.hypot(dx, dy) || 1, L = 20;
          const ex = p[0] + (dx / n) * L, ey = p[1] + (dy / n) * L;
          return (
            <g key={"a" + i} stroke="var(--accent)" strokeWidth="1.3" opacity={tab === "train" ? 0.95 : 0.55}>
              <line x1={p[0]} y1={p[1]} x2={ex} y2={ey} />
              <line x1={ex} y1={ey} x2={ex - (dx / n) * 5 + (dy / n) * 3} y2={ey - (dy / n) * 5 - (dx / n) * 3} />
              <line x1={ex} y1={ey} x2={ex - (dx / n) * 5 - (dy / n) * 3} y2={ey - (dy / n) * 5 + (dx / n) * 3} />
            </g>
          );
        })}
        {pos.map((p, i) => (
          <circle key={"p" + i} cx={p[0]} cy={p[1]} r="3.1" fill="var(--accent)" opacity="0.9" />
        ))}
      </svg>

      {tab === "gen" ? (
        <div style={{ display: "flex", gap: "0.6rem", alignItems: "center", marginTop: "0.35rem" }}>
          <input type="range" min="0" max="1" step="0.005" value={t} style={{ flex: 1 }}
            onChange={(e) => { setAnim(false); setT(parseFloat(e.target.value)); }} aria-label="denoising time t" />
          <code style={{ fontSize: "0.8rem", minWidth: "5.5rem" }}>t = {t.toFixed(2)}</code>
        </div>
      ) : (
        <div style={{ marginTop: "0.35rem", fontSize: "0.8rem" }}>
          <code>t = {trainT.toFixed(2)}</code> — the network sees only (position, t) and must output the accent
          arrow; the loss is the mean squared error against the true straight-line velocity x₁ − x₀.
        </div>
      )}
      <p style={{ margin: "0.45rem 0 0", fontSize: "0.78rem", color: "var(--mut)" }}>
        Every point moves on a straight line from its noise sample to its data sample; the velocity is the same at
        every t, which is what makes the regression target simple. The network never sees the pairing — it must
        infer the average direction "home" from (position, t) alone. Generation = start at t 0 and integrate the
        learned field to t 1. DreamZero uses exactly this objective, jointly over video latents and action latents.
      </p>
    </div>
  );
}
