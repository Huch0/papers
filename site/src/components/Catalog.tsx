import { useEffect, useMemo, useRef, useState } from "react";
import type { PaperEntry } from "@/lib/catalog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { type Reads, marker, getReads, isRead, setRead, setUnread, pullRemote } from "@/lib/reads";

const TRIAGE_RANK: Record<string, number> = { MUST_READ: 0, READ_SOON: 1, SKIM: 2, TRACK_ONLY: 3, SKIP: 4 };
const TRIAGE_CLS: Record<string, string> = {
  MUST_READ: "bg-red-700 text-white", READ_SOON: "bg-amber-600 text-white",
  SKIM: "bg-green-700 text-white", TRACK_ONLY: "bg-neutral-600 text-white", SKIP: "bg-neutral-400 text-white",
};
const ALL = "__all__";
type Row = Pick<PaperEntry, "canonical_key" | "title" | "authors" | "year" | "venue" | "tags" | "topic_groups" | "triage_label" | "score">
  & { latest_version?: string | null; summary_date?: string | null; source_updated_at?: string | null };

export default function Catalog({ papers, base }: { papers: Row[]; base: string }) {
  const [q, setQ] = useState("");
  const [venue, setVenue] = useState(ALL);
  const [year, setYear] = useState(ALL);
  const [tag, setTag] = useState(ALL);
  const [topic, setTopic] = useState(ALL);
  const [triage, setTriage] = useState(ALL);
  const [readStatus, setReadStatus] = useState(ALL); // All | unread | read
  const [sort, setSort] = useState("triage");
  const [dir, setDir] = useState<"asc" | "desc">("asc"); // default matches triage (MUST_READ first)
  const defaultDir = (s: string): "asc" | "desc" => (s === "triage" || s === "title" ? "asc" : "desc");
  const changeSort = (s: string) => { setSort(s); setDir(defaultDir(s)); };

  // per-browser read state
  const [reads, setReads] = useState<Reads>({});
  useEffect(() => {
    setReads(getReads());                                   // instant local cache
    pullRemote().then((r) => { if (r) setReads(r); }).catch(() => { /* stays local */ }); // sync if connected
  }, []);
  const mk = (p: Row) => marker(p.latest_version, p.summary_date);
  const read = (p: Row) => isRead(reads, p.canonical_key, mk(p));
  const toggleRead = (p: Row) => setReads(read(p) ? setUnread(p.canonical_key) : setRead(p.canonical_key, mk(p)));

  // Pagefind full-text search, intersected with the facet filters below.
  const pf = useRef<any>(null);
  const [pfReady, setPfReady] = useState(false);
  const [searchKeys, setSearchKeys] = useState<Set<string> | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const mod = await import(/* @vite-ignore */ `${base}pagefind/pagefind.js`);
        await mod.init?.();
        if (!cancelled) { pf.current = mod; setPfReady(true); }
      } catch { /* no index in dev → fall back to local title/author match */ }
    })();
    return () => { cancelled = true; };
  }, [base]);

  useEffect(() => {
    const term = q.trim();
    if (!term || !pfReady || !pf.current) { setSearchKeys(null); return; }
    let cancelled = false;
    const t = setTimeout(async () => {
      try {
        const res = await pf.current.search(term);
        const datas = await Promise.all(res.results.slice(0, 200).map((r: any) => r.data()));
        const keys = new Set<string>();
        for (const d of datas) {
          const k = String(d.url).replace(/\/+$/, "").split("/").pop();
          if (k) keys.add(k);
        }
        if (!cancelled) setSearchKeys(keys);
      } catch { if (!cancelled) setSearchKeys(null); }
    }, 180);
    return () => { cancelled = true; clearTimeout(t); };
  }, [q, pfReady]);

  const f = useMemo(() => {
    const uniq = (xs: (string | null)[]) => Array.from(new Set(xs.filter((x): x is string => !!x))).sort();
    return {
      venues: uniq(papers.map((p) => p.venue)),
      years: Array.from(new Set(papers.map((p) => p.year).filter((y): y is number => !!y))).sort((a, b) => b - a),
      tags: uniq(papers.flatMap((p) => p.tags)),
      topics: uniq(papers.flatMap((p) => p.topic_groups)),
    };
  }, [papers]);

  const ql = q.toLowerCase().trim();
  const textOk = (p: Row) => {
    if (!ql) return true;
    if (pfReady && searchKeys) return searchKeys.has(p.canonical_key);          // full-text (prod)
    return (p.title + " " + (p.authors || []).join(" ")).toLowerCase().includes(ql); // fallback (dev)
  };

  const shown = useMemo(() => {
    const out = papers.filter(
      (p) =>
        textOk(p) &&
        (venue === ALL || p.venue === venue) &&
        (year === ALL || String(p.year) === year) &&
        (tag === ALL || (p.tags || []).includes(tag)) &&
        (topic === ALL || (p.topic_groups || []).includes(topic)) &&
        (triage === ALL || p.triage_label === triage) &&
        (readStatus === ALL || (readStatus === "read" ? read(p) : !read(p))),
    );
    const sign = dir === "asc" ? 1 : -1;
    const dkey = (p: Row) => p.source_updated_at || `${p.year ?? 0}-01-01`; // ISO sorts chronologically
    out.sort((a, b) => {
      let cmp: number; // ascending comparison for the chosen field
      if (sort === "score") cmp = (a.score ?? 0) - (b.score ?? 0);
      else if (sort === "date") cmp = dkey(a).localeCompare(dkey(b));
      else if (sort === "title") cmp = a.title.localeCompare(b.title);
      else cmp = (TRIAGE_RANK[a.triage_label ?? ""] ?? 9) - (TRIAGE_RANK[b.triage_label ?? ""] ?? 9);
      cmp *= sign;
      return cmp || (b.score ?? 0) - (a.score ?? 0); // stable tiebreak: score desc
    });
    return out;
  }, [papers, q, venue, year, tag, topic, triage, readStatus, reads, sort, dir, searchKeys, pfReady]);

  const unreadCount = useMemo(() => papers.filter((p) => !read(p)).length, [papers, reads]);

  const href = (key: string) => `${base}papers/${key}/`.replace(/\/+/g, "/");
  const facet = (label: string, value: string, set: (v: string) => void, opts: (string | number)[]) => (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <Select value={value} onValueChange={set}>
        <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>All</SelectItem>
          {opts.map((o) => (<SelectItem key={String(o)} value={String(o)}>{o}</SelectItem>))}
        </SelectContent>
      </Select>
    </div>
  );

  return (
    <div>
      <div className="flex flex-wrap items-end gap-3 my-4">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">Search (full-text + title/author)</span>
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="search summaries…" className="w-64" />
        </div>
        {facet("Venue", venue, setVenue, f.venues)}
        {facet("Year", year, setYear, f.years)}
        {facet("Tag", tag, setTag, f.tags)}
        {facet("Topic", topic, setTopic, f.topics)}
        {facet("Triage", triage, setTriage, ["MUST_READ", "READ_SOON", "SKIM", "TRACK_ONLY", "SKIP"])}
        <div className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">Status</span>
          <Select value={readStatus} onValueChange={setReadStatus}>
            <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>All</SelectItem>
              <SelectItem value="unread">Unread</SelectItem>
              <SelectItem value="read">Read</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">Sort</span>
          <div className="flex gap-1">
            <Select value={sort} onValueChange={changeSort}>
              <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="triage">Triage</SelectItem><SelectItem value="score">Score</SelectItem>
                <SelectItem value="date">Publish date</SelectItem><SelectItem value="title">Title</SelectItem>
              </SelectContent>
            </Select>
            <button
              onClick={() => setDir((d) => (d === "asc" ? "desc" : "asc"))}
              className="border rounded px-2 text-sm hover:border-[var(--accent)] whitespace-nowrap"
              title={dir === "asc" ? "Ascending — click for descending" : "Descending — click for ascending"}
            >{dir === "asc" ? "↑ Asc" : "↓ Desc"}</button>
          </div>
        </div>
      </div>

      <p className="text-sm text-muted-foreground mb-2">
        {shown.length} shown · <span className="font-medium">{unreadCount} unread</span>{ql && !pfReady ? " · (full-text search active on the deployed site)" : ""}
      </p>

      <div className="flex flex-col gap-3">
        {shown.map((p) => {
          const r = read(p);
          return (
          <Card key={p.canonical_key} className={r ? "opacity-60" : ""}>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2 flex-wrap">
                {!r && <span className="inline-block w-2 h-2 rounded-full bg-primary" title="unread" />}
                {p.triage_label && (<Badge className={TRIAGE_CLS[p.triage_label] ?? ""}>{p.triage_label}</Badge>)}
                <CardTitle className="text-base"><a className="hover:underline" href={href(p.canonical_key)}>{p.title}</a></CardTitle>
                <button
                  onClick={() => toggleRead(p)}
                  className="ml-auto text-xs border rounded px-2 py-0.5 hover:border-[var(--accent)] whitespace-nowrap"
                  title={r ? "Mark as unread" : "Mark as read"}
                >{r ? "✓ Read" : "Mark read"}</button>
              </div>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground pt-0">
              {(p.authors || []).slice(0, 4).join(", ")}{(p.authors || []).length > 4 ? " et al." : ""} · {p.venue ?? "Preprint"} · {p.source_updated_at ? p.source_updated_at.slice(0, 10) : (p.year ?? "—")}{p.score != null ? ` · score ${p.score}` : ""}
              {p.tags?.length ? <div className="mt-1 text-xs">{p.tags.join(" · ")}</div> : null}
            </CardContent>
          </Card>
          );
        })}
      </div>
    </div>
  );
}
