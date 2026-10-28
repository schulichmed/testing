"""
Purpose: Build the neurological clinical skills page (neuro-exam/index.html) from the
         manoeuvre tables in the medwiki note "Summary Notes - Neurological Clinical Skills".
Author: Noor Simsam
Date: 2026-10-28
Input: the vault note (POM2_VAULT or the default vault path); img/credits.json; clips.json
       (the Health Education Media Library's neurology videos, by test, region or card)
Output: neuro-exam/index.html

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
NOTE = VAULT / "01 - Lectures/99 - Clinical Skills/Summary Notes - Neurological Clinical Skills.md"

# section number in the note -> region on the page
REGIONS = {
    2: ("mental", "Mental status", "PPES 2 · Weeks 8–9", "#3d6fb6"),
    3: ("cranial", "Cranial nerves", "PPES 2 · Weeks 8–9", "#23798a"),
    4: ("motor", "Motor", "PPES 2 · Weeks 8–9", "#7a3fb0"),
    5: ("sensory", "Sensory", "PPES 2 · Weeks 8–9", "#a8366f"),
    6: ("reflexes", "Reflexes", "PPES 2 · Weeks 8–9", "#b4501f"),
    7: ("coordination", "Coordination", "PPES 2 · Weeks 8–9", "#7d6413"),
    8: ("gait", "Gait and balance", "PPES 2 · Weeks 8–9", "#2f6b4f"),
    9: ("lesion", "Where is the lesion?", "PoM 2 · Neurology", "#4d5590"),
}

# the note's opening section, shown as the first band
GENERAL = [(1, "The general approach")]

# manoeuvre name as the note shows it -> (problem heading, picture in img/)
TESTS = {
    "CN I, olfactory: smell": ("Smell and hearing (I, VIII)", None),
    "CN VIII, vestibulocochlear: hearing": ("Smell and hearing (I, VIII)", None),
    "CN II, optic: visual acuity": ("The eye (II, III, IV, VI)", None),
    "CN II: visual fields by confrontation": ("The eye (II, III, IV, VI)", None),
    "CN II and III: pupillary light reflex": ("The eye (II, III, IV, VI)", None),
    "CN II: fundoscopy": ("The eye (II, III, IV, VI)", None),
    "CN III, IV, VI: eye movements": ("The eye (II, III, IV, VI)", None),
    "CN V, trigeminal: sensation": ("The face (V, VII)", None),
    "CN V: motor": ("The face (V, VII)", None),
    "CN V and VII: corneal reflex": ("The face (V, VII)", None),
    "CN VII, facial: motor": ("The face (V, VII)", None),
    "CN VII: sensory": ("The face (V, VII)", None),
    "CN IX and X: palate": ("Throat, neck and tongue (IX–XII)", None),
    "CN IX and X: gag reflex": ("Throat, neck and tongue (IX–XII)", None),
    "CN XI, spinal accessory": ("Throat, neck and tongue (IX–XII)", None),
    "CN XII, hypoglossal": ("Throat, neck and tongue (IX–XII)", None),
    "Shoulder abduction": ("Arm power (C5–T1)", None),
    "Elbow flexion": ("Arm power (C5–T1)", None),
    "Elbow extension": ("Arm power (C5–T1)", None),
    "Finger abduction": ("Arm power (C5–T1)", None),
    "Grip strength": ("Arm power (C5–T1)", None),
    "Hip flexion": ("Leg power (L2–S1)", None),
    "Knee extension": ("Leg power (L2–S1)", None),
    "Knee flexion": ("Leg power (L2–S1)", None),
    "Ankle dorsiflexion": ("Leg power (L2–S1)", None),
    "Ankle plantar flexion": ("Leg power (L2–S1)", None),
    "Pain (pinprick)": ("Pain and temperature (spinothalamic)", None),
    "Temperature": ("Pain and temperature (spinothalamic)", None),
    "Light touch": ("Light touch", None),
    "Vibration": ("Vibration and position (dorsal columns)", None),
    "Proprioception (joint position)": ("Vibration and position (dorsal columns)", None),
    "Stereognosis": ("Cortical sensation", None),
    "Graphesthesia": ("Cortical sensation", None),
    "Biceps": ("Arm reflexes", None),
    "Brachioradialis": ("Arm reflexes", None),
    "Triceps": ("Arm reflexes", None),
    "Knee (patellar)": ("Leg reflexes", None),
    "Ankle (Achilles)": ("Leg reflexes", None),
    "Plantar response": ("Upper motor neuron sign", None),
    "Rapid alternating movements": ("Arms", None),
    "Finger-nose": ("Arms", None),
    "Heel-shin": ("Legs", None),
    "Tandem gait": ("Walking", None),
    "Romberg test": ("Balance", None),
}

EXAM = exam_page.Exam(
    key="neuro", folder=HERE, note=NOTE, regions=REGIONS, general=GENERAL, tests=TESTS, opening={},
    h1="Neurological exam, top down",
    lead="The general approach first, then each part of the exam in the order you do it: what to look for, "
         "each manoeuvre grouped under what it tests (numbered steps and what counts as positive), and its pearls. "
         "Built from the course objectives; anything only the PoM 2 Neurology session teaches is tagged "
         "<i>later</i>. For the dermatomes and myotomes drawn on a body, see the <a href=\"../body-map/\">body map</a>.",
    find="Find a manoeuvre or a level (e.g. C7, cerebellum)",
    root="Mental status → Cranial nerves → Motor → Sensory → Reflexes → Coordination → Gait",
    root_note="Compare left with right, and near the trunk with far. Every finding answers one question: where is "
              "the lesion, and is it an upper or a lower motor neuron problem?",
    video_credit='Videos from the <a href="https://rsc.lib.uwo.ca/s/healthedu/item-set">Health Education Media Library</a> '
                 "(Western Libraries; Clinical Neurological Sciences, Schulich School of Medicine and Dentistry), "
                 "CC BY-NC 4.0, played from the library's own server. Each opens only when you tap it.",
    clips=json.loads((HERE / "clips.json").read_text(encoding="utf-8")),
    general_title="General approach", general_week="Every neuro exam",
    spine_heading="What to look for", spine_title="Before the manoeuvres", pearls_heading="Pearls", count_noun="manoeuvres",
)


if __name__ == "__main__":
    exam_page.build(EXAM)
