"""
Purpose: Build the spine view for the dermatome prototype: real vertebrae, discs, sacrum and hip
         bones from BodyParts3D, plus a drawn spinal cord and the 31 pairs of spinal nerve roots,
         each leaving through the gap (intervertebral foramen) it really exits by.
Author: nsimsam, with Claude Code
Date: 2026-10-19
Input: the BodyParts3D 4.0 "is_a" OBJ archive unzipped at BP3D_DIR
       (https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip)
Output: dermatomes/spine.glb (bones) and dermatomes/roots.json (cord and root paths), in metres, Y up
Usage: python build_spine.py <BP3D_DIR>   (needs trimesh, fast-simplification, numpy)
"""

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
KEEP_FRACTION = 0.45  # share of triangles kept when simplifying each bone

VERTEBRAE = {
    "C1": "FJ3176", "C2": "FJ3177", "C3": "FJ3161", "C4": "FJ3164", "C5": "FJ3167", "C6": "FJ3170", "C7": "FJ3172",
    "T1": "FJ3158", "T2": "FJ3160", "T3": "FJ3163", "T4": "FJ3166", "T5": "FJ3169", "T6": "FJ3171", "T7": "FJ3173",
    "T8": "FJ3174", "T9": "FJ3175", "T10": "FJ3154", "T11": "FJ3155", "T12": "FJ3156",
    "L1": "FJ3157", "L2": "FJ3159", "L3": "FJ3162", "L4": "FJ3165", "L5": "FJ3168",
}
SACRUM = "FJ3393"
HIPS = {"hip_right": "FJ3152", "hip_left": "FJ3288"}
DISCS = [f"FJ{n}" for n in range(3202, 3225)]
ORDER = list(VERTEBRAE)

# Spinal cord segments sit higher than the vertebrae of the same name (the cord ends near L1/L2).
# Each segment is placed by a fraction along the vertebral column: (segment, vertebra, 0 = top, 1 = bottom of it).
SEGMENT_ANCHORS = [
    ("C1", "C1", 0.0), ("C8", "C7", 0.3), ("T1", "C7", 0.9), ("T6", "T4", 0.5), ("T12", "T9", 0.8),
    ("L1", "T10", 0.4), ("L5", "T11", 0.9), ("S1", "T12", 0.3), ("S5", "L1", 0.9),
]
SEGMENTS = (
    [f"C{i}" for i in range(1, 9)] + [f"T{i}" for i in range(1, 13)]
    + [f"L{i}" for i in range(1, 6)] + [f"S{i}" for i in range(1, 6)] + ["Co1"]
)


def load(file_id: str, bp3d_dir: Path) -> trimesh.Trimesh:
    """Load one BodyParts3D OBJ (millimetres, Z up, -Y anterior)."""
    return trimesh.load(bp3d_dir / f"{file_id}.obj", process=True, force="mesh")


