"""
Purpose: Take the upper limb muscle tables of Netter's Atlas of Human Anatomy (Tables 6-1 to 6-4) and keep
         what the brachial plexus pages need: which muscles each plexus nerve supplies, exactly, and each
         muscle's blood supply. Only muscles in our anatomy tables, nerves in our plexus and arteries named
         in our MSK lecture notes are kept.
Author: nsimsam, with Claude Code
Date: 2026-10-21
Input: the Netter atlas PDF (pages 512-515 of the file, the upper limb muscle tables)
Output: anatomy-tables/netter_upper_limb.json
        {"muscles": {our muscle name: {"blood": [...]}}, "nerves": {plexus id: [[muscle, branch, blood, note], ...]}}
Usage: python netter_tables.py "<path to Netter Anatomy.pdf>"   (needs pymupdf)
"""

import json
import logging
import re
import sys
from pathlib import Path

import pymupdf

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent
PAGES = range(511, 515)  # 0-based: the upper limb muscle tables

# Netter's muscle name -> our anatomy table's name (muscles not listed here are not in our curriculum)
OURS = {
    "Abductor digiti minimi": "Abductor digiti minimi", "Abductor pollicis brevis": "Abductor pollicis brevis",
    "Abductor pollicis longus": "Abductor pollicis longus", "Adductor pollicis": "Adductor pollicis", "Anconeus": "Anconeus",
    "Biceps brachii": "Biceps brachii", "Brachialis": "Brachialis", "Brachioradialis": "Brachioradialis",
    "Coracobrachialis": "Coracobrachialis", "Deltoid": "Deltoid", "Dorsal interosseous muscles": "Interossei",
    "Palmar interosseous muscles": "Interossei", "Extensor carpi radialis brevis": "Extensor carpi radialis brevis",
    "Extensor carpi radialis longus": "Extensor carpi radialis longus", "Extensor carpi ulnaris": "Extensor carpi ulnaris",
    "Extensor digiti minimi": "Extensor digiti minimi", "Extensor digitorum": "Extensor digitorum",
    "Extensor indicis": "Extensor indicis", "Extensor pollicis brevis": "Extensor pollicis brevis",
    "Extensor pollicis longus": "Extensor pollicis longus", "Flexor carpi radialis": "Flexor carpi radialis",
    "Flexor carpi ulnaris": "Flexor carpi ulnaris", "Flexor digiti minimi brevis": "Flexor digiti minimi brevis",
    "Flexor digitorum profundus": "Flexor digitorum profundus", "Flexor digitorum superficialis": "Flexor digitorum superficialis",
    "Flexor pollicis brevis": "Flexor pollicis brevis", "Flexor pollicis longus": "Flexor pollicis longus",
    "Infraspinatus": "Infraspinatus", "Latissimus dorsi": "Latissimus dorsi", "Levator scapulae": "Levator scapulae",
    "Lumbrical, first and second": "Lumbricals", "Lumbrical, third and fourth": "Lumbricals",
    "Opponens digiti minimi": "Opponens digiti minimi", "Opponens pollicis": "Opponens pollicis", "Palmaris longus": "Palmaris longus",
    "Pectoralis major": "Pectoralis major", "Pectoralis minor": "Pectoralis minor", "Pronator quadratus": "Pronator quadratus",
    "Pronator teres": "Pronator teres", "Rhomboid major": "Rhomboids (major and minor)", "Rhomboid minor": "Rhomboids (major and minor)",
    "Serratus anterior": "Serratus anterior", "Subscapularis": "Subscapularis", "Supinator": "Supinator",
    "Supraspinatus": "Supraspinatus", "Teres major": "Teres major", "Teres minor": "Teres minor", "Trapezius": "Trapezius",
    "Triceps brachii": "Triceps",
}
# How a muscle is named in a nerve's list, where one of our rows covers two of Netter's or splits between nerves
SHOWN = {"Dorsal interosseous muscles": "Dorsal interossei", "Palmar interosseous muscles": "Palmar interossei",
         "Lumbrical, first and second": "Lumbricals 1 and 2", "Lumbrical, third and fourth": "Lumbricals 3 and 4",
         "Rhomboid major": "Rhomboid major", "Rhomboid minor": "Rhomboid minor"}

# Arteries named in our MSK lecture notes (Week 8: neurovascular supply of the proximal and distal upper extremity)
OUR_ARTERIES = re.compile(r"subclavian|axillary|thoraco-?\s?acromial|lateral thoracic|subscapular|thoracodorsal|circumflex|"
                          r"dorsal scapular|suprascapular|brachial|profunda brachii|radial|ulnar|interosseous|palmar", re.I)

