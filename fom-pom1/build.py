"""
Purpose: Build interactive note-chart pages for FoM and PoM 1: one page per block with a
         lecture picker, holding each lecture's tables and flowcharts (word for word from the
         portal's notes data) with Look / Walk / Test, plus an index.
Author: nsimsam (with Claude Code)
Date: 2026-10-18
Input: <preclerkship>/{fom,pom1}/data/notes/<block>.json
Output: fom-pom1/<course>-<block>.html and fom-pom1/index.html in this repo.

Usage: python3 fom-pom1/build.py [--repo ~/repos/preclerkship]
"""
import argparse
import html
import json
import logging
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSES = {
    "fom": ("Foundations of Medicine", {"b1": "Principles & Development", "b2": "Regulation, Neoplasia & Aging",
                                        "b3": "Hematology", "b4": "Infection & Immunity"}),
    "pom1": ("PoM 1", {"cardio": "Cardiology", "resp": "Respirology", "gi": "Gastroenterology",
                       "gu": "Nephrology & Urology", "ent": "Ear, Nose & Throat"}),
}
HEADING = re.compile(r"^\s*<h[1-6]")

log = logging.getLogger("fom-pom1")


def lecture_items(lec: dict) -> list:
    """The lecture's tables and flowcharts, each section heading kept only when one follows."""
    items, pending = [], None
    for b in lec.get("blocks", []):
        t = b.get("t")
        if t == "note" and HEADING.match(b.get("html", "")):
            pending = {"t": "head", "html": b["html"]}
        elif t == "table" and b.get("rows"):
            if pending:
                items.append(pending)
                pending = None
            items.append({k: b[k] for k in ("t", "cols", "rows", "lead") if k in b})
        elif t == "pathway" and b.get("mermaid"):
            if pending:
                items.append(pending)
                pending = None
            items.append({"t": "pathway", "mermaid": b["mermaid"]})
    return items


def page(course: str, block: str, lectures: list) -> str:
    """One block's page."""
    cname, blocks = COURSES[course]
    title = f"{blocks[block]} · {cname}"
    data = json.dumps({"course": course, "block": block, "lectures": lectures}, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive">
<meta name="referrer" content="no-referrer">
<title>{html.escape(title)}: interactive charts</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="notes-chart.css">
</head>
<body>
<div class="wrap">
<header>
<p class="eyebrow"><a href="./">All FoM and PoM 1 blocks</a> · prototype, not on the live site</p>
<h1>{html.escape(title)}</h1>
<p class="lead">Each lecture's tables and flowcharts from the notes, unchanged, with three ways to use them.</p>
</header>
<div class="top">
<button type="button" id="prev" aria-label="Previous lecture">←</button>
<select id="pick" aria-label="Lecture"></select>
<button type="button" id="next" aria-label="Next lecture">→</button>
</div>
<div class="chips modes" id="modes" role="tablist" aria-label="Mode">
<button class="chip" data-mode="look" aria-pressed="true">Look: click to focus</button>
<button class="chip" data-mode="walk" aria-pressed="false">Walk: answer the flowcharts</button>
<button class="chip" data-mode="test" aria-pressed="false">Test: tap to reveal, one at a time</button>
</div>
<p class="tipbar" id="bar"></p>
<main id="body"></main>
</div>
<script>var D = {data};</script>
<script src="notes-chart.js"></script>
</body>
</html>
"""


def index(entries: list) -> str:
    """Every block, with its count of lectures, tables and flowcharts."""
    parts = []
    for course, (cname, _) in COURSES.items():
        parts.append(f"<h2>{cname}</h2><ul class=\"list\">")
        for e in [x for x in entries if x["course"] == course]:
            parts.append(f"<li><a href=\"{e['file']}\">{html.escape(e['name'])}</a> "
                         f"<span>{e['lectures']} lectures · {e['tables']} tables · {e['walks']} flowcharts</span></li>")
        parts.append("</ul>")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>FoM and PoM 1 charts</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="notes-chart.css">
</head>
<body>
<div class="wrap">
<header>
<p class="eyebrow"><a href="../">All prototypes</a> · not on the live site</p>
<h1>FoM and PoM 1 charts, interactive</h1>
<p class="lead">Every lecture's tables and flowcharts from the Foundations of Medicine and PoM 1 notes, word for word, with three modes: Look (click a column or row to focus it), Walk (answer a flowchart's questions from the top, with the route lit), and Test (each table starts with only its labels; every tap reveals the next box, in order).</p>
</header>
{''.join(parts)}
</div>
</body>
</html>
"""


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path.home() / "repos/preclerkship")
    args = ap.parse_args()
    entries = []
    for course, (_, blocks) in COURSES.items():
        for block, name in blocks.items():
            data = json.loads((args.repo / course / "data/notes" / f"{block}.json").read_text())
            lectures = []
            for week in data["weeks"]:
                for lec in week["lectures"]:
                    items = lecture_items(lec)
                    if not any(i["t"] != "head" for i in items):
                        continue
                    lectures.append({"id": lec["id"], "num": lec.get("num", ""), "name": lec["name"],
                                     "title": lec.get("title") or lec["name"], "framing": lec.get("framing", ""),
                                     "week": week["n"], "weekLabel": week["label"], "items": items})
            if not lectures:
                log.info("%s %s: no tables or flowcharts, skipped", course, block)
                continue
            fname = f"{course}-{block}.html"
            (HERE / fname).write_text(page(course, block, lectures))
            tables = sum(1 for l in lectures for i in l["items"] if i["t"] == "table")
            walks = sum(1 for l in lectures for i in l["items"] if i["t"] == "pathway")
            entries.append({"course": course, "file": fname, "name": name, "lectures": len(lectures),
                            "tables": tables, "walks": walks})
            log.info("%s: %d lectures, %d tables, %d flowcharts", fname, len(lectures), tables, walks)
    (HERE / "index.html").write_text(index(entries))


if __name__ == "__main__":
    main()
