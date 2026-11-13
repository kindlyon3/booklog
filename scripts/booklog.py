"""Manage books.yaml and fetch metadata from Open Library."""

import argparse
import io
import json
import math
import re
import statistics
import sys
import time
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent.parent
BOOKS = ROOT / "src/data/books.yaml"
META = ROOT / "src/data/meta.json"
COVERS = ROOT / "src/assets/covers"

FORMS = ("fiction", "nonfiction", "poetry", "religion")
SEARCH_URL = "https://openlibrary.org/search.json"
COVER_URL = "https://covers.openlibrary.org/b/id/{}-L.jpg?default=false"
FIELDS = "key,title,author_name,author_alternative_name,first_publish_year,edition_count,cover_i"
HONORIFICS = re.compile(r"^(saint|st\.|pope|brother|sister)\s+", re.IGNORECASE)

session = requests.Session()
session.headers["User-Agent"] = "booklog/1.0 (personal reading log)"
session.mount(
    "https://",
    HTTPAdapter(max_retries=Retry(total=5, backoff_factor=2, status_forcelist=(429, 500, 502, 503, 504))),
)

yaml = YAML()
yaml.indent(mapping=2, sequence=2, offset=0)
yaml.width = 4096


def fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", fold(text)).strip("-")


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", fold(text).replace("'", "")).split())


def authors(book: dict[str, Any]) -> list[str]:
    value = book["author"]
    return list(value) if isinstance(value, list) else [value]


def load_books() -> CommentedSeq:
    return yaml.load(BOOKS)


def save_books(books: CommentedSeq) -> None:
    out = io.StringIO()
    yaml.dump(books, out)
    spaced = re.sub(r"\n(?=- )", "\n\n", out.getvalue())
    BOOKS.write_text(re.sub(r"\n{3,}", "\n\n", spaced))


def load_meta() -> dict[str, dict[str, Any]]:
    return json.loads(META.read_text()) if META.exists() else {}


def save_meta(meta: dict[str, dict[str, Any]]) -> None:
    META.write_text(json.dumps(dict(sorted(meta.items())), indent=2, ensure_ascii=False) + "\n")


def get_json(url: str, params: dict[str, str]) -> dict[str, Any]:
    time.sleep(1)
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def search(**params: str) -> list[dict[str, Any]]:
    return get_json(SEARCH_URL, {**params, "fields": FIELDS, "limit": "10"}).get("docs", [])


def author_name(book: dict[str, Any]) -> str:
    return normalize(HONORIFICS.sub("", authors(book)[0]))


def same_person(wanted: str, candidate: str) -> bool:
    """Surname must match; first initial too when both names have one."""
    want, have = wanted.split(), normalize(candidate).split()
    if not want or want[-1] not in have:
        return False
    return len(want) == 1 or len(have) == 1 or want[0][0] == have[0][0]


def author_matches(doc: dict[str, Any], name: str) -> bool:
    names = doc.get("author_name", []) + doc.get("author_alternative_name", [])
    return any(same_person(name, n) for n in names)


def score(doc: dict[str, Any], title: str, name: str) -> float:
    title_score = SequenceMatcher(None, normalize(title), normalize(doc.get("title", ""))).ratio()
    popularity = min(math.log10(doc.get("edition_count", 0) + 1), 2) / 4
    return (1 if author_matches(doc, name) else 0) + title_score + popularity


def find(book: dict[str, Any]) -> tuple[dict[str, Any] | None, bool]:
    if olid := book.get("olid"):
        docs = search(q=f"key:/works/{olid}")
        return (docs[0], True) if docs else (None, False)
    title = book["title"].split(":")[0]
    name = author_name(book)
    by_author = search(q=f"{normalize(title)} {name}") or search(q=f"{normalize(title)} {name.split()[-1]}")
    docs = by_author + search(title=title)
    if not docs:
        return None, False
    best = max(docs, key=lambda d: score(d, title, name))
    return best, author_matches(best, name)


def english_editions(work_key: str) -> list[dict[str, Any]]:
    entries = get_json(f"https://openlibrary.org{work_key}/editions.json", {"limit": "100"})["entries"]
    english = [e for e in entries if {"key": "/languages/eng"} in e.get("languages", [])]
    return english or entries


def download_cover(cover_id: int, path: Path) -> None:
    resp = session.get(COVER_URL.format(cover_id), timeout=60)
    if resp.status_code == 200:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(resp.content)


