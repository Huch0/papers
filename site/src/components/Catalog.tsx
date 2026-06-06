import { useMemo, useState } from "react";
import type { PaperEntry } from "@/lib/catalog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

const TRIAGE_RANK: Record<string, number> = { MUST_READ: 0, READ_SOON: 1, SKIM: 2, TRACK_ONLY: 3, SKIP: 4 };
const TRIAGE_CLS: Record<string, string> = {
  MUST_READ: "bg-red-700 text-white", READ_SOON: "bg-amber-600 text-white",
  SKIM: "bg-green-700 text-white", TRACK_ONLY: "bg-neutral-600 text-white", SKIP: "bg-neutral-400 text-white",
};
const ALL = "__all__";
type Row = Pick<PaperEntry, "canonical_key"|"title"|"authors"|"year"|"venue"|"tags"|"topic_groups"|"triage_label"|"score">;

export default function Catalog({ papers, base }: { papers: Row[]; base: string }) {
  const [q, setQ] = useState(""); const [venue, setVenue] = useState(ALL); const [year, setYear] = useState(ALL);
  const [tag, setTag] = useState(ALL); const [topic, setTopic] = useState(ALL); const [triage, setTriage] = useState(ALL);
  const [sort, setSort] = useState("triage");
  const f = useMemo(() => {
    const uniq = (xs: (string | null)[]) => Array.from(new Set(xs.filter((x): x is string => !!x))).sort();
    return {
      venues: uniq(papers.map((p) => p.venue)),
      years: Array.from(new Set(papers.map((p) => p.year).filter((y): y is number => !!y))).sort((a, b) => b - a),
      tags: uniq(papers.flatMap((p) => p.tags)),
      topics: uniq(papers.flatMap((p) => p.topic_groups)),
    };
  }, [papers]);
  const shown = useMemo(() => {
    const ql = q.toLowerCase().trim();
    const out = papers.filter((p) => {
      const hay = (p.title + " " + (p.authors || []).join(" ")).toLowerCase();
      return (!ql || hay.includes(ql)) && (venue === ALL || p.venue === venue) &&
        (year === ALL || String(p.year) === year) && (tag === ALL || (p.tags || []).includes(tag)) &&
        (topic === ALL || (p.topic_groups || []).includes(topic)) && (triage === ALL || p.triage_label === triage);
    });
    out.sort((a, b) => {
      if (sort === "score") return (b.score ?? 0) - (a.score ?? 0);
      if (sort === "year") return (b.year ?? 0) - (a.year ?? 0);
      if (sort === "title") return a.title.localeCompare(b.title);
      return (TRIAGE_RANK[a.triage_label ?? ""] ?? 9) - (TRIAGE_RANK[b.triage_label ?? ""] ?? 9) || (b.score ?? 0) - (a.score ?? 0);
    });
    return out;
  }, [papers, q, venue, year, tag, topic, triage, sort]);
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
          <span className="text-xs text-muted-foreground">Filter title/author</span>
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="type to filter…" className="w-56" />
        </div>
        {facet("Venue", venue, setVenue, f.venues)}
        {facet("Year", year, setYear, f.years)}
        {facet("Tag", tag, setTag, f.tags)}
        {facet("Topic", topic, setTopic, f.topics)}
        {facet("Triage", triage, setTriage, ["MUST_READ", "READ_SOON", "SKIM", "TRACK_ONLY", "SKIP"])}
        <div className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">Sort</span>
          <Select value={sort} onValueChange={setSort}>
            <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="triage">Triage</SelectItem><SelectItem value="score">Score</SelectItem>
              <SelectItem value="year">Year</SelectItem><SelectItem value="title">Title</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <p className="text-sm text-muted-foreground mb-2">{shown.length} shown</p>
      <div className="flex flex-col gap-3">
        {shown.map((p) => (
          <Card key={p.canonical_key}>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2 flex-wrap">
                {p.triage_label && (<Badge className={TRIAGE_CLS[p.triage_label] ?? ""}>{p.triage_label}</Badge>)}
                <CardTitle className="text-base"><a className="hover:underline" href={href(p.canonical_key)}>{p.title}</a></CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground pt-0">
              {(p.authors || []).slice(0, 4).join(", ")}{(p.authors || []).length > 4 ? " et al." : ""} · {p.venue ?? "Preprint"} · {p.year ?? "—"}{p.score != null ? ` · score ${p.score}` : ""}
              {p.tags?.length ? <div className="mt-1 text-xs">{p.tags.join(" · ")}</div> : null}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
