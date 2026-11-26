# Parse the quadrant transcriptions (q_*.md) into map nodes and inline them into the page.
import re, json, sys, html, pathlib

HI = pathlib.Path(sys.argv[1]); PAGE = pathlib.Path(sys.argv[2]); OUT = pathlib.Path(sys.argv[3])

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "node"

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    return s

def plain(s):
    return re.sub(r"\*+", "", s)

nodes, raw_links = [], []
for f in sorted(HI.glob("q_*.md")):
    quad = f.stem[2:]
    cur = None; skip = False
    for line in f.read_text(encoding="utf-8").splitlines():
        if re.match(r"^#\s", line):
            skip = quad == "BR" and line.startswith("# Section A"); continue
        if skip: continue
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m and not line.startswith("###"):
            cur = {"title": m.group(1), "quad": quad, "lines": [], "zone_txt": "", "tile": None, "links_txt": ""}
            nodes.append(cur); continue
        if cur is None or not line.strip() or line.startswith("#") or line.strip() == "---":
            continue
        mm = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if not mm:
            continue
        ind, txt = len(mm.group(1).expandtabs(2)), mm.group(2)
        low = txt.lower()
        if ind == 0 and re.match(r"^(zone|tile|links):", low):
            li = low.find("links:")
            meta = txt[:li] if li >= 0 else txt
            if li >= 0: cur["links_txt"] = txt[li + 6:].strip()
            zt = re.search(r"zone:\s*(.*?)(;|$)", meta, re.I)
            tt = re.search(r"tile:\s*r(\d)\s*c(\d)", meta, re.I)
            if zt: cur["zone_txt"] = zt.group(1)
            if tt: cur["tile"] = (int(tt.group(1)), int(tt.group(2)))
            continue
        cur["lines"].append((ind, txt))

# drop pure section headers (no tile) and edge duplicates (keep the fuller copy)
nodes = [n for n in nodes if n["tile"] and not n["title"].lower().startswith(("map header", "(fragment)", "primary (unprovoked"))]
def dkey(t):
    t = re.sub(r"\((?:[^)]*(?:boundary|duplicate|dashed box|boxed)[^)]*)\)|📍|⭐|❗", "", t.lower())
    t = re.sub(r"^localization to\s+", "", t.strip())
    return re.sub(r"[^a-z0-9]+", " ", t).strip()
best = {}
for n in nodes:
    k = dkey(n["title"])
    if k not in best or len(n["lines"]) > len(best[k]["lines"]):
        if k in best and not n["links_txt"]: n["links_txt"] = best[k]["links_txt"]
        best[k] = n
    elif not best[k]["links_txt"]: best[k]["links_txt"] = n["links_txt"]
nodes = [n for n in nodes if best[dkey(n["title"])] is n]

prev = {}
for n in nodes:
    if not n['zone_txt']: n['zone_txt'] = prev.get(n['quad'], '')
    prev[n['quad']] = n['zone_txt']

def zone_of(n):
    r, c = n["tile"]; z = n["zone_txt"].lower()
    if r >= 3:
        return "local" if c <= 3 else "eye"
    if re.search(r"ophthal|cranial|eye|cerebell|basal|vision|visual|ptosis|diplopia", z): return "eye"
    if re.search(r"umn|lmn|localiz|cortex|spinal", z): return "local"
    if re.search(r"approach|above", z): return "approach"
    return "disorder"

