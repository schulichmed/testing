"""
Purpose: Build the anatomy tables page: the cranial nerve table and the muscle tables (back to
         foot), each as a grid in lecture order with a Test mode that hides a column until tapped.
Author: nsimsam (with Claude Code)
Date: 2026-10-19
Input: anatomy-tables/vault_tables.json, the "summary table" sections of the nine medwiki anatomy
       notes (Andy's CNs.xlsx and MSK-muscles.xlsx, already tidied in the vault), snapshotted.
       FIXES below corrects the rows that disagree with the notes' own lecture content.
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


def box_parts(muscle: str, note: str) -> tuple[str, str]:
    """Title a clinical note by its own subject ("Snuff box: ...") rather than the row it sat on."""
    first, _, rest = note.partition("<br>")
    head, sep, tail = first.partition(": ")
    if sep and len(head) <= 60:
        if head.lower().startswith("lesion"):
            head = f"{muscle} lesion{head[6:]}"
        return head, tail + (f"<br>{rest}" if rest else "")
    return muscle, note


def build_region(table: dict, region: str, seen_notes: set[str]) -> str:
    """Render one region's muscle grid, then its clinical notes as boxes below it.

    A nerve is bolded where it breaks its group's majority nerve (flexor carpi ulnaris among
    the median-supplied flexors): that is what the grid exists to tell apart.
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
    body, notes = [], []
    bolded: set[str] = set()
    for r, g in zip(rows, groups):
        muscle, action, nerve, clinical = (clean(c) for c in r[1:5])
        group_cell = f'<td class="gcol">{html.escape(clean(r[0]))}</td>'
        bold_nerve = nerve and g in majority and nerve != majority[g]
        nerve_html = cell_html(nerve) if nerve else '<span class="na">—</span>'
        if bold_nerve:
            nerve_html = f"<b>{nerve_html}</b>"
        primary = [ph for ph in PRIMARY if ph.lower() in action.lower() and ph not in bolded]
        bolded.update(primary)
        action_html = cell_html(action, primary)
        body.append(
            f"<tr>{group_cell}<th scope=\"row\">{html.escape(muscle)}</th>"
            f'<td data-col="act">{action_html}</td><td data-col="nerve">{nerve_html}</td></tr>')
        for n in split_notes(clinical):
            key = re.sub(r"\W+", "", re.sub(r"\(\w+\)", "", n.lower()))[:40]
            if key in seen_notes:
                continue
            seen_notes.add(key)
            notes.append((muscle, n))
    th = "<th>Group</th><th>Muscle</th><th>Action</th><th>Nerve</th>"
    grid = (f'<div class="scroll"><table class="grid mu-grid"><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')
    boxes = "".join(
        f'<div class="box"><p class="box-h">{html.escape(h)}</p>{cell_html(b)}</div>'
        for h, b in (box_parts(m, n) for m, n in notes))
    return grid + (f'<h3 class="clin">Clinical notes</h3><div class="boxes">{boxes}</div>' if boxes else "")


def main() -> None:
    """Build anatomy-tables/index.html from the snapshot."""
    tables = json.loads((HERE / "vault_tables.json").read_text(encoding="utf-8"))
    by_stem = {Path(t["note"]).stem: t for t in tables}
    cn = next(t for s, t in by_stem.items() if s.startswith("05 - Cranial Nerve"))
    sections = [("cn", "Cranial nerves", "Cranial nerves I to XII", build_cn(cn))]
    seen: set[str] = set()
    for prefix, tab, heading in REGIONS:
        table = next(t for s, t in by_stem.items() if s.startswith(prefix))
        sections.append((re.sub(r"\W+", "-", tab.lower()), tab, heading, build_region(table, tab, seen)))
        log.info("%s: %d rows", tab, len(table["rows"]))
    template = (HERE / "template.html").read_text(encoding="utf-8")
    tabs = "".join(
        f'<button role="tab" data-sec="{sid}" aria-selected="{"true" if i == 0 else "false"}">{html.escape(tab)}</button>'
        for i, (sid, tab, _, _) in enumerate(sections))
    secs = "".join(
        f'<section id="{sid}" data-kind="{"cn" if sid == "cn" else "mu"}"{"" if i == 0 else " hidden"}>'
        f"<h2>{html.escape(heading)}</h2>{body}</section>"
        for i, (sid, _, heading, body) in enumerate(sections))
    out = template.replace("{{TABS}}", tabs).replace("{{SECTIONS}}", secs)
    (HERE / "index.html").write_text(out, encoding="utf-8")
    log.info("wrote %s", HERE / "index.html")


if __name__ == "__main__":
    main()
