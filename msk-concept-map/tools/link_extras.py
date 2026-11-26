# Add "extras" (other testing prototypes) to matching MSK concept-map boxes: the MSK exam's joint sections
# and the anatomy tables' tabs. usage: python -I link_extras.py <nodes.json>
import json, sys

T = "https://schulichmed.github.io/testing/"
EXAM = {"shoulder": "shoulder", "elbow": "elbow", "wrist": "wrist", "hand-finger": "wrist", "hip": "hip", "knee": "knee",
        "ankle": "ankle", "foot": "ankle", "neck": "cspine", "low-back": "lspine", "neck-back-pain": "lspine"}
ANAT = {  # node id -> (tab, label)
 "summary-of-lower-limb-innervation": ("dermatomes", "the dermatome map"), "lower-limb-sensory-innervation": ("dermatomes", "the dermatome map"),
 "memory-trick-for-dermatomes-myotomes-lower-limb": ("dermatome-levels", "dermatome levels"),
 "l2-l4-obturator-n": ("hip-thigh", "hip and thigh muscles"), "l2-l4-femoral-n": ("hip-thigh", "hip and thigh muscles"),
 "inferior-gluteal-n": ("hip-thigh", "hip and thigh muscles"), "superior-gluteal-n": ("hip-thigh", "hip and thigh muscles"),
 "l4-s3-sciatic-n": ("hip-thigh", "hip and thigh muscles"), "tibial-division-of-sciatic": ("hip-thigh", "hip and thigh muscles"),
 "hamstrings": ("hip-thigh", "hip and thigh muscles"), "other-n-in-gluteal-region": ("hip-thigh", "hip and thigh muscles"),
 "common-fibular-division-of-sciatic": ("leg", "leg muscles"), "common-fibular-n": ("leg", "leg muscles"), "tibial-n": ("leg", "leg muscles"),
 "superficial-fibular-n": ("leg", "leg muscles"), "deep-fibular-n": ("leg", "leg muscles"),
 "medial-plantar-n": ("foot", "foot muscles"), "lateral-plantar-n": ("foot", "foot muscles"),
 "hip": ("hip-thigh", "hip and thigh muscles"), "knee": ("leg", "leg muscles"), "ankle": ("foot", "foot muscles"), "foot": ("foot", "foot muscles"),
 "shoulder": ("shoulder", "shoulder muscles"), "elbow": ("forearm", "forearm muscles"), "wrist": ("hand", "hand muscles"),
 "hand-finger": ("hand", "hand muscles"), "neck": ("back", "back muscles"), "low-back": ("back", "back muscles"),
}
p = sys.argv[1]; d = json.load(open(p, encoding="utf-8"))
hit = 0
for n in d["nodes"]:
    ex = []
    if n["id"] in EXAM:
        ex.append({"name": "MSK exam", "url": T + "msk-exam/#" + EXAM[n["id"]], "what": "this joint's exam"})
    if n["id"] in ANAT:
        tab, what = ANAT[n["id"]]
        ex.append({"name": "Anatomy tables", "url": T + "anatomy-tables/#" + tab, "what": what})
    if ex: n["extras"] = ex; hit += 1
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("extras on", hit, "boxes")
