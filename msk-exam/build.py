"""
Purpose: Build the MSK clinical skills chart page (msk-exam/index.html) from the
         special-test tables in the medwiki note "Summary Notes - MSK Clinical Skills".
Author: Noor Simsam
Date: 2026-10-26
Input: the vault note (POM2_VAULT or the default vault path); img/credits.json
Output: msk-exam/index.html

The note is the single source of the steps and positive findings: edit the note,
then rerun this script. Which problem heading each test sits under, and its
picture, are set here.
"""

import html
import json
import logging
import os
import re
import sys
from pathlib import Path

LOG = logging.getLogger("msk_exam")
HERE = Path(__file__).resolve().parent
VAULT = Path(os.environ.get("POM2_VAULT", "/mnt/c/Users/nsims/medwiki"))
NOTE = VAULT / "01 - Lectures/99 - PoM 2/03 - MSK/Summary Notes - MSK Clinical Skills.md"

# section number in the note -> region on the page
REGIONS = {
    4: ("cspine", "Cervical spine", "Week 1", "#3d6fb6"),
    5: ("lspine", "Lumbar spine", "Week 1", "#23798a"),
    6: ("shoulder", "Shoulder", "Week 2", "#7a3fb0"),
    7: ("elbow", "Elbow", "Week 2", "#a8366f"),
    8: ("wrist", "Wrist and hand", "Week 2", "#b4501f"),
    9: ("hip", "Hip", "Week 3", "#7d6413"),
    10: ("knee", "Knee", "Week 3", "#2f6b4f"),
    11: ("ankle", "Ankle and foot", "Week 3", "#4d5590"),
}

# test name as the note shows it -> (problem heading, picture in img/)
TESTS = {
    "Spurling's maneuver": ("Nerve root compression (radiculopathy)", "spurling-s-maneuver.jpg"),
    "Cervical distraction": ("Nerve root compression (radiculopathy)", None),
    "Straight leg raise (Lasègue)": ("Low lumbar root (L5/S1): disc herniation", "straight-leg-raise-lasegue.jpg"),
    "Bragard's sign": ("Low lumbar root (L5/S1): disc herniation", None),
    "Bowstring sign": ("Low lumbar root (L5/S1): disc herniation", None),
    "Crossed straight leg raise": ("Low lumbar root (L5/S1): disc herniation", None),
    "Femoral stretch test": ("Upper lumbar root (L2-L4)", "femoral-nerve-stretch-test.jpg"),
    "Modified Schober's test": ("Inflammatory back disease", "modified-schober-test.jpg"),
    "Adam's forward bend test": ("Scoliosis", None),
    "Painful arc": ("Impingement", "painful-arc-shoulder.jpg"),
    "Neer's test": ("Impingement", "neer-test.jpg"),
    "Hawkins test": ("Impingement", "hawkins-kennedy-test.jpg"),
    "Empty can test": ("Rotator cuff tendon", "empty-can-jobe-test.jpg"),
    "Resisted external rotation": ("Rotator cuff tendon", None),
    "Lift-off test": ("Rotator cuff tendon", "lift-off-gerber-test.jpg"),
    "Belly press test": ("Rotator cuff tendon", "belly-press-test.jpg"),
    "Speed's test": ("Biceps tendon", "speed-s-test.jpg"),
    "Yergason's test": ("Biceps tendon", "yergason-s-test.jpg"),
    "Apprehension test": ("Anterior instability", "shoulder-apprehension-and-relocation-test.jpg"),
    "Relocation test (Fowler's sign)": ("Anterior instability", None),
    "Scarf test (cross-arm)": ("AC joint", "scarf-cross-body-adduction-test.jpg"),
    "Valgus and varus stress": ("Collateral ligaments", "elbow-valgus-stress-test.jpg"),
    'Lateral epicondylitis ("tennis elbow")': ("Tendons at the epicondyles", None),
    'Medial epicondylitis ("golfer\'s elbow")': ("Tendons at the epicondyles", None),
    "Tinel's sign (elbow)": ("Ulnar nerve", None),
    "Tinel's sign (wrist)": ("Carpal tunnel (median nerve)", None),
    "Phalen's test": ("Carpal tunnel (median nerve)", "phalen-s-test.jpg"),
    "1st CMC grind test": ("Thumb base arthritis", "cmc-grind-test.jpg"),
    "Finkelstein's test": ("De Quervain's tenosynovitis", "finkelstein-s-test.jpg"),
    "Thomas test": ("Flexion contracture", "thomas-test.jpg"),
    "Trendelenburg sign": ("Weak hip abductors", "trendelenburg-sign.jpg"),
    "Stinchfield test": ("Inside the hip joint", "stinchfield-test.jpg"),
    "FABER test (Flexion, ABduction, External Rotation)": ("SI joint (or hip)", "faber-patrick-test.jpg"),
    "Thigh thrust": ("SI joint (or hip)", None),
    "Ober's test": ("IT band", "ober-s-test.jpg"),
    "True and apparent leg length": ("Leg length", "true-leg-length-measurement.jpg"),
    "Wipe (bulge) test": ("Effusion", None),
    "Patellar ballottement": ("Effusion", None),
    "Valgus / varus stress": ("Collateral ligaments (MCL, LCL)", None),
    "Lachman test": ("Cruciate ligaments (ACL, PCL)", "lachman-test.jpg"),
    "Anterior drawer": ("Cruciate ligaments (ACL, PCL)", None),
    "Posterior drawer": ("Cruciate ligaments (ACL, PCL)", None),
    "Posterior sag sign": ("Cruciate ligaments (ACL, PCL)", "posterior-sag-sign.jpg"),
    "McMurray's test": ("Meniscus", None),
    "Thessaly's test": ("Meniscus", "thessaly-test.jpg"),
    "Crouch compression (duck walk)": ("Meniscus", None),
    "Patellar apprehension": ("Patella", "patellar-apprehension-test.jpg"),
    "Patellar grind (Osmond-Clarke)": ("Patella", "patellar-grind-clarke-test.jpg"),
    "Anterior drawer (ankle)": ("Ligaments (sprain)", "ankle-anterior-drawer.jpg"),
    "Talar tilt": ("Ligaments (sprain)", None),
    "Passive external rotation": ("Ligaments (sprain)", None),
    "Thompson test": ("Achilles rupture", "thompson-simmonds-test.jpg"),
    "Homan's sign": ("Deep vein thrombosis", None),
    "Metatarsal squeeze": ("Morton's neuroma", None),
}

