"""
Purpose: Build the respiratory clinical skills page (resp-exam/index.html) from the
         manoeuvre tables in the medwiki note "Summary Notes - Respiratory Clinical Skills".
Author: Noor Simsam
Date: 2026-10-28
Input: the vault note (POM2_VAULT or the default vault path); img/credits.json; clips.json
       (the Health Education Media Library's respiratory exam videos, by region or card)
Output: resp-exam/index.html

The note is the single source of the steps and positive findings: edit the note,
then rerun this script. Which problem heading each manoeuvre sits under, and its
picture, are set here. How the page looks lives in clinical-skills/exam_page.py,
shared by every exam page.
"""

import importlib.util
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("exam_page", HERE.parent / "clinical-skills/exam_page.py")
exam_page = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exam_page)
VAULT = Path(os.environ.get("POM2_VAULT", "/mnt/c/Users/nsims/medwiki"))
NOTE = VAULT / "01 - Lectures/99 - Clinical Skills/Summary Notes - Respiratory Clinical Skills.md"

# section number in the note -> region on the page
REGIONS = {
    3: ("general-inspection", "General inspection", "PPES 1 · Week 2", "#3d6fb6"),
    4: ("chest-inspection", "Chest inspection", "PPES 1 · Week 2", "#23798a"),
    5: ("palpation", "Palpation", "PPES 1 · Week 2", "#7a3fb0"),
    6: ("percussion", "Percussion", "PPES 1 · Week 2", "#a8366f"),
    7: ("auscultation", "Auscultation", "PPES 1 · Week 2", "#b4501f"),
    8: ("anterior", "Anterior chest", "PPES 1 · Week 2", "#7d6413"),
    9: ("together", "Putting it together", "PoM 1 · Respirology", "#2f6b4f"),
    10: ("finish", "Finishing the exam", "PoM 1 · Respirology", "#4d5590"),
}

# the note's opening sections, shown as the first band
GENERAL = [(1, "The general approach"), (2, "Before you examine: the respiratory history")]

# manoeuvre name as the note shows it -> (problem heading, picture in img/)
TESTS = {
    "Clubbing (Schamroth sign)": ("Hands: chronic lung disease", "clubbing-schamroth-sign.jpg"),
    "Asterixis": ("Hands: chronic lung disease", None),
    "Capillary refill": ("Hands: chronic lung disease", "capillary-refill.jpg"),
    "Tracheal position": ("Neck: what is pushing or pulling", "tracheal-position.jpg"),
    "Cervical and supraclavicular lymph nodes": ("Neck: what is pushing or pulling", None),
    "Chest shape and skin (SEADS)": ("Shape and movement", "chest-shape-and-skin-seads.jpg"),
    "Respiratory movement and accessory muscles": ("Shape and movement", "respiratory-movement-and-accessory-muscles.jpg"),
    "Spine and renal angle tenderness": ("Tenderness", None),
    "Chest expansion": ("Movement and vibration", "chest-expansion.jpg"),
    "Tactile fremitus": ("Movement and vibration", None),
    "Percussing a lung field": ("Air, fluid or solid?", "posterior-ladder.jpg"),
    "Diaphragmatic excursion": ("Diaphragm", None),
    "Auscultating a lung field": ("Breath sounds", "auscultating-a-lung-field.jpg"),
    "Egophony": ("Voice tests for consolidation", "egophony.jpg"),
    "Whispered pectoriloquy": ("Voice tests for consolidation", "whispered-pectoriloquy.jpg"),
    "Anterior percussion": ("Front lung fields", "posterior-ladder.jpg"),
    "Anterior auscultation": ("Front lung fields", "anterior-auscultation.jpg"),
    "Right middle lobe": ("Front lung fields", "right-middle-lobe.jpg"),
    "Clubbing (upper limb)": ("Hands and legs", "clubbing-schamroth-sign.jpg"),
    "Pitting edema (lower limbs)": ("Hands and legs", "pitting-edema-lower-limbs.jpg"),
}

EXAM = exam_page.Exam(
    key="resp", folder=HERE, note=NOTE, regions=REGIONS, general=GENERAL, tests=TESTS, opening={},
    h1="Respiratory exam, front to back",
    lead="The general approach and the history first, then each part of the exam in the order you do it: what to look for, "
         "each manoeuvre grouped under what it tests (numbered steps and what counts as positive), and its pearls. "
         "Built from the course objectives; anything only the PoM 1 Respirology session teaches is tagged "
         "<i>later</i>. Each side of the chest goes inspect, palpate, percuss, auscultate, always comparing left with right.",
    find="Find a manoeuvre or a finding (e.g. fremitus, crackles)",
    root="General inspection → Posterior chest → Anterior chest → Finish",
    root_note="Inspect, palpate, percuss, auscultate; compare left with right at the same level, and cover every lung "
              "field from apex to base. The right middle lobe can only be reached from the front.",
    video_credit='Videos and most photos from the <a href="https://rsc.lib.uwo.ca/s/healthedu/item-set">Health Education Media Library</a> '
                 "(Western Libraries; Schulich School of Medicine and Dentistry), CC BY-NC 4.0, played from the library's own server. "
                 "Each opens only when you tap it.",
    clips=json.loads((HERE / "clips.json").read_text(encoding="utf-8")),
    general_title="General approach", general_week="Every respiratory exam",
    spine_heading="What to do", spine_title="Before the manoeuvres", pearls_heading="Pearls", count_noun="manoeuvres",
)


if __name__ == "__main__":
    exam_page.build(EXAM)
