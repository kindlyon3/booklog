import type { ImageMetadata } from "astro";
import { getCollection, type CollectionEntry } from "astro:content";
import meta from "../data/meta.json";
import { slugify } from "./slugify";

type Fetched = { olid?: string; pages?: number; published?: number };

export type Book = Omit<CollectionEntry<"books">["data"], "author"> & {
  id: string;
  authors: string[];
  cover?: ImageMetadata;
};

export type Author = { name: string; slug: string; books: Book[] };

const covers = import.meta.glob<{ default: ImageMetadata }>("../assets/covers/*.jpg", {
  eager: true,
});

export function url(path = ""): string {
  return `${import.meta.env.BASE_URL.replace(/\/$/, "")}/${path}`;
}

export async function getBooks(): Promise<Book[]> {
  const entries = await getCollection("books");
  const books = entries.map(({ id, data }) => {
    const fetched: Fetched = (meta as Record<string, Fetched>)[id] ?? {};
    return {
      ...data,
      id,
      authors: [data.author].flat(),
      pages: data.pages ?? fetched.pages,
      published: data.published ?? fetched.published,
      olid: data.olid ?? fetched.olid,
      cover: covers[`../assets/covers/${id}.jpg`]?.default,
    };
  });
  return books.sort((a, b) => (b.finished ?? "9999").localeCompare(a.finished ?? "9999"));
}

export async function getAuthors(): Promise<Author[]> {
  const credits = (await getBooks()).flatMap((book) =>
    book.authors.map((name) => ({ name, book })),
  );
  return groupBy(credits, (credit) => credit.name)
    .map(([name, group]) => ({ name, slug: slugify(name), books: group.map((c) => c.book) }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function isFinished(book: Book): book is Book & { finished: string } {
  return book.finished !== undefined;
}

export function monthName(finished: string): string {
  const [year, month] = finished.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1)).toLocaleString("en-US", {
    month: "long",
    timeZone: "UTC",
  });
}

export function totalPages(books: Book[]): number {
  return books.reduce((sum, book) => sum + (book.pages ?? 0), 0);
}

export function groupBy<T>(items: T[], key: (item: T) => string): [string, T[]][] {
  const groups = new Map<string, T[]>();
  for (const item of items) {
    const group = groups.get(key(item));
    if (group) group.push(item);
    else groups.set(key(item), [item]);
  }
  return [...groups];
}
