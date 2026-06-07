// Fast per-file MDX syntax validator. Usage (run from site/):
//   node scripts/check-mdx.mjs <path-to-summary.mdx> [...more]
// Strips YAML frontmatter, then compiles the body with @mdx-js/mdx so authors can
// confirm a summary parses BEFORE finalizing. Exit 0 = all valid; non-zero = failures.
import { readFileSync } from "node:fs";
import { compile } from "@mdx-js/mdx";

const files = process.argv.slice(2);
let bad = 0;
for (const f of files) {
  let src;
  try { src = readFileSync(f, "utf8"); }
  catch (e) { bad++; console.error(`MISSING ${f}: ${e.message}`); continue; }
  src = src.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, "");
  try {
    await compile(src, { jsx: true });
  } catch (e) {
    bad++;
    const loc = e.line ? ` (line ${e.line}:${e.column})` : "";
    console.error(`FAIL ${f}${loc}: ${String(e.message).split("\n")[0]}`);
  }
}
console.log(bad ? `\n${bad} file(s) FAILED MDX compile` : `all ${files.length} OK`);
process.exit(bad ? 1 : 0);
