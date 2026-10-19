"""
Purpose: Build interactive overview charts (Look / Walk / Test) for FoM and PoM 1: one page per
         drawn overview chart whose source is a column_pathway content file, plus an index.
         Same pages as the portal's PoM 2 charts (preclerkship tools/interactive_charts.py).
Author: nsimsam (with Claude Code)
Date: 2026-10-18
Input: <preclerkship>/tools/pathways/src/*.content.json (FoM and PoM 1 charts), the portal's
       {fom,pom1}/data/notes/<block>.json for lecture names, and the vault's rendered
       "<name>.svg" for the "compare with the chart" panel.
Output: fom-pom1/<chart id>/index.html and fom-pom1/index.html in this repo; the pages share
        fom-pom1/chart.js and chart.css (copied from the portal's pom2/charts).

Usage: python3 fom-pom1/build.py [--repo ~/repos/preclerkship] [--vault /mnt/c/Users/nsims/medwiki]
"""
import argparse
import html
import json
import logging
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
# chart-id prefix -> (course dir, notes file, block name)
BLOCKS = {
    "fom-b1": ("fom", "b1", "FoM · Principles & Development"),
    "fom-b2": ("fom", "b2", "FoM · Regulation, Neoplasia & Aging"),
    "fom-b3": ("fom", "b3", "FoM · Hematology"),
    "fom-b4": ("fom", "b4", "FoM · Infection & Immunity"),
    "cardio": ("pom1", "cardio", "PoM 1 · Cardiology"),
    "resp": ("pom1", "resp", "PoM 1 · Respirology"),
    "ent": ("pom1", "ent", "PoM 1 · Ear, Nose & Throat"),
    "gi": ("pom1", "gi", "PoM 1 · Gastroenterology"),
    "gu": ("pom1", "gu", "PoM 1 · Nephrology & Urology"),
}

log = logging.getLogger("charts")


def lecture_names(repo: Path) -> dict:
    """Map lecture id -> lecture name from the portal's note data."""
    names = {}
    for prefix, (course, notes, _) in BLOCKS.items():
        data = json.loads((repo / course / "data/notes" / f"{notes}.json").read_text())
        for week in data["weeks"]:
            for lec in week["lectures"]:
                key = f"fom-{lec['id']}" if course == "fom" else lec["id"]
                names[key] = (week["n"], lec.get("num", ""), lec["name"])
    return names


def notes_embedding(vault: Path, svg_name: str) -> list:
    """Lecture notes (file stems) that embed the chart's SVG."""
    lectures = vault / "01 - Lectures"
    needle = f"![[{svg_name}"
    found = list(lectures.glob("99 - FoM/Block */Week */*.md")) + list(lectures.glob("99 - PoM 1/*/Week */*.md"))
    return sorted(p.stem for p in found if needle in p.read_text(errors="ignore"))


def page(spec: dict, title: str, covers: list, svg: str, block: str) -> str:
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
<p class="eyebrow"><a href="../">All FoM and PoM 1 charts</a> · {BLOCKS[block][2]} · prototype, not on the live site</p>
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
            parts.append(f"<h2>{BLOCKS[block][2]}</h2>")
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
<title>FoM and PoM 1 charts</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="chart.css">
</head>
<body>
<div class="wrap">
<header>
<p class="eyebrow"><a href="../">All prototypes</a> · not on the live site</p>
<h1>FoM and PoM 1 overview charts, interactive</h1>
<p class="lead">The overview chart of every clinical lecture in Foundations of Medicine and PoM 1, built the same way as the PoM 2 charts, with three ways to use it: Look (focus one column), Walk (answer the chart's questions from the top), and Test (each column starts as its name; tap to reveal the next row).</p>
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
        block = next((b for b in BLOCKS if chart_id.startswith(b + "-")), None)
        if block is None:
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
        out.write_text(page(spec, name, covers, svg, block))
        entries.append({"id": chart_id, "block": block, "week": week, "num": num, "title": name, "covers": covers})
    order = list(BLOCKS)
    entries.sort(key=lambda e: (order.index(e["block"]), e["week"], e["num"]))
    (HERE / "index.html").write_text(index(entries))
    log.info("built %d chart pages", len(entries))


if __name__ == "__main__":
    main()
