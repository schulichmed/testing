"""
Purpose: Build an interactive page (Look / Walk / Test) for every drawn overview chart whose
         source is a column_pathway content file, plus an index page linking them.
Author: nsimsam (with Claude Code)
Date: 2026-10-18
Input: <preclerkship>/tools/pathways/src/*.content.json (endo, repro, msk), the portal's
       pom2/data/notes/<block>.json for lecture names, and the vault's rendered
       "<name>.svg" for the "compare with the chart" panel.
Output: charts/<chart id>/index.html and charts/index.html in this repo.

Usage: python3 charts/build.py [--repo ~/repos/preclerkship] [--vault /mnt/c/Users/nsims/medwiki]
"""
import argparse
import html
import json
import logging
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLOCKS = {"endo": "Endocrinology", "repro": "Reproduction", "msk": "Musculoskeletal"}

log = logging.getLogger("charts")


def lecture_names(repo: Path) -> dict:
    """Map lecture id -> lecture name from the portal's note data."""
    names = {}
    for block in BLOCKS:
        data = json.loads((repo / "pom2/data/notes" / f"{block}.json").read_text())
        for week in data["weeks"]:
            for lec in week["lectures"]:
                names[lec["id"]] = (week["n"], lec.get("num", ""), lec["name"])
    return names


def notes_embedding(vault: Path, svg_name: str) -> list:
    """Lecture notes (file stems) that embed the chart's SVG."""
    lectures = vault / "01 - Lectures/99 - PoM 2"
    needle = f"![[{svg_name}"
    return sorted(p.stem for p in lectures.glob("0[1-3]*/Week */*.md") if needle in p.read_text(errors="ignore"))


def page(spec: dict, title: str, covers: list, svg: str) -> str:
    """One chart page."""
    data = json.dumps({"spec": spec}, ensure_ascii=False).replace("</", "<\\/")
    covers_html = ""
    if len(covers) > 1:
        covers_html = "<p class=\"lead\">Covers: " + " · ".join(html.escape(c) for c in covers) + "</p>"
    compare = ""
    if svg:
        compare = ("<details class=\"orig\"><summary>Compare with the chart as it is in the notes</summary>"
                   f"<div class=\"paper\">{svg}</div></details>")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive">
<meta name="referrer" content="no-referrer">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../chart.css">
</head>
<body>
<div class="wrap">
<header>
<p class="eyebrow"><a href="../">All interactive charts</a> · prototype, not on the live site</p>
<h1>{html.escape(title)}</h1>
{covers_html}
{compare}
</header>
<section class="v" id="chart" style="margin-top:28px">
<div class="chips modes" id="modes" role="tablist" aria-label="Mode">
<button class="chip" data-mode="look" aria-pressed="true">Look: click a column to focus it</button>
<button class="chip" data-mode="walk" aria-pressed="false">Walk: answer its questions</button>
<button class="chip" data-mode="test" aria-pressed="false">Test: tap to reveal, one row at a time</button>
</div>
<div class="walkbar" id="bar"></div>
<div class="map" id="map"></div>
</section>
<footer>The content is the overview chart from the notes, unchanged; only what you can do with it is new.</footer>
</div>
<script>var D = {data};</script>
<script src="../chart.js"></script>
</body>
</html>
"""


def index(entries: list) -> str:
    """The list of every chart, by block and week."""
    parts, block, week = [], None, None
    for e in entries:
        if e["block"] != block:
            if block:
                parts.append("</ul>")
            block, week = e["block"], None
            parts.append(f"<h2>{BLOCKS[block]}</h2>")
        if e["week"] != week:
            if week is not None:
                parts.append("</ul>")
            week = e["week"]
            parts.append(f"<h3>Week {week}</h3><ul class=\"list\">")
        covers = f"<span>{html.escape(' · '.join(e['covers']))}</span>" if len(e["covers"]) > 1 else ""
        parts.append(f"<li><a href=\"{e['id']}/\">{html.escape(e['title'])}</a>{covers}</li>")
    parts.append("</ul>")
    body = "\n".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>Interactive charts</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="chart.css">
</head>
<body>
<div class="wrap">
<header>
<p class="eyebrow">Prototype · not on the live site</p>
<h1>Interactive overview charts</h1>
<p class="lead">Every overview chart from the endocrinology, reproduction and musculoskeletal notes, with three ways to use it: Look (focus one column), Walk (answer the chart's questions from the top), and Test (each column starts as its name; tap to reveal the next row).</p>
</header>
{body}
</div>
</body>
</html>
"""


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path.home() / "repos/preclerkship")
    ap.add_argument("--vault", type=Path, default=Path("/mnt/c/Users/nsims/medwiki"))
    args = ap.parse_args()
    names = lecture_names(args.repo)
    entries = []
    for src in sorted((args.repo / "tools/pathways/src").glob("*.content.json")):
        chart_id = src.name.replace(".content.json", "")
        block = chart_id.split("-")[0]
        if block not in BLOCKS:
            continue
        spec = json.loads(src.read_text())
        lec_id = re.sub(r"_\d+$", "", chart_id)
        week, num, name = names.get(lec_id, (int(re.search(r"-w(\d+)", lec_id).group(1)), "", lec_id))
        svg_name = spec["name"] + ".svg"
        svg_path = args.vault / "Attachments" / svg_name
        svg = svg_path.read_text() if svg_path.exists() else ""
        svg = re.sub(r"<\?xml[^>]*>", "", svg)
        covers = notes_embedding(args.vault, svg_name)
        if not covers:
            log.warning("%s: no note embeds %s", chart_id, svg_name)
        out = HERE / chart_id / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(page(spec, name, covers, svg))
        entries.append({"id": chart_id, "block": block, "week": week, "num": num, "title": name, "covers": covers})
    order = list(BLOCKS)
    entries.sort(key=lambda e: (order.index(e["block"]), e["week"], e["num"]))
    (HERE / "index.html").write_text(index(entries))
    log.info("built %d chart pages", len(entries))


if __name__ == "__main__":
    main()
