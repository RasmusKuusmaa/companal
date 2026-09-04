/**
 * Renders lesson prose to sanitized HTML.
 *
 * Lesson content is authored by us and seeded from the repository, never
 * submitted by a user - so this isn't defending against a hostile author.
 * It's defending against the day some content becomes user-supplied (a
 * shared composition's notes, a comment on a lesson) and someone reaches
 * for the renderer that already exists. Sanitizing unconditionally means
 * that day can't introduce an XSS hole by omission.
 *
 * GFM is on for tables, which theory content leans on constantly - interval
 * charts, figured-bass symbols, key signatures. Line breaks are *not*
 * converted to `<br>`: authored prose wraps at whatever width the file
 * happens to use, and turning those wraps into hard breaks would mangle
 * every paragraph.
 */

import DOMPurify from "dompurify";
import { marked } from "marked";

marked.use({ gfm: true, breaks: false });

/** Adds safe link behaviour to anything the lesson links out to. */
DOMPurify.addHook("afterSanitizeAttributes", (node) => {
  if (node instanceof HTMLAnchorElement && node.hasAttribute("href")) {
    node.setAttribute("target", "_blank");
    node.setAttribute("rel", "noopener noreferrer");
  }
});

export function renderMarkdown(source: string): string {
  // `async: false` keeps the return type a plain string rather than a
  // promise - none of the extensions in use here need to await anything.
  const html = marked.parse(source, { async: false });
  return DOMPurify.sanitize(html);
}
