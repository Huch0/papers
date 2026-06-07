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
      // tolerate YAML auto-parsing an unquoted date into a Date object
      summary_date: z.coerce.string().optional(),
    })
    .passthrough(),
});

export const collections = { summaries };
