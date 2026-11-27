# Add "extras" (other testing prototypes) to matching hematology concept-map boxes: the abdominal exam's spleen
# and liver sections, and the lymph node parts of the head and neck and breast exams.
# usage: python -I link_extras.py <nodes.json>
import json, re, sys

T = "https://schulichmed.github.io/testing/"
RULES = [  # (pattern on the plain lower-case title, name, url, what)
 (r"splenomegaly|^spleen$", "Abdominal exam", T + "abdo-exam/#spleen", "palpating and percussing the spleen"),
 (r"^liver disease$", "Abdominal exam", T + "abdo-exam/#liver", "examining the liver"),
 (r"lymphadenopathy|^lymphoma$|hodgkin", "Head and neck exam", T + "hn-exam/#neck", "the neck's lymph nodes"),
 (r"lymphadenopathy", "Breast exam", T + "breast-exam/#axilla", "the axillary nodes"),
]
p = sys.argv[1]; d = json.load(open(p, encoding="utf-8"))
hit = 0
for n in d["nodes"]:
    t = re.sub(r"<[^>]+>", "", n["title"]).lower()
    ex = [{"name": nm, "url": u, "what": w} for pat, nm, u, w in RULES if re.search(pat, t)]
    if ex: n["extras"] = ex; hit += 1
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("extras on", hit, "boxes")