# Netter's innervation wording -> plexus ids of the anatomy tables' plexus tab
NERVE_RULES = [
    (r"ulnar", "uln"), (r"median", "medn"), (r"radial", "rad"), (r"musculocutaneous", "mc"), (r"axillary", "ax"),
    (r"suprascapular", "ss"), (r"thoracodorsal", "td"), (r"dorsal scapular", "ds"), (r"long thoracic", "lt"),
    (r"medial and lateral pectoral", "lp+mp"), (r"medial pectoral", "mp"), (r"upper and lower subscapular", "us+ls"),
    (r"lower subscapular", "ls"),
]
# Nerves our own table adds to a muscle that Netter does not list: (plexus id, muscle, branch, note)
OUR_EXTRA = [
    ("uln", "Flexor pollicis brevis", "deep branch", "deep head, per our table; Netter lists the median nerve only"),
    ("lp", "Pectoralis minor", "", "per our table; Netter lists the medial pectoral nerve only"),
]


def cell_text(page, rect) -> str:
    words = [w for w in page.get_text("words") if pymupdf.Rect(w[:4]).intersect(rect).get_area() > 0.6 * pymupdf.Rect(w[:4]).get_area()]
    words.sort(key=lambda w: (round(w[1] / 3), w[0]))
    return re.sub(r"\s+", " ", " ".join(w[4] for w in words).replace("﻿", "")).replace("- ", "-").strip()


def read_rows(pdf: Path) -> list[list[str]]:
    doc, rows = pymupdf.open(pdf), []
    for i in PAGES:
        page = doc[i]
        for table in page.find_tables().tables:
            for row in table.rows:
                cells = [cell_text(page, pymupdf.Rect(c)) if c else "" for c in row.cells]
                if cells and cells[0] and cells[0] != "MUSCLE":
                    rows.append(cells)
    return rows


def our_blood(text: str) -> list[str]:
    """Netter's blood supply, cut down to the arteries our notes name."""
    text = text.replace("thoraco- acromial", "thoracoacromial").replace("thoraco-acromial", "thoracoacromial")
    text = text.replace("intercostal lateral thoracic", "lateral thoracic").replace(" OR ", ", ")
    text = re.sub(r"(\w+) and (\w+(?: \w+)?) arteries", r"\1 artery, \2 artery", text)  # "ulnar and radial arteries"
    parts = [p.strip() for p in re.split(r",| and (?=[a-z ]*arter)", text) if p.strip()]
    keep = []
    for p in parts:
        if re.search(r"intercostal|lumbar|subcostal|transverse cervical|ascending cervical|internal thoracic", p, re.I):
            continue
        if OUR_ARTERIES.search(p):
            p = re.sub(r"\barteries$", "artery", p if re.search(r"arter|arch", p) else p + " artery")
            p = re.sub(r"\bartery artery\b", "artery", p)
            keep.append(p[0].upper() + p[1:])
    return keep


def main(pdf: Path) -> None:
    rows = read_rows(pdf)
    log.info("Netter rows: %d", len(rows))
    muscles, nerves = {}, {}
    for name, _, _, innervation, _, blood, _ in rows:
        if name not in OURS:
            log.info("not in our tables, left out: %s", name)
            continue
        ours, shown, art = OURS[name], SHOWN.get(name, name), our_blood(blood)
        muscles.setdefault(ours, {"blood": []})
        muscles[ours]["blood"] += [a for a in art if a not in muscles[ours]["blood"]]
        # FDP is split by Netter: "Medial part: ulnar nerve Lateral part: median nerve"
        pieces = re.findall(r"(Medial|Lateral) part: ([^:]+?)(?= (?:Medial|Lateral) part|$)", innervation) or [("", innervation)]
        for part, text in pieces:
            left = text  # a muscle can have two nerves ("musculocutaneous nerve and radial nerve")
            for pattern, ids in NERVE_RULES:
                if re.search(pattern, left, re.I):
                    left = re.sub(pattern, "", left, flags=re.I)
                    branch = re.search(r"\(([^)C]+)\)", text)
                    label = shown + (f" ({part.lower()} part)" if part else "")
                    note = "radial nerve supplies part of it (C7), per Netter" if name == "Brachialis" and ids == "rad" else ""
                    for nid in ids.split("+"):
                        nerves.setdefault(nid, []).append([label, branch.group(1) if branch else "", art, note])
    for nid, muscle, branch, note in OUR_EXTRA:
        nerves[nid].append([muscle, branch, muscles.get(muscle, {}).get("blood", []), note])
    for nid in nerves:
        nerves[nid].sort(key=lambda m: m[0])
    out = {"source": "Netter, Atlas of Human Anatomy, Tables 6-1 to 6-4 (upper limb muscles), filtered to our curriculum",
           "muscles": muscles, "nerves": nerves}
    (HERE / "netter_upper_limb.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    log.info("netter_upper_limb.json: %d muscles, %s", len(muscles), {k: len(v) for k, v in nerves.items()})


if __name__ == "__main__":
    main(Path(sys.argv[1]))
