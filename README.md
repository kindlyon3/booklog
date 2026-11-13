# booklog

A month-by-month log of books read, built with [Astro](https://astro.build) and published to GitHub Pages. Book details and covers come from [Open Library](https://openlibrary.org).

## Setup

```sh
npm install
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Adding books

All books live in [`src/data/books.yaml`](src/data/books.yaml). The `booklog` command edits it and fetches page counts, publication years, and covers.

```sh
./booklog add "Gilead" "Marilynne Robinson" fiction 4.5   # finished this month
./booklog add "Gilead" "Marilynne Robinson" fiction --reading
./booklog finish "Gilead" 4                               # reading → finished
./booklog add "Hamlet" "William Shakespeare" fiction 4 --edition Folger --month 2025-04
```

Forms: `fiction`, `nonfiction`, `poetry`, `religion`. Ratings run 0.5–5 in half steps and are optional.

Editing the YAML by hand works too; run `./booklog enrich` afterwards to fetch details for new entries.

### From a phone

Open a new issue with the **Book** template, using the book's title as the issue title. Choosing **Finished** for the title being read marks it finished; any other title is added. A workflow applies it, fetches details, commits, redeploys, and closes the issue with what it matched. If something is wrong it comments with the error; edit the issue to retry. Only issues opened by the repository owner are applied.

Pull before editing locally, since these commits happen on GitHub.

### Book fields

```yaml
- title: "Contemporary Catholic Poetry: An Anthology" # quote titles containing ": "
  author: [April Lindner, Ryan Wilson] # string, or list for several
  role: editor # optional: editor | translator
  edition: Folger # optional, shown after the title
  form: poetry
  status: reading # only while reading; omit once finished
  finished: 2026-03 # YYYY-MM
  rating: 4.5 # optional
  note: A short thought. # optional
  pages: 206 # optional override
  published: 2008 # optional override
  olid: OL2625412W # optional: pin the exact Open Library work
```

### Fixing details

- **Wrong pages or year:** set `pages` or `published` on the entry.
- **Wrong book matched:** find the work on openlibrary.org, set `olid`, then run `./booklog enrich --only "Title"`.
- **Wrong or missing cover:** replace or add `src/assets/covers/<slug>.jpg`, where the slug is the lowercased, hyphenated title (`the-wax-child.jpg`). Downloaded covers are never overwritten; delete one to fetch it again.

Fetched data lives in `src/data/meta.json`; don't edit it by hand.

## Development

```sh
npm run dev       # local server at http://localhost:4321/booklog/
npm run build     # production build in dist/
npm run preview   # serve the build
npm run lint      # ESLint + Prettier check
npm run format    # fix formatting and lint issues
npm run check     # type check
.venv/bin/ruff check scripts && .venv/bin/ruff format scripts
```

Pushing to `main` lints, type-checks, builds, and deploys via GitHub Actions.

See [DESIGN.md](DESIGN.md) for colors, type, and components.
