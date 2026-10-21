"""
Purpose: Build the anatomy tables page: the cranial nerve table and the muscle tables (back to
         foot), each as a grid in lecture order with a Test mode that hides a column until tapped.
Author: nsimsam (with Claude Code)
Date: 2026-10-19
Input: anatomy-tables/vault_tables.json, the "summary table" sections of the nine medwiki anatomy
       notes (Andy's CNs.xlsx and MSK-muscles.xlsx, already tidied in the vault), snapshotted.
       FIXES below corrects the rows that disagree with the notes' own lecture content.
       anatomy-tables/plexus.html, the interactive brachial plexus tab (from the lecture slides and
       the vault's "Anatomy of the Brachial Plexus" note), dropped in after the back.
       anatomy-tables/cnmap.html, the drawn cranial nerve map (brain, opening, target), dropped in after
       the cranial nerve table, with that table's corrected rows filled in for its panel.
Output: anatomy-tables/index.html

Usage: python3 anatomy-tables/build.py
"""
import html
import json
import logging
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# Muscle tables in lecture order: (note file stem prefix, tab label, region heading)
REGIONS = [
    ("02.1 - Anatomy of the Back", "Back", "Back and neck"),
    ("02.1 - Anatomy of the Muscles of the Shoulder", "Shoulder", "Pectoral region and shoulder"),
    ("03.1 - Anatomy of the Muscles of the Arm", "Arm", "Arm"),
    ("06.1 - Anatomy of the Muscles of the Distal", "Forearm", "Forearm"),
    ("08.1 - Anatomy of the Wrist and Hand", "Hand", "Hand"),
    ("04 - Anatomy of the Gluteal", "Hip & thigh", "Gluteal region and thigh"),
    ("08 - Anatomy of the Leg", "Leg", "Leg"),
    ("01.1 - Anatomy of the Ankle and Foot", "Foot", "Foot"),
]

# (row key, column index, old text, new text): corrections to the vault rows.
FIXES = [
    # Cranial nerves only carry sympathetic fibres; the same note says so in its opening.
    ("VII", 4, "<br>Sympathetic (SNS): lacrimal/nasal/palatine glands", ""),
    ("VII", 4, "PNS: lacrimal", "Parasympathetic: lacrimal"),
    ("VII", 6, "(vs. optic nerve lesion that causes ptosis)",
     "(vs. an oculomotor nerve (CN III) lesion, which causes ptosis)"),
    ("VII", 6, "middle cavity", "middle ear"),
    ("VII", 2, "runs together", "runs with CN VIII"),
    ("VIII", 2, "runs together", "runs with CN VII"),
    ("IX", 2, "<br>- CN XI originates from superior 5-6 cervical segments → enter cranial cavity via foramen magnum", ""),
    ("X", 2, "<br>- CN XI originates from superior 5-6 cervical segments → enter cranial cavity via foramen magnum", ""),
    ("XI", 2, "Lateral medulla<br>- CN XI originates from superior 5-6 cervical segments → enter cranial cavity via foramen magnum",
     "Upper 5-6 cervical segments → enters the cranial cavity through the foramen magnum"),
    ("IX", 4, "PNS: parotid", "Parasympathetic: parotid"),
    ("X", 4, "PNS: thoracic", "Parasympathetic: thoracic"),
    ("IX", 6, "PNS dysfunction", "parasympathetic dysfunction"),
    ("X", 6, "PNS dysfunction", "parasympathetic dysfunction"),
    # A relative afferent pupillary defect is an optic nerve sign (optic neuritis), in front of the chiasm.
    ("II", 5, "- Improper response → lesion posterior to optic chiasm (e.g. in optic tract)",
     "- Abnormal: both pupils dilate when the light swings to the affected eye → lesion of that optic nerve, in front of the chiasm (e.g. optic neuritis)"),
    ("Anconeus", 0, "Posterior - Random", "Posterior - other"),
    ("Abductor pollicis longus", 0, "Posterior - Deep (Outcropping)", "Posterior - deep (thumb outcropping)"),
]

# Phrases that tell a cranial nerve apart from its neighbours: the only bold in that grid.
CN_BOLD = [
    "NOT the superior oblique and lateral rectus", "sole innervation", "does NOT exit cranium",
    "spares entire forehead", "entire ipsilateral face", "towards weak side",
    "Never a cortical problem", "superior orbital fissure", "foramen rotundum", "foramen ovale",
    "Jugular foramen", "Hypoglossal canal", "Optic canal",
]