def enrich_one(book: dict[str, Any], meta: dict[str, dict[str, Any]]) -> str:
    slug = slugify(book["title"])
    doc, confident = find(book)
    if doc is None:
        meta[slug] = {}
        return f"  NOT FOUND  {book['title']}"
    entry: dict[str, Any] = {
        "olid": doc["key"].removeprefix("/works/"),
        "matched": f"{doc.get('title')} / {', '.join(doc.get('author_name', [])[:2])}",
    }
    editions = english_editions(doc["key"])
    page_counts = [e["number_of_pages"] for e in editions if e.get("number_of_pages")]
    if page_counts:
        entry["pages"] = int(statistics.median(page_counts))
    if published := doc.get("first_publish_year"):
        entry["published"] = published
    meta[slug] = entry

    cover = COVERS / f"{slug}.jpg"
    cover_ids = [c for e in editions for c in e.get("covers") or [] if c and c > 0]
    if doc.get("cover_i"):
        cover_ids.append(doc["cover_i"])
    if cover_ids and not cover.exists():
        download_cover(cover_ids[0], cover)

    flag = "ok " if confident else "CHECK"
    missing = [k for k in ("pages", "published") if k not in entry] + ([] if cover.exists() else ["cover"])
    gaps = f"  missing: {', '.join(missing)}" if missing else ""
    return f"  {flag:5} {book['title']}  ->  {entry['matched']}{gaps}"


def enrich(force: bool = False, only: str | None = None) -> None:
    books = load_books()
    slugs = {slugify(b["title"]) for b in books}
    meta = {slug: entry for slug, entry in load_meta().items() if slug in slugs}
    for book in books:
        slug = slugify(book["title"])
        if only and slug != slugify(only):
            continue
        if slug in meta and not force and not only:
            continue
        print(enrich_one(book, meta), flush=True)
        save_meta(meta)
    save_meta(meta)


def insert_finished(books: CommentedSeq, book: CommentedMap) -> None:
    later = (i for i, b in enumerate(books) if b.get("finished", "9999") <= book["finished"])
    books.insert(next(later, len(books)), book)


def add(args: argparse.Namespace) -> None:
    if args.reading and (args.rating is not None or args.month):
        sys.exit("A book being read has no rating or month yet; set them with finish")
    books = load_books()
    if any(slugify(b["title"]) == slugify(args.title) for b in books):
        sys.exit(f"{args.title!r} is already in the booklog")
    book = CommentedMap(title=args.title)
    names = [name.strip() for name in args.author.split(",")]
    if len(names) > 1:
        book["author"] = CommentedSeq(names)
        book["author"].fa.set_flow_style()
    else:
        book["author"] = names[0]
    if args.edition:
        book["edition"] = args.edition
    book["form"] = args.form
    if args.reading:
        book["status"] = "reading"
        books.insert(0, book)
    else:
        book["finished"] = args.month or date.today().strftime("%Y-%m")
        if args.rating is not None:
            book["rating"] = args.rating
        insert_finished(books, book)
    save_books(books)
    print(f"Added {args.title}")
    enrich(only=args.title)


def finish(args: argparse.Namespace) -> None:
    books = load_books()
    match = next((b for b in books if slugify(b["title"]) == slugify(args.title)), None)
    if match is None or match.get("status") != "reading":
        sys.exit(f"No book being read titled {args.title!r}")
    books.remove(match)
    del match["status"]
    match["finished"] = args.month or date.today().strftime("%Y-%m")
    if args.rating is not None:
        match["rating"] = args.rating
    insert_finished(books, match)
    save_books(books)
    print(f"Finished {args.title}")


def rating(value: str) -> float | int:
    number = float(value)
    if not (0.5 <= number <= 5 and (number * 2).is_integer()):
        raise argparse.ArgumentTypeError("rating must be 0.5-5 in half steps")
    return int(number) if number.is_integer() else number


def month(value: str) -> str:
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
        raise argparse.ArgumentTypeError("month must be YYYY-MM")
    return value


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="booklog")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a finished or in-progress book")
    p_add.add_argument("title")
    p_add.add_argument("author")
    p_add.add_argument("form", choices=FORMS)
    p_add.add_argument("rating", nargs="?", type=rating)
    p_add.add_argument("--reading", action="store_true", help="mark as currently reading")
    p_add.add_argument("--edition")
    p_add.add_argument("--month", type=month, help="YYYY-MM, defaults to this month")
    p_add.set_defaults(func=add)

    p_finish = sub.add_parser("finish", help="mark a book being read as finished")
    p_finish.add_argument("title")
    p_finish.add_argument("rating", nargs="?", type=rating)
    p_finish.add_argument("--month", type=month, help="YYYY-MM, defaults to this month")
    p_finish.set_defaults(func=finish)

    p_enrich = sub.add_parser("enrich", help="fetch metadata for books missing it")
    p_enrich.add_argument("--force", action="store_true", help="refetch every book")
    p_enrich.add_argument("--only", metavar="TITLE", help="refetch a single book")
    p_enrich.set_defaults(func=lambda a: enrich(a.force, a.only))

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
