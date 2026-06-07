import fs from "node:fs";
import path from "node:path";

// Derived login -> {name} map (registry/contributors.json, from config/contributors.yaml).
const F = path.resolve(process.cwd(), "..", "registry", "contributors.json");
let MAP: Record<string, { name: string }> = {};
try { MAP = JSON.parse(fs.readFileSync(F, "utf-8")); } catch { /* none yet */ }

export interface Person { id: string; name: string; github: string | null; avatar: string | null; url: string | null; }

// `id` is a GitHub login when it's in the contributor map (ADR-0006), else a raw git name.
export function person(id: string): Person {
  if (!id) return { id: "unknown", name: "unknown", github: null, avatar: null, url: null };
  const rec = MAP[id];
  const github = rec ? id : null; // mapped → it's a real GitHub login
  return {
    id,
    name: rec?.name ?? id,
    github,
    avatar: github ? `https://github.com/${github}.png?size=64` : null,
    url: github ? `https://github.com/${github}` : null,
  };
}

export function initials(name: string): string {
  return name.split(/\s+/).filter(Boolean).map((w) => w[0]).slice(0, 2).join("").toUpperCase() || "?";
}