# An action's "primary" claim tells the muscle from its group; bolded on first appearance only,
# since a merged spreadsheet cell copied it onto every muscle in the group.
PRIMARY = ["primary hip flexor", "primary hip abductor", "primary hip lateral rotator",
           "primary forearm flexor", "primary elbow extensor", "primary knee flexors", "first 15°"]

WIKILINK = re.compile(r"\[\[(?:[^\]|\\]+)\\?\|([^\]]+)\]\]|\[\[([^\]]+)\]\]")


def clean(text: str) -> str:
    """Strip vault markup (wikilinks, highlights, bold stars, escapes) to plain text.

    Parameters
    ----------
    text : str
        A table cell as written in the vault.

    Returns
    -------
    str
        The cell as plain text, `<br>` line breaks kept.
    """
    text = WIKILINK.sub(lambda m: m.group(1) or m.group(2), text)
    text = text.replace("==", "").replace("**", "").replace("\\*", "*").replace("\\|", "|")
    return text.strip()


def cell_html(text: str, bold: list[str] | None = None) -> str:
    """Render a cleaned cell: `<br>` lines become lines, `- ` lines become indented sub-points.

    Parameters
    ----------
    text : str
        Cleaned cell text.
    bold : list of str, optional
        Phrases to wrap in <b>, matched case-insensitively.

    Returns
    -------
    str
        Safe HTML for the cell.
    """
    out = []
    for line in text.split("<br>"):
        line = line.strip()
        if not line:
            continue
        is_sub = line.startswith("- ")
        body = html.escape(line[2:] if is_sub else line)
        for phrase in bold or []:
            body = re.sub(re.escape(html.escape(phrase)), lambda m: f"<b>{m.group(0)}</b>", body, flags=re.I)
        out.append(f'<span class="{"sub" if is_sub else "ln"}">{body}</span>')
    return "".join(out)


def apply_fixes(rows: list[list[str]], key_col: int) -> None:
    """Apply FIXES in place to rows whose key column matches; fail loudly on a stale fix."""
    for key, col, old, new in FIXES:
        for row in rows:
            if clean(row[key_col]) == key:
                if old not in row[col]:
                    raise ValueError(f"fix for {key} col {col} no longer matches: {old!r}")
                row[col] = row[col].replace(old, new)


def build_cn_map(table: dict) -> str:
    """The cranial nerve map tab, with the corrected table rows it shows when a nerve is clicked."""
    rows = [list(r) for r in table["rows"]]
    apply_fixes(rows, 0)
    data = json.dumps([[clean(c) for c in r] for r in rows], ensure_ascii=False).replace("</", "<\\/")
    return (HERE / "cnmap.html").read_text(encoding="utf-8").replace("/*CN_ROWS*/[]", data)


