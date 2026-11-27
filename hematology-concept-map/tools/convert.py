# Parse the agents' transcriptions (t_<map>_<region>.md) into map nodes, each placed on its own map
# from the detected highlighter boxes (blobs_<map>.json) or the agent's tile-local rectangle.
# usage: python -I convert.py <ov dir with t_*.md + blobs_*.json> <out map-data.json>
import re, json, sys, html, pathlib
sys.stdout.reconfigure(encoding="utf-8")

OV = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
TILE_OV = 70
MAPS = ["w9", "w10", "w11"]
BLOBS = {k: json.load(open(OV / f"blobs_{k}.json")) for k in MAPS}

GREEK = {"α": " alpha ", "β": " beta ", "γ": " gamma ", "δ": " delta ", "↑": " high ", "↓": " low ", "°": " ", "1°": "primary", "2°": "secondary", "3°": "tertiary"}
def translit(s):
    for a in ("1°", "2°", "3°"): s = s.replace(a, GREEK[a])
    for a, b in GREEK.items(): s = s.replace(a, b)
    return s
def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", translit(s).lower()).strip("-")[:48] or "node"

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s

def plain(s):
    return re.sub(r"\*+", "", s)

def dash(s):  # no em or en dashes in anything the reader sees
    return s.replace(" — ", ": ").replace("—", "-").replace("–", "-")

