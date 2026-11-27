# Link each hematology concept-map node to the FoM overview chart (and column) that teaches it, and to the
# lecture notes on the portal's FoM Block 3 page (fom/b3.html#n-<lecture id>).
# usage: python -I chart_links.py <map-data.json> <out.json> <preclerkship repo>
import html, json, re, sys, pathlib

BASE = "https://schulichmed.github.io/preclerkship/fom/"
NAMES = {}   # chart id -> title, read from the portal's chart pages
LECT = {}    # lecture id -> title, lectures that have a written note

# (pattern on the lower-case title, chart suffix, column or None, maps or None); first match wins, two charts at most
R = [
 # --- week 9: anemia
 (r"^anemia$", "w9-02_2", None, "w9"), (r"^cbc$|hematological investigations|peripheral blood smear|^differential$", "w9-02_2", None, None),
 (r"microcytic anemia", "w9-03_2", None, None), (r"microcytic anemia", "w9-02_2", "mi", None),
 (r"iron deficiency", "w9-03_2", "ida", None), (r"anemia of chronic", "w9-03_2", "aci", None),
 (r"sideroblastic|lead poisoning", "w9-03_2", "sid", None),
 (r"thalass|hemoglobin h disease|bart", "w9-03_2", "tha", None),
 (r"iron metabolism|hepcidin|tibc|iron poisoning", "w9-03_2", None, None),
 (r"normocytic anemia", "w9-04_2", None, None), (r"normocytic anemia", "w9-02_2", "no", None),
 (r"acute blood loss", "w9-04_2", "bl", None),
 (r"sickle cell|^scd|hemoglobin s$|hemoglobin c$|s-hpfh", "w9-04_2", "sc", None),
 (r"aplastic|pure red cell|fanconi|dyskeratosis|decreased rbc production|dyserythropoietic", "w9-04_2", "em", None),
 (r"myelophthisis|leukemia or lymphoma", "w9-04_2", "my", None), (r"^myelofibrosis$", "w9-04_2", "my", "w9"),
 (r"chronic kidney disease|erythropoietin", "w9-04_2", None, "w9"),
 (r"macrocytic anemia", "w9-05_2", None, None), (r"macrocytic anemia", "w9-02_2", "ma", None),
 (r"b12|cobalamin", "w9-05_2", "b12", None), (r"b9|folate", "w9-05_2", "fol", None),
 (r"megaloblastic anemia|functions of vit|hyperhomocysteinemia|^drugs$", "w9-05_2", None, "w9"),
 (r"^non-megaloblastic", "w9-05_2", None, None),
 (r"^liver disease$", "w9-05_2", "liv", "w9"), (r"reticulocytosis", "w9-05_2", "ret", None),
 (r"lab artifact|agglutination|rouleaux", "w9-05_2", "ps", None), (r"hypothyroidism", "w9-05_2", "thy", None),
 (r"warm aiha", "w9-06_2", "wa", None), (r"cold aiha", "w9-06_2", "co", None), (r"g6pd", "w9-06_2", "g6", None),
 (r"spherocytosis", "w9-06_2", "hs", None),
 (r"hemolytic anemia|hemolytic|elliptocytosis|^hereditary$|alloimmune|^acquired$|^immune$|^non-immune$|^infections$|thermal injury|mechanical injury|heart valves|paroxysmal", "w9-06_2", None, "w9"),
 (r"hemolytic anemia", "w9-02_2", "he", None),
 (r"dic, ttp, hus", "w10-05_2", None, None),
 (r"myelodysplastic", "w9-08_2", None, None),
 (r"^multiple myeloma$", "w12-06_2", "mm", None),
 (r"acute myeloid leukemia", "w11-04_2", "aml", None),
 # --- week 10: hemostasis, bleeding, thrombosis
 (r"von willebrand|^vwd|vwf", "w10-01_2", "vwd", None), (r"von willebrand|^vwd", "w10-04_2", "vwd", None),
 (r"hemophilia", "w10-01_2", "hem", None), (r"hereditary hemophilia", "w10-04_2", "hem", None), (r"acquired hemophilia|factor inhibition", "w10-03_2", "inh", None),
 (r"platelet function|antiplatelet|1° hemostasis|platelet disorders|^platelets$|^adhesion|^activation|^aggregation", "w10-01_2", "pfd", None),
 (r"vascular disorders", "w10-01_2", None, "w10"), (r"disorders due to (increased destruction|decreased production)", "w10-05_2", None, "w10"),
 (r"diagnosing bleeding|bleeding assessment|practical / clinical", "w10-01_2", None, None),
 (r"transfusion|blood bank|cryoprecipitate|fibrinogen concentrate|prothrombin complex|massively bleeding|^plasma|plasma components|^red cell|^platelet transfusion", "w10-01_2", None, "w10"),
 (r"factor deficienc|multiple factor", "w10-03_2", "def", None), (r"mixing study", "w10-03_2", None, None),
 (r"pt and factor vii|isolated ↑inr|extrinsic", "w10-03_2", "f7", None),
 (r"^liver disease$|liver, vitamin k|liver and vitamin", "w10-03_2", "liv", "w10"),
 (r"vitamin k deficiency", "w10-03_2", "vk", None),
 (r"coagulation disorders|common pathway|intrinsic pathway|inr/pt|ptt ↑|coagulation cascade|2° hemostasis|lupus anticoagulant", "w10-03_2", None, None),
 (r"hemorrhagic disease|neonates", "w10-04_2", "hdn", None),
 (r"immune thrombocytopenic|^itp", "w10-05_2", "itp", None), (r"immune thrombocytopenic|^itp", "w10-04_2", "itp", None),
 (r"thrombotic thrombocytopenic|^ttp", "w10-05_2", "ttp", None), (r"hemolytic uremic|^hus", "w10-05_2", "hus", None),
 (r"disseminated intravascular|^dic$", "w10-05_2", "dic", None),
 (r"heparin.induced|^hit", "w10-05_2", "hit", None), (r"heparin.induced|^hit", "w10-07_2", "ufh", None),
 (r"pseudothrombocytopenia", "w10-05_2", "oth", None), (r"^thrombocytopenia$|thrombotic microangiopath", "w10-05_2", None, None),
 (r"^spleen|sequestration|splenomegaly", "w10-05_2", None, "w10"),
 (r"unfractionated", "w10-07_2", "ufh", None), (r"low molecular", "w10-07_2", "lmwh", None), (r"fondaparinux", "w10-07_2", "fon", None),
 (r"warfarin", "w10-07_2", "war", None), (r"warfarin", "w10-03_2", "vk", None),
 (r"direct xa", "w10-07_2", "xa", None), (r"direct thrombin \(ii?a\)|dabigatran", "w10-07_2", "dab", None),
 (r"direct iv thrombin|hirudin|bivalirudin|argatroban", "w10-07_2", "ivd", None),
 (r"heparin|doac|anticoagula", "w10-07_2", None, "w10"),
 (r"thrombosis|thrombophilia|thromboembolism|dvt|pulmonary embolism|leiden|prothrombin gene|protein c|antithrombin|antiphospholipid", "w10-07_2", None, "w10"),
 # --- weeks 11 and 12: white cells, MPNs, leukemia
 (r"febrile neutropenia", "w11-03_2", "fn", None), (r"acquired neutropenia", "w11-03_2", "aq", None),
 (r"neutropenia|leukopenia", "w11-03_2", None, None),
 (r"pancytopenia|^cytopenia|↑ destruction", "w11-06_2", None, None),
 (r"^thrombocytopenia$", "w10-05_2", None, "w11"), (r"^anemia$", "w9-02_2", None, "w11"),
 (r"neutrophilia", "w11-02_2", "rn", None), (r"lymphocytosis", "w11-02_2", "rl", None),
 (r"secondary leukocytosis|monocytes|eosinophils|basophils", "w11-02_2", "rn", None),
 (r"primary leukocytosis|leukocytosis|^cytosis", "w11-02_2", None, None),
 (r"polycythemia vera", "w11-05_2", "pv", None), (r"polycythemia vera", "w11-02_2", "mp", None),
 (r"erythrocytosis", "w11-05_2", None, None),
 (r"essential thrombocyth", "w11-06_2", "et", None), (r"essential thrombocyth", "w11-02_2", "mp", None),
 (r"^myelofibrosis|myelofibrosis \(mf\)", "w11-06_2", "mf", "w11"), (r"progression of et", "w11-06_2", None, None),
 (r"reactive \(2°\) thrombocytosis", "w11-06_2", "in", None), (r"spurious", "w11-06_2", None, None),
 (r"thrombocytosis", "w11-06_2", None, None),
 (r"myeloproliferative|chronic myeloid disorders|^hydroxyurea", "w11-02_2", "mp", None),
 (r"myelodysplastic syndrome \(mds\)|chronic myelomonocytic", "w9-08_2", None, None),
 (r"chronic myeloid leukemia", "w11-04_2", "cml", None), (r"chronic myeloid leukemia", "w11-02_2", "mp", None),
 (r"acute myeloid", "w11-04_2", "aml", None), (r"promyelocytic", "w11-04_2", "apl", None),
 (r"acute lymphoblastic", "w11-04_2", "all", None),
 (r"chronic lymphoid leukemias|b-cell cll|small lymphocytic|monoclonal b cell", "w11-04_2", "cll", None),
 (r"chronic lymphoid leukemias|b-cell cll|chronic lymphoproliferative|small lymphocytic|monoclonal b cell", "w11-02_2", "cl", None),
 (r"leukemia presentation|cml, aml|myeloid disorders|lymphoid disorders|leukemia complications|leukostasis|progressive", "w11-04_2", None, None),
 (r"^dic$", "w10-05_2", "dic", "w11"), (r"^dic$", "w11-04_2", "apl", "w11"),
 (r"tumor lysis|tls ", "w11-04_2", None, None),
 # --- week 12: lymph nodes, lymphoma, myeloma, treatment
 (r"lymphadenopathy", "w12-02_2", None, None), (r"mediastinal mass", "w12-06_2", None, None),
 (r"hodgkin's lymphoma|hodgkin lymphoma", "w12-05_2", "hl", None),
 (r"diffuse large", "w12-05_2", "dl", None), (r"follicular", "w12-05_2", "fl", None),
 (r"lymphoma|ann arbor", "w12-05_2", None, None),
 (r"mgus", "w12-06_2", "mg", None), (r"smoldering", "w12-06_2", "sm", None), (r"plasma cell leukemia", "w12-06_2", "pc", None),
 (r"multiple myeloma|plasmacytoma|poems|amyloidosis|plasma cell dyscrasias|immunoglobulins", "w12-06_2", "mm", None),
 (r"alkylating", "w12-07_2", "alk", None), (r"anti-metabolites", "w12-07_2", "ame", None),
 (r"topoisomerase|anti-tumor antibiotics", "w12-07_2", "top", None), (r"anti-microtubule", "w12-07_2", "mic", None),
 (r"monoclonal antibodies|rituximab|daratumumab|zevalin|chop-r", "w12-07_2", "mab", None),
 (r"small molecule|tyrosine kinase|ibrutinib|proteosome|immunomodulatory|differentiating", "w12-07_2", "sm", None),
 (r"radiation", "w12-08_2", None, None),
 (r"chemotherapy|chemo side|treatment for leukemia|hormonal therap|targeted therap|immunotherap|checkpoint|car-t|pd-1", "w12-07_2", None, None),
]
# lecture notes: (pattern, lecture id, maps or None); every lecture of a box's charts is added after these, three notes at most
NOTES = [
 (r"hematopoiesis|erythropoietin|hemoglobin|beta chains|alpha chains|peripheral blood smear|bone marrow|^scd|s-hpfh|sickle|thalass|bart", "b3-w9-01", "w9"),
 (r"^cbc$|hematological investigations|^differential$|^anemia$", "b3-w9-02", "w9"),
 (r"iron metabolism|hepcidin|tibc|iron poisoning|heme synthesis|b12|b9|folate|cobalamin|functions of vit|hyperhomocysteinemia", "b3-w9-08", "w9"),
 (r"hemostasis|coagulation cascade|anticoagulants$|antithrombin iii$|fibrinoly|d-dimer|mixing study|ptt ↑|inr/pt|factor viii bound|^liver$|^bone marrow$|platelets|endothel|spleen|regulation of|adhesion|activation|aggregation|specialized testing", "b3-w10-02", "w10"),
 (r"transfusion|blood bank|cryoprecipitate|fibrinogen|prothrombin complex|massively bleeding|^plasma|plasma components|^red cell", "b3-w10-01", "w10"),
 (r"thrombosis|thrombophilia|thromboembolism|dvt|pulmonary embolism|leiden|prothrombin gene|protein c|antithrombin iii \(|antiphospholipid|^hereditary$|^acquired$", "b3-w10-05", "w10"),
 (r"leukemia|leukostasis|tumor lysis|tls |progressive|myeloid disorders|lymphoid disorders", "b3-w11-08", "w11"),
 (r"acute|leukemia presentation|flow|cytogenetic", "b3-w11-07", "w11"),
 (r"lymphoma|ann arbor|hodgkin", "b3-w12-04", "w11"),
 (r"chemotherapy|chemo side|treatment for|hormonal|targeted|immunotherap|checkpoint|car-t|pd-1|monoclonal antibodies|rituximab|daratumumab|zevalin|chop-r|small molecule|tyrosine|ibrutinib|proteosome|immunomodulatory|differentiating|alkylating|anti-|topoisomerase|^hydroxyurea", "b3-w12-07", "w11"),
]

