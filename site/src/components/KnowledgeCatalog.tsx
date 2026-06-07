import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

const ALL = "__all__";
export interface ConceptRow {
  slug: string; title: string; tags: string[]; linked: number; updated: string; summary: string;
}

export default function KnowledgeCatalog({ concepts, base }: { concepts: ConceptRow[]; base: string }) {
  const [q, setQ] = useState("");
  const [tag, setTag] = useState(ALL);
  const [sort, setSort] = useState("linked");

  const tags = useMemo(
    () => Array.from(new Set(concepts.flatMap((c) => c.tags))).filter(Boolean).sort(),
    [concepts],
  );
  const ql = q.toLowerCase().trim();
  const shown = useMemo(() => {
    const out = concepts.filter(
      (c) =>
        (!ql || (c.title + " " + c.summary).toLowerCase().includes(ql)) &&
        (tag === ALL || c.tags.includes(tag)),
    );
    out.sort((a, b) => {
      if (sort === "title") return a.title.localeCompare(b.title);
      if (sort === "recency") return (b.updated || "").localeCompare(a.updated || "");
      return b.linked - a.linked; // default: most-linked first
    });
    return out;
  }, [concepts, ql, tag, sort]);

  const href = (s: string) => `${base}knowledge/${s}/`.replace(/\/+/g, "/");
  return (
    <div>
      <div className="flex flex-wrap items-end gap-3 my-4">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">Filter</span>
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="filter concepts…" className="w-56" />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">Tag</span>
          <Select value={tag} onValueChange={setTag}>
            <SelectTrigger className="w-44"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>All</SelectItem>
              {tags.map((t) => (<SelectItem key={t} value={t}>{t}</SelectItem>))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground">Sort</span>
          <Select value={sort} onValueChange={setSort}>
            <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="linked">Most linked</SelectItem>
              <SelectItem value="recency">Recently updated</SelectItem>
              <SelectItem value="title">Title</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <p className="text-sm text-muted-foreground mb-2">{shown.length} concept(s)</p>
      <div className="flex flex-col gap-3">
        {shown.map((c) => (
          <Card key={c.slug}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base"><a className="hover:underline" href={href(c.slug)}>{c.title}</a></CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground pt-0">
              {c.summary}
              <div className="mt-1 flex gap-2 items-center flex-wrap">
                {c.tags.map((t) => (<Badge key={t} variant="secondary">{t}</Badge>))}
                <span className="text-xs">· {c.linked} linked paper{c.linked === 1 ? "" : "s"}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