# fracture rules the note gives as prose: one card, no picture
OTTAWA = {
    "name": "Ottawa ankle and foot rules", "problem": "Fracture: X-ray or not?", "img": None,
    "for": "Who needs an <b>X-ray</b> (age 18 or over)",
    "steps": ["Press the <b>back edge and tip of each malleolus</b> (distal 6 cm of tibia and fibula)",
              "Press the <b>base of the 5th metatarsal</b> and the <b>navicular</b>",
              "Ask them to <b>walk 4 steps</b>"],
    "pos": "<b>Any bony tenderness there</b>, or <b>cannot bear weight for 4 steps</b> (right after the injury and in the emergency department) → X-ray",
}


def inline(md: str) -> str:
    """Convert the note's inline markdown (wikilinks, bold) to HTML text.

    Parameters
    ----------
    md : str
        One table cell.

    Returns
    -------
    str
        Escaped HTML with <b> for bold.
    """
    md = re.sub(r"\[\[[^\]|\\]*\\?\|([^\]]*)\]\]", r"\1", md)
    md = re.sub(r"\[\[([^\]]*)\]\]", r"\1", md)
    out = html.escape(md, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)


def plain(md: str) -> str:
    """Return a cell as plain text, for matching test names."""
    return re.sub(r"<[^>]+>", "", html.unescape(inline(md))).strip()


def read_note(path: Path) -> list[dict]:
    """Read every special-test row of the note, with its section number.

    Parameters
    ----------
    path : Path
        The summary note.

    Returns
    -------
    list of dict
        One dict per row: section, name, for, steps, pos.
    """
    rows, section = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        head = re.match(r"## (\d+)\. ", line)
        if head:
            section = int(head.group(1))
            continue
        if section not in REGIONS or not line.startswith("| ") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line)[1:-1]]
        if cells[0] == "Test" or len(cells) < 4:
            continue
        steps = [re.sub(r"^\d+\.\s*", "", s) for s in cells[2].split("<br>")]
        rows.append({"section": section, "name": plain(cells[0]), "for": inline(cells[1]),
                     "steps": [inline(s) for s in steps], "pos": inline(cells[3])})
    return rows


