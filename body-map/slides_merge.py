"""
Purpose: Merge what this year's MSK lecture slides say (one extraction per group of decks) into body-map/slides.json,
         the source the body map follows for what it shows: each muscle's action, nerve and clinical points, the
         arteries, ligaments and bone landmarks the slides name, and the regional clinical boxes. The slides are a
         cut-down version of the full tables (flexor pollicis brevis just "flexes CMC joint"), to keep the load down.
Author: nsimsam, with Claude Code
Date: 2026-10-21
Input: slides_A.json ... slides_D.json, each read from the OneNote lecture decks (PoM 2 B3 MSK, Asynch Weeks 7-10)
Output: body-map/slides.json
Usage: python slides_merge.py <folder with slides_A..D.json>
"""

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent
DECKS = {
    "d01": "Clinical Approach to Mechanical Back Pain", "d03": "Osteology and Joints of the Proximal Upper Extremity",
    "d04": "Brachial Plexus", "d05": "Muscles of the Shoulder", "d06": "Muscles of the Arm",
    "d07": "Neurovascular Supply to the Proximal Upper Extremity", "d08": "Osteology of the Distal Upper Extremity and the Elbow",
    "d09": "Muscles of the Distal Upper Extremity", "d10": "Neurovascular Supply to the Distal Upper Extremity",
    "d11": "Wrist and Hand, part 1", "d12": "Wrist and Hand, part 2", "d13": "Anatomy of the Gluteal Region and Thigh",
    "d14": "Clinical Approach to the Hip", "d15": "Clinical Approach to the Knee, part 1", "d16": "Clinical Approach to the Knee, part 2",
    "d17": "Anatomy of the Leg", "d18": "Clinical Approach to the Ankle and Foot",
}
# slide artery name -> the body map's artery id
ARTERY = {
    "Vertebral artery": "vertebral", "Subclavian artery": "subclavian", "Axillary artery": "axillary", "Brachial artery": "brachial",
    "Profunda brachii (deep brachial) artery": "deep_brachial", "Radial artery": "radial", "Ulnar artery": "ulnar",
    "Superficial palmar arch": "sup_palmar_arch", "Deep palmar arch": "deep_palmar_arch", "Common and proper palmar digital arteries": "palmar_digital",
    "Superior gluteal artery": "sup_gluteal", "Inferior gluteal artery": "inf_gluteal", "Obturator artery": "obturator",
    "External iliac artery": "external_iliac", "Femoral artery": "femoral", "Deep femoral (profunda femoris) artery": "deep_femoral",
    "Perforating arteries": "perforating", "Medial circumflex femoral artery": "med_circumflex_femoral",
    "Lateral circumflex femoral artery": "lat_circumflex_femoral", "Popliteal artery": "popliteal",
    "Artery of the ligament of the head of the femur": "ligament_head_femur",  # drawn with its ligament
    "Anterior tibial artery": "ant_tibial", "Posterior tibial artery": "post_tibial", "Fibular artery": "fibular",
    "Dorsalis pedis artery": "dorsalis_pedis", "Medial plantar artery": "med_plantar", "Lateral plantar artery": "lat_plantar",
}
# (extraction letter, slide ligament name) -> the body map's ligament id; the same name can mean different places per deck
LIGAMENT = {
    "Anterior longitudinal ligament": "all", "Posterior longitudinal ligament": "pll", "Ligamentum flavum": None,
    "Supraspinous ligament": "supraspinous", "Interspinous ligament": "interspinous", "Ligamentum nuchae": "nuchal",
    "Acromioclavicular ligament": "acromioclavicular", "Coracoclavicular ligament": "coracoclavicular", "Glenohumeral ligaments": "glenohumeral",
    "Coracoacromial ligament": "coracoacromial", "Coracohumeral ligament": "coracohumeral",
    "Ulnar (medial) collateral ligament": "ucl", "Radial (lateral) collateral ligament": "rcl_elbow", "Anular ligament": "annular_ligament",
    ("B", "Interosseous membrane"): "interosseous_membrane_forearm", ("B", "Flexor retinaculum"): "flexor_retinaculum",
    ("B", "Extensor retinaculum"): "extensor_retinaculum_wrist", "Palmar carpal ligament": "palmar_carpal",
    "Palmar aponeurosis": None, "Flexor retinaculum (transverse carpal ligament)": "flexor_retinaculum", "Fibrous digital sheaths": None,
    "Sacrospinous ligament": "sacrospinous", "Sacrotuberous ligament": "sacrotuberous", "Iliotibial (IT) band": "itb", "IT band": "itb",
    "Inguinal ligament": "inguinal", "Ligament of the head of the femur": "ligament_head_femur", "Acetabular labrum": "acetabular_labrum",
    "Hip capsular ligaments (unnamed on slide)": "hip_capsular",
    "Anterior cruciate ligament": "acl", "Posterior cruciate ligament": "pcl", "Tibial (medial) collateral ligament": "mcl",
    "Fibular (lateral) collateral ligament": "lcl", "Medial meniscus": "medial_meniscus", "Lateral meniscus": "lateral_meniscus",
    "Patellar tendon": "patellar_ligament", "Anterior talofibular ligament": "atfl", "Calcaneofibular ligament": "calcaneofibular",
    "Posterior talofibular ligament": "ptfl", "Deltoid ligament": "deltoid_ankle", "Spring (calcaneonavicular) ligament": "spring",
    "Long plantar ligament": "long_plantar", "Interosseous talocalcaneal ligaments": None,
    ("D", "Interosseous membrane"): "interosseous_membrane_leg", ("D", "Flexor retinaculum"): "flexor_retinaculum_ankle",
    "Extensor retinacula": "extensor_retinaculum_ankle", "Fibular retinacula": None,
}
# slide bone or landmark -> the body map's bone id (the bone it sits on)
BONE = {
    "Vertebral column": "spine", "Vertebra (typical)": "spine", "Intervertebral disc": "spine", "Zygapophysial (facet) joints": "spine",
    "Cervical vertebrae": "cervical_vertebrae", "Thoracic vertebrae": "thoracic_vertebrae", "Lumbar vertebrae": "lumbar_vertebrae",
    "Atlas (C1)": "atlas", "Axis (C2)": "axis", "Sacrum": "sacrum", "Coccyx": "coccyx", "Iliac crest": "hip_bone", "Ribs 6-12": "ribs",
    "Clavicle": "clavicle", "Scapula": "scapula", "Acromion": "scapula", "Coracoid process": "scapula", "Glenoid fossa": "scapula",
    "Supraglenoid tubercle": "scapula", "Infraglenoid tubercle": "scapula", "Humerus (proximal)": "humerus", "Humerus (distal)": "humerus",
    "Humerus": "humerus", "Trochlea": "humerus", "Capitulum": "humerus", "Coronoid fossa": "humerus", "Medial epicondyle": "humerus",
    "Lateral epicondyle": "humerus", "Olecranon": "ulna", "Coronoid process (ulna)": "ulna", "Coronoid process": "ulna",
    "Ulnar head": "ulna", "Ulnar styloid process": "ulna", "Radial head": "radius", "Radial tuberosity": "radius",
    "Radial styloid process": "radius", "Distal radius": "radius", "Elbow joint": "humerus", "Radioulnar joints": "radius",
    "Carpal bones": "carpals", "Scaphoid": "scaphoid", "Trapezium": "carpals", "Hook of hamate": "carpals", "Metacarpals": "metacarpals",
    "Phalanges": "phalanges_hand", "Hand joints (CMC, MCP, IP)": "metacarpals",
    "ASIS (anterior superior iliac spine)": "hip_bone", "AIIS (anterior inferior iliac spine)": "hip_bone", "Ischial tuberosity": "hip_bone",
    "Greater sciatic foramen": "hip_bone", "Greater trochanter": "femur", "Femoral neck": "femur", "Femur": "femur",
    "Lateral femoral condyle": "femur", "Medial femoral condyle": "femur", "Intercondylar fossa (notch)": "femur",
    "Patella": "patella", "Patellar surface": "femur", "Tibia": "tibia", "Lateral tibial condyle": "tibia", "Medial tibial condyle": "tibia",
    "Tibial tuberosity": "tibia", "Intercondylar eminence": "tibia", "Pes anserinus": "tibia", "Fibula": "fibula", "Head of fibula": "fibula",
    "Medial malleolus": "tibia", "Lateral malleolus": "fibula", "Talus": "talus", "Calcaneus": "calcaneus", "Calcaneal tuberosity": "calcaneus",
    "Sustentaculum tali": "calcaneus", "Navicular": "navicular", "Cuboid": "cuboid", "Cuneiforms": "cuneiforms",
    "Tuberosity of 5th metatarsal": "metatarsals", "Heads of metatarsals": "metatarsals",
}
SKIP_BONES = {"Sesamoid bones"}  # no bone of their own in the model


