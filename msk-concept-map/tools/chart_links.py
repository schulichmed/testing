# Link each MSK concept-map node to the preclerkship overview chart (and column) that teaches it,
# and to the lecture notes on the portal's MSK page (msk.html#n-<lecture id>).
# usage: python -I chart_links.py <map-data.json> <out.json>
import html, json, re, sys

NAMES = {
 "msk-w7-02.2_2": "Mechanical back and neck pain", "msk-w7-03.2_2": "Non-mechanical back and neck pain",
 "msk-w7-04_2": "Spine X-ray", "msk-w7-05.2_2": "Shoulder bones and joints", "msk-w8-02.2_2": "Rotator cuff",
 "msk-w8-03.2_2": "Anterior shoulder pain", "msk-w8-05.2_2": "Elbow pain", "msk-w8-06.2_2": "Forearm muscles",
 "msk-w8-07.2_2": "Elbow and forearm nerves", "msk-w8-08.2_2": "Distal radius and scaphoid fractures",
 "msk-w8-08.2_3": "Wrist and hand", "msk-w9-03.2_2": "Hip fracture", "msk-w9-05_2": "Hip pain", "msk-w9-06.2_3": "Knee",
 "msk-w10-01.2_2": "Ankle and foot", "msk-w10-03_2": "Nerve injury", "msk-w10-04_2": "Fracture radiology",
 "msk-w10-05_2": "Fracture management", "msk-w10-06_2": "Chronic pain", "msk-w10-07_2": "Psychology of chronic pain",
 "msk-w10-08_2": "Pediatric orthopedics", "msk-w10-09_2": "The child with a limp", "msk-w10-10_2": "Physical activity prescription",
 "msk-w10-11_2": "Soft tissue mass", "msk-w11-01_2": "MSK infections", "msk-w11-02_2": "Polyarthritis",
 "msk-w11-03_2": "Juvenile idiopathic arthritis", "msk-w11-04_2": "Osteoarthritis", "msk-w11-06_2": "Connective tissue disease",
 "msk-w11-06_3": "Lupus criteria", "msk-w11-07_2": "Vasculitis", "msk-w11-08_2": "Acute monoarthritis",
 "msk-w12-01_2": "Rheumatology labs", "msk-w12-03_2": "Body pain", "msk-w12-06_2": "Cranial nerves",
}
R = [  # (pattern on the node title, chart suffix, column or None); first match wins, up to two different charts
 # --- joint infection and crystals
 (r"hand septic arthritis", "w11-01_2", "deep"), (r"disseminated gonococcal|^gonococcal", "w11-01_2", "oth"),
 (r"septic arthritis|joint infection|^etiologies|non-gonococcal", "w11-08_2", "sep"), (r"infectious polyarthritis", "w11-02_2", "sep"),
 (r"pseudogout", "w11-08_2", "cppd"), (r"gout", "w11-08_2", "gout"), (r"crystalline|acute monoarthritis|^monoarthritis", "w11-08_2", None),
 (r"chronic monoarthritis", "w11-04_2", None),
 (r"osteoarthritis|degenerative arthritis", "w11-04_2", "oa"), (r"osteoarthritis|degenerative arthritis", "w11-02_2", "oa"),
 # --- polyarthritis
 (r"rheumatoid|seropositive", "w11-02_2", "ra"), (r"ankylosing", "w11-02_2", "as"), (r"ankylosing", "w7-04_2", "as"),
 (r"psoriatic", "w11-02_2", "psa"), (r"reactive arthritis", "w11-02_2", "rea"),
 (r"connective tissue disorder associated", "w11-02_2", "ctd"), (r"diagnostic arthrocentesis", "w11-02_2", None),
 (r"seronegative|enteropathic|polyarthritis|inflammatory arthritis|^arthritis|^joint pain", "w11-02_2", None),
 (r"juvenile|jia", "w11-03_2", None),
 # --- body pain
 (r"polymyalgia", "w12-03_2", "pmr"), (r"fibromyalgia|centralizing", "w12-03_2", "fm"), (r"centralizing", "w10-06_2", "neu"),
 (r"^joint pain|non-inflammatory|non-articular|^inflammatory$", "w12-03_2", None),
 # --- connective tissue disease
 (r"lupus \(sle\) glomerulo", "w11-06_3", "renal"), (r"lupus|\(sle\)", "w11-06_2", "sle"), (r"lupus|\(sle\)", "w11-06_3", None),
 (r"antiphospholipid", "w11-06_2", "aps"), (r"sj.gren", "w11-06_2", "sjo"),
 (r"polymyositis", "w11-06_2", "myo"), (r"polymyositis", "w12-03_2", "myo"), (r"scleroderma", "w11-06_2", "ssc"),
 (r"raynaud|mixed connective", "w11-06_2", None),
 # --- vasculitis
 (r"giant cell|large vessel", "w11-07_2", "gca"), (r"anca", "w11-07_2", "anca"), (r"small vessel|henoch", "w11-07_2", "lcv"),
 (r"vasculitis|kawasaki", "w11-07_2", None),
 # --- infections, oncology
 (r"diabetic foot", "w11-01_2", "dfi"), (r"diabetic foot", "w10-01.2_2", "dm"),
 (r"hand cellulitis|hand infections", "w11-01_2", "cel"), (r"abscess|suppurative tenosynovitis", "w11-01_2", "deep"),
 (r"osteomyelitis|bone infection|om invx", "w11-01_2", "om"), (r"pediatric osteomyelitis", "w10-09_2", "sep"),
 (r"msk infections|antibiotics", "w11-01_2", None),
 (r"msk oncology|sarcoma", "w10-11_2", "sar"),
 # --- paediatrics
 (r"transient synovitis", "w10-09_2", "ts"), (r"pediatric hip", "w10-09_2", None),
 (r"salter", "w10-08_2", "sh"), (r"pediatric fractures", "w10-08_2", "frac"), (r"pa?ediatric ortho|msk paediatrics", "w10-08_2", None),
 # --- orthopaedics
 (r"^fractures", "w10-04_2", None), (r"^fractures", "w10-05_2", None),
 (r"^elbow", "w8-05.2_2", None), (r"^elbow", "w8-06.2_2", None),
 (r"^wrist", "w8-08.2_3", None), (r"^wrist", "w8-08.2_2", None), (r"^hand & finger", "w8-08.2_3", None),
 (r"^shoulder", "w7-05.2_2", None), (r"^shoulder", "w8-02.2_2", None),
 (r"^hip$", "w9-05_2", None), (r"^hip$", "w9-03.2_2", None), (r"^knee", "w9-06.2_3", None),
 (r"^ankle|^foot", "w10-01.2_2", None),
 (r"^neck|^low back", "w7-02.2_2", None), (r"^low back|red flags", "w7-03.2_2", None),
 (r"nerve lesions|^l2-l4 (obturator|femoral)|sciatic n\.|gluteal n\.|^common fibular n|^tibial n|^(superficial|deep) fibular", "w10-03_2", "mono"),
 (r"post-infection|rheumatic fever|post-streptococcal", "w11-02_2", None),
]
# lecture notes beyond the charts' own lectures: (pattern, lecture id); listed before the charts' lectures, three at most
NOTES = [
 (r"seronegative|spondyloarthritis|ankylosing|psoriatic|reactive arthritis|enteropathic|post-infection", "msk-w11-05"),
 (r"treatments in|^others|acetaminophen|colchicine|nsaid|steroid|gastritis|osteoporosis|dmard|methotrexate|hydroxychloroquine|biologics|tnf|therapeutic arthrocentesis", "msk-w12-02"),
 (r"diagnostic arthrocentesis|infection vs\. inflammation", "msk-w12-01"),
 (r"femoral|obturator|saphenous|gluteal|sciatic|cutaneous n\. of thigh|hamstrings|lower limb (sensory|nerve)|memory trick|summary of lower limb", "msk-w9-04"),
 (r"fibular|tibial|sural|plantar|lower limb (sensory|nerve)|memory trick|summary of lower limb", "msk-w9-08"),
 (r"plantar|^foot|^ankle", "msk-w10-01.1"), (r"nerve lesions", "msk-w10-03"),
 (r"^knee", "msk-w9-07.2"), (r"^wrist|^hand & finger", "msk-w9-01.2"), (r"^shoulder", "msk-w8-03.2"),
 (r"vertebral osteomyelitis", "msk-w7-03.2"), (r"^fractures", "msk-w9-02"),
]
LECT = {}
BASE = "https://schulichmed.github.io/preclerkship/pom2/"

