"""
Purpose: The body map's Blood supply layer: the arteries named in our MSK lecture notes (medwiki, PoM 2 Weeks 7-10),
         right side, kept to the ones this year's slides name and each with what the slides say about it.
         BodyParts3D has most of them as meshes; the few it lacks (deep femoral, medial circumflex femoral, obturator,
         superior and inferior gluteal, internal pudendal, fibular, posterior interosseous) are drawn as tubes from
         bony landmarks and the arteries they branch from, so they are approximate.
Author: nsimsam, with Claude Code
Date: 2026-10-21
Input: the BodyParts3D 4.0 "is_a" OBJ archive unzipped at BP3D_DIR; body-map/slides.json (slides_merge.py)
Output: body-map/arteries.glb (one node per artery piece, ar_<id>_<n>) and body-map/arteries.json
        ({"info": {id: {...}}, "drawn": {id: [path, ...]}, "groups": [[title, [ids]]]})
Usage: python build_arteries.py <BP3D_DIR>   (needs trimesh, fast-simplification, numpy, scipy)
"""

import json
import logging
import sys
from pathlib import Path

import numpy as np
import trimesh

from build_layers import Skeleton
from build_nerves import Y_UP, along, centerline, load, oriented, simplify, to_three

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent
MIRROR = {"FJ2090", "FJ2072", "FJ2093"}  # only the left side's mesh exists; mirror it to the right