def src(entry: dict) -> str:
    deck, slides = entry.get("deck", ""), entry.get("slides") or ([entry["slide"]] if entry.get("slide") else [])
    return f"{DECKS.get(deck, deck)}, slide {', '.join(map(str, slides))}" if slides else DECKS.get(deck, deck)


def main(folder: Path) -> None:
    out = {"muscles": {}, "excluded": [], "arteries": {}, "ligaments": {}, "bones": {}, "regional": {}}
    for letter in "ABCD":
        d = json.loads((folder / f"slides_{letter}.json").read_text(encoding="utf-8"))
        for name, m in d["muscles"].items():
            out["muscles"].setdefault(name, {"action": m["action"], "innervation": m["innervation"],
                                              "clinical": m.get("clinical", []), "src": src(m)})
        out["excluded"] += d.get("muscles_not_on_slides", [])
        for name, a in d["arteries"].items():
            k = ARTERY[name]
            e = out["arteries"].setdefault(k, {"name": name, "facts": [], "src": []})
            e["facts"] += [f for f in a["facts"] if f not in e["facts"]]
            e["src"].append(src(a))
        for name, li in d["ligaments"].items():
            k = LIGAMENT.get((letter, name), LIGAMENT.get(name, "?"))
            if k == "?":
                raise KeyError(f"{letter}: no id for ligament {name!r}")
            if k is None:
                log.info("not drawn (no shape for it): %s", name)
                continue
            e = out["ligaments"].setdefault(k, {"name": name, "facts": [], "src": []})
            e["facts"] += [f for f in li["facts"] if f not in e["facts"]]
            e["src"].append(src(li))
        for name, b in d["bones"].items():
            if name in SKIP_BONES:
                continue
            out["bones"].setdefault(BONE[name], []).append({"name": name, "facts": b["facts"], "src": src(b)})
        for r in d["regional_clinical"]:
            out["regional"].setdefault(r["region"], []).append({"title": r["title"], "text": r["text"], "src": src(r)})
    # the plantar fascia is a muscle-table row in the foot, but a ligament-like band on the body
    pf = out["muscles"].get("Plantar fascia")
    if pf:
        out["ligaments"]["plantar_fascia"] = {"name": "Plantar fascia", "facts": [pf["action"]] + pf["clinical"], "src": [pf["src"]]}
    (HERE / "slides.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    log.info("slides.json: %d muscles (%d not on the slides), %d arteries, %d ligaments, %d bones, regions %s",
             len(out["muscles"]), len(out["excluded"]), len(out["arteries"]), len(out["ligaments"]), len(out["bones"]),
             {k: len(v) for k, v in out["regional"].items()})


if __name__ == "__main__":
    main(Path(sys.argv[1]))
