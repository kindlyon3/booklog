"""Apply a Book issue form to books.yaml."""

import os
import re
import sys

import booklog


def fields(body: str) -> dict[str, str]:
    parts = re.split(r"^### (.+)$", body, flags=re.MULTILINE)[1:]
    values = {label.strip(): value.strip() for label, value in zip(parts[::2], parts[1::2], strict=True)}
    return {label: "" if value == "_No response_" else value for label, value in values.items()}


def command(form: dict[str, str]) -> list[str]:
    title, rating, month = form["Title"], form.get("Rating", ""), form.get("Month finished", "")
    if form["Status"] == "Reading":
        if rating or month:
            sys.exit("Leave rating and month blank for a book being read")
        argv = ["add", title, form["Author"], form["Form"], "--reading"]
    elif any(
        b.get("status") == "reading" and booklog.slugify(b["title"]) == booklog.slugify(title)
        for b in booklog.load_books()
    ):
        argv = ["finish", title]
    else:
        argv = ["add", title, form["Author"], form["Form"]]
    if rating:
        argv.append(rating)
    if month:
        argv += ["--month", month]
    if form.get("Edition") and argv[0] == "add":
        argv += ["--edition", form["Edition"]]
    return argv


if __name__ == "__main__":
    argv = command(fields(os.environ["ISSUE_BODY"]))
    booklog.main(argv)
    verb = {"finish": "Finish", "add": "Start" if "--reading" in argv else "Add"}[argv[0]]
    with open(os.environ["MESSAGE_FILE"], "w") as f:
        f.write(f"{verb} {argv[1]}\n")