def simplify(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Cut the triangle count so the page loads quickly on a phone."""
    v, f = fast_simplification.simplify(mesh.vertices, mesh.faces, 1 - KEEP_FRACTION)
    return trimesh.Trimesh(v, f, process=True)


def to_three(p: np.ndarray) -> np.ndarray:
    """BodyParts3D millimetres, Z up -> metres, Y up, front facing +Z (three.js convention)."""
    p = np.asarray(p, dtype=float)
    return np.stack([p[..., 0], p[..., 2], -p[..., 1]], axis=-1) / 1000.0


def canal(mesh: trimesh.Trimesh) -> dict:
    """
    Find the spinal canal of one vertebra: the biggest front-to-back gap among bone points near the midline,
    and how wide it is sideways.

    Returns
    -------
    dict
        y (front-back centre), half_width, top, bottom, body_back (back surface of the vertebral body), in mm.
    """
    v = mesh.vertices
    z0, z1 = v[:, 2].min(), v[:, 2].max()
    mid = v[(v[:, 2] > z0 + 0.3 * (z1 - z0)) & (v[:, 2] < z1 - 0.3 * (z1 - z0))]
    near = mid[np.abs(mid[:, 0]) < 4]
    ys = np.sort(near[:, 1])
    gaps = np.diff(ys)
    i = int(np.argmax(gaps))
    front, back = ys[i], ys[i + 1]
    cy = (front + back) / 2
    row = mid[np.abs(mid[:, 1] - cy) < 4]
    left = row[row[:, 0] > 0][:, 0]
    right = row[row[:, 0] < 0][:, 0]
    half = (min(left.min() if len(left) else 12, -(right.max() if len(right) else -12)))
    return {"y": cy, "half_width": max(half, 6.0), "top": z1, "bottom": z0, "body_back": front}


def main(bp3d_dir: Path) -> None:
    scene = trimesh.Scene()
    info = {}
    for name, fid in VERTEBRAE.items():
        mesh = load(fid, bp3d_dir)
        info[name] = canal(mesh)
        scene.add_geometry(simplify(mesh).apply_transform(Y_UP), node_name=name, geom_name=name)
    sacrum = load(SACRUM, bp3d_dir)
    scene.add_geometry(simplify(sacrum).apply_transform(Y_UP), node_name="sacrum", geom_name="sacrum")
    for name, fid in HIPS.items():
        scene.add_geometry(simplify(load(fid, bp3d_dir)).apply_transform(Y_UP), node_name=name, geom_name=name)
    for fid in DISCS:
        path = bp3d_dir / f"{fid}.obj"
        if path.exists():
            scene.add_geometry(simplify(load(fid, bp3d_dir)).apply_transform(Y_UP), node_name=f"disc_{fid}", geom_name=f"disc_{fid}")
    scene.export(OUT_DIR / "spine.glb")
    log.info("spine.glb: %.1f MB", (OUT_DIR / "spine.glb").stat().st_size / 1e6)

    # the column as a list of heights: canal centre per vertebra
    def z_at(vert: str, frac: float) -> float:
        c = info[vert]
        return c["top"] - frac * (c["top"] - c["bottom"])

    anchors = [(SEGMENTS.index(s), z_at(v, f)) for s, v, f in SEGMENT_ANCHORS]
    seg_z = np.interp(range(len(SEGMENTS)), [a[0] for a in anchors], [a[1] for a in anchors])

    def canal_y(z: float) -> float:
        zs = [info[v]["top"] / 2 + info[v]["bottom"] / 2 for v in ORDER]
        return float(np.interp(-z, [-q for q in zs], [info[v]["y"] for v in ORDER]))

    cord_top = info["C1"]["top"] + 12
    conus = seg_z[SEGMENTS.index("S5")] - 6
    cord = [[0.0, canal_y(z), z] for z in np.linspace(cord_top, conus, 40)]
    radius = lambda z: 4.2 if z > info["T1"]["bottom"] else 3.4  # cervical enlargement is thicker

    # where each root leaves: the gap below the vertebra it is named after (C1-C7 leave above theirs)
    def foramen(root: str) -> tuple:
        if root == "C1":
            v = info["C1"]; return v["top"] + 3, v
        if root.startswith("C") and root != "C8":
            n = int(root[1:]); v = info[f"C{n}"]; up = info[f"C{n-1}"]
            return (v["top"] + up["bottom"]) / 2, v
        if root == "C8":
            return (info["C7"]["bottom"] + info["T1"]["top"]) / 2, info["C7"]
        if root[0] in "TL" and root != "L5":
            i = ORDER.index(root)
            return (info[root]["bottom"] + info[ORDER[i + 1]]["top"]) / 2, info[root]
        if root == "L5":
            return info["L5"]["bottom"] - 4, info["L5"]
        return None, None

    s_top, s_bot = sacrum.bounds[1][2], sacrum.bounds[0][2]
    sac_y = float(np.median(sacrum.vertices[np.abs(sacrum.vertices[:, 0]) < 5][:, 1]))
    roots = []
    for k, root in enumerate(SEGMENTS):
        z_cord = seg_z[k] if root != "Co1" else conus - 2
        for side in (-1, 1):
            start = [side * radius(z_cord) * 0.9, canal_y(z_cord), z_cord]
            if root in ("S1", "S2", "S3", "S4", "S5", "Co1"):
                # sacral roots run down the sacral canal and leave through the sacral foramina
                j = ["S1", "S2", "S3", "S4", "S5", "Co1"].index(root)
                zf = s_top - (0.16 + 0.15 * j) * (s_top - s_bot)
                lat = max(26 - 3.5 * j, 8)
                yin = sac_y - 6 + 2 * j
                path = [start, [side * 3, canal_y(min(z_cord, info["L5"]["bottom"])), info["L5"]["bottom"] - 2],
                        [side * lat * 0.5, yin, zf + 6], [side * lat, yin - 14, zf - 2], [side * (lat + 14), yin - 30, zf - 16]]
            else:
                zf, v = foramen(root)
                y_f = v["body_back"] + 4
                w = v["half_width"] + 3
                drop = max(z_cord - zf, 0)
                path = [start]
                if drop > 18:   # long descent inside the canal: the cauda equina below the cord's end
                    path.append([side * (w - 4), canal_y(zf + 8), zf + 10])
                lumbar = root[0] == "L"
                path += [[side * w, y_f, zf], [side * (w + 16), y_f - (3 if lumbar else 8), zf - (12 if lumbar else 8)],
                         [side * (w + 32), y_f - (6 if lumbar else 20), zf - (30 if lumbar else 20)]]
            roots.append({"root": root, "side": side, "path": to_three(np.array(path)).round(4).tolist()})
    data = {
        "cord": to_three(np.array(cord)).round(4).tolist(),
        "cord_radius": [round(radius(z) / 1000, 4) for z in np.linspace(cord_top, conus, 40)],
        "roots": roots,
        "vertebrae": {v: to_three(np.array([0, info[v]["y"] - 40, (info[v]["top"] + info[v]["bottom"]) / 2])).round(4).tolist() for v in ORDER},
        "conus_vertebra": "L1",
    }
    (OUT_DIR / "roots.json").write_text(json.dumps(data))
    log.info("roots.json: %d roots", len(roots))


Y_UP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float) @ np.diag([0.001, 0.001, 0.001, 1])

if __name__ == "__main__":
    main(Path(sys.argv[1]))
