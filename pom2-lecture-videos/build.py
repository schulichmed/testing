"""
Purpose: Stage the PoM 2 notes with their new "Watch" video accordions as a preview, without
         copying the portal's figures, charts or Anki decks into this repo
Author: Claude Code for nhmidans@uwo.ca
Date: 2026-11-04
Input: a preclerkship clone carrying the videos work (default ~/repos/preclerkship-videos,
       branch pom2-lecture-videos): the five block pages, the shared scripts and styles,
       and pom2/data/notes/*.json with each lecture's `videos`
Output: this folder: the pages and scripts copied, the notes with their pictures, charts
        and body map pointed at the live portal, and no sync or analytics script

    python3 pom2-lecture-videos/build.py [path/to/preclerkship]
"""
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / "repos/preclerkship-videos")
LIVE = "https://schulichmed.github.io/preclerkship/pom2/"
BLOCKS = ["endo", "repro", "msk", "neuro", "psych"]
SHARED = ["base.css", "portal.css", "portal.js", "notes.js"]
# what a note or page reaches relative to pom2/ and this preview does not carry
LIVE_DIRS = ("assets/", "charts/", "body-map/", "anki/")
# the preview shares an origin with the live portal: no progress sync, analytics or online count
SCRIPT = re.compile(r"\s*<script\b[^>]*>.*?</script>", re.S)
DROP = ("sync.js", "PORTAL_SYNC_CFG", "cloudflareinsights", "preclerkship-presence")
# the bank is not staged: the note's "Practice questions" links land here and go on to the live one
QBANK = """<!doctype html><meta charset="utf-8"><title>Question bank</title>
<script>location.replace("%sqbank.html" + location.search + location.hash)</script>
""" % LIVE


def to_live(text: str) -> str:
    """Point every pom2-relative asset, chart and body-map link at the live portal."""
    for d in LIVE_DIRS:
        text = re.sub(r'(["\'(])' + re.escape(d), r"\1" + LIVE + d, text)
    return text


def main() -> None:
    for name in SHARED:
        shutil.copyfile(SRC / name, HERE / name)
    (HERE / "pom2/data/notes").mkdir(parents=True, exist_ok=True)
    for b in BLOCKS:
        page = (SRC / "pom2" / f"{b}.html").read_text(encoding="utf-8")
        page = SCRIPT.sub(lambda m: "" if any(d in m.group(0) for d in DROP) else m.group(0),
                          to_live(page))
        # icons and the manifest are the live portal's; the preview has no root of its own
        page = re.sub(r'href="\.\./(apple-touch-icon\.png|site\.webmanifest)"',
                      r'href="https://schulichmed.github.io/preclerkship/\1"', page)
        (HERE / "pom2" / f"{b}.html").write_text(page, encoding="utf-8")
        notes = (SRC / "pom2/data/notes" / f"{b}.json").read_text(encoding="utf-8")
        (HERE / "pom2/data/notes" / f"{b}.json").write_text(to_live(notes), encoding="utf-8")
    (HERE / "pom2/qbank.html").write_text(QBANK, encoding="utf-8")
    print(f"staged {len(BLOCKS)} blocks from {SRC}")


if __name__ == "__main__":
    main()