def build_regions(rows: list[dict]) -> list[dict]:
    """Group the note's rows into regions and, inside each, problem headings.

    Parameters
    ----------
    rows : list of dict
        Output of read_note.

    Returns
    -------
    list of dict
        Regions in note order, each with its problems in first-seen order.
    """
    missing = [r["name"] for r in rows if r["name"] not in TESTS]
    if missing:
        sys.exit(f"tests not mapped in TESTS: {missing}")
    regions = []
    for num, (key, title, week, color) in REGIONS.items():
        problems: dict[str, list] = {}
        for r in (r for r in rows if r["section"] == num):
            problem, img = TESTS[r["name"]]
            problems.setdefault(problem, []).append({**r, "img": img})
        if key == "ankle":
            problems.setdefault(OTTAWA["problem"], []).append(OTTAWA)
        regions.append({"key": key, "title": title, "week": week, "color": color,
                        "problems": [{"name": k, "tests": v} for k, v in problems.items()]})
    return regions


def card(t: dict) -> str:
    """Render one test card."""
    img = (f'<img src="img/{t["img"]}" alt="{html.escape(t["name"])}" loading="lazy">'
           if t.get("img") else "")
    steps = "".join(f"<li>{s}</li>" for s in t["steps"])
    words = " ".join([t["name"], re.sub(r"<[^>]+>", "", t["for"])]).lower()
    return (f'<article class="test" tabindex="0" data-words="{html.escape(words)}">'
            f'<h4>{html.escape(t["name"])}</h4><p class="for">{t["for"]}</p>{img}'
            f'<div class="hide h1"><span class="lbl">Steps</span><ol>{steps}</ol></div>'
            f'<div class="hide h2 pos"><span class="lbl">Positive</span><p>{t["pos"]}</p></div>'
            f'<span class="pill">Tap to reveal</span></article>')


def render(regions: list[dict], credits: list[dict]) -> str:
    """Render the whole page."""
    chips = "".join(f'<a class="rchip" href="#{r["key"]}" style="--c:{r["color"]}">'
                    f'<b>{r["title"]}</b><span>{r["week"]}</span></a>' for r in regions)
    bands = []
    for r in regions:
        probs = "".join(f'<div class="prob"><h3>{html.escape(p["name"])}</h3>'
                        f'<div class="tests">{"".join(card(t) for t in p["tests"])}</div></div>'
                        for p in r["problems"])
        n = sum(len(p["tests"]) for p in r["problems"])
        bands.append(f'<section class="band" id="{r["key"]}" style="--c:{r["color"]}">'
                     f'<header class="bandhead"><h2>{r["title"]}</h2><span>{r["week"]} · {n} tests</span></header>'
                     f'{probs}</section>')
    cred = "".join(
        f'<li>{html.escape(c["test"])}: {html.escape(c["author"])}, {html.escape(c["licence"])}, '
        f'<a href="{html.escape(c["source_page_url"])}">source</a></li>' for c in credits)
    return PAGE.replace("{{CHIPS}}", chips).replace("{{BANDS}}", "".join(bands)).replace("{{CREDITS}}", cred)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MSK special tests</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#f7f5fa;--card:#fff;--ink:#201436;--muted:#5f5670;--line:#ddd5ea;--accent:#7a3fb0;--ok:#2f6b4f;--ok-bg:#e9f4ee;--rail:#6b6380}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15111c;--card:#1f1a29;--ink:#f1ecf8;--muted:#b3a9c4;--line:#3a3149;--accent:#c39bea;--ok:#7fd1a6;--ok-bg:#16291f;--rail:#a89fbb}}
