// Per-user read/unread tracking for summaries.
//
// Storage model (ADR-0007): localStorage is the instant local cache; if the reader
// connects a GitHub token, their read map is synced to a PRIVATE GIST on their own
// account (file `papers-reads.json`) — giving automatic, free, per-user cross-device
// sync with no server. Last-writer-wins: marking pushes the full map (debounced);
// opening pulls the gist and overwrites the local cache. Without a token it is pure
// localStorage (per-browser). A paper is "read" only while the stored marker matches
// the current version+summary-date, so a new version / updated summary re-surfaces it.
const LKEY = "paper-reads";        // local cache {canonical_key: marker}
const TKEY = "gh-gist-token";      // fine-grained PAT (Gists read/write)
const GKEY = "gh-reads-gist-id";   // resolved gist id (cache)
const GIST_FILE = "papers-reads.json";
const GIST_DESC = "papers reading-tracker — per-user summary read/unread state";

export type Reads = Record<string, string>;
export function marker(latestVersion?: string | null, summaryDate?: string | null): string {
  return `${latestVersion ?? "v?"}__${summaryDate ?? ""}`;
}

// ---- local cache ----
export function getReads(): Reads { try { return JSON.parse(localStorage.getItem(LKEY) || "{}"); } catch { return {}; } }
function saveLocal(r: Reads) { try { localStorage.setItem(LKEY, JSON.stringify(r)); } catch { /* ignore */ } }
export function isRead(r: Reads, key: string, mk: string): boolean { return r[key] === mk; }

// ---- token / gist plumbing ----
export function getToken(): string { try { return localStorage.getItem(TKEY) || ""; } catch { return ""; } }
export function setToken(t: string) { try { t ? localStorage.setItem(TKEY, t) : localStorage.removeItem(TKEY); } catch { /* ignore */ } }
export function syncEnabled(): boolean { return !!getToken(); }
function getGistId(): string { try { return localStorage.getItem(GKEY) || ""; } catch { return ""; } }
function setGistId(id: string) { try { id ? localStorage.setItem(GKEY, id) : localStorage.removeItem(GKEY); } catch { /* ignore */ } }
export function disconnect() { setToken(""); setGistId(""); }

async function gh(path: string, opts: RequestInit = {}): Promise<any> {
  const res = await fetch(`https://api.github.com${path}`, {
    ...opts,
    headers: { Authorization: `Bearer ${getToken()}`, Accept: "application/vnd.github+json", ...(opts.headers || {}) },
  });
  if (!res.ok) throw new Error(`GitHub ${res.status}`);
  return res.json();
}

export async function whoami(): Promise<string | null> { try { return (await gh("/user")).login ?? null; } catch { return null; } }

async function findOrCreateGist(): Promise<string> {
  const cached = getGistId();
  if (cached) return cached;
  const gists = await gh("/gists?per_page=100");
  const found = (gists || []).find((g: any) => g.files && g.files[GIST_FILE]);
  if (found) { setGistId(found.id); return found.id; }
  const created = await gh("/gists", {
    method: "POST",
    body: JSON.stringify({ description: GIST_DESC, public: false, files: { [GIST_FILE]: { content: "{}" } } }),
  });
  setGistId(created.id);
  return created.id;
}

// Pull the gist and make it the local cache (returns the merged map). No-op without sync.
export async function pullRemote(): Promise<Reads | null> {
  if (!syncEnabled()) return null;
  const id = await findOrCreateGist();
  const g = await gh(`/gists/${id}`);
  const f = g.files?.[GIST_FILE];
  let content = f?.content ?? "{}";
  if (f?.truncated && f?.raw_url) content = await (await fetch(f.raw_url)).text();
  let remote: Reads = {}; try { remote = JSON.parse(content || "{}"); } catch { /* keep {} */ }
  saveLocal(remote);
  return remote;
}

// Marking auto-syncs: each mark schedules a debounced push (batches rapid clicks); a
// flush on tab hide/close covers the case of leaving within the debounce window.
let pushTimer: ReturnType<typeof setTimeout> | null = null;
let dirty = false;
export function schedulePush() {
  if (!syncEnabled()) return;
  dirty = true;
  if (pushTimer) clearTimeout(pushTimer);
  pushTimer = setTimeout(() => { pushNow().catch(() => { /* offline/invalid token: stays local */ }); }, 1200);
}
export async function pushNow(opts?: { keepalive?: boolean }): Promise<void> {
  if (!syncEnabled()) return;
  if (pushTimer) { clearTimeout(pushTimer); pushTimer = null; }
  const id = await findOrCreateGist();
  await gh(`/gists/${id}`, {
    method: "PATCH",
    keepalive: opts?.keepalive,
    body: JSON.stringify({ files: { [GIST_FILE]: { content: JSON.stringify(getReads()) } } }),
  });
  dirty = false;
}
// flush any pending mark before the page is hidden/closed (keepalive lets it finish)
if (typeof window !== "undefined") {
  const flush = () => { if (dirty && syncEnabled()) pushNow({ keepalive: true }).catch(() => { /* stays local */ }); };
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") flush(); });
  window.addEventListener("pagehide", flush);
}

// ---- mutations (instant local + debounced sync) ----
export function setRead(key: string, mk: string): Reads { const r = getReads(); r[key] = mk; saveLocal(r); schedulePush(); return r; }
export function setUnread(key: string): Reads { const r = getReads(); delete r[key]; saveLocal(r); schedulePush(); return r; }

// ---- manual backup (works with or without sync) ----
export function importMerge(json: string): Reads {
  let inc: Reads = {}; try { inc = JSON.parse(json); } catch { return getReads(); }
  const r = { ...getReads(), ...inc }; saveLocal(r); schedulePush(); return r;
}