# id: (name, BodyParts3D meshes, from, what our notes say, clinical, regex for Netter's blood-supply wording)
ARTERIES = {
    "vertebral": ("Vertebral artery", ["FJ1725"], "Subclavian artery",
                  "Ascends through the transverse foramina from C6 to C1 (only the vertebral vein passes through C7's); grooves the upper surface of the atlas", "", None),
    "subclavian": ("Subclavian artery", ["FJ3579"], "Brachiocephalic trunk on the right, the aortic arch on the left",
                   "Becomes the axillary artery at the lateral border of the 1st rib. Two branches join the anastomosis around the scapula", "", r"subclavian"),
    "dorsal_scapular": ("Dorsal scapular artery", ["FJ2284"], "Subclavian artery", "Upper superficial back muscles", "", r"dorsal scapular"),
    "suprascapular": ("Suprascapular artery", ["FJ2303"], "Subclavian artery (often the thyrocervical trunk)",
                      "Back of the shoulder. Runs with the suprascapular nerve, above the superior transverse scapular ligament", "", r"suprascapular"),
    "axillary": ("Axillary artery", ["FJ2268"], "Subclavian artery, at the lateral border of the 1st rib",
                 "Ends at the lower border of teres major. Three parts, set by pectoralis minor in front of it (1st above it, 2nd behind it, 3rd below it); the plexus cords are named for where they sit around it", "", r"^axillary"),
    "thoracoacromial": ("Thoracoacromial artery", ["FJ2304", "FJ2263", "FJ2282", "FJ2361"], "Axillary artery, 2nd part",
                        "Acromial, clavicular, deltoid and pectoral branches; joins the anastomosis around the glenohumeral joint", "", r"thoraco-?acromial"),
    "subscapular": ("Subscapular artery", ["FJ2298"], "Axillary artery, 3rd part",
                    "A short trunk that splits into the thoracodorsal and circumflex scapular arteries", "", r"^subscapular"),
    "thoracodorsal": ("Thoracodorsal artery", ["FJ2305"], "Subscapular artery", "Superficial back (latissimus dorsi); runs with the thoracodorsal nerve", "", r"thoracodorsal"),
    "circumflex_scapular": ("Circumflex scapular artery", ["FJ2273"], "Subscapular artery",
                            "Curves round the lateral border of the scapula, deep to teres minor and infraspinatus, into the scapular anastomosis", "", r"circumflex scapular"),
    "ant_circumflex_humeral": ("Anterior circumflex humeral artery", ["FJ2264"], "Axillary artery, 3rd part",
                               "Encircles the surgical neck of the humerus laterally; a branch to the glenohumeral joint", "", r"anterior circumflex humeral"),
    "post_circumflex_humeral": ("Posterior circumflex humeral artery", ["FJ2291"], "Axillary artery, 3rd part",
                                "Encircles the surgical neck medially and joins the anterior one; runs with the axillary nerve",
                                "A surgical neck fracture threatens it with the axillary nerve", r"posterior circumflex humeral"),
    "brachial": ("Brachial artery", ["FJ2271"], "Axillary artery, at the lower border of teres major",
                 "Runs medial to biceps, in front of coracobrachialis and brachialis; ends in the cubital fossa as the radial (lateral) and ulnar (medial) arteries. In the cubital fossa: biceps Tendon, brachial Artery, median Nerve (TAN, lateral to medial)",
                 "Blood pressure is taken over it. It lies against the medial humeral shaft, so a mid-shaft or supracondylar fracture can injure it", r"^brachial|muscular branches of brachial"),
    "deep_brachial": ("Profunda brachii (deep brachial) artery", ["FJ2277", "FJ2262"], "Brachial artery",
                      "Posterior compartment of the arm, in the radial groove with the radial nerve; becomes the radial collateral artery at the elbow",
                      "Adherent to the humerus in the radial groove, so a mid-shaft fracture threatens it with the radial nerve", r"profunda brachii|deep brachial"),
    "sup_ulnar_collateral": ("Superior ulnar collateral artery", ["FJ2373"], "Brachial artery",
                             "The network around the elbow; joins the posterior ulnar recurrent", "", r"superior ulnar collateral"),
    "inf_ulnar_collateral": ("Inferior ulnar collateral artery", ["FJ2267"], "Brachial artery",
                             "The network around the elbow; joins the anterior ulnar recurrent", "", r"inferior ulnar collateral"),
    "radial": ("Radial artery", ["FJ2294"], "Brachial artery, in the cubital fossa",
               "Lateral forearm, deep to brachioradialis; at the wrist it wraps laterally onto the back, across the floor of the anatomical snuffbox, and enters the palm between the two heads of the 1st dorsal interosseous to form the deep palmar arch",
               "Radial pulse between the flexor carpi radialis and abductor pollicis longus tendons, and in the snuffbox. A scaphoid fragment cut off from its radial artery supply can undergo avascular necrosis", r"^radial artery|superficial palmar branch of radial"),
    "radial_recurrent": ("Recurrent radial artery", ["FJ2295"], "Radial artery", "Joins the radial collateral artery in the network around the elbow", "", r"radial recurrent|recurrent radial"),
    "ulnar": ("Ulnar artery", ["FJ2310"], "Brachial artery, in the cubital fossa",
              "Medial forearm, deep to pronator teres; enters the wrist beside the pisiform, over the flexor retinaculum, through Guyon's canal with the ulnar nerve, and forms the superficial palmar arch",
              "Not in the carpal tunnel: it passes on top of the flexor retinaculum", r"^ulnar artery|muscular branches of ulnar|deep palmar branch of ulnar"),
    "ant_ulnar_recurrent": ("Anterior ulnar recurrent artery", ["FJ2311"], "Ulnar artery", "Joins the inferior ulnar collateral artery around the elbow", "", r"anterior ulnar recurrent"),
    "post_ulnar_recurrent": ("Posterior ulnar recurrent artery", ["FJ2293"], "Ulnar artery", "Joins the superior ulnar collateral artery around the elbow", "", r"posterior ulnar recurrent"),
    "common_interosseous": ("Common interosseous artery", ["FJ2275"], "Ulnar artery, at the distal cubital fossa",
                            "Splits almost at once into the anterior and posterior interosseous arteries", "", r"common interosseous"),
    "ant_interosseous": ("Anterior interosseous artery", ["FJ2266"], "Common interosseous artery",
                         "Runs with the anterior interosseous nerve on the front of the interosseous membrane", "", r"anterior interosseous"),
    "post_interosseous": ("Posterior interosseous artery", [], "Common interosseous artery",
                          "Passes into the posterior compartment above the interosseous membrane", "", r"posterior interosseous"),
    "sup_palmar_arch": ("Superficial palmar arch", ["FJ2300"], "Mainly the ulnar artery, completed by the superficial palmar branch of the radial",
                        "Just deep to the palmar aponeurosis; gives the common palmar digital arteries, which divide into proper palmar digital arteries", "", r"superficial palmar arch|superficial and deep palmar arches"),
    "deep_palmar_arch": ("Deep palmar arch", ["FJ2279"], "Mainly the radial artery, completed by the deep branch of the ulnar",
                         "Across the metacarpals just past their bases; gives 3 palmar metacarpal arteries", "", r"deep palmar arch|superficial and deep palmar arches"),
    "princeps_pollicis": ("Princeps pollicis artery", ["FJ2371"], "Radial artery", "The thumb", "", None),
    "radialis_indicis": ("Radialis indicis artery", ["FJ2342"], "Radial artery", "The lateral side of the index finger", "", None),
    "palmar_digital": ("Common and proper palmar digital arteries", ["FJ2343", "FJ2344", "FJ2345", "FJ2370", "FJ2364", "FJ2365", "FJ2366", "FJ2367", "FJ2368", "FJ2369"],
                       "Superficial palmar arch", "Common palmar digital arteries divide into proper palmar digital arteries along the fingers", "", None),
    "palmar_metacarpal": ("Palmar metacarpal arteries", ["FJ2289"], "Deep palmar arch", "Three, from the deep arch", "", None),
    "internal_iliac": ("Internal iliac artery", ["FJ3569"], "Common iliac artery", "Gives the superior and inferior gluteal, internal pudendal and obturator arteries", "", None),
    "sup_gluteal": ("Superior gluteal artery", [], "Internal iliac artery (its largest and final branch)",
                    "Gluteal region: leaves the pelvis through the greater sciatic foramen above piriformis, with the superior gluteal nerve and vein", "", None),
    "inf_gluteal": ("Inferior gluteal artery", [], "Internal iliac artery",
                    "Gluteal region: leaves the pelvis through the greater sciatic foramen below piriformis, with the inferior gluteal nerve and vein; supplies the posterior thigh too",
                    "Part of the cruciate anastomosis round the hip with the medial and lateral circumflex and 1st perforating arteries", None),
    "internal_pudendal": ("Internal pudendal artery", [], "Internal iliac artery",
                          "Out the greater sciatic foramen below piriformis, then into the perineum through the lesser; supplies the perineum. The pudendal nerve (S2-S4) runs with it", "", None),
    "obturator": ("Obturator artery", [], "Internal iliac artery", "Medial compartment of the thigh, with the perforating branches", "", None),
    "external_iliac": ("External iliac artery", ["FJ3567"], "Common iliac artery", "Becomes the femoral artery under the inguinal ligament", "", None),
    "femoral": ("Femoral artery", ["FJ2143"], "External iliac artery, under the inguinal ligament",
                "Anterior thigh. In the femoral triangle (NAVEL, lateral to medial: nerve, artery, vein, empty canal, lymphatics), inside the femoral sheath; becomes the popliteal artery after the adductor hiatus",
                "Superficial in the femoral triangle, so easily injured; the femoral pulse", None),
    "deep_femoral": ("Deep femoral (profunda femoris) artery", [], "Femoral artery, an early branch",
                     "Its perforating branches (usually 3-4) pierce adductor magnus to the posterior thigh and supply all three compartments; gives the medial and lateral circumflex femoral arteries", "", None),
    "perforating": ("Perforating arteries", ["FJ2090"], "Deep femoral artery",
                    "Pierce adductor magnus to the posterior thigh; supply the medial and posterior compartments (the posterior compartment has no artery of its own)", "", None),
    "med_circumflex_femoral": ("Medial circumflex femoral artery", [], "Deep femoral artery",
                               "Most of the femoral head and neck",
                               "Cruciate anastomosis (medial and lateral circumflex, inferior gluteal, 1st perforating) keeps the leg alive after femoral artery ligation", None),
    "lat_circumflex_femoral": ("Lateral circumflex femoral artery", ["FJ2158", "FJ2057"], "Deep femoral artery",
                               "Lateral thigh: an ascending branch to the femoral neck, a transverse one round the femur and a descending one to the knee (the knee's collateral circulation)", "", None),
    "popliteal": ("Popliteal artery", ["FJ2170"], "Femoral artery, after the adductor hiatus",
                  "Through the popliteal fossa, deepest of artery, vein, nerve (AVN); splits at its lower border into the anterior and posterior tibial arteries",
                  "Popliteal aneurysm is the most common peripheral aneurysm: embolism, thrombosis, rupture; 80% have no symptoms", None),
    "ant_tibial": ("Anterior tibial artery", ["FJ2130"], "Popliteal artery",
                   "Through a gap at the top of the interosseous membrane into the anterior compartment with the deep fibular nerve, between tibialis anterior and extensor digitorum longus; becomes dorsalis pedis between the malleoli", "", None),
    "post_tibial": ("Posterior tibial artery", ["FJ2172"], "Popliteal artery",
                    "Deep posterior compartment with the tibial nerve, between flexor digitorum longus and tibialis posterior; behind the medial malleolus through the tarsal tunnel (Tom, Dick, And Not Harry) into the medial and lateral plantar arteries",
                    "Pulse between the medial malleolus and the Achilles tendon; invert the foot to relax the flexor retinaculum", None),
    "fibular": ("Fibular artery", [], "Posterior tibial artery, its largest branch",
                "Down toward the fibula within flexor hallucis longus; muscular branches to the posterior and lateral compartments", "", None),
    "dorsalis_pedis": ("Dorsalis pedis artery", ["FJ2055", "FJ2133", "FJ2163"], "Anterior tibial artery, past the malleoli",
                       "Dorsum of the foot, with the deep fibular nerve: lateral tarsal and arcuate branches; the deep plantar artery dives between metatarsals 1 and 2 to the sole",
                       "Pulse lateral to the extensor hallucis longus tendon; diminished or absent = peripheral arterial disease", None),
    "deep_plantar": ("Deep plantar artery", ["FJ2136"], "Dorsalis pedis artery", "Dives between the 1st and 2nd metatarsals to complete the deep plantar arch", "", None),
    "lat_plantar": ("Lateral plantar artery", ["FJ2159", "FJ2058"], "Posterior tibial artery", "Runs along the lateral sole, then arches medially as the deep plantar arch", "", None),
    "med_plantar": ("Medial plantar artery", ["FJ2164"], "Posterior tibial artery", "Medial sole and big toe; contributes to the deep plantar arch", "", None),
    "plantar_arch": ("Deep plantar arch", ["FJ2169"], "Lateral plantar artery, completed by the deep plantar artery",
                     "Gives four plantar metatarsal arteries, which go on as the digital arteries", "", None),
    "foot_digital": ("Digital arteries of the foot", ["FJ2072", "FJ2093"], "Plantar and dorsal metatarsal arteries", "The toes", "", None),
}
GROUPS = [
    ["Neck and shoulder", ["vertebral", "subclavian", "dorsal_scapular", "suprascapular", "axillary", "thoracoacromial", "subscapular",
                           "thoracodorsal", "circumflex_scapular", "ant_circumflex_humeral", "post_circumflex_humeral"]],
    ["Arm and elbow", ["brachial", "deep_brachial", "sup_ulnar_collateral", "inf_ulnar_collateral", "radial_recurrent", "ant_ulnar_recurrent", "post_ulnar_recurrent"]],
    ["Forearm and hand", ["radial", "ulnar", "common_interosseous", "ant_interosseous", "post_interosseous", "sup_palmar_arch", "deep_palmar_arch",
                          "princeps_pollicis", "radialis_indicis", "palmar_digital", "palmar_metacarpal"]],
    ["Pelvis and hip", ["internal_iliac", "sup_gluteal", "inf_gluteal", "internal_pudendal", "obturator", "external_iliac"]],
    ["Thigh and knee", ["femoral", "deep_femoral", "perforating", "med_circumflex_femoral", "lat_circumflex_femoral", "popliteal"]],
    ["Leg and foot", ["ant_tibial", "post_tibial", "fibular", "dorsalis_pedis", "deep_plantar", "lat_plantar", "med_plantar", "plantar_arch", "foot_digital"]],
]


