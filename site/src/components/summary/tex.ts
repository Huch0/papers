// Recover raw LaTeX from rendered slot HTML.
// Astro renders MDX children to HTML before we see them, so a template-literal child
// arrives wrapped in markup with HTML-escaped entities; undo both.
export function texFromSlot(rendered: string | undefined): string {
  if (!rendered) return "";
  return rendered
    .replace(/<[^>]*>/g, "")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&")
    .trim();
}
