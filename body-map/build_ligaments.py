"""
Purpose: The body map's Ligaments and Bones layers. BodyParts3D has almost no ligaments, so the ones our MSK
         notes discuss are drawn (right side, plus the spine's midline ligaments) from landmarks on the real
         bones: tubes for cords, ribbons for membranes and bands. Only the ligaments the slides name are kept, and
         they and the bones get only what the slides say about them.
Author: nsimsam, with Claude Code
Date: 2026-10-21
Input: the BodyParts3D 4.0 "is_a" OBJ archive unzipped at BP3D_DIR; body-map/slides.json (slides_merge.py: what this
       year's lecture slides say about each ligament and bone)
Output: body-map/ligaments.json ({"drawn": [...], "info": {...}, "groups": [...], "bones": {FJ id: [name, fact id]}})
Usage: python build_ligaments.py <BP3D_DIR>   (needs trimesh, numpy, scipy)
"""

import csv
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np

from build_layers import Skeleton

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent


def to_three(p) -> list:
    p = np.asarray(p, dtype=float)
    return (np.stack([p[..., 0], p[..., 2], -p[..., 1]], axis=-1) / 1000.0).round(4).tolist()


def ext(pts: np.ndarray, axis: int, most: bool) -> np.ndarray:
    return pts[np.argmax(pts[:, axis])] if most else pts[np.argmin(pts[:, axis])]


def band(pts: np.ndarray, axis: int, lo: float, hi: float) -> np.ndarray:
    return pts[(pts[:, axis] >= lo) & (pts[:, axis] <= hi)]


def near(pts: np.ndarray, p) -> np.ndarray:
    return pts[np.argmin(np.linalg.norm(pts - np.asarray(p), axis=1))]