seen = {}
for n in nodes:
    t = n["title"]
    n["loc"] = "📍" in t or t.lower().startswith("localization to")
    t = t.replace("📍", "").strip()
    n["star"] = "⭐" in t or any("⭐" in x for _, x in n["lines"])
    t = re.sub(r"\s*[⭐❗]+\s*", " ", t).strip()
    t = re.sub(r"^localization to\s+", "", t, flags=re.I)
    t = re.sub(r"\s*\((?:[^)]*(?:boundary|duplicate|dashed box|boxed|symbol|flag|badge|vertical section|clinical box|red pin|in VOR diagram|circ|bracket|yellow|stars|highway|diagram|green =)[^)]*)\)", "", t, flags=re.I).strip()
    if sum(ch.isupper() for ch in t) > 0.6 * max(1, sum(ch.isalpha() for ch in t)):
        KEEP = {"CN","CNS","MS","ICP","MCS","SNS","PSNS","CRAO","ION","GCA","ARMD","EOM","HSV","LOC","TIA","SAH","ICH","GBS","ALS","MSA","PSP","VOR","NMJ","UMN","LMN","PEX","AEDS","DR","OM","BPPV","SSCD","CRPS","TRAP","HPI","MCA","ACA","PCA","HHV-6","I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","V1","V2","V3"}
        def fix(w):
            core = re.sub(r"[^A-Za-z0-9-]", "", w)
            return w if core.upper() in KEEP or any(c.isdigit() for c in core) else w[:1] + w[1:].lower()
        t = " ".join(fix(w) for w in t.split(" "))
        t = re.sub(r"(\(|/|-)([a-z])", lambda m: m.group(1) + m.group(2).upper(), t)
    t = re.sub(r"(?<=\S )\b(To|Of|The|And|In|For|W\.|Aka|On|Vs)\b", lambda m: m.group(1).lower(), t)
    t = re.sub(r'(["“])([a-z])', lambda m: m.group(1) + m.group(2).upper(), t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    t = re.sub(r"^([A-Z][A-Z ]{3,}) \(secondary seizure cause\)", lambda m: m.group(1).capitalize() + " (seizure cause)", t, flags=re.I)
    t = t.replace("(TPA)", "(tPA)"); t = re.sub(r"\bCns\b", "CNS", t)
    n["title_plain"] = plain(t)
    base = slug(n["title_plain"]); i = base; k = 2
    while i in seen: i = f"{base}-{k}"; k += 1
    seen[i] = 1; n["id"] = i
    n["zone"] = zone_of(n)
    n["r"], n["c"] = n["tile"]

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

def short(s, n=95):
    s = plain(s)
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"

# link resolution
norm = lambda s: re.sub(r"[^a-z0-9 ]", " ", plain(s).lower()).split()
keys = [(set(norm(n["title_plain"])) - {"the", "of", "and", "to", "w", "a"}, n) for n in nodes]
def find(target, self_id):
    tw = set(norm(target)) - {"the", "of", "and", "to", "w", "a"}
    best, bs = None, 0
    for kw, n in keys:
        if not kw or n["id"] == self_id: continue
        inter = len(kw & tw)
        score = inter / len(kw)
        if score > bs or (score == bs and best and len(kw) > len(keys_by[best]) ):
            best, bs = n["id"], score
    return best if bs >= 0.75 else None
keys_by = {n["id"]: set(norm(n["title_plain"])) for n in nodes}

pairs = set()
for n in nodes:
    n["links"] = []
for n in nodes:
    for part in re.split(r";", n["links_txt"]):
        p = part.strip()
        if not p: continue
        incoming = p.startswith("←")
        label = ""
        q = re.search(r'["“](.+?)["”]', p)
        if re.match(r"^(vs|VS)\b", p) or "VS" in p.split(" ")[:2]: label = "vs"
        name = re.sub(r'\(.*?\)|["“].*?["”]', "", p)
        name = re.sub(r"^[←→↓↑↕—–\-\s]*(VS|vs)?\s*(\(dashed\)|\(dotted\))?\s*", "", name)
        name = re.split(r"\s+(via|into|label|w\.)\s+", name)[0]
        for piece in re.split(r",| and |/", name):
            tgt = find(piece, n["id"])
            if not tgt: continue
            a, b = (tgt, n["id"]) if incoming else (n["id"], tgt)
            key = tuple(sorted((a, b)))
            if key in pairs: continue
            pairs.add(key)
            src = next(x for x in nodes if x["id"] == a)
            src["links"].append({"to": b, **({"label": label} if label else {})})

HUBS = re.compile(r"^(clinical approach|neurological disorders|localization$|cranial nerves$|.*approach to)", re.I)
data = []
for n in nodes:
    tops = [x for i, x in n["lines"] if i == 0]
    data.append({
        "id": n["id"], "title": inline(n["title_plain"]) + (' <span title="Localization" style="opacity:.6">📍</span>' if n["loc"] else ""),
        "zone": n["zone"], "r": n["r"], "c": n["c"], "star": n["star"],
        "hub": bool(HUBS.match(n["title_plain"])),
        "summary": inline(short(tops[0])) if tops else "",
        "body": to_html(n["lines"]), "links": n["links"],
    })

payload = json.dumps({"nodes": data}, ensure_ascii=False, separators=(",", ":"))
open(OUT.parent / "map-data.json", "w", encoding="utf-8", newline="\n").write(payload)
src = PAGE.read_text(encoding="utf-8")
open(OUT, "w", encoding="utf-8", newline="\n").write(src.replace("<!--MAPDATA-->", "<script>window.MAP=" + payload.replace("</", "<\/") + ";</script>"))
print(len(data), "nodes,", sum(len(d["links"]) for d in data), "links,", len(payload) // 1024, "KB data")
