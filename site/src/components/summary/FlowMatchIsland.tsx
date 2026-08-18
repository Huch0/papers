import { useEffect, useRef, useState } from "react";

// Interactive flow-matching explainer (toy 2-D transport).
// Convention matches DreamZero/Wan (Eq.2 of arXiv 2602.15922): t=0 is pure noise,
// t=1 is clean data, x_t = t*x1 + (1-t)*x0, constant velocity v = x1 - x0.
// Three views: Generate (ride the field), Train (regress the arrows), and Field —
// the EXACT marginal field of this toy, which has a closed form for finite data +
// Gaussian noise: u*(x,t) = (softmax-weighted data mean − x) / (1 − t).
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
const SIGMA = 40; // std of the toy noise cloud, used by makeNoise AND the exact field

function makeData(): [number, number][] {
  const pts: [number, number][] = [];
  const [cx, cy] = DATA_C, R = 74;
  for (let i = 0; i < 18; i++) {
    const a = (i / 18) * 2 * Math.PI;
    pts.push([cx + R * Math.cos(a), cy + R * Math.sin(a)]);
  }
  for (const ex of [-27, 27])
    for (const [dx, dy] of [[0, 0], [-7, 6], [7, 6]] as [number, number][])
      pts.push([cx + ex + dx, cy - 22 + dy]);
  for (let i = 0; i < 7; i++) {
    const a = Math.PI * (0.2 + 0.6 * (i / 6));
    pts.push([cx + 38 * Math.cos(a), cy + 12 + 26 * Math.sin(a)]);
  }
  return pts;
}
function makeNoise(seed: number, n: number, center: number[]): [number, number][] {
  const rnd = mulberry32(seed);
  return Array.from({ length: n }, () => [
    center[0] + gauss(rnd) * SIGMA,
    center[1] + gauss(rnd) * SIGMA,
  ] as [number, number]);
}

// Exact marginal field of the toy: posterior over which data point the point is
// heading to (Gaussian noise), then (posterior-mean destination − x) / (1 − t).
function marginalField(px: number, py: number, t: number, data: [number, number][]) {
  const om = Math.max(1 - t, 0.03);
  const denom = 2 * SIGMA * SIGMA * om * om;
  let sw = 0, mx = 0, my = 0, best = -Infinity;
  const logs = data.map(([dx, dy]) => {
    const ex = px - t * dx, ey = py - t * dy;
    const l = -(ex * ex + ey * ey) / denom;
    if (l > best) best = l;
    return l;
  });
  data.forEach(([dx, dy], i) => {
    const w = Math.exp(logs[i] - best);
    sw += w; mx += w * dx; my += w * dy;
  });
  mx /= sw; my /= sw;
  return [(mx - px) / om, (my - py) / om];
}

const btn: React.CSSProperties = {
  border: "1px solid var(--line)", borderRadius: 6, padding: "0.15rem 0.55rem",
  background: "var(--soft)", color: "inherit", fontSize: "0.78rem", cursor: "pointer",
};
const btnOn: React.CSSProperties = { ...btn, borderColor: "var(--accent)", color: "var(--accent)", fontWeight: 600 };

