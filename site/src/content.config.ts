import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

// Summary bodies are authored as MDX (or legacy MD) colocated in the harness library.
// We glob them directly (ADR-0001) — no copy step. Schema is permissive so legacy .md
// files without frontmatter still load; metadata for the page comes from papers.jsonl.
const summaries = defineCollection({
  loader: glob({ pattern: "**/summary.{md,mdx}", base: "../library" }),
  schema: z
    .object({
      canonical_key: z.string().optional(),
      version_key: z.string().optional(),
      title: z.string().optional(),
      authors: z.array(z.string()).optional(),
      venue: z.string().nullable().optional(),
      year: z.number().nullable().optional(),
      tags: z.array(z.string()).optional(),
      topic_groups: z.array(z.string()).optional(),
      triage_label: z.string().nullable().optional(),
      triage_confidence: z.string().nullable().optional(),
      source_link: z.string().nullable().optional(),
      summary_date: z.coerce.string().optional(),
      curated_by: z.string().optional(),
      contributors: z.array(z.string()).optional(),
    })
    .passthrough(),
});

// Concepts: the global, cross-paper knowledge base (ADR-0005).
const concepts = defineCollection({
  loader: glob({ pattern: "*.{md,mdx}", base: "../knowledge/concepts" }),
  schema: z
    .object({
      name: z.string().optional(),
      title: z.string().optional(),
      aliases: z.array(z.string()).optional(),
      tags: z.array(z.string()).optional(),
      related_papers: z.array(z.string()).optional(),
      related_concepts: z.array(z.string()).optional(),
      created: z.coerce.string().optional(),
      updated: z.coerce.string().optional(),
      curated_by: z.string().optional(),
      contributors: z.array(z.string()).optional(),
    })
    .passthrough(),
});

// Q&A: paper-scoped questions+answers, colocated in the version dir (ADR-0005).
const qa = defineCollection({
  loader: glob({ pattern: "**/qa.mdx", base: "../library" }),
  schema: z
    .object({ canonical_key: z.string().optional(), version_key: z.string().optional() })
    .passthrough(),
});

export const collections = { summaries, concepts, qa };