def landmarks(sk: Skeleton) -> dict:
    """Named points (mm, right side: medial +X, anterior -Y, up +Z) the ligaments are strung between."""
    F = lambda pat: sk.find(pat)
    sc, cl, hu = F(r"^right scapula$"), F(r"^right clavicle$"), F(r"^right humerus$")
    ra, ul = F(r"^right radius$"), F(r"^right ulna$")
    hip, fe, ti, fi = F(r"^right hip bone$"), F(r"^right femur$"), F(r"^right tibia$"), F(r"^right fibula$")
    pa, ta, ca = F(r"^right patella$"), F(r"^right talus$"), F(r"^right calcaneus$")
    nav, cub = F(r"navicular bone of right foot"), F(r"^right cuboid bone$")
    sac = F(r"^sacrum$")
    L = {}

    # shoulder: acromion = the scapula's most lateral point high up; coracoid = its most anterior point
    top = band(sc, 2, sc[:, 2].max() - 45, sc[:, 2].max())
    L["acromion"] = ext(top, 0, False)
    L["coracoid"] = ext(sc, 1, False)
    L["coracoid_base"] = L["coracoid"] * 0.4 + near(sc, L["coracoid"] + [12, 25, 5]) * 0.6
    L["clav_lat_under"] = ext(band(cl, 0, L["acromion"][0] + 12, L["acromion"][0] + 40), 2, False)
    L["clav_lat_end"] = ext(cl, 0, False)
    hh = band(hu, 2, hu[:, 2].max() - 40, hu[:, 2].max())
    L["greater_tub"] = ext(hh, 0, False)
    L["hum_head_med"] = ext(hh, 0, True)
    L["glenoid"] = near(sc, L["hum_head_med"])
    L["hum_neck_ant"] = ext(band(hu, 2, hu[:, 2].max() - 55, hu[:, 2].max() - 35), 1, False)
    sup = band(sc, 0, L["coracoid_base"][0] + 10, L["coracoid_base"][0] + 30)
    L["supra_notch"] = ext(sup, 2, True) + [0, 0, -3]

    # elbow and wrist
    lo = band(hu, 2, hu[:, 2].min(), hu[:, 2].min() + 45)
    L["lat_epi"] = ext(lo, 0, False)
    rh = band(ra, 2, ra[:, 2].max() - 14, ra[:, 2].max())
    L["rad_head_lat"] = ext(rh, 0, False)
    rd, ud = band(ra, 2, ra[:, 2].min(), ra[:, 2].min() + 30), band(ul, 2, ul[:, 2].min(), ul[:, 2].min() + 30)
    L["rad_dist_ant"], L["uln_dist_ant"] = ext(rd, 1, False), ext(ud, 1, False)
    L["rad_dist_post"], L["uln_dist_post"] = ext(rd, 1, True), ext(ud, 1, True)
    L["rad_styloid"], L["uln_styloid"] = ext(rd, 0, False), ext(ud, 0, True)

    def shaft(bone, s):
        z = bone[:, 2].max() - s * np.ptp(bone[:, 2])
        return bone[np.argsort(np.abs(bone[:, 2] - z))[:40]].mean(axis=0)  # the cross-section nearest that height
    L["shaft"] = shaft

    # pelvis and hip
    L["asis"] = ext(band(hip, 2, hip[:, 2].max() - 60, hip[:, 2].max() - 25), 1, False)
    front = band(hip, 0, hip[:, 0].max() - 25, hip[:, 0].max())
    L["pubic_tub"] = ext(front, 1, False) + [-12, 0, 6]
    fh = band(fe, 2, fe[:, 2].max() - 70, fe[:, 2].max())
    L["fem_head_med"] = ext(fh, 0, True)
    L["acetab"] = near(hip, L["fem_head_med"])
    L["greater_troch"] = ext(fh, 0, False)
    L["aiis"] = near(hip, L["acetab"] + [-20, -20, 35])
    it = band(fe, 2, fe[:, 2].max() - 95, fe[:, 2].max() - 40)
    L["intertroch_top"] = ext(band(it, 2, it[:, 2].max() - 15, it[:, 2].max()), 1, False)
    L["intertroch_low"] = ext(band(it, 2, it[:, 2].min(), it[:, 2].min() + 15), 1, False)
    neck = (L["fem_head_med"] + L["greater_troch"]) / 2
    L["fem_neck"] = neck
    L["ischial_tub"] = ext(hip, 2, False)
    L["pubic_ramus"] = near(hip, L["acetab"] + [28, -10, -12])
    L["ischium_post"] = near(hip, L["acetab"] + [-5, 30, -18])
    sz = sac[:, 2].max() - 0.6 * np.ptp(sac[:, 2])
    L["sacrum_lat"] = ext(band(sac, 2, sz - 8, sz + 8), 0, False)
    L["psis"] = ext(band(hip, 1, hip[:, 1].max() - 25, hip[:, 1].max()), 2, True)
    spine_zone = band(band(hip, 2, L["ischial_tub"][2] + 30, L["ischial_tub"][2] + 70), 1, L["acetab"][1] + 10, 500)
    L["ischial_spine"] = ext(spine_zone, 0, True)

    # knee
    L["patella_apex"] = ext(pa, 2, False)
    tt = band(ti, 2, ti[:, 2].max() - 60, ti[:, 2].max() - 30)
    L["tib_tuberosity"] = ext(tt, 1, False)
    tp = band(ti, 2, ti[:, 2].max() - 25, ti[:, 2].max() - 10)
    L["tib_med_post"] = ext(band(tp, 0, tp[:, 0].mean(), 500), 1, True)
    fc = band(fe, 2, fe[:, 2].min() + 20, fe[:, 2].min() + 50)
    L["fem_lat_cond_post"] = ext(band(fc, 0, -500, fc[:, 0].mean()), 1, True)

    # ankle and foot
    L["med_malleolus"] = ext(ti, 2, False)
    L["lat_malleolus"] = ext(fi, 2, False)
    L["nav_med"] = ext(nav, 0, True)
    L["sustentaculum"] = ext(band(ca, 2, ca[:, 2].max() - 25, ca[:, 2].max() - 8), 0, True)
    L["calc_lat"] = ext(band(ca, 2, ca[:, 2].min() + 15, ca[:, 2].min() + 30), 0, False)
    L["calc_med"] = ext(band(ca, 2, ca[:, 2].min() + 15, ca[:, 2].min() + 30), 0, True)
    L["talus_post"] = ext(ta, 1, True)
    L["talus_neck_lat"] = ext(band(ta, 1, -500, ta[:, 1].mean()), 0, False)
    L["calc_plantar"] = ext(ca, 2, False) + [0, -15, 2]
    L["cub_plantar"] = ext(cub, 2, False)
    L["nav_plantar"] = ext(nav, 2, False)
    mts = [sk.find(rf"right {w} metatarsal") for w in ("second", "third", "fourth", "fifth")]
    L["mt_bases_plantar"] = [ext(band(m, 1, m[:, 1].max() - 12, m[:, 1].max()), 2, False) for m in mts]
    L["tib_ant_low"] = ext(band(ti, 2, ti[:, 2].min() + 35, ti[:, 2].min() + 45), 1, False)
    L["fib_ant_low"] = ext(band(fi, 2, fi[:, 2].min() + 35, fi[:, 2].min() + 45), 1, False)
    L["ti"], L["fi"], L["ra"], L["ul"] = ti, fi, ra, ul
    return L