def top_down(line: np.ndarray) -> np.ndarray:
    return line if line[0, 2] > line[-1, 2] else line[::-1]


def drawn_paths(sk: Skeleton, V) -> dict:
    """Tubes for the arteries BodyParts3D lacks, placed from bones and the arteries they branch from (mm)."""
    fem, fib = sk.find(r"right femur"), sk.find(r"right fibula")
    hip, sacrum = sk.find(r"right hip bone"), sk.find(r"^sacrum")
    rad, uln = sk.find(r"right radius"), sk.find(r"right ulna")

    def shaft(bone: np.ndarray, s: float) -> np.ndarray:
        """Centre of a long bone's cross-section a fraction s from its top."""
        z = bone[:, 2].max() - s * (bone[:, 2].max() - bone[:, 2].min())
        return bone[np.abs(bone[:, 2] - z) < 6].mean(axis=0)

    F = top_down(centerline(V("FJ2143"), 10))
    II = top_down(centerline(V("FJ3569"), 6))
    PT = top_down(centerline(V("FJ2172"), 12))
    CI = V("FJ2275").mean(axis=0)

    # femoral neck: between the head (most medial top of the femur) and the greater trochanter
    top = fem[fem[:, 2] > fem[:, 2].max() - 60]
    head = top[np.argmax(top[:, 0])]
    troch = top[np.argmin(top[:, 0])]
    neck = (head + troch) / 2
    # greater sciatic notch: the back of the hip bone, beside the sacrum, at the level of the sacrum's upper half
    sz = sacrum[:, 2].max() - 0.35 * (sacrum[:, 2].max() - sacrum[:, 2].min())
    band = hip[(np.abs(hip[:, 2] - sz) < 12) & (hip[:, 0] < sacrum[:, 0].min() - 5)]
    notch = band[np.argmax(band[:, 1])]
    isch = hip[np.argmin(hip[:, 2])]  # ischial tuberosity
    pubic = hip[np.argmax(hip[:, 0])]  # the symphysis end of the pubis
    obt = isch * 0.45 + pubic * 0.55 + [-12, 0, 20]  # obturator foramen, roughly
    ii_end = II[-1]

    df0 = along(F, 0.12)
    DF = [df0, df0 + [6, 14, -25], shaft(fem, 0.25) + [16, 14, 0], shaft(fem, 0.42) + [14, 16, 0], shaft(fem, 0.6) + [12, 14, 0]]
    mc0 = along(np.array(DF), 0.05)
    return {
        "deep_femoral": [DF],
        "med_circumflex_femoral": [[mc0, mc0 + [12, 10, 2], neck + [18, 6, -22], neck + [8, 26, -12], neck + [-14, 28, 0]]],
        "sup_gluteal": [[ii_end, notch + [6, -8, 18], notch + [-6, 10, 26], notch + [-40, 24, 38], notch + [-70, 30, 40]],
                        [notch + [-40, 24, 38], notch + [-60, 22, 10]]],
        "inf_gluteal": [[ii_end, notch + [6, -6, -10], notch + [-4, 14, -30], notch + [-20, 34, -60], isch + [-20, 36, -20]]],
        "internal_pudendal": [[ii_end + [2, 0, -6], notch + [8, -2, -22], notch + [2, 12, -48], isch + [18, 8, 18], isch + [40, -10, 6], pubic + [-6, 0, -30]]],
        "obturator": [[ii_end + [0, -10, 4], (ii_end + obt) / 2 + [-10, -10, 0], obt, obt + [-10, -20, -25], obt + [-25, -25, -70]]],
        "fibular": [[along(PT, 0.1), shaft(fib, 0.2) + [14, 12, 0], shaft(fib, 0.45) + [12, 10, 0], shaft(fib, 0.7) + [10, 8, 0], shaft(fib, 0.88) + [10, 10, 0]]],
        "post_interosseous": [[CI, CI + [4, 12, -12], (shaft(rad, 0.22) + shaft(uln, 0.22)) / 2 + [0, 16, 0],
                               (shaft(rad, 0.5) + shaft(uln, 0.5)) / 2 + [0, 14, 0], (shaft(rad, 0.8) + shaft(uln, 0.8)) / 2 + [0, 12, 0]]],
    }


