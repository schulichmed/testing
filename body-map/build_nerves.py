"""
Purpose: Build the two nerve views of the body map:
         1. Cranial nerves: a drawn brainstem with the twelve nerves (right side) running from where they
            leave the brain, through the opening they leave the skull by, to what they supply. Where
            BodyParts3D has the nerve itself (the optic and trochlear nerves, the oculomotor and
            ophthalmic branches in the orbit) the real mesh is used; the rest is drawn from landmarks.
         2. Brachial plexus (right side): roots from their real intervertebral foramina, trunks between
            the scalenes, divisions behind the clavicle, cords around the axillary artery and the branches
            down the arm alongside the arteries they travel with (BodyParts3D has the arteries, not the nerves).
Author: nsimsam, with Claude Code
Date: 2026-10-21
Input: the BodyParts3D 4.0 "is_a" OBJ archive unzipped at BP3D_DIR; dermatomes/roots.json (spinal root paths);
       anatomy-tables/plexus.html (the plexus tab's structures and notes, read with node);
       anatomy-tables/netter_upper_limb.json (each nerve's exact muscles and their blood supply)
Output: body-map/nerves.glb (real meshes: cn_<nerve>_<n>, ctx_<name>) and body-map/nerves.json
        (drawn paths, brainstem shapes, label points, plexus data); metres, Y up, front facing +Z
Usage: python build_nerves.py <BP3D_DIR>   (needs trimesh, fast-simplification, numpy, scipy; node)

Drawn courses are approximate: they follow the textbook route between real landmarks.
"""

import json
import logging
import re
import subprocess
import sys
from pathlib import Path

import fast_simplification
import numpy as np
import trimesh
from scipy.spatial import cKDTree

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent
Y_UP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float) @ np.diag([0.001, 0.001, 0.001, 1])
MESH_FACES = 1500

# Real right-side cranial nerve meshes in the orbit: nerve -> BodyParts3D files
CN_MESHES = {
    "II": ["FJ1364", "FJ1313"],  # both optic nerves, so the chiasm is whole
    "III": ["FJ1344", "FJ1372"],  # inferior and superior branches
    "IV": ["FJ1381"],  # the whole trochlear nerve, from the back of the midbrain to the superior oblique
    "V": ["FJ1363", "FJ1341", "FJ1376", "FJ1377", "FJ1351", "FJ1361", "FJ1369", "FJ1347", "FJ1333", "FJ1366", "FJ1362"],
}
# What the nerves run to or beside, shown faintly: name -> file
CONTEXT = {
    "eye": "FJ1368", "lateral_rectus": "FJ1355", "superior_oblique": "FJ1373", "tongue": "FJ2761",
    "sternocleidomastoid": "FJ1595", "basilar_artery": "FJ1672", "vertebral_artery": "FJ1725",
    "internal_carotid": "FJ1682", "common_carotid": "FJ3564", "internal_jugular": "FJ3585",
    "subclavian_artery": "FJ3579", "axillary_artery": "FJ2268", "brachial_artery": "FJ2271",
    "radial_artery": "FJ2294", "ulnar_artery": "FJ2310", "scalenus_anterior": "FJ1592", "scalenus_medius": "FJ1593",
}
CONTEXT_VIEW = {k: "cn" for k in ["eye", "lateral_rectus", "superior_oblique", "tongue", "sternocleidomastoid",
                                   "basilar_artery", "vertebral_artery", "internal_carotid", "common_carotid", "internal_jugular"]}
CONTEXT_VIEW.update({k: "bp" for k in ["subclavian_artery", "axillary_artery", "brachial_artery", "radial_artery",
                                        "ulnar_artery", "scalenus_anterior", "scalenus_medius"]})


def load(obj_dir: Path, fid: str) -> trimesh.Trimesh:
    return trimesh.load(obj_dir / f"{fid}.obj", process=True, force="mesh")