def build_cn(table: dict) -> str:
    """Render the cranial nerve grid."""
    rows = [list(r) for r in table["rows"]]
    apply_fixes(rows, 0)
    head = ["Nerve", "Origin", "Exits via", "Fibres and function", "Test", "Clinical notes"]
    hideable = {2: "exit", 3: "fn", 4: "test"}
    th = "".join(f"<th>{h}</th>" for h in head)
    body = []
    for r in rows:
        r = [clean(c) for c in r]
        tds = [f'<th scope="row"><span class="cn">{html.escape(r[0])}</span>{html.escape(r[1])}</th>']
        for i, c in enumerate(r[2:], start=1):
            content = cell_html(c, CN_BOLD) if c else '<span class="na">—</span>'
            tag = f' data-col="{hideable[i]}"' if i in hideable and c else ""
            tds.append(f"<td{tag}>{content}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return (f'<div class="scroll"><table class="grid cn-grid"><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def split_notes(cell: str) -> list[str]:
    """Split a muscle's clinical cell into separate notes, dropping 'As for X (above)' pointers."""
    notes = []
    for part in re.split(r" · ", cell):
        part = part.strip()
        if not part or re.match(r"As for .*\((above|see [^)]*)\)$", part):
            continue
        # A line that is not a sub-point starts a new note.
        current = []
        for line in part.split("<br>"):
            if current and not line.strip().startswith("- "):
                notes.append("<br>".join(current))
                current = []
            current.append(line)
        if current:
            notes.append("<br>".join(current))
    return notes


# Where each clinical note belongs. The spreadsheet's merged cells left a note on whichever row
# the merge began at (tennis elbow and de Quervain's on anconeus), so every note is placed by
# hand: (region, start of the note, target). A target is a muscle row, "@<group>" for a note about
# the whole group (shown in the merged group cell), REGION for a space, landmark or nerve injury
# (a box under the table), JOIN_NEXT for a bare heading that titles the next note, or PREV for a
# fragment the vault split off the note before it.
PLACES = [
    ("Shoulder", "Lesion → winged scapula", "Serratus anterior"),
    ("Shoulder", "Impingement", "Supraspinatus"),
    ("Arm", "Tendinopathy", "Biceps brachii"),
    ("Arm", "Long head: more lateral", "Biceps brachii"),
    ("Arm", "Short head", "Biceps brachii"),
    ("Arm", "Long head: between", "Triceps"),
    ("Arm", "Lateral head", "Triceps"),
    ("Arm", "Medial head", "Triceps"),
    ("Forearm", "Medial epicondylitis", "@Anterior - Superficial"),
    ("Forearm", "Continues as lumbricals", "Flexor digitorum profundus"),
    ("Forearm", "Lateral epicondylitis", "@Posterior - Superficial"),
    ("Forearm", "Synovial cyst", "REGION"),
    ("Forearm", "de Quervain", "Abductor pollicis longus"),
    ("Forearm", "Snuff box", "REGION"),
    ("Forearm", "Mallet finger", "Extensor digitorum"),
    ("Hand", "Proximal median nerve", "REGION"),
    ("Hand", "Distal median nerve", "REGION"),
    ("Hand", "Proximal ulnar nerve", "REGION"),
    ("Hand", "Distal ulnar nerve lesion", "JOIN_NEXT"),
    ("Hand", "Ulnar canal syndrome", "REGION"),
    ("Hand", "Good test of recurrent", "Opponens pollicis"),
    ("Hand", "Extends off flexor", "Lumbricals"),
    ("Hand", "Test by tugging at paper squeezed between digits 1/2", "Adductor pollicis"),
    ("Hand", "Palmar interossei", "Interossei"),
    ("Hand", "Dorsal interossei", "Interossei"),
    ("Hip & thigh", "Hip extension: myotome L5", "Gluteus maximus"),
    ("Hip & thigh", "Hip fracture", "REGION"),
    ("Hip & thigh", "Lesion → trendelenburg", "Gluteus medius/minimus"),
    ("Hip & thigh", "Forms posterior wall", "Piriformis"),
    ("Hip & thigh", "Piriformis syndrome", "Piriformis"),
    ("Hip & thigh", "Intragluteal injections", "REGION"),
    ("Hip & thigh", "Important landmark", "Piriformis"),
    ("Hip & thigh", "Exit pelvis via greater", "Piriformis"),
    # Obturator internus is the muscle that leaves through the lesser sciatic foramen.
    ("Hip & thigh", "Exit pelvis via lesser", "Obturator internus"),
    ("Hip & thigh", "Femoral triangle", "REGION"),
    ("Hip & thigh", "Hip flexion: myotome L2", "Iliopsoas"),
    ("Hip & thigh", "Pes anserinus", "Sartorius"),
    ("Hip & thigh", "Knee extension: myotome", "@Anterior - Quadriceps femoris"),
    ("Hip & thigh", "Hamstring strains", "@Posterior - Hamstrings"),
    ("Hip & thigh", "Avulsion fracture of common hamstring", "@Posterior - Hamstrings"),
    ("Hip & thigh", "Popliteal fossa", "REGION"),
    ("Hip & thigh", "Hip extension/knee flexion", "@Posterior - Hamstrings"),
    ("Hip & thigh", "All originate from ischial", "@Posterior - Hamstrings"),
    ("Hip & thigh", "Semitendinosus inserts", "@Posterior - Hamstrings"),
    ("Hip & thigh", "Groin pull", "@Medial"),
    ("Hip & thigh", "Anterior superior iliac spine", "Sartorius"),
    ("Hip & thigh", "Adductor canal", "REGION"),
    ("Hip & thigh", "Adductor hiatus", "Adductor magnus"),
    ("Hip & thigh", "Straddled by", "Adductor brevis"),
    ("Hip & thigh", "Disposable", "Gracilis"),
    ("Leg", "Shin splint", "Tibialis anterior"),
    ("Leg", "Common peroneal nerve injury", "REGION"),
    ("Leg", "Deep peroneal nerve sensory", "@Anterior"),
    ("Leg", "Dorsalis pedis", "REGION"),
    ("Leg", "Not always present", "Fibularis tertius"),
    ("Leg", "Superficial peroneal nerve sensory", "@Lateral"),
    ("Leg", "Insertion into posterior calcaneus", "@Posterior - Superficial"),
    ("Leg", "non-surgical repair", "PREV"),
    ("Leg", "Standing calf raise", "Gastrocnemius"),
    ("Leg", "Seated calf raise", "Soleus"),
    ("Leg", "Tarsal tunnel", "REGION"),
    ("Leg", "Pes planus", "Tibialis posterior"),
    ("Foot", "Tendon passes under sustentaculum", "Flexor hallucis longus tendon"),
    ("Foot", "Plantar fasciitis", "Plantar fascia"),
]


def note_html(note: str, title: str = "") -> str:
    """Render one note: its own subject ("Snuff box: ...") in bold, then the rest."""
    first, _, rest = note.partition("<br>")
    head, sep, tail = first.partition(": ")
    is_bare_heading = not sep and rest and all(ln.startswith("- ") for ln in rest.split("<br>"))
    if title:
        head, tail, rest = title, first, rest
    elif is_bare_heading:
        # "Proximal median nerve lesions" over its "- " sub-points is a heading by itself.
        return f'<div class="note"><b class="nh">{html.escape(first)}</b>{cell_html(rest)}</div>'
    elif not (sep and len(head) <= 60):
        return f'<div class="note">{cell_html(note)}</div>'
    body = cell_html(tail + (f"<br>{rest}" if rest else ""))
    return f'<div class="note"><b class="nh">{html.escape(head)}</b>{body}</div>'


def place_notes(region: str, notes: list[str]) -> list[tuple[str, str]]:
    """Pair each note with its PLACES target, failing on a note with no place or a stale place."""
    places = [(start, target) for reg, start, target in PLACES if reg == region]
    used, placed, title = set(), [], ""
    for n in notes:
        hit = next(((s, tg) for s, tg in places if n.lower().startswith(s.lower())), None)
        if hit is None:
            raise ValueError(f"{region}: no place for note {n[:60]!r}")
        used.add(hit[0])
        target = hit[1]
        if target == "JOIN_NEXT":
            title = n
            continue
        if target == "PREV":
            prev_target, prev_html = placed[-1]
            placed[-1] = (prev_target, prev_html.removesuffix("</div>") + f"{cell_html(n)}</div>")
            continue
        placed.append((target, note_html(n, title) if title else note_html(n)))
        title = ""
    stale = {s for s, _ in places} - used
    if stale:
        raise ValueError(f"{region}: places matched no note: {sorted(stale)}")
    return placed


def build_region(table: dict, region: str, seen_notes: set[str]) -> str:
    """Render one region's muscle grid with each clinical note on the row it is about.

    A nerve is bolded where it breaks its group's majority nerve (flexor carpi ulnaris among
    the median-supplied flexors): that is what the grid exists to tell apart. Each group opens
    with a band row carrying the notes about the whole group; spaces, landmarks and nerve
    injuries go in boxes under the table.
    """
    rows = [list(r) for r in table["rows"]]
    apply_fixes(rows, 1)
    if region == "Foot":
        # The long flexors are leg muscles, already on the Leg table: drop flexor digitorum
        # longus, and keep flexor hallucis longus only for its tendon's clinical note.
        rows = [r for r in rows if clean(r[1]) != "Flexor digitorum longus"]
        for r in rows:
            if clean(r[1]) == "Flexor hallucis longus":
                r[1:4] = ["Flexor hallucis longus tendon", "Muscle sits in the posterior leg (see Leg)", ""]
    group = ""
    groups = []
    for r in rows:
        group = clean(r[0]) or group
        groups.append(group)
    majority = {}
    for g in set(groups):
        nerves = Counter(clean(r[3]) for r, gg in zip(rows, groups) if gg == g and clean(r[3]))
        top = nerves.most_common(2)
        # A group needs three supplied muscles before one can "break its rule".
        if top and sum(nerves.values()) >= 3 and (len(top) == 1 or top[0][1] > top[1][1]):
            majority[g] = top[0][0]
    raw_notes = []
    for r in rows:
        for n in split_notes(clean(r[4])):
            key = re.sub(r"\W+", "", re.sub(r"\(\w+\)", "", n.lower()))[:40]
            if key not in seen_notes:
                seen_notes.add(key)
                raw_notes.append(n)
    placed = place_notes(region, raw_notes)
    muscles = {clean(r[1]) for r in rows}
    for target, _ in placed:
        if target not in muscles and target != "REGION" and target[1:] not in groups:
            raise ValueError(f"{region}: note target {target!r} is not a row or group here")
    by_target: dict[str, list[str]] = {}
    for target, h in placed:
        by_target.setdefault(target, []).append(h)
    body = []
    bolded: set[str] = set()
    for i, (r, g) in enumerate(zip(rows, groups)):
        muscle, action, nerve = (clean(c) for c in r[1:4])
        if i == 0 or groups[i - 1] != g:
            group_notes = "".join(by_target.get(f"@{g}", []))
            notes_div = f'<div class="gnotes">{group_notes}</div>' if group_notes else ""
            body.append(f'<tr class="band"><td colspan="4"><span class="gname">{html.escape(g)}</span>'
                        f"{notes_div}</td></tr>")
        bold_nerve = nerve and g in majority and nerve != majority[g]
        nerve_html = cell_html(nerve) if nerve else '<span class="na">—</span>'
        if bold_nerve:
            nerve_html = f"<b>{nerve_html}</b>"
        primary = [ph for ph in PRIMARY if ph.lower() in action.lower() and ph not in bolded]
        bolded.update(primary)
        action_html = cell_html(action, primary)
        notes_html = "".join(by_target.get(muscle, []))
        body.append(
            f"<tr><th scope=\"row\">{html.escape(muscle)}</th>"
            f'<td data-col="act">{action_html}</td><td data-col="nerve">{nerve_html}</td>'
            f'<td class="ncol">{notes_html}</td></tr>')
    th = "<th>Muscle</th><th>Action</th><th>Nerve</th><th>Clinical notes</th>"
    grid = (f'<div class="scroll"><table class="grid mu-grid"><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')
    boxes = "".join(f'<div class="box">{h}</div>' for h in by_target.get("REGION", []))
    return grid + (f'<h3 class="clin">Spaces, landmarks and nerve injuries</h3><div class="boxes">{boxes}</div>'
                   if boxes else "")


KINDS = {"cn": "cn", "cn-map": "bp", "plexus": "bp", "dermatomes": "derm", "dermatome-levels": "derm"}
DERMATOMES = ('<iframe class="derm-frame" data-src="../dermatomes/?embed=1" title="Dermatome map in 3D" '
              'loading="lazy" allow="autoplay; fullscreen; xr-spatial-tracking"></iframe>'
              '<p class="help">Also on its own page: <a href="../dermatomes/">dermatome map in 3D</a>.</p>')
# The body map's painted dermatomes (skin cut by level from the skeleton under it, labelled, with a quiz)
SKIN_DERMATOMES = ('<iframe class="skin-frame" data-src="../body-map/?view=derm&embed=1" title="Dermatomes on the body" '
                   'loading="lazy"></iframe>'
                   '<p class="help">Also on its own page: <a href="../body-map/?view=derm">dermatomes on the body</a>.</p>')


def main() -> None:
    """Build anatomy-tables/index.html from the snapshot."""
    tables = json.loads((HERE / "vault_tables.json").read_text(encoding="utf-8"))
    by_stem = {Path(t["note"]).stem: t for t in tables}
    cn = next(t for s, t in by_stem.items() if s.startswith("05 - Cranial Nerve"))
    sections = [("cn", "Cranial nerves", "Cranial nerves I to XII", build_cn(cn)),
                ("cn-map", "Cranial nerve map", "Cranial nerve map", build_cn_map(cn))]
    seen: set[str] = set()
    for prefix, tab, heading in REGIONS:
        table = next(t for s, t in by_stem.items() if s.startswith(prefix))
        sections.append((re.sub(r"\W+", "-", tab.lower()), tab, heading, build_region(table, tab, seen)))
        log.info("%s: %d rows", tab, len(table["rows"]))
        if tab == "Back":
            # Dermatomes are taught in the back and neck lecture; the 3D page is framed, not merged,
            # since it brings its own three.js scene and styles. It loads when the tab opens.
            sections.append(("dermatomes", "Dermatomes", "Dermatomes", DERMATOMES))
            sections.append(("dermatome-levels", "Dermatome levels", "Dermatomes on the body", SKIN_DERMATOMES))
            # The brachial plexus lecture opens Week 8, between the back and the shoulder.
            plexus = (HERE / "plexus.html").read_text(encoding="utf-8")
            sections.append(("plexus", "Brachial plexus", "Brachial plexus", plexus))
    template = (HERE / "template.html").read_text(encoding="utf-8")
    tabs = "".join(
        f'<button role="tab" data-sec="{sid}" aria-selected="{"true" if i == 0 else "false"}">{html.escape(tab)}</button>'
        for i, (sid, tab, _, _) in enumerate(sections))
    secs = "".join(
        f'<section id="{sid}" data-kind="{KINDS.get(sid, "mu")}"{"" if i == 0 else " hidden"}>'
        f"<h2>{html.escape(heading)}</h2>{body}</section>"
        for i, (sid, _, heading, body) in enumerate(sections))
    out = template.replace("{{TABS}}", tabs).replace("{{SECTIONS}}", secs)
    (HERE / "index.html").write_text(out, encoding="utf-8")
    log.info("wrote %s", HERE / "index.html")


if __name__ == "__main__":
    main()