def main(bp3d_dir: Path) -> None:
    obj_dir = bp3d_dir / "objs" / "isa_BP3D_4.0_obj_99"
    sk = Skeleton(bp3d_dir, obj_dir)
    V = lambda fid: load(obj_dir, fid).vertices
    # only the arteries this year's slides name, with what the slides say about them (slides_merge.py)
    slides = json.loads((HERE / "slides.json").read_text(encoding="utf-8"))["arteries"]
    scene = trimesh.Scene()
    info, faces = {}, 0
    for aid, (name, meshes, frm, text, clinical, pattern) in ARTERIES.items():
        if aid not in slides:
            continue
        for n, fid in enumerate(meshes):
            m = simplify(load(obj_dir, fid))
            if fid in MIRROR:
                m.vertices[:, 0] *= -1
                m.invert()
            faces += len(m.faces)
            scene.add_geometry(m.apply_transform(Y_UP), node_name=f"ar_{aid}_{n}", geom_name=f"ar_{aid}_{n}")
        facts = [f for f in slides[aid]["facts"] if "overview" not in f]  # drop "it is on the overview diagram" filler
        info[aid] = {"name": name, "facts": facts, "src": slides[aid]["src"], "drawn": not meshes}
    drawn = {k: [to_three(np.array(p, float)) for p in ps] for k, ps in drawn_paths(sk, V).items() if k in info}
    scene.export(HERE / "arteries.glb")
    groups = [[t, [i for i in ids if i in info]] for t, ids in GROUPS]
    (HERE / "arteries.json").write_text(json.dumps({"info": info, "drawn": drawn, "groups": [g for g in groups if g[1]]}, ensure_ascii=False))
    log.info("arteries.glb: %.1f MB, %d faces; %d arteries (%d drawn)", (HERE / "arteries.glb").stat().st_size / 1e6, faces, len(info), len(drawn))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
