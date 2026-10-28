"""
Purpose: Build the clinical skills course prototype in the portal's own structure: a course
         page of block cards (index.html), one block page per section (history.html,
         exam.html, pocus.html, osce.html), and a copy of the portal landing with the
         clinical skills card beside the four courses (landing.html).
Author: Noor Simsam
Date: 2026-10-28
Input: SECTIONS and SKILLS below (from the 2025-26 and 2026-27 clinical skills syllabi);
       portal_theme.html and portal_theme_btn.html, copied from the portal's pom2/index.html
Output: the five pages above, styled by the live portal's base.css and portal.css
"""

import html
import logging
from pathlib import Path

LOG = logging.getLogger("clinical_skills")
HERE = Path(__file__).resolve().parent
PORTAL = "https://schulichmed.github.io/preclerkship/"
COURSES = {"fom": "FoM", "pom1": "PoM 1", "pom2": "PoM 2", "t2c": "T2C"}

# (slug, name, when, hue, what): the hues are the PoM 2 block hues, so the cards sit in the family
SECTIONS = [
    ("history", "History taking", "FoM to T2C", "#8c3566",
     "The interview every history is built on, then the special histories: obstetric, psychiatric, paediatric and geriatric."),
    ("exam", "Physical exam", "FoM to T2C", "#2f5d7c",
     "One page per system, from vital signs to the pelvic exam: each region's look, feel and move, its special tests, and a test-yourself mode."),
    ("pocus", "Ultrasound", "PoM 1 and T2C", "#0d6154",
     "Point-of-care views of the heart and the abdomen."),
    ("osce", "OSCE prep", "Every TOSCE and the OSCE", "#4b3f96",
     "How a station runs, what is marked, and putting a whole encounter together."),
]

# (section, name, courses in teaching order, page once built)
SKILLS = [
    ("history", "The patient-centred interview", ["fom", "pom1"], None),
    ("history", "Cultural humility", ["pom1"], None),
    ("history", "Presenting a case", ["fom", "t2c"], None),
    ("history", "Obstetric and gynecologic history", ["pom2"], None),
    ("history", "Psychiatric interview", ["pom2"], None),
    ("history", "Paediatric history", ["t2c"], None),
    ("history", "Geriatric assessment", ["t2c"], None),
    ("exam", "Vital signs", ["fom"], None),
    ("exam", "Respiratory", ["fom", "pom1"], None),
    ("exam", "Abdominal", ["fom", "pom1"], None),
    ("exam", "Cardiovascular", ["fom", "pom1"], None),
    ("exam", "Breast", ["fom"], None),
    ("exam", "Head and neck, eye, ear", ["pom1", "t2c"], None),
    ("exam", "Neurological", ["pom1", "pom2"], None),
    ("exam", "Musculoskeletal", ["pom1", "pom2"], "../msk-exam/"),
    ("exam", "Male genital and rectal", ["t2c"], None),
    ("exam", "Pelvic", ["t2c"], None),
    ("pocus", "Heart and abdomen", ["pom1", "t2c"], None),
    ("osce", "How a station runs", ["fom", "t2c"], None),
    ("osce", "Putting it together", ["t2c"], None),
]

THEME = (HERE / "portal_theme.html").read_text(encoding="utf-8")
THEME_BTN = (HERE / "portal_theme_btn.html").read_text(encoding="utf-8")

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive">
<meta name="theme-color" content="#ffffff">
<title>{title}</title>
{theme}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{portal}base.css">
<link rel="stylesheet" href="{portal}portal.css">
<style>
/* prototype only: an exam that has no page yet is listed but dimmed */
.deck-lecs .todo .lc-n{{color:var(--muted);}}
.deck-lecs a.lc-n{{font-weight:600;}}
</style>
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<div class="pom2-page">
"""

FOOT = """
<footer>
<p><strong>Unofficial and student-run.</strong> For any inquiries, email <a href="mailto:schulichmedfriend@gmail.com">schulichmedfriend@gmail.com</a>.</p>
</footer>
</div>
</body>
</html>
"""


def esc(text: str) -> str:
    """Escape text for HTML."""
    return html.escape(text, quote=True)


def head(title: str) -> str:
    """Return the page head and the opening of the portal's page wrapper."""
    return HEAD.format(title=esc(title), theme=THEME, portal=PORTAL)


def tally(slug: str) -> tuple[int, int]:
    """Return (topics, pages built) for one section."""
    rows = [s for s in SKILLS if s[0] == slug]
    return len(rows), sum(1 for s in rows if s[3])


def noun(slug: str, n: int) -> str:
    """Return 'exams' for the physical exam section, else 'topic(s)'."""
    return "exams" if slug == "exam" else ("topic" if n == 1 else "topics")


def block_card(slug: str, name: str, when: str, hue: str, what: str, number: int) -> str:
    """Return one section as a portal block card."""
    total, built = tally(slug)
    return f"""<a class="block-card" href="{slug}.html" style="--hue:{hue}">
<p class="bmeta">Section {number} &middot; {esc(when)}</p>
<h2>{esc(name)}</h2>
<p>{esc(what)}</p>
<span class="tally">
<span><b>{total}</b> {noun(slug, total)}</span>
<span><b>{built}</b> ready</span>
</span>
</a>"""


