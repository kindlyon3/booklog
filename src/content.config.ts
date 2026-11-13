import { defineCollection } from "astro:content";
import { file } from "astro/loaders";
import { z } from "astro/zod";
import { parse } from "yaml";
import { slugify } from "./lib/slugify";

export const FORMS = ["fiction", "nonfiction", "poetry", "religion"] as const;

const books = defineCollection({
  loader: file("src/data/books.yaml", {
    parser: (text) =>
      (parse(text) as { title: string }[]).map((book) => ({ id: slugify(book.title), ...book })),
  }),
  schema: z
    .object({
      title: z.string(),
      author: z.union([z.string(), z.array(z.string()).nonempty()]),
      role: z.enum(["editor", "translator"]).optional(),
      edition: z.string().optional(),
      form: z.enum(FORMS),
      status: z.enum(["reading", "read"]).default("read"),
      finished: z
        .string()
        .regex(/^\d{4}-(0[1-9]|1[0-2])$/, "use YYYY-MM")
        .optional(),
      rating: z.number().min(0.5).max(5).multipleOf(0.5).optional(),
      pages: z.number().int().positive().optional(),
      published: z.number().int().optional(),
      olid: z.string().optional(),
      note: z.string().optional(),
    })
    .refine((book) => book.status === "reading" || book.finished, {
      message: "finished (YYYY-MM) is required unless status is reading",
    }),
});

export const collections = { books };