:root[data-theme="dark"]{--bg:#15111c;--card:#1f1a29;--ink:#f1ecf8;--muted:#b3a9c4;--line:#3a3149;--accent:#c39bea;--ok:#7fd1a6;--ok-bg:#16291f;--rail:#a89fbb}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 Inter,-apple-system,BlinkMacSystemFont,sans-serif}
.wrap{max-width:1240px;margin:0 auto;padding:28px 16px 80px}
h1,h2,h3{font-family:Fraunces,Georgia,serif;font-weight:600;margin:0;letter-spacing:-.01em}
h1{font-size:clamp(28px,5vw,40px);line-height:1.1}
.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:12px;font-weight:600;color:var(--accent);margin:0 0 8px}
.lead{color:var(--muted);max-width:74ch;margin:10px 0 0}
.bar{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(6px);padding:10px 0;margin-top:14px;display:flex;flex-wrap:wrap;gap:8px;align-items:center;border-bottom:1px solid var(--line)}
.mode{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:var(--card)}
.mode button{border:0;background:none;color:var(--ink);font:500 14px Inter,sans-serif;padding:7px 14px;cursor:pointer}
.mode button[aria-pressed="true"]{background:var(--accent);color:var(--card)}
.bar input{flex:1;min-width:180px;font:14px Inter,sans-serif;padding:8px 12px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink)}
.hint{font-size:13px;color:var(--muted);width:100%;margin:0}
/* the tree: root fans out to every region */
.tree{margin-top:22px}
.root{background:#201436;color:#fff;border-radius:12px;padding:12px 16px;text-align:center;max-width:760px;margin:0 auto}
.root b{font-family:Fraunces,Georgia,serif;font-size:18px;font-weight:600}
.root p{margin:4px 0 0;color:#d8cfe8;font-size:14px}
.stem{width:2px;height:18px;background:var(--rail);margin:0 auto}
.fan{display:grid;grid-template-columns:repeat(8,1fr);gap:8px;position:relative;padding-top:18px}
.fan::before{content:"";position:absolute;top:0;left:6.25%;right:6.25%;height:2px;background:var(--rail)}
.rchip{position:relative;display:block;text-align:center;text-decoration:none;color:#fff;background:var(--c);border-radius:10px;padding:8px 6px}
.rchip::before{content:"";position:absolute;top:-18px;left:50%;width:2px;height:12px;background:var(--rail)}
.rchip::after{content:"";position:absolute;top:-7px;left:calc(50% - 5px);border:5px solid transparent;border-top:6px solid var(--rail)}
.rchip b{display:block;font-size:14px}.rchip span{font-size:12px;opacity:.9}
@media (max-width:820px){.fan{grid-template-columns:repeat(4,1fr);padding-top:12px}.fan::before,.rchip::before,.rchip::after{display:none}.stem{display:none}}
a{color:var(--accent)}
@media (max-width:420px){.fan{grid-template-columns:repeat(2,1fr)}}
/* region bands */
.band{margin-top:28px;border-radius:14px;padding:10px;background:color-mix(in srgb,var(--c) 9%,transparent);scroll-margin-top:110px}
.bandhead{background:var(--c);color:#fff;border-radius:10px;padding:9px 14px;display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap}
.bandhead h2{font-size:22px}.bandhead span{font-size:13px;opacity:.9}
.prob{margin-top:12px}
.prob h3{font-size:16px;color:color-mix(in srgb,var(--c) 80%,var(--ink));margin:0 4px 6px}
.tests{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
.test{background:var(--card);border:1.5px solid color-mix(in srgb,var(--c) 45%,var(--line));border-radius:10px;padding:10px 12px;position:relative;outline-offset:2px}
.test h4{margin:0;font-size:15px}
.test .for{margin:2px 0 6px;color:var(--muted);font-size:13px}
.test img{display:block;width:100%;height:170px;object-fit:contain;background:#fff;border-radius:8px;border:1px solid var(--line);margin-bottom:6px}
.test ol{margin:2px 0 0;padding-left:20px;font-size:13.5px}.test ol li{margin:2px 0}
.lbl{display:block;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:6px}
.pos{background:var(--ok-bg);border-radius:8px;padding:2px 8px 6px;margin-top:8px}
.pos .lbl{color:var(--ok)}.pos p{margin:2px 0 0;font-size:13.5px}
.pill{display:none}
.test.gone{display:none}.prob.gone,.band.gone{display:none}
/* test mode: reveal steps, then the positive */
body.quiz .test{cursor:pointer}
body.quiz .test .hide{display:none}
body.quiz .test[data-s="1"] .h1,body.quiz .test[data-s="2"] .h1,body.quiz .test[data-s="2"] .h2{display:block}
body.quiz .test:not([data-s="2"]) .pill{display:inline-block;margin-top:8px;font-size:12px;font-weight:600;color:var(--c);border:1px solid var(--c);border-radius:999px;padding:2px 10px}
body.quiz.hideimg .test img{display:none}
.credits{margin-top:40px;font-size:12.5px;color:var(--muted)}.credits a{color:var(--accent)}
.credits ul{padding-left:18px}
:focus-visible{outline:3px solid var(--accent)}
</style></head>
<body><div class="wrap">
<p class="eyebrow">PoM 2 · MSK clinical skills</p>
<h1>MSK special tests, by region</h1>
<p class="lead">Every test from the suggested-videos list, grouped under the problem you suspect, with the steps and what counts as positive. Built from the course objectives; videos for each test are at <a href="https://mskmedicine.com">mskmedicine.com</a>. The neuro screen (dermatomes, myotomes, reflexes) is in the <a href="../body-map/">body map</a>.</p>
<div class="bar">
<div class="mode" role="group" aria-label="Mode"><button data-m="look" aria-pressed="true">Look</button><button data-m="quiz" aria-pressed="false">Test</button><button data-m="blind" aria-pressed="false">Test, no pictures</button></div>
<input type="search" id="q" placeholder="Find a test or a problem (e.g. meniscus, ulnar)">
<p class="hint" id="hint">Look: everything shown. Pick a region below to jump to it.</p>
</div>
<div class="tree">
<div class="root"><b>Every joint: Look → Feel → Move → Special tests → Neurovascular</b>
<p>Compare left with right · examine the joint above and below · watch gait for the back and legs. A test counts only when it reproduces the patient's own symptom or differs from the other side.</p></div>
<div class="stem"></div>
<nav class="fan">{{CHIPS}}</nav>
</div>
{{BANDS}}
<section class="credits"><h3>Image credits</h3><p>Images reused under their open licences (Creative Commons or public domain). Some were cropped to hide faces.</p><ul>{{CREDITS}}</ul></section>
</div>
<script>
(function(){
  var body=document.body, hint=document.getElementById('hint');
  var hints={look:'Look: everything shown. Pick a region below to jump to it.',
    quiz:'Test: say the steps, then tap the card to check them; tap again for the positive finding.',
    blind:'Test, no pictures: picture the test from its name alone, then tap to check.'};
  document.querySelectorAll('.mode button').forEach(function(b){
    b.addEventListener('click',function(){
      document.querySelectorAll('.mode button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});
      var m=b.dataset.m; body.classList.toggle('quiz',m!=='look'); body.classList.toggle('hideimg',m==='blind');
      document.querySelectorAll('.test').forEach(function(t){t.dataset.s='0'});
      hint.textContent=hints[m];
    });
  });
  function step(t){ if(!body.classList.contains('quiz'))return; t.dataset.s=String(Math.min(2,(+t.dataset.s||0)+1)); }
  document.querySelectorAll('.test').forEach(function(t){
    t.addEventListener('click',function(){step(t)});
    t.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();step(t)}});
  });
  document.getElementById('q').addEventListener('input',function(e){
    var q=e.target.value.trim().toLowerCase();
    document.querySelectorAll('.prob').forEach(function(p){
      var ph=p.querySelector('h3').textContent.toLowerCase(), any=false;
      p.querySelectorAll('.test').forEach(function(t){
        var hit=!q||ph.indexOf(q)>-1||t.dataset.words.indexOf(q)>-1; t.classList.toggle('gone',!hit); any=any||hit;});
      p.classList.toggle('gone',!any);
    });
    document.querySelectorAll('.band').forEach(function(b){b.classList.toggle('gone',!b.querySelector('.prob:not(.gone)'))});
  });
})();
</script>
</body></html>
"""


def main() -> None:
    """Build msk-exam/index.html."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    regions = build_regions(read_note(NOTE))
    credits = json.loads((HERE / "img/credits.json").read_text(encoding="utf-8"))
    used = {t["img"] for r in regions for p in r["problems"] for t in p["tests"] if t.get("img")}
    for name in used:
        if not (HERE / "img" / name).exists():
            sys.exit(f"missing picture img/{name}")
    credits = [c for c in credits if c["slug"] in used]
    (HERE / "index.html").write_text(render(regions, credits), encoding="utf-8")
    n = sum(len(p["tests"]) for r in regions for p in r["problems"])
    LOG.info("wrote %d tests in %d regions, %d pictures", n, len(regions), len(used))


if __name__ == "__main__":
    main()