def course_page() -> str:
    """Return the course page: hero and the four section cards, as pom2/index.html."""
    cards = "\n".join(block_card(*s, number=i) for i, s in enumerate(SECTIONS, 1))
    return head("Clinical skills") + f"""
<header class="topline">
<a class="uplink" href="landing.html">&larr; All courses</a>
{THEME_BTN}
</header>

<main id="content" tabindex="-1">

<div class="page-hero compact">
<h1>Clinical skills.</h1>
<p>
Every <strong>history</strong> and <strong>exam</strong> from Years 1 and 2, one page each.
Most exams are taught twice, a basic version first and the full one later; their page holds
both, and says which course teaches each.
</p>
</div>

<div class="block-grid hub-grid">
{cards}
</div>

</main>
""" + FOOT


def blocknav(current: str) -> str:
    """Return the section bar every block page opens on, as the PoM 2 block pages."""
    links = [f'<a class="home" href="landing.html">All courses</a>']
    for i, (slug, name, *_rest) in enumerate(SECTIONS, 1):
        here = ' class="here"' if slug == current else ""
        links.append(f'<a href="{slug}.html"{here}>{i} &middot; {esc(name)}</a>')
    return '<nav class="blocknav" aria-label="Sections">\n' + "\n".join(links) + f"\n{THEME_BTN}\n</nav>"


def section_page(number: int, slug: str, name: str, when: str, hue: str, what: str) -> str:
    """Return one section's block page: masthead, scoreboard and its list of topics."""
    total, built = tally(slug)
    rows = []
    for _sec, skill, taught, page in (s for s in SKILLS if s[0] == slug):
        label = f'<a class="lc-n" href="{page}">{esc(skill)} &rarr;</a>' if page else f'<span class="lc-n">{esc(skill)}</span>'
        when_taught = " &rarr; ".join(COURSES[c] for c in taught)
        rows.append(f'<li{"" if page else " class=\"todo\""}>{label}<span class="lc-c">{when_taught}</span></li>')
    return head(f"{name} - Clinical skills") + blocknav(slug) + f"""

<header class="q-masthead" id="content" tabindex="-1">
<div>
<p class="eyebrow">Schulich Clinical Skills &middot; Section {number} &middot; {esc(when)}</p>
<h1>{esc(name)}</h1>
<p class="lead">{esc(what)}</p>
</div>
<div class="scoreboard">
<div class="score"><b><span>{built}</span><span class="of">/{total}</span></b><span>Pages ready</span></div>
</div>
</header>

<main>
<div class="deck-weeks">
<section class="deck-week">
<p class="panel-h">{esc(name)} <span class="tc">{total}</span></p>
<ul class="deck-lecs">
{chr(10).join(rows)}
</ul>
</section>
</div>
</main>
""" + FOOT


LANDING_CARDS = [
    ("fom/index.html", "#4f2683", "Year 1 &middot; 4 blocks", "Foundations of Medicine",
     "The first fifteen weeks: what a physician does, then the body from cells up, then blood, then infection and immunity."),
    ("pom1/index.html", "#6b3fb8", "Year 1 &middot; 5 blocks", "Principles of Medicine 1",
     "The second half of first year, system by system."),
    ("pom2/index.html", "#7a3fb0", "Year 2 &middot; 5 blocks", "Principles of Medicine 2",
     "The five blocks of second year, with a written note for every lecture that has one and a coverage map for the rest."),
    ("t2c/index.html", "#3a2a6e", "Year 2 &middot; 6 blocks", "Transition to Clerkship",
     "The bridge into clerkship at the end of second year."),
]


def landing_page() -> str:
    """Return the portal landing with clinical skills as a fifth card, running across all four."""
    cards = [f"""<a class="block-card" href="{PORTAL}{href}" style="--hue:{hue}">
<p class="bmeta">{meta}</p>
<h2>{name}</h2>
<p>{what}</p>
</a>""" for href, hue, meta, name, what in LANDING_CARDS]
    exams = sum(1 for s in SKILLS if s[0] == "exam")
    cards.append(f"""<a class="block-card" href="index.html" style="--hue:#2f5d7c">
<p class="bmeta">Years 1 and 2 &middot; alongside every course</p>
<h2>Clinical Skills</h2>
<p>Every history and exam, one page each, arranged by skill rather than by semester.</p>
<span class="tally">
<span><b>{exams}</b> exams</span>
<span><b>{len(SKILLS) - exams}</b> histories and other skills</span>
</span>
</a>""")
    return head("Schulich Pre-clerkship") + f"""
<main id="content" tabindex="-1">

<div class="page-hero">
<h1>Schulich Pre-clerkship.</h1>
<p>
A centralized, dynamic, up-to-date resource for all Schulich med students in
pre-clerkship.
</p>
</div>

<div class="block-grid hub-grid">
{chr(10).join(cards)}
</div>

</main>
""" + FOOT


def main() -> None:
    """Write the course page, the section pages and the landing preview."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    pages = {"index.html": course_page(), "landing.html": landing_page()}
    for i, section in enumerate(SECTIONS, 1):
        pages[f"{section[0]}.html"] = section_page(i, *section)
    for name, text in pages.items():
        (HERE / name).write_text(text, encoding="utf-8")
        LOG.info("wrote %s", name)


if __name__ == "__main__":
    main()
