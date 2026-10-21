"""
Purpose: Build the 3D body for the body-map prototype: the whole skeleton from BodyParts3D, the
         right-side muscles and tendons the MSK charts talk about, and drawn ligaments, bursae and
         nerves (BodyParts3D has almost no ligaments) placed from landmarks on the real bones.
Author: nsimsam, with Claude Code
Date: 2026-10-21
Input: the BodyParts3D 4.0 "is_a" OBJ archive unzipped at BP3D_DIR, with isa_element_parts.txt beside
       the objs/ folder (https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip)
Output: body-map/body.glb (bones named bone_<FJ id>, muscles named st_<key>) and body-map/body.json
        (drawn structures and region anchors), in metres, Y up, front facing +Z
Usage: python build_body.py <BP3D_DIR>   (needs trimesh, fast-simplification, numpy)
"""

import csv
import json
import logging
import sys
from pathlib import Path

import fast_simplification
import numpy as np
import trimesh

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

OUT_DIR = Path(__file__).parent
TARGET_FACES = 2500  # bones above this are simplified down towards it, so the page loads on a phone
MIN_KEEP = 0.12

# Right-side bones the landmarks are taken from (BodyParts3D: millimetres, Z up, -X is the body's right, -Y anterior)
BONE = {
    "humerus": "FJ3368", "ulna": "FJ3391", "radius": "FJ3349", "scapula": "FJ3384", "clavicle": "FJ3362",
    "hip": "FJ3152", "femur": "FJ3365", "tibia": "FJ3387", "fibula": "FJ3366", "patella": "FJ3381",
    "talus": "FJ3385", "calcaneus": "FJ3360", "capitate": "FJ3361", "pisiform": "FJ3382", "hamate": "FJ3367",
    "scaphoid": "FJ3383", "mt1": "FJ3351", "mt2": "FJ3353", "mt3": "FJ3355", "mt4": "FJ3357", "mt5": "FJ3359",
    "c4": "FJ3164", "l3": "FJ3162",
}

# Right-side muscles and tendons that are their own structure: key -> BodyParts3D file
MUSCLES = {
    "supraspinatus": "FJ1506", "infraspinatus": "FJ1500", "teres_minor": "FJ1508", "subscapularis": "FJ1504",
    "biceps_long_head": "FJ1478", "ecrb": "FJ1489", "fcu_humeral": "FJ1473", "pronator_teres": "FJ1474",
    "flexor_retinaculum": "FJ1471", "piriformis": "FJ1428", "gluteus_medius": "FJ1419", "itb": "FJ1423",
    "achilles": "FJ1405", "tibialis_posterior": "FJ1440",
}


def load(file_id: str, obj_dir: Path) -> trimesh.Trimesh:
    """Load one BodyParts3D OBJ."""
    return trimesh.load(obj_dir / f"{file_id}.obj", process=True, force="mesh")