def lecture_of(chart):
    return re.sub(r"_\d+$", "", chart)

def note(lid):
    return {"id": lid, "name": LECT[lid], "url": BASE + "msk.html#n-" + lid}

def links_for(title):
    t = html.unescape(re.sub(r"<[^>]+>|📍", "", title)).strip().lower()
    out = []
    for pat, ch, col in R:
        if re.search(pat, t):
            cid = "msk-" + ch
            if any(o["chart"] == cid for o in out): continue
            out.append({"chart": cid, "col": col, "name": NAMES[cid], "url": BASE + "charts/" + cid + "/" + (f"#col={col}" if col else "")})
            if len(out) == 2: break
    notes = []
    for pat, lid in NOTES:
        if re.search(pat, t) and lid not in notes: notes.append(lid)
    for c in out:
        lid = lecture_of(c["chart"])
        if lid in LECT and lid not in notes: notes.append(lid)
    return out, [note(l) for l in notes[:3]]

if __name__ == "__main__":
    roster = json.load(open(r"C:/Users/nsims/projects/preclerkship/pom2/data/notes/msk.json", encoding="utf-8"))
    for w in roster["weeks"]:
        for l in w["lectures"]:
            if l.get("hasNote"): LECT[l["id"]] = l["title"]
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    n_with = n_notes = 0; used = set(); used_notes = set()
    for n in data["nodes"]:
        n["charts"], n["notes"] = links_for(n["title"])
        if n["charts"]: n_with += 1
        if n["notes"]: n_notes += 1
        used.update(c["chart"] for c in n["charts"]); used_notes.update(x["id"] for x in n["notes"])
    json.dump(data, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    sys.stdout.reconfigure(encoding="utf-8")
    print(n_with, "of", len(data["nodes"]), "nodes linked to a chart;", len(used), "of", len(NAMES), "charts used")
    print("unused charts:", sorted(set(NAMES) - used))
    print(n_notes, "nodes linked to lecture notes;", len(used_notes), "of", len(LECT), "lectures used")
    print("unused lectures:", sorted(set(LECT) - used_notes))
    print("no chart:", [re.sub(r"<[^>]+>", "", n["title"]) for n in data["nodes"] if not n["charts"]])
    print("no note:", [re.sub(r"<[^>]+>", "", n["title"]) for n in data["nodes"] if not n["notes"]])