def lecture_of(chart):
    return "b3-" + re.match(r"w\d+-\d+", chart).group(0)

def note(lid):
    return {"id": lid, "name": LECT[lid], "url": BASE + "b3.html#n-" + lid}

def links_for(title, m):
    t = html.unescape(re.sub(r"<[^>]+>", "", title)).strip().lower()
    out = []
    for pat, ch, col, maps in R:
        if maps and m not in maps.split(","): continue
        if re.search(pat, t):
            cid = "fom-b3-" + ch
            if any(o["chart"] == cid for o in out): continue
            out.append({"chart": cid, "col": col, "name": NAMES[cid], "url": BASE + "charts/" + cid + "/" + (f"#col={col}" if col else "")})
            if len(out) == 2: break
    notes = []
    for pat, lid, maps in NOTES:
        if maps and m not in maps.split(","): continue
        if re.search(pat, t) and lid in LECT and lid not in notes: notes.append(lid)
    for c in out:
        lid = lecture_of(c["chart"][7:])
        if lid in LECT and lid not in notes: notes.append(lid)
    return out, [note(l) for l in notes[:3]]

if __name__ == "__main__":
    repo = pathlib.Path(sys.argv[3])
    for f in sorted((repo / "fom/charts").glob("fom-b3-*/index.html")):
        NAMES[f.parent.name] = html.unescape(re.search(r"<title>([^<]*)", f.read_text(encoding="utf-8")).group(1))
    roster = json.load(open(repo / "fom/data/notes/b3.json", encoding="utf-8"))
    for w in roster["weeks"]:
        for l in w["lectures"]:
            if l.get("hasNote"): LECT[l["id"]] = l["title"]
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    n_with = n_notes = 0; used = set(); used_notes = set()
    for n in data["nodes"]:
        n["charts"], n["notes"] = links_for(n["title"], n["map"])
        if n["charts"]: n_with += 1
        if n["notes"]: n_notes += 1
        used.update(c["chart"] for c in n["charts"]); used_notes.update(x["id"] for x in n["notes"])
    json.dump(data, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    sys.stdout.reconfigure(encoding="utf-8")
    print(n_with, "of", len(data["nodes"]), "nodes linked to a chart;", len(used), "of", len(NAMES), "charts used")
    print("unused charts:", sorted(set(NAMES) - used))
    print(n_notes, "nodes linked to lecture notes;", len(used_notes), "of", len(LECT), "lectures used")
    print("unused lectures:", sorted(set(LECT) - used_notes))
    print("no chart:", [n["map"] + ":" + re.sub(r"<[^>]+>", "", n["title"]) for n in data["nodes"] if not n["charts"]])
    print("no note:", [n["map"] + ":" + re.sub(r"<[^>]+>", "", n["title"]) for n in data["nodes"] if not n["notes"]])
