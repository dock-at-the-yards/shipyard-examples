#!/usr/bin/env python3
"""Validate docs/manifest.json and everything it references.

This is the import contract with shipyard-web: that site fetches these pages
at build time, so a manifest that points at a missing file — or a page with a
dead relative link — is a broken docs deploy waiting to happen, and it is
caught here instead.

Checks:

  1. manifest.json parses; schemaVersion is 1; category and pages are present
  2. page ids are unique and URL-safe; files are unique and inside docs/
  3. every page file exists, starts with an H1, and has content
  4. every *.md under docs/ is referenced by the manifest (no orphans)
  5. every relative link in every page resolves to a real file or directory

Uses only the standard library, so it runs anywhere python3 does.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
MANIFEST = os.path.join(DOCS, "manifest.json")

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "/")


def main() -> int:
    problems: list[str] = []

    try:
        with open(MANIFEST) as fh:
            manifest = json.load(fh)
    except Exception as exc:
        print(f"FAIL  docs/manifest.json does not parse: {exc}")
        return 1

    if manifest.get("schemaVersion") != 1:
        problems.append("manifest: schemaVersion must be 1")
    if not isinstance(manifest.get("category"), str) or not manifest["category"]:
        problems.append("manifest: category is required")

    pages = manifest.get("pages")
    if not isinstance(pages, list) or not pages:
        print("FAIL  manifest: pages must be a non-empty list")
        return 1

    seen_ids: set[str] = set()
    seen_files: set[str] = set()

    for i, page in enumerate(pages):
        where = f"pages[{i}]"
        for key in ("id", "file", "title", "summary"):
            if not isinstance(page.get(key), str) or not page[key].strip():
                problems.append(f"{where}: missing or empty '{key}'")

        page_id = page.get("id", "")
        if page_id and not ID_RE.match(page_id):
            problems.append(f"{where}: id '{page_id}' is not URL-safe (a-z, 0-9, -)")
        if page_id in seen_ids:
            problems.append(f"{where}: duplicate id '{page_id}'")
        seen_ids.add(page_id)

        rel = page.get("file", "")
        if rel:
            if os.path.basename(rel) != rel or not rel.endswith(".md"):
                problems.append(f"{where}: file '{rel}' must be a plain .md name inside docs/")
                continue
            if rel in seen_files:
                problems.append(f"{where}: duplicate file '{rel}'")
            seen_files.add(rel)

            path = os.path.join(DOCS, rel)
            if not os.path.isfile(path):
                problems.append(f"{where}: file '{rel}' does not exist under docs/")
                continue

            with open(path) as fh:
                text = fh.read()
            if not text.startswith("# "):
                problems.append(f"docs/{rel}: must start with an H1 ('# ...')")
            if len(text.strip()) < 100:
                problems.append(f"docs/{rel}: suspiciously empty ({len(text.strip())} bytes)")

    # No orphans: docs/ is the import surface, so every page must be listed.
    for entry in sorted(os.listdir(DOCS)):
        if entry.endswith(".md") and entry not in seen_files:
            problems.append(f"docs/{entry}: not referenced by manifest.json (orphan page)")

    # Every relative link must resolve, so a reader on GitHub or the docs
    # site never lands on a 404 the build could have caught.
    for page in pages:
        rel = page.get("file", "")
        path = os.path.join(DOCS, rel)
        if not os.path.isfile(path):
            continue
        base = os.path.dirname(path)
        with open(path) as fh:
            text = fh.read()
        for target in LINK_RE.findall(text):
            if target.startswith(SKIP_PREFIXES):
                continue
            resolved = os.path.normpath(os.path.join(base, target.split("#", 1)[0]))
            if not os.path.exists(resolved):
                problems.append(f"docs/{rel}: link target '{target}' does not exist")

    if problems:
        for p in problems:
            print(f"FAIL  {p}")
        print(f"\n{len(problems)} problem(s)")
        return 1

    print(f"OK    docs/manifest.json: {len(pages)} pages, all files present, all links resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
