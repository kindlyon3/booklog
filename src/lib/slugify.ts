export function fold(text: string): string {
  return text.normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase();
}

// Must match slugify() in scripts/booklog.py so cover and metadata lookups line up.
export function slugify(text: string): string {
  return fold(text)
    .replace(/[^ -~]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
