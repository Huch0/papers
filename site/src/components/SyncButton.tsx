import { useEffect, useRef, useState } from "react";
import { getReads, getToken, setToken, syncEnabled, whoami, pullRemote, pushNow, disconnect, importMerge } from "@/lib/reads";

export default function SyncButton() {
  const [open, setOpen] = useState(false);
  const [login, setLogin] = useState<string | null>(null);
  const [tok, setTok] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { if (syncEnabled()) whoami().then(setLogin); }, []);
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    const onEsc = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDoc); document.addEventListener("keydown", onEsc);
    return () => { document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onEsc); };
  }, [open]);

  const connect = async () => {
    setBusy(true); setMsg(""); setToken(tok.trim());
    const who = await whoami();
    if (!who) { setToken(""); setBusy(false); setMsg("Token didn't authenticate (401). Check you pasted it fully and it hasn't expired."); return; }
    // Validate Gist access for real — don't show "connected" if gists fail.
    try { await pullRemote(); }
    catch (e: any) {
      setToken("");
      setBusy(false);
      setMsg(`Authenticated as ${who}, but Gist access failed (${e?.message || "error"}). Your token needs Gist read/write: a classic token with the 'gist' scope, or a fine-grained token with Account → Gists: Read and write.`);
      return;
    }
    setLogin(who); setMsg(`Connected as ${who} — syncing across devices.`); setBusy(false);
    setTimeout(() => location.reload(), 700);
  };
  const off = () => { disconnect(); setLogin(null); setMsg("Disconnected (read state stays local)."); setTimeout(() => location.reload(), 400); };
  const syncNow = async () => { setBusy(true); try { await pushNow(); await pullRemote(); location.reload(); } catch (e: any) { setMsg(`Sync failed (${e?.message || "error"}). The token likely lacks Gist read/write — reconnect with a 'gist'-scoped (classic) or Account→Gists (fine-grained) token.`); setBusy(false); } };
  const doExport = () => {
    const blob = new Blob([JSON.stringify(getReads(), null, 2)], { type: "application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "papers-reads.json"; a.click(); URL.revokeObjectURL(a.href);
  };
  const onImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]; if (!f) return;
    const rd = new FileReader(); rd.onload = () => { importMerge(String(rd.result || "{}")); location.reload(); }; rd.readAsText(f);
  };

  return (
    <div className="relative inline-block align-middle" ref={ref}>
      <button onClick={() => setOpen((o) => !o)} title="Read-state sync"
        className="border rounded px-2 py-1 leading-none text-xs hover:text-[var(--accent)]">
        {login ? `⇅ ${login}` : "⇅ Sync"}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-72 z-50 rounded-lg border bg-card text-card-foreground shadow-xl p-3 text-sm"
          style={{ fontFamily: "var(--font-body)" }}>
          <div className="text-[0.62rem] uppercase tracking-wider text-muted-foreground mb-1.5">Read-state sync</div>
          {login ? (
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">Synced to a private gist on <b>{login}</b>. Your read/unread follows you across devices.</p>
              <div className="flex gap-2">
                <button onClick={syncNow} disabled={busy} className="text-xs border rounded px-2 py-1 hover:border-[var(--accent)]">Sync now</button>
                <button onClick={off} className="text-xs border rounded px-2 py-1 hover:border-[var(--accent)]">Disconnect</button>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">
                Optional cross-device sync. Paste a GitHub token with <b>Gist read/write</b> —
                a <a href="https://github.com/settings/tokens/new?scopes=gist&description=papers-reads" target="_blank" rel="noopener" className="underline">classic token with the <code>gist</code> scope</a> (easiest),
                or a <a href="https://github.com/settings/tokens?type=beta" target="_blank" rel="noopener" className="underline">fine-grained token</a> with <b>Account → Gists: Read and write</b>.
                Stored only in this browser; sent only to GitHub. Without it, read state stays per-browser.
              </p>
              <input type="password" value={tok} onChange={(e) => setTok(e.target.value)} placeholder="github_pat_…"
                className="w-full border rounded px-2 py-1 text-xs bg-transparent" />
              <button onClick={connect} disabled={busy || !tok.trim()} className="text-xs border rounded px-2 py-1 hover:border-[var(--accent)]">
                {busy ? "Connecting…" : "Connect & sync"}
              </button>
            </div>
          )}
          {msg && <p className="text-xs mt-2 text-[var(--accent)]">{msg}</p>}
          <div className="border-t mt-2 pt-2 flex gap-2 items-center">
            <span className="text-[0.62rem] uppercase tracking-wider text-muted-foreground">Backup</span>
            <button onClick={doExport} className="text-xs border rounded px-2 py-0.5 hover:border-[var(--accent)]">Export</button>
            <button onClick={() => fileRef.current?.click()} className="text-xs border rounded px-2 py-0.5 hover:border-[var(--accent)]">Import</button>
            <input ref={fileRef} type="file" accept="application/json" className="hidden" onChange={onImport} />
          </div>
        </div>
      )}
    </div>
  );
}
