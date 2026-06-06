// @ts-check
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import react from "@astrojs/react";
import pagefind from "astro-pagefind";
import tailwindcss from "@tailwindcss/vite";

// For GitHub Pages project sites the site is served under /<repo>/. Override via env:
//   SITE_URL=https://<user>.github.io  BASE_PATH=/papers  (or /pr-preview/pr-N for previews)
const base = process.env.BASE_PATH || "/";
const site = process.env.SITE_URL || "https://example.github.io";

export default defineConfig({
  site,
  base,
  output: "static",
  trailingSlash: "ignore",
  integrations: [mdx(), react(), pagefind()],
  vite: { plugins: [tailwindcss()] },
  build: { format: "directory" },
});