def simplify(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    if len(mesh.faces) <= MESH_FACES:
        return mesh
    v, f = fast_simplification.simplify(mesh.vertices, mesh.faces, 1 - MESH_FACES / len(mesh.faces))
    return trimesh.Trimesh(v, f, process=True)


def to_three(p) -> list:
    p = np.asarray(p, dtype=float)
    return (np.stack([p[..., 0], p[..., 2], -p[..., 1]], axis=-1) / 1000.0).round(4).tolist()


def centerline(v: np.ndarray, n: int = 10) -> np.ndarray:
    """A vessel's centre line: slices along its longest axis, each replaced by its centroid."""
    c = v.mean(axis=0)
    axis = np.linalg.svd(v - c, full_matrices=False)[2][0]
    t = (v - c) @ axis
    edges = np.linspace(t.min(), t.max(), n + 1)
    pts = [v[(t >= a) & (t <= b)].mean(axis=0) for a, b in zip(edges[:-1], edges[1:]) if ((t >= a) & (t <= b)).sum()]
    return np.array(pts)


def along(line: np.ndarray, s: float) -> np.ndarray:
    """The point a fraction s of the way along a polyline."""
    seg = np.linalg.norm(np.diff(line, axis=0), axis=1)
    d = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
    return np.array([np.interp(s, d, line[:, k]) for k in range(3)])


def oriented(line: np.ndarray, start_near) -> np.ndarray:
    """Put a centre line in the direction that starts near a point."""
    return line if np.linalg.norm(line[0] - start_near) < np.linalg.norm(line[-1] - start_near) else line[::-1]


def plexus_data() -> dict:
    """The plexus tab's own structures (names, parents, roots) and notes, so both stay the same."""
    src = (HERE.parent / "anatomy-tables" / "plexus.html").read_text(encoding="utf-8")
    js = src[src.index("var R = "):src.index("var FROM = ")]
    js = js.replace("var R = ", "R = ").replace("var S = ", "S = ").replace("var INFO = ", "INFO = ")
    out = subprocess.run(["node", "-e", "let R,S,INFO;" + js + ";process.stdout.write(JSON.stringify({R,S,INFO}))"],
                         capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    netter = json.loads((HERE.parent / "anatomy-tables" / "netter_upper_limb.json").read_text(encoding="utf-8"))
    data["SUPPLY"] = netter["nerves"]  # exactly which muscles each nerve supplies, with action and blood supply
    data["MOVES"] = netter["moves"]  # what each nerve does, in one line
    for s in data["S"].values():  # the 2D drawing's coordinates mean nothing here
        s.pop("pts", None)
        s.pop("lbl", None)
    return data


def main(bp3d_dir: Path) -> None:
    obj = bp3d_dir / "objs" / "isa_BP3D_4.0_obj_99"
    V = lambda fid: load(obj, fid).vertices

    # ---------------- real meshes ----------------
    scene = trimesh.Scene()
    for nerve, files in CN_MESHES.items():
        for n, fid in enumerate(files):
            m = simplify(load(obj, fid)).apply_transform(Y_UP)
            scene.add_geometry(m, node_name=f"cn_{nerve}_{n}", geom_name=f"cn_{nerve}_{n}")
    for name, fid in CONTEXT.items():
        m = simplify(load(obj, fid)).apply_transform(Y_UP)
        scene.add_geometry(m, node_name=f"ctx_{CONTEXT_VIEW[name]}_{name}", geom_name=f"ctx_{CONTEXT_VIEW[name]}_{name}")
    scene.export(HERE / "nerves.glb")
    log.info("nerves.glb: %.1f MB", (HERE / "nerves.glb").stat().st_size / 1e6)

    # ---------------- cranial nerves (BodyParts3D mm: -X right, -Y front, Z up) ----------------
    skin = load(obj, "FJ2810")
    skin_tree = cKDTree(skin.vertices)
    head_c = np.array([0, -95, 1500.0])

    def on_skin(p, depth=3.0) -> np.ndarray:
        """The nearest point of the skin, pulled a little inside it, so a branch ends just under the surface."""
        s = skin.vertices[skin_tree.query(p)[1]]
        return s + (head_c - s) / np.linalg.norm(head_c - s) * depth

    sclera = V("FJ1368")
    eye_r = sclera[sclera[:, 0] < -5]
    lat_rect = V("FJ1355")
    optic = V("FJ1364")
    canal = optic[np.abs(optic[:, 1] + 112) < 3].mean(axis=0)  # where the optic nerve passes the optic canal
    ophth = V("FJ1363")
    ganglion = ophth[np.argmax(ophth[:, 1])] + [-3, 4, -4]  # trigeminal ganglion, just behind V1's start
    sof = np.array([-22, -116, 1525.0])
    tongue = V("FJ2761")
    scm = V("FJ1595")
    scm_r = scm[scm[:, 0] < 0]
    trap = V("FJ1520")

    brainstem = [
        {"kind": "capsule", "a": to_three([0, -84, 1527]), "b": to_three([0, -85, 1539]), "r": 0.011},   # midbrain
        {"kind": "ellipsoid", "c": to_three([0, -80, 1517]), "r": [0.017, 0.013, 0.014]},                # pons (x, y, z in three.js)
        {"kind": "capsule", "a": to_three([0, -80, 1503]), "b": to_three([0, -68, 1477]), "r": 0.009},    # medulla
        {"kind": "capsule", "a": to_three([0, -66, 1478]), "b": to_three([0, -64, 1395]), "r": 0.0065},  # cervical cord
    ]
    bulb = {"kind": "ellipsoid", "c": to_three([-6, -138, 1531]), "r": [0.003, 0.0025, 0.009]}

    # each nerve: list of drawn paths, and the three points its table columns are shown at
    cn = {
        "I": {"paths": [[[-14, -106, 1531], [-9, -125, 1532], [-6, -146, 1531]],
                        [[-6, -140, 1530], [-6, -141, 1521]], [[-8, -134, 1530], [-9, -135, 1520]]],
              "origin": [-14, -106, 1531], "exit": [-6, -140, 1526], "target": [-7, -150, 1512]},
        "II": {"paths": [], "origin": [0, -104, 1530], "exit": canal.tolist(), "target": eye_r[np.argmax(eye_r[:, 1])].tolist()},
        "III": {"paths": [[[-4, -95, 1530], [-10, -101, 1531], [-15, -106, 1528], [-20, -113, 1526], [-23, -116, 1524]]],
                "origin": [-4, -95, 1530], "exit": sof.tolist(), "target": [-24, -145, 1527]},
        "IV": {"paths": [], "origin": [-8, -72, 1530], "exit": (sof + [3, 0, 4]).tolist(), "target": V("FJ1373").mean(axis=0).tolist()},
        "V": {"paths": [[[-17, -82, 1518], [-20, -88, 1520], ganglion.tolist()],
                        [ganglion.tolist(), ophth[np.argmax(ophth[:, 1])].tolist()],
                        [ganglion.tolist(), [-25, -110, 1509], [-28, -124, 1502], [-27, -150, 1503], [-25, -170, 1502],
                         on_skin([-28, -180, 1495]).tolist()],
                        [ganglion.tolist(), [-28, -100, 1497], [-36, -108, 1482], [-44, -118, 1464], [-40, -140, 1447],
                         [-24, -162, 1442], on_skin([-22, -175, 1438]).tolist()],
                        [[-40, -112, 1474], [-22, -132, 1450], [-12, -140, 1447]],
                        [[-36, -108, 1482], [-50, -115, 1478], on_skin([-60, -125, 1470], 6).tolist()]],
              "origin": [-17, -82, 1518], "exit": [-28, -100, 1497], "target": [-24, -162, 1442],
              "sub": {"V1": sof.tolist(), "V2": [-25, -110, 1509], "V3": [-28, -100, 1497]}},
        "VI": {"paths": [[[-5, -93, 1503], [-7, -99, 1515], [-11, -104, 1524], [-16, -108, 1526], [-21, -116, 1522],
                          lat_rect[np.argmax(lat_rect[:, 1])].tolist(), lat_rect.mean(axis=0).tolist()]],
               "origin": [-5, -93, 1503], "exit": (sof + [1, 0, -3]).tolist(), "target": lat_rect.mean(axis=0).tolist()},
        "VII": {"paths": [[[-13, -84, 1503], [-24, -84, 1505], [-32, -83, 1505], [-35, -90, 1507], [-41, -82, 1499],
                           [-42, -84, 1481], [-46, -100, 1476], [-50, -112, 1478]]]
                + [[[-50, -112, 1478], m, on_skin(t).tolist()] for m, t in [
                    ([-55, -130, 1505], [-55, -158, 1538]),  # temporal
                    ([-55, -138, 1495], [-50, -168, 1508]),  # zygomatic
                    ([-50, -140, 1475], [-30, -178, 1468]),  # buccal
                    ([-48, -135, 1455], [-28, -170, 1436]),  # marginal mandibular
                    ([-48, -122, 1450], [-45, -140, 1410])]],  # cervical
                "origin": [-13, -84, 1503], "exit": [-42, -84, 1481], "target": on_skin([-50, -168, 1508]).tolist()},
        "VIII": {"paths": [[[-15, -80, 1502], [-25, -81, 1503], [-33, -82, 1504], [-38, -84, 1504]],
                           [[-38, -84, 1504], [-38, -90, 1502], [-34, -91, 1501], [-34, -87, 1502], [-36, -86, 1503]],
                           [[-38, -84, 1504], [-42, -79, 1507], [-45, -81, 1510]]],
                 "origin": [-15, -80, 1502], "exit": [-32, -82, 1504], "target": [-38, -88, 1502]},
        "IX": {"paths": [[[-9, -76, 1496], [-20, -76, 1492], [-29, -76, 1488], [-35, -92, 1465], [-30, -112, 1450], [-14, -122, 1448]]],
               "origin": [-9, -76, 1496], "exit": [-29, -76, 1488], "target": [-14, -122, 1448]},
        "X": {"paths": [[[-9, -75, 1491], [-20, -75, 1488], [-30, -74, 1485], [-31, -88, 1465], [-24, -103, 1430],
                         [-21, -108, 1390], [-20, -106, 1355], [-22, -100, 1300], [-18, -92, 1240]],
                        [[-21, -106, 1350], [-34, -106, 1332], [-30, -100, 1328], [-18, -108, 1350], [-10, -120, 1390]]],
              "origin": [-9, -75, 1491], "exit": [-30, -74, 1485], "target": [-18, -92, 1245]},
        "XI": {"paths": [[[-9, -74, 1486], [-20, -73, 1484], [-31, -72, 1482]],
                         [[-7, -64, 1420], [-9, -65, 1450], [-11, -67, 1478], [-20, -71, 1484]],
                         [[-31, -72, 1482], [-38, -82, 1462], scm_r[np.argmin(np.abs(scm_r[:, 2] - 1440))].tolist(),
                          [-70, -62, 1385], [-92, -40, 1345]]],
               "origin": [-9, -74, 1486], "exit": [-31, -72, 1482], "target": [-92, -40, 1345]},
        "XII": {"paths": [[[-4, -84, 1490], [-12, -82, 1485], [-19, -80, 1482], [-28, -86, 1462], [-32, -102, 1440],
                           [-24, -128, 1430], [-10, -140, 1440]]],
                "origin": [-4, -84, 1490], "exit": [-19, -80, 1482], "target": tongue[np.argmin(tongue[:, 2])].tolist()},
    }
    cn_out = {}
    for k, c in cn.items():
        cn_out[k] = {"paths": [to_three(np.array(p, float)) for p in c["paths"]],
                     "origin": to_three(c["origin"]), "exit": to_three(c["exit"]), "target": to_three(c["target"])}
        if "sub" in c:
            cn_out[k]["sub"] = {s: to_three(p) for s, p in c["sub"].items()}

    # ---------------- brachial plexus ----------------
    roots = json.loads((HERE.parent / "dermatomes" / "roots.json").read_text())["roots"]
    mm = lambda q: [q[0] * 1000, -q[2] * 1000, q[1] * 1000]
    root_path = {r["root"]: np.array([mm(q) for q in r["path"]])[1:] for r in roots if r["side"] == -1 and r["root"] in ("C5", "C6", "C7", "C8", "T1")}
    hum = V("FJ3368")
    epi = hum[hum[:, 2] < hum[:, 2].min() + 45]
    med_epi, lat_epi = epi[np.argmax(epi[:, 0])], epi[np.argmin(epi[:, 0])]
    pis = V("FJ3382").mean(axis=0)
    retin = V("FJ1471").mean(axis=0)
    rad_sty = V("FJ3349")[np.argmin(V("FJ3349")[:, 2])]
    A = oriented(centerline(V("FJ2268"), 8), [-77, -100, 1335])  # axillary artery, medial to lateral
    B = oriented(centerline(V("FJ2271"), 10), [-143, -85, 1274])  # brachial artery, top down
    Ra = oriented(centerline(V("FJ2294"), 10), [-215, -100, 1024])
    Ua = oriented(centerline(V("FJ2310"), 10), [-215, -100, 1024])
    DB = oriented(centerline(V("FJ2277"), 6), [-174, -60, 1184])  # deep brachial (spiral groove)
    PC = oriented(centerline(V("FJ2291"), 6), [-140, -85, 1292])  # posterior circumflex humeral (quadrangular space)
    SS = oriented(centerline(V("FJ2303"), 8), [-45, -95, 1350])   # suprascapular
    TD = oriented(centerline(V("FJ2305"), 6), [-130, -85, 1281])  # thoracodorsal
    DS = oriented(centerline(V("FJ2284"), 8), [-55, -95, 1360])   # dorsal scapular

    J = {"sup": np.array([-58, -91, 1378.0]), "mid": np.array([-60, -88, 1362.0]), "inf": np.array([-58, -84, 1340.0])}
    D = {"sup": np.array([-82, -92, 1352.0]), "mid": np.array([-82, -89, 1344.0]), "inf": np.array([-80, -86, 1334.0])}
    a0, a1 = along(A, 0.22), along(A, 0.78)
    off = {"lat": np.array([0, -3, 9.0]), "post": np.array([0, 9, 2.0]), "med": np.array([2, -2, -9.0])}
    cord0 = {k: a0 + o for k, o in off.items()}
    cord1 = {k: a1 + o for k, o in off.items()}
    Bp = lambda s, o: along(B, s) + o
    bp = {
        "C5": [*root_path["C5"], J["sup"]], "C6": [*root_path["C6"], J["sup"]], "C7": [*root_path["C7"], J["mid"]],
        "C8": [*root_path["C8"], J["inf"]], "T1": [*root_path["T1"], J["inf"]],
        "sup": [J["sup"], D["sup"]], "mid": [J["mid"], D["mid"]], "inf": [J["inf"], D["inf"]],
        "supA": [D["sup"], cord0["lat"]], "midA": [D["mid"], cord0["lat"]], "infA": [D["inf"], cord0["med"]],
        "supP": [D["sup"], (D["sup"] + cord0["post"]) / 2 + [0, 4, 0], cord0["post"]],
        "midP": [D["mid"], cord0["post"]], "infP": [D["inf"], (D["inf"] + cord0["post"]) / 2 + [0, 4, 0], cord0["post"]],
        "lat": [cord0["lat"], along(A, 0.5) + off["lat"], cord1["lat"]],
        "post": [cord0["post"], along(A, 0.5) + off["post"], cord1["post"]],
        "med": [cord0["med"], along(A, 0.5) + off["med"], cord1["med"]],
        "mc": [cord1["lat"], cord1["lat"] + [-18, -6, -22], Bp(0.25, [-16, -14, 0]), Bp(0.6, [-18, -16, 0]),
               lat_epi + [-4, -26, 8], along(Ra, 0.25) + [-8, -6, 0], along(Ra, 0.6) + [-10, -6, 0]],
        "medn": [cord1["lat"], along(A, 0.9) + [0, -10, 0], cord1["med"], along(A, 0.9) + [0, -10, 0],
                 Bp(0.15, [-6, -5, 0]), Bp(0.5, [0, -6, 0]), Bp(0.9, [7, -5, 0]), B[-1] + [6, -8, -10],
                 (along(Ra, 0.4) + along(Ua, 0.4)) / 2 + [0, 4, 0], (along(Ra, 0.8) + along(Ua, 0.8)) / 2 + [0, 2, 0],
                 retin + [0, -2, 0], retin + [-4, -8, -30]],
        "uln": [cord1["med"], Bp(0.2, [12, 4, 0]), Bp(0.6, [14, 8, 0]), med_epi + [2, 10, 12], med_epi + [0, 10, -6],
                along(Ua, 0.25) + [8, 4, 0], along(Ua, 0.7) + [6, 2, 0], pis + [3, -6, 6], pis + [2, -8, -28]],
        "ax": [cord1["post"], *PC[1:], PC[-1] + [-12, -6, 0]],
        "rad": [cord1["post"], Bp(0.12, [6, 10, 0]), *DB, lat_epi + [-6, -14, 22], lat_epi + [-4, -18, -10],
                along(Ra, 0.5) + [-10, 0, 0], rad_sty + [-4, 10, -6], rad_sty + [-2, 16, -30]],
        "ds": [root_path["C5"][1], *DS[1:]],
        "lt": [root_path["C5"][1] + [0, 6, 0], root_path["C6"][1] + [0, 8, -6], root_path["C7"][1] + [-4, 10, -14],
               [-80, -72, 1300], [-115, -92, 1230], [-127, -100, 1140], [-132, -98, 1070]],
        "ss": [(J["sup"] + D["sup"]) / 2, *SS[1:]],
        "lp": [along(A, 0.35) + off["lat"], along(A, 0.35) + [0, -28, 6], along(A, 0.35) + [6, -45, -6]],
        "mp": [along(A, 0.55) + off["med"], along(A, 0.55) + [2, -30, -10], along(A, 0.55) + [4, -46, -18]],
        "us": [along(A, 0.35) + off["post"], along(A, 0.35) + [4, 26, -6]],
        "td": [along(A, 0.6) + off["post"], TD[0] + [0, 6, 0], *TD[1:]],
        "ls": [along(A, 0.7) + off["post"], along(A, 0.7) + [2, 24, -24], along(A, 0.7) + [-4, 34, -50]],
        "mca": [along(A, 0.7) + off["med"], Bp(0.2, [20, 4, 0]), Bp(0.55, [22, 2, 0])],
        "mcf": [along(A, 0.8) + off["med"], Bp(0.3, [16, -4, 0]), Bp(0.8, [16, -8, 0]), along(Ua, 0.3) + [14, -10, 0], along(Ua, 0.65) + [12, -10, 0]],
    }
    bp_out = {k: to_three(np.array(v, float)) for k, v in bp.items()}

    data = {"cn": cn_out, "brainstem": brainstem, "bulb": bulb, "bp": bp_out, "plexus": plexus_data()}
    (HERE / "nerves.json").write_text(json.dumps(data))
    log.info("nerves.json: %d cranial nerves, %d plexus parts", len(cn_out), len(bp_out))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