def simplify(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Cut big meshes towards TARGET_FACES triangles; small ones are left alone."""
    n = len(mesh.faces)
    if n <= TARGET_FACES:
        return mesh
    keep = max(TARGET_FACES / n, MIN_KEEP)
    v, f = fast_simplification.simplify(mesh.vertices, mesh.faces, 1 - keep)
    return trimesh.Trimesh(v, f, process=True)


def to_three(p) -> list:
    """BodyParts3D millimetres, Z up -> metres, Y up, front facing +Z (three.js convention)."""
    p = np.asarray(p, dtype=float)
    return (np.stack([p[..., 0], p[..., 2], -p[..., 1]], axis=-1) / 1000.0).round(4).tolist()


Y_UP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float) @ np.diag([0.001, 0.001, 0.001, 1])


class Bone:
    """Landmark helpers on one bone's vertices."""

    def __init__(self, mesh: trimesh.Trimesh):
        self.v = mesh.vertices
        self.lo, self.hi = mesh.bounds

    def slab(self, z0: float, z1: float) -> np.ndarray:
        """Vertices with z between z0 and z1 (absolute mm)."""
        return self.v[(self.v[:, 2] >= z0) & (self.v[:, 2] <= z1)]

    def top(self, depth: float) -> np.ndarray:
        return self.slab(self.hi[2] - depth, self.hi[2])

    def bottom(self, depth: float) -> np.ndarray:
        return self.slab(self.lo[2], self.lo[2] + depth)

    def mid(self) -> np.ndarray:
        return self.v.mean(axis=0)


def extreme(pts: np.ndarray, axis: int, most: bool) -> np.ndarray:
    """The point furthest along an axis (most=True: largest value)."""
    return pts[np.argmax(pts[:, axis])] if most else pts[np.argmin(pts[:, axis])]


def ring(centre, normal, radius: float, arc: float = 2 * np.pi, start: float = 0.0, n: int = 28) -> list:
    """Points on a circle (or arc) around centre, in the plane normal to `normal` (all mm)."""
    normal = np.asarray(normal, float) / np.linalg.norm(normal)
    a = np.cross(normal, [0, 0, 1] if abs(normal[2]) < 0.9 else [1, 0, 0])
    a /= np.linalg.norm(a)
    b = np.cross(normal, a)
    t = np.linspace(start, start + arc, n)
    return (np.asarray(centre)[None] + radius * (np.cos(t)[:, None] * a + np.sin(t)[:, None] * b)).tolist()


def main(bp3d_dir: Path) -> None:
    obj_dir = bp3d_dir / "objs" / "isa_BP3D_4.0_obj_99"
    with open(bp3d_dir / "isa_element_parts.txt") as fh:
        bones = sorted({r[2] for r in csv.reader(fh, delimiter="\t") if r[1] == "bone organ"})
    bones += ["FJ3290", "FJ3178", "FJ3153"]  # the sternum (manubrium, body, xiphoid) is filed as zones, not as a "bone organ"

    scene = trimesh.Scene()
    faces = 0
    for fid in bones:
        m = simplify(load(fid, obj_dir))
        faces += len(m.faces)
        scene.add_geometry(m.apply_transform(Y_UP), node_name=f"bone_{fid}", geom_name=f"bone_{fid}")
    for key, fid in MUSCLES.items():
        m = simplify(load(fid, obj_dir))
        faces += len(m.faces)
        scene.add_geometry(m.apply_transform(Y_UP), node_name=f"st_{key}", geom_name=f"st_{key}")
    scene.export(OUT_DIR / "body.glb")
    log.info("body.glb: %d bones, %d muscles, %d triangles, %.1f MB", len(bones), len(MUSCLES), faces,
             (OUT_DIR / "body.glb").stat().st_size / 1e6)

    b = {k: Bone(load(fid, obj_dir)) for k, fid in BONE.items()}
    MED, LAT = True, False  # on the right side, medial is +X (towards the midline)

    # Elbow
    hum, uln, rad = b["humerus"], b["ulna"], b["radius"]
    dist_hum = hum.bottom(45)
    med_epi = extreme(dist_hum, 0, MED)
    lat_epi = extreme(dist_hum, 0, LAT)
    sublime = extreme(uln.slab(uln.hi[2] - 55, uln.hi[2] - 25), 0, MED)
    olecranon = extreme(uln.top(20), 1, True)
    rad_head = rad.top(14).mean(axis=0)
    rad_tub = extreme(rad.slab(rad.hi[2] - 45, rad.hi[2] - 25), 1, False)
    hum_front = extreme(hum.slab(hum.lo[2] + 90, hum.lo[2] + 110), 1, False)

    # Shoulder
    head_med = extreme(hum.top(60), 0, MED)
    sc = b["scapula"].v
    glenoid = sc[np.argmin(np.linalg.norm(sc - head_med, axis=1))]
    ac = extreme(b["clavicle"].v, 0, LAT)

    # Wrist
    pis, ham = b["pisiform"].mid(), extreme(b["hamate"].v, 1, False)

    # Hip
    fem = b["femur"]
    fem_head = extreme(fem.top(70), 0, MED)
    hp = b["hip"].v
    acetab = hp[np.argmin(np.linalg.norm(hp - fem_head, axis=1))]
    fem_head_c = fem.top(60)[fem.top(60)[:, 0] > fem_head[0] - 45].mean(axis=0)

    # Knee
    tib, fib = b["tibia"], b["fibula"]
    plateau = tib.top(8).mean(axis=0)
    zj = tib.hi[2]
    pw = np.ptp(tib.top(8)[:, 0])
    fem_med_epi = extreme(fem.slab(fem.lo[2] + 25, fem.lo[2] + 55), 0, MED)
    fem_lat_epi = extreme(fem.slab(fem.lo[2] + 25, fem.lo[2] + 55), 0, LAT)
    tib_med = extreme(tib.slab(zj - 70, zj - 50), 0, MED)
    fib_head = extreme(fib.top(15), 0, LAT)
    patella_front = extreme(b["patella"].v, 1, False)
    tib_back = extreme(tib.top(20), 1, True)

    # Ankle and foot
    fib_tip = extreme(fib.bottom(20), 2, False)
    talus_neck = extreme(b["talus"].v[b["talus"].v[:, 1] < b["talus"].mid()[1]], 0, LAT)
    calc_tub = b["calcaneus"].bottom(12)
    calc_tub = calc_tub[calc_tub[:, 1] > np.percentile(calc_tub[:, 1], 60)].mean(axis=0)

    def mt_head(k: str) -> np.ndarray:
        v = b[k].v
        return v[v[:, 1] < v[:, 1].min() + 10].mean(axis=0)

    heads = {k: mt_head(k) for k in ("mt1", "mt2", "mt3", "mt4", "mt5")}

    def tube(key, pts, r):
        return {"key": key, "kind": "tube", "path": to_three(pts), "r": r / 1000}

    def ball(key, c, r, squash=(1, 1, 1)):
        return {"key": key, "kind": "ball", "c": to_three(c), "r": r / 1000, "squash": list(squash)}

    def loop(key, pts, r, closed=True):
        return {"key": key, "kind": "tube", "path": to_three(pts), "r": r / 1000, "closed": closed}

    up = np.array([0, 0, 1.0])
    drawn = [
        tube("ucl", [med_epi + [-2, 0, -4], (med_epi + sublime) / 2 + [3, 0, 0], sublime + [2, 0, 0]], 3.2),
        ball("olecranon_bursa", olecranon + [0, 9, -6], 11, (1, 1.1, 0.6)),
        loop("annular_ligament", ring(rad_head + [0, 0, -6], up, 13), 2.4),
        tube("distal_biceps", [rad_tub, rad_tub + [8, -18, 30], hum_front + [5, -22, 0]], 3.5),
        tube("ulnar_nerve_elbow", [med_epi + [-6, 25, 90], med_epi + [2, 10, 0], sublime + [4, 8, -40], sublime + [-4, -4, -120]], 2.2),
        loop("glenoid_labrum", ring(glenoid, head_med - glenoid, 16), 2.6),
        ball("ac_joint", ac, 9),
        tube("guyon_canal", [pis + [-3, -8, 22], (pis + ham) / 2 + [0, -6, 0], pis + [-6, -8, -24]], 3.2),
        loop("acetabular_labrum", ring(acetab, fem_head - acetab, 26), 3.2),
        tube("acl", [plateau + [-8, 12, 26], plateau + [-2, 2, 12], plateau + [2, -10, 1]], 3.6),
        tube("pcl", [plateau + [9, -6, 26], plateau + [5, 6, 12], plateau + [0, 20, -6]], 3.8),
        tube("mcl", [fem_med_epi + [2, 0, 4], (fem_med_epi + tib_med) / 2 + [5, 0, 0], tib_med + [2, 0, 0]], 3.6),
        tube("lcl", [fem_lat_epi + [-2, 0, 4], (fem_lat_epi + fib_head) / 2 + [-5, 0, 0], fib_head + [-1, 0, 2]], 3.2),
        loop("medial_meniscus", ring(plateau + [pw * 0.24, 0, 3], up, pw * 0.2, arc=1.6 * np.pi, start=0.7 * np.pi), 3.4, closed=False),
        loop("lateral_meniscus", ring(plateau + [-pw * 0.24, 0, 3], up, pw * 0.18, arc=1.75 * np.pi, start=-0.6 * np.pi), 3.4, closed=False),
        ball("prepatellar_bursa", patella_front + [0, -7, 0], 14, (1, 0.45, 1.2)),
        ball("bakers_cyst", tib_back + [12, 18, 10], 15),
        tube("atfl", [fib_tip + [0, -6, 6], talus_neck + [-3, 0, 0]], 3.2),
        tube("plantar_fascia", [calc_tub + [0, 0, -3], heads["mt1"] * 0.35 + heads["mt5"] * 0.15 + calc_tub * 0.5 + [0, 0, -9],
                                (heads["mt2"] + heads["mt3"] + heads["mt4"]) / 3 + [0, 4, -6]], 4.5),
        ball("first_mtp", heads["mt1"] + [5, -6, 0], 11),
        ball("mortons", (heads["mt3"] + heads["mt4"]) / 2 + [0, 2, -8], 6),
        ball("femoral_neck", (fem_head_c * 0.55 + fem.top(110).mean(axis=0) * 0.45), 13, (1.3, 1, 1)),
        ball("distal_radius", rad.bottom(25).mean(axis=0), 14, (1.1, 1, 1)),
        ball("scaphoid", b["scaphoid"].mid(), 9),
    ]

    anchors = {
        "neck": b["c4"].mid() + [0, 40, 0],
        "back": b["l3"].mid() + [0, 40, 0],
        "shoulder": hum.top(40).mean(axis=0),
        "arm": hum.mid(),
        "elbow": (med_epi + lat_epi) / 2,
        "forearm": (rad.mid() + uln.mid()) / 2,
        "hand": b["capitate"].mid(),
        "hip": fem_head_c,
        "knee": plateau + [0, 0, 10],
        "leg": tib.mid(),
        "foot": b["talus"].mid(),
    }
    data = {"drawn": drawn, "anchors": {k: to_three(v) for k, v in anchors.items()}}
    (OUT_DIR / "body.json").write_text(json.dumps(data))
    log.info("body.json: %d drawn structures, %d anchors", len(drawn), len(anchors))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