nodes = []
for f in sorted(OV.glob("t_*.md"), key=lambda p: (MAPS.index(p.stem.split("_")[1]), p.stem)):
    key = f.stem.split("_")[1]
    B = BLOBS[key]; W, H, cols, rows = B["W"], B["H"], B["cols"], B["rows"]
    blob = {b["id"]: b for b in B["blobs"]}
    cur = None; section = None
    for line in f.read_text(encoding="utf-8").splitlines():
        if re.match(r"^#\s", line):
            section = line[2:].strip().lower(); cur = None; continue
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            section = None
            cur = {"map": key, "title": dash(m.group(1)), "lines": [], "rect": None, "links_txt": "", "hint": False, "src": f.name}
            nodes.append(cur); continue
        if cur is None or section or not line.strip():
            continue
        mm = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if not mm:
            continue
        ind, txt = len(mm.group(1).expandtabs(2)), dash(mm.group(2).strip())
        if ind == 0:
            b = re.match(r"^box:\s*(\d+)", txt, re.I)
            a = re.match(r"^at:\s*r(\d+)\s*c(\d+)\s+x?(-?\d+)\s*,\s*y?(-?\d+)\s*,\s*w?(\d+)\s*,\s*h?(\d+)", txt, re.I)
            if b and int(b.group(1)) in blob:
                x = blob[int(b.group(1))]; cur["rect"] = [x["x"], x["y"], x["w"], x["h"]]; cur["blob"] = x["id"]; continue
            if a:
                r, c, x, y, w, h = map(int, a.groups())
                x0, y0 = max(0, c * W // cols - TILE_OV), max(0, r * H // rows - TILE_OV)
                cur["rect"] = [x0 + x, y0 + y, w, h]; continue
            if re.match(r"^(box|at):", txt, re.I):
                print("bad position:", key, cur["title"], txt); continue
            if re.match(r"^links:", txt, re.I):
                cur["links_txt"] = txt[6:].strip(); continue
            if re.match(r"^hint:", txt, re.I):
                cur["hint"] = "yes" in txt.lower(); continue
        cur["lines"].append((ind, txt))

def dkey(n):
    return n["map"] + ":" + re.sub(r"[^a-z0-9]+", " ", translit(plain(n["title"])).lower()).strip()
best = {}
for n in nodes:
    k = dkey(n)
    o = best.get(k)
    j = 2
    while o is not None and "blob" in o and "blob" in n and o["blob"] != n["blob"]:  # two real boxes that share a title
        k = dkey(n) + f" #{j}"; o = best.get(k); j += 1
    n["dk"] = k
    if o is None: best[k] = n; continue
    keep, drop = (n, o) if len(n["lines"]) > len(o["lines"]) else (o, n)
    if "blob" not in keep and "blob" in drop: keep["rect"], keep["blob"] = drop["rect"], drop["blob"]
    if not keep["links_txt"]: keep["links_txt"] = drop["links_txt"]
    best[k] = keep
dropped = [n for n in nodes if best[n["dk"]] is not n]
nodes = [n for n in nodes if best[n["dk"]] is n]
# the same blob claimed by two headings: keep it on the first, report it
claimed = {}
for n in nodes:
    if "blob" in n:
        k = (n["map"], n["blob"])
        if k in claimed: print("blob claimed twice:", k, claimed[k], "|", n["title"])
        else: claimed[k] = n["title"]
nodes = [n for n in nodes if not re.match(r"^(foundations of|hematology i+\b)", plain(n["title"]).lower())]
nopos = [n["map"] + ":" + n["title"] for n in nodes if not n["rect"]]
nodes = [n for n in nodes if n["rect"]]

KEEP = set("""AML APL ALL CML CLL SLL MDS ITP TTP HUS DIC HIT DVT PE PT PTT INR CBC MGUS POEMS AL ET PV MF PMF MPN MPNS NHL DLBCL TLS VTE RBC RBCS WBC WBCS
G6PD AIHA IDA HBH HBA HBF HBS HBC CAR-T PD-1 CTLA-4 TKI TKIS ATRA BCR-ABL MAHA PCC PCCS FFP ABO RH HLA II III IV VII VIII IX X XI XII XIII B12 B9 EPO TPO
TIBC HPLC CD20 CKD IGG IGM LMWH UFH DOAC DOACS VWD VWF ADAMTS-13 TF TPA AT AT-III APS PNH SCD BM PBS MCV HB HCT CRAB ATIII CNS CT MRI LDH TB HIV EBV CMV
GI MM MPNS DDX CMML MBL PD-L1 PDL-1 NH IIA AKA NSAIDS ASA DDAVP TXA PRBC PRBCS IVIG HDN MAT ACD SLE RA DAT VS NK TCR DNA RNA LP""".split())
SMALL = {"of", "to", "in", "on", "or", "by", "an", "as", "at", "is", "it", "no", "vs"}
def tidy(t):
    t = re.sub(r"\s{2,}", " ", t).strip()
    letters = [ch for ch in t if ch.isalpha()]
    if letters and sum(ch.isupper() for ch in letters) > 0.6 * len(letters):
        def fix(w):
            core = re.sub(r"[^A-Za-z0-9-]", "", w)
            if core.upper() in KEEP or any(ch.isdigit() for ch in core): return w
            if len(core) <= 2 and core.isupper() and core.lower() not in SMALL: return w
            return w[:1] + w[1:].lower()
        t = " ".join("/".join(fix(x) for x in w.split("/")) for w in t.split(" "))
        t = re.sub(r"(\(|/|-)([a-z])", lambda m: m.group(1) + m.group(2).upper(), t)
        t = re.sub(r"(?<=\S )\b(To|Of|The|And|In|For|With|Vs|On|By|From|A|An|Or)\b", lambda m: m.group(1).lower(), t)
    t = re.sub(r"Ddx|DDX", "DDx", t); t = re.sub(r"Hemophilia a", "Hemophilia A", t); t = t.replace("(Iia)", "(IIa)").replace("(Cmml)", "(CMML)").replace("(Mbl)", "(MBL)")
    t = re.sub(r"Anemia of", "Anemia of", t); t = t.replace("Vwd", "vWD").replace("VWD", "vWD").replace("VWF", "vWF").replace("Hbh", "HbH").replace("HBH", "HbH")
    t = re.sub(r"\bDOACS\b", "DOACs", t); t = re.sub(r"\bMPNS\b", "MPNs", t); t = re.sub(r"\bRBCS\b", "RBCs", t); t = re.sub(r"\bWBCS\b", "WBCs", t)
    t = re.sub(r"\bTKIS\b", "TKIs", t); t = re.sub(r"\bPCCS\b", "PCCs", t); t = re.sub(r"\bNSAIDS\b", "NSAIDs", t); t = re.sub(r"\bIGG\b", "IgG", t); t = re.sub(r"\bIGM\b", "IgM", t)
    return t

seen = {}
for n in nodes:
    n["title_plain"] = tidy(plain(n["title"]))
    base = slug(n["title_plain"]); i = base
    if i in seen: i = f"{base}-{n['map']}"
    k = 2
    while i in seen: i = f"{base}-{n['map']}-{k}"; k += 1
    seen[i] = 1; n["id"] = i

def to_html(lines):
    out, stack = [], []
    for ind, txt in lines:
        lvl = ind // 2
        while len(stack) > lvl + 1: out.append("</li></ul>"); stack.pop()
        if len(stack) == lvl + 1: out.append("</li><li>" + inline(txt))
        else:
            while len(stack) < lvl + 1: out.append("<ul><li>"); stack.append(1)
            out[-1] += inline(txt)
    while stack: out.append("</li></ul>"); stack.pop()
    return "".join(out)

STOP = {"the", "of", "and", "to", "w", "a", "in", "for"}
norm = lambda s: [w for w in re.sub(r"[^a-z0-9 ]", " ", translit(plain(s)).lower()).split() if w not in STOP]
def find(target, src):
    tw = set(norm(target))
    best, bs, bl = None, 0, 0
    for n in nodes:
        if n["id"] == src["id"]: continue
        kw = set(norm(n["title_plain"]))
        if not kw: continue
        score = len(kw & tw) / len(kw) * (1 if n["map"] == src["map"] else .8)
        if score > bs or (score == bs and len(kw) > bl): best, bs, bl = n["id"], score, len(kw)
    if bs >= 0.75: return best
    # the target's words all inside a longer heading: the shortest such heading, this map first
    cands = [(n["map"] != src["map"], len(set(norm(n["title_plain"]))), n["id"]) for n in nodes
             if n["id"] != src["id"] and tw and tw <= set(norm(n["title_plain"]))]
    return min(cands)[2] if cands else None

pairs = set(); unresolved = []
for n in nodes: n["links"] = []
byid = {n["id"]: n for n in nodes}
for n in nodes:
    for part in n["links_txt"].split(";"):
        p = part.strip()
        if not p: continue
        incoming = p.startswith("←")
        name = re.sub(r"^[←→↓↑↕\-\s]*", "", p)
        label = "vs" if re.match(r"^vs\.?\s", name, re.I) else ""
        name = re.sub(r"^vs\.?\s*", "", name, flags=re.I)
        tgt = find(name, n)
        if not tgt:
            unresolved.append(n["title_plain"] + " -> " + name); continue
        a, b = (tgt, n["id"]) if incoming else (n["id"], tgt)
        k = tuple(sorted((a, b)))
        if k in pairs: continue
        pairs.add(k)
        byid[a]["links"].append({"to": b, **({"label": label} if label else {})})

data = [{"id": n["id"], "map": n["map"], "title": inline(n["title_plain"]), "star": n["hint"], "rect": n["rect"],
         "body": to_html(n["lines"]), "links": n["links"]} for n in nodes]
OUT.write_text(json.dumps({"nodes": data}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
for k in MAPS: print(k, sum(1 for d in data if d["map"] == k), "nodes")
print(len(data), "nodes,", sum(len(d["links"]) for d in data), "links; duplicates dropped:", [(n["map"], n["title"], n["src"]) for n in dropped])
print("no position:", nopos)
print("unresolved links:", len(unresolved)); [print("   ", u) for u in unresolved]