export default function FlowMatchIsland() {
  const [t, setT] = useState(0);
  const [tab, setTab] = useState<"gen" | "train" | "field">("gen");
  const [seed, setSeed] = useState(7);
  const [trainT, setTrainT] = useState(0.45);
  const [anim, setAnim] = useState(false);
  const [sameSpace, setSameSpace] = useState(false);
  const raf = useRef(0);

  const data = useRef(makeData()).current;
  const noise = makeNoise(seed, data.length, sameSpace || tab === "field" ? DATA_C : NOISE_C);
  const tt = tab === "train" ? trainT : t;
  const pos = data.map((d, i) => [
    tt * d[0] + (1 - tt) * noise[i][0],
    tt * d[1] + (1 - tt) * noise[i][1],
  ] as [number, number]);

  useEffect(() => {
    if (!anim) return;
    const t0 = performance.now();
    const step = (now: number) => {
      const cur = Math.min((now - t0) / 2600, 1);
      setT(cur);
      if (cur < 1) raf.current = requestAnimationFrame(step);
      else setAnim(false);
    };
    raf.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf.current);
  }, [anim]);

  const nextTrainT = () => setTrainT((p) => { const v = (p * 9301 + 49297) % 233280 / 233280; return 0.12 + 0.72 * v; });

  // arrow-grid of the exact marginal field (field view)
  const grid: { x: number; y: number; dx: number; dy: number; len: number }[] = [];
  if (tab === "field") {
    for (let gx = 30; gx <= 452; gx += 42)
      for (let gy = 44; gy <= 288; gy += 40) {
        const [ux, uy] = marginalField(gx, gy, t, data);
        const mag = Math.hypot(ux, uy) || 1e-6;
        const len = 26 * Math.tanh(mag / 150);
        if (len < 2.2) continue;
        grid.push({ x: gx, y: gy, dx: ux / mag, dy: uy / mag, len });
      }
  }

  return (
    <div style={{ border: "1px solid var(--line)", borderRadius: 8, padding: "0.6rem 0.7rem", margin: "0.8rem 0" }}>
      <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.45rem" }}>
        <button style={tab === "gen" ? btnOn : btn} onClick={() => setTab("gen")}>Generate: ride the field</button>
        <button style={tab === "train" ? btnOn : btn} onClick={() => { setAnim(false); setTab("train"); }}>Train: regress the arrows</button>
        <button style={tab === "field" ? btnOn : btn} onClick={() => setTab("field")}>Field: the marginal wind</button>
        <span style={{ flex: 1 }} />
        {tab !== "train" && (
          <button style={btn} onClick={() => { setT(0); setAnim(true); }}>▶ animate t: 0 → 1</button>
        )}
        {tab === "train" && <button style={btn} onClick={nextTrainT}>sample a new t</button>}
        {tab !== "field" && <button style={btn} onClick={() => setSeed((s) => s + 1)}>re-draw the noise</button>}
        {tab !== "field" && (
          <button style={sameSpace ? btnOn : btn} onClick={() => setSameSpace(v => !v)}>{sameSpace ? "same-space view ✓" : "separated for legibility"}</button>
        )}
      </div>

      <svg viewBox={"0 0 " + W + " " + H} style={{ width: "100%", height: "auto", display: "block" }} role="img"
        aria-label="Toy flow matching. Generate and train views: points travel straight lines from a Gaussian noise cloud to a smiley-shaped data distribution, with velocity arrows. Field view: an arrow grid showing the exact marginal velocity field at the chosen time, defined at every grid point without any particles.">
        {tab === "field" ? (
          <g>
            <text x={W / 2} y={24} textAnchor="middle" fill="currentColor" opacity="0.65" fontSize="12">the marginal field u(x, t) — one arrow per point of space, particles optional</text>
            {data.map((d, i) => (
              <circle key={"d" + i} cx={d[0]} cy={d[1]} r="1.8" fill="currentColor" opacity="0.28" />
            ))}
            {grid.map((a, i) => {
              const ex = a.x + a.dx * a.len, ey = a.y + a.dy * a.len;
              return (
                <g key={i} stroke="var(--accent)" strokeWidth="1.15" opacity="0.8">
                  <line x1={a.x} y1={a.y} x2={ex} y2={ey} />
                  <line x1={ex} y1={ey} x2={ex - a.dx * 4.4 + a.dy * 2.6} y2={ey - a.dy * 4.4 - a.dx * 2.6} />
                  <line x1={ex} y1={ey} x2={ex - a.dx * 4.4 - a.dy * 2.6} y2={ey - a.dy * 4.4 + a.dx * 2.6} />
                </g>
              );
            })}
          </g>
        ) : (
          <g>
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
          </g>
        )}
      </svg>

      {tab !== "train" ? (
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
      {tab === "field" ? (
        <p style={{ margin: "0.45rem 0 0", fontSize: "0.78rem", color: "var(--mut)" }}>
          The exact marginal field of this toy, drawn the honest way: freeze time, draw one arrow per grid
          point (a wind map), scrub t. No particles are needed — the field is defined everywhere. Near t = 0
          every arrow points at the data centroid (broad posterior); as t → 1 arrows sharpen toward the
          nearest cluster of data points (posterior collapse) and their true magnitude grows like 1/(1 − t) —
          displayed lengths are tanh-compressed, so direction is faithful and length is indicative only.
        </p>
      ) : (
        <p style={{ margin: "0.45rem 0 0", fontSize: "0.78rem", color: "var(--mut)" }}>
          Every point moves on a straight line from its noise sample to its data sample; the velocity is the same at
          every t, which is what makes the regression target simple. The side-by-side layout is only for
          legibility — noise and data live in one space (toggle the same-space view), so true directions
          point every way. Arrows are drawn direction-only at a fixed display length; every true target
          has its pair's full magnitude ‖x₁ − x₀‖, constant along the whole line. The network never sees the pairing — it must
          infer the average direction "home" from (position, t) alone. Generation = start at t 0 and integrate the
          learned field to t 1. DreamZero uses exactly this objective, jointly over video latents and action latents.
        </p>
      )}
    </div>
  );
}