def spine_points(sk: Skeleton) -> dict:
    """Front and back of each vertebral body and each spinous tip, top to bottom, on the midline."""
    names = (["atlas", "axis"] + [f"{w} cervical vertebra" for w in ("third", "fourth", "fifth", "sixth", "seventh")] +
             [f"{w} thoracic vertebra" for w in ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth",
                                                  "tenth", "eleventh", "twelfth")] +
             [f"{w} lumbar vertebra" for w in ("first", "second", "third", "fourth", "fifth")])
    front, back, tip = [], [], []
    for n in names:
        v = sk.find(rf"^{n}$")
        mid = v[np.abs(v[:, 0]) < 5]
        if len(mid) < 10:
            continue
        ys = np.sort(mid[:, 1])
        gaps = np.diff(ys)
        g = np.argmax(gaps[: len(gaps) // 2 + 1]) if n not in ("atlas",) else None
        z = mid[:, 2].mean()
        if n != "atlas":
            front.append([0, ys[0] - 1, mid[np.argmin(mid[:, 1]), 2]])
            back.append([0, ys[g] + 1, z])  # the body's back surface: just before the gap that is the canal
        tip.append(mid[np.argmax(mid[:, 1])])
    occ = sk.find(r"^occipital bone$")
    ext_occ = ext(occ[np.abs(occ[:, 0]) < 6], 1, True)
    return {"front": np.array(front), "back": np.array(back), "tip": np.array(tip), "ext_occ": ext_occ}


def drawn(sk: Skeleton) -> list:
    L = landmarks(sk)
    S = spine_points(sk)
    sh = L["shaft"]
    out = []

    def tube(key, pts, r, sub=None):
        out.append({"key": key, "kind": "tube", "path": to_three(np.array(pts, float)), "r": r / 1000, **({"sub": sub} if sub else {})})

    def sheet(key, a, b):
        """A ribbon between two edges (each a list of points)."""
        out.append({"key": key, "kind": "sheet", "a": to_three(np.array(a, float)), "b": to_three(np.array(b, float))})

    c, cb = L["coracoid"], L["coracoid_base"]
    tube("coracoclavicular", [cb + [0, 4, 6], L["clav_lat_under"] + [6, 0, -2]], 3.2, "conoid")
    tube("coracoclavicular", [cb + [-8, 0, 6], L["clav_lat_under"] + [-8, -2, -2]], 3.2, "trapezoid")
    tube("coracoacromial", [c + [0, 2, 3], (c + L["acromion"]) / 2 + [0, 0, 10], L["acromion"] + [6, -2, 0]], 2.8)
    tube("acromioclavicular", [L["clav_lat_end"] + [8, 0, 5], L["acromion"] + [4, 0, 5]], 2.6)
    tube("coracohumeral", [cb + [-4, 0, 2], L["greater_tub"] + [4, -6, 4]], 2.6)
    g, hn = L["glenoid"], L["hum_neck_ant"]
    for k, dz in (("superior", 10), ("middle", 0), ("inferior", -12)):
        tube("glenohumeral", [g + [0, -8, dz], hn + [4, -2, dz * 0.7]], 1.6, k)
    tube("transverse_scapular", [L["supra_notch"] + [8, 0, 0], L["supra_notch"] + [-8, 0, 0]], 1.8)
    tube("rcl_elbow", [L["lat_epi"] + [-2, 0, -2], (L["lat_epi"] + L["rad_head_lat"]) / 2 + [-4, 0, 0], L["rad_head_lat"] + [-3, 0, 0]], 2.8)
    tube("palmar_carpal", [L["uln_dist_ant"] + [0, -6, 14], (L["uln_dist_ant"] + L["rad_dist_ant"]) / 2 + [0, -9, 14], L["rad_dist_ant"] + [0, -6, 14]], 2.6)
    tube("extensor_retinaculum_wrist", [L["uln_dist_post"] + [2, 6, 18], (L["uln_dist_post"] + L["rad_dist_post"]) / 2 + [0, 9, 18],
                                        L["rad_dist_post"] + [-2, 6, 18]], 3.0)
    ra, ul = L["ra"], L["ul"]
    sheet("interosseous_membrane_forearm", [sh(ra, s) + [6, 0, 0] for s in np.linspace(0.18, 0.86, 8)],
          [sh(ul, s) + [-6, 0, 0] for s in np.linspace(0.18, 0.86, 8)])
    tube("inguinal", [L["asis"] + [2, -3, 0], (L["asis"] + L["pubic_tub"]) / 2 + [0, -14, -12], L["pubic_tub"] + [0, -3, 0]], 2.8)
    # the slides show the hip's capsular ligaments colour-coded but unnamed, so they are one structure here
    tube("hip_capsular", [L["aiis"] + [0, -6, 0], L["intertroch_top"] + [0, -5, 0]], 3.4, "front, from the ilium")
    tube("hip_capsular", [L["aiis"] + [0, -6, 0], L["intertroch_low"] + [0, -5, 0]], 3.4, "front, from the ilium")
    tube("hip_capsular", [L["pubic_ramus"] + [0, -5, 0], L["fem_neck"] + [8, -10, -14]], 3.0, "from the pubis")
    tube("hip_capsular", [L["ischium_post"] + [0, 4, 0], L["fem_neck"] + [-6, 12, 8], L["greater_troch"] + [8, 10, 0]], 3.0, "behind, from the ischium")
    tube("ligament_head_femur", [L["acetab"] + [-2, 0, -4], L["fem_head_med"] + [-4, 0, 0]], 2.4)
    tube("sacrotuberous", [L["psis"] + [4, 6, -20], L["sacrum_lat"] + [-2, 10, 0], L["ischial_tub"] + [6, 6, 6]], 3.6)
    tube("sacrospinous", [L["sacrum_lat"] + [-2, 4, -6], L["ischial_spine"] + [2, 0, 0]], 3.2)
    tube("patellar_ligament", [L["patella_apex"] + [0, -2, 2], L["tib_tuberosity"] + [0, -2, 2]], 4.5)
    tube("oblique_popliteal", [L["tib_med_post"] + [0, 4, 0], (L["tib_med_post"] + L["fem_lat_cond_post"]) / 2 + [0, 9, 4], L["fem_lat_cond_post"] + [0, 4, 0]], 2.6)
    ti, fi = L["ti"], L["fi"]
    sheet("interosseous_membrane_leg", [sh(ti, s) + [-8, 2, 0] for s in np.linspace(0.12, 0.82, 8)],
          [sh(fi, s) + [6, 0, 0] for s in np.linspace(0.12, 0.82, 8)])
    mm = L["med_malleolus"]
    for to, k in ((L["nav_med"], "tibionavicular"), (L["sustentaculum"], "tibiocalcaneal"), (L["talus_post"] + [14, -4, 4], "posterior tibiotalar")):
        tube("deltoid_ankle", [mm + [0, 0, 6], to + [3, 0, 0]], 2.6, k)
    lm = L["lat_malleolus"]
    tube("calcaneofibular", [lm + [0, 2, 4], L["calc_lat"] + [-3, 0, 0]], 2.8)
    tube("ptfl", [lm + [0, 6, 6], L["talus_post"] + [-4, 2, 0]], 2.8)
    tube("spring", [L["sustentaculum"] + [2, -4, -4], L["nav_plantar"] + [2, 0, -3]], 3.2)
    tube("long_plantar", [L["calc_plantar"] + [0, 0, -3], L["cub_plantar"] + [0, 0, -4], *[p + [0, 0, -3] for p in L["mt_bases_plantar"][::-1]][:1]], 3.4)
    tube("flexor_retinaculum_ankle", [mm + [0, 6, 8], (mm + L["calc_med"]) / 2 + [8, 14, 0], L["calc_med"] + [3, 4, 0]], 3.0)
    tube("extensor_retinaculum_ankle", [L["fib_ant_low"] + [-2, -4, 0], (L["fib_ant_low"] + L["tib_ant_low"]) / 2 + [0, -14, 0], L["tib_ant_low"] + [2, -4, 0]], 3.0)
    # spine
    tube("all", list(S["front"]), 2.4)
    tube("pll", list(S["back"]), 2.0)
    tube("supraspinous", list(S["tip"][6:]), 2.0)  # C7 down
    tube("nuchal", [S["ext_occ"] + [0, 4, 0], *S["tip"][1:7]], 2.4)
    for a, b in zip(S["tip"][6:-1], S["tip"][7:]):
        tube("interspinous", [a + [0, -8, -4], b + [0, -8, 4]], 1.6)
    return out


# Ligaments the body map already draws (body.json), by id: kept, and given the notes' facts too
EXISTING = ["ucl", "annular_ligament", "glenoid_labrum", "acetabular_labrum", "acl", "pcl", "mcl", "lcl", "medial_meniscus",
            "lateral_meniscus", "atfl", "plantar_fascia", "flexor_retinaculum", "itb"]
GROUPS = [
    ["Shoulder", ["coracoclavicular", "coracoacromial", "acromioclavicular", "coracohumeral", "glenohumeral", "glenoid_labrum", "transverse_scapular"]],
    ["Elbow, forearm and wrist", ["ucl", "rcl_elbow", "annular_ligament", "interosseous_membrane_forearm", "palmar_carpal", "flexor_retinaculum", "extensor_retinaculum_wrist"]],
    ["Spine", ["all", "pll", "supraspinous", "interspinous", "nuchal"]],
    ["Pelvis and hip", ["inguinal", "hip_capsular", "ligament_head_femur", "acetabular_labrum", "sacrotuberous", "sacrospinous", "itb"]],
    ["Knee", ["acl", "pcl", "mcl", "lcl", "medial_meniscus", "lateral_meniscus", "patellar_ligament", "oblique_popliteal", "interosseous_membrane_leg"]],
    ["Ankle and foot", ["deltoid_ankle", "atfl", "calcaneofibular", "ptfl", "spring", "long_plantar", "plantar_fascia", "flexor_retinaculum_ankle", "extensor_retinaculum_ankle"]],
]

# Bone name (BodyParts3D, any side) -> the facts file's bone id
BONE_IDS = [
    (r"clavicle", "clavicle"), (r"scapula", "scapula"), (r"humerus", "humerus"), (r"radius", "radius"), (r"ulna\b", "ulna"),
    (r"scaphoid", "scaphoid"), (r"lunate|triquetral|pisiform|trapezium|trapezoid|capitate|hamate", "carpals"),
    (r"metacarpal", "metacarpals"), (r"phalanx of .*(finger|thumb)", "phalanges_hand"), (r"^atlas", "atlas"), (r"^axis", "axis"),
    (r"cervical vertebra", "cervical_vertebrae"), (r"thoracic vertebra", "thoracic_vertebrae"),
    (r"lumbar vertebra", "lumbar_vertebrae"), (r"sacrum", "sacrum"), (r"coccy", "coccyx"), (r"\brib\b", "ribs"),
    (r"sternum|manubrium|xiphoid", "sternum"), (r"hip bone", "hip_bone"), (r"femur", "femur"), (r"patella", "patella"),
    (r"tibia", "tibia"), (r"fibula", "fibula"), (r"talus", "talus"), (r"calcaneus", "calcaneus"), (r"navicular", "navicular"),
    (r"cuboid", "cuboid"), (r"cuneiform", "cuneiforms"), (r"metatarsal", "metatarsals"), (r"phalanx of .*toe", "phalanges_foot"),
]


def bone_names(bp3d_dir: Path) -> dict:
    """Every bone in body.glb: its plain name and its facts id."""
    with open(bp3d_dir / "isa_element_parts.txt") as fh:
        rows = [r for r in csv.reader(fh, delimiter="\t") if r[0] != "concept id"]
    ids = {r[2] for r in rows if r[1] == "bone organ"} | {"FJ3290", "FJ3178", "FJ3153"}
    names: dict[str, list[str]] = {}
    for _, name, fid in rows:
        if fid in ids:
            names.setdefault(fid, []).append(name)
    out = {}
    for fid, ns in names.items():
        sided = [n for n in ns if re.match(r"(right|left) ", n)]
        name = (sided or sorted(ns, key=len))[0]
        if fid == "FJ3290":
            name = "manubrium"
        fact = next((k for pat, k in BONE_IDS if re.search(pat, name)), None)
        out[fid] = [name[0].upper() + name[1:], fact]
    return out


def main(bp3d_dir: Path) -> None:
    obj_dir = bp3d_dir / "objs" / "isa_BP3D_4.0_obj_99"
    sk = Skeleton(bp3d_dir, obj_dir)
    # only the ligaments and bones this year's slides name, with what the slides say (slides_merge.py)
    slides = json.loads((HERE / "slides.json").read_text(encoding="utf-8"))
    lig = slides["ligaments"]
    if "ligament_head_femur" in slides["arteries"]:  # the slides teach its artery with it
        lig.setdefault("ligament_head_femur", {"name": "Ligament of the head of the femur", "facts": [], "src": []})
        lig["ligament_head_femur"]["facts"] += slides["arteries"]["ligament_head_femur"]["facts"]
        lig["ligament_head_femur"]["src"] += slides["arteries"]["ligament_head_femur"]["src"]
    shapes = [d for d in drawn(sk) if d["key"] in lig]
    groups = [[t, [k for k in ids if k in lig]] for t, ids in GROUPS]
    info = {k: {"name": re.sub(r" \(unnamed on slide\)", "", lig[k]["name"]), "facts": lig[k]["facts"], "src": lig[k]["src"]}
            for _, ids in groups for k in ids}
    bones = bone_names(bp3d_dir)
    vertebra = {"atlas", "axis", "cervical_vertebrae", "thoracic_vertebrae", "lumbar_vertebrae"}
    for fid, (name, fact) in bones.items():
        bones[fid] = [name, [f for f in ([fact] + (["spine"] if fact in vertebra else [])) if f in slides["bones"]]]
    out = {"drawn": shapes, "info": info, "groups": [g for g in groups if g[1]], "existing": [k for k in EXISTING if k in lig],
           "bones": bones, "bone_facts": slides["bones"]}
    (HERE / "ligaments.json").write_text(json.dumps(out, ensure_ascii=False))
    log.info("ligaments.json: %d drawn pieces, %d ligaments, %d bones (%d with slide facts)", len(shapes), len(info), len(bones),
             sum(1 for v in bones.values() if v[1]))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
