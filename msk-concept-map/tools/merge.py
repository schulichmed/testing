# Merge transcription (map-data-linked.json from convert.py + chart_links.py), detected boxes (blobs.json)
# and the agents' matches (match_*.tsv) into the page's nodes.json.
# usage: python -I merge.py <map-data-linked.json> <ov dir with blobs.json + match_*.tsv> <out nodes.json>
import json, sys, glob, os
d = json.load(open(sys.argv[1], encoding="utf-8"))
B = {b["id"]: b for b in json.load(open(os.path.join(sys.argv[2], "blobs.json")))["blobs"]}
M = {}
for f in glob.glob(os.path.join(sys.argv[2], "match_*.tsv")):
    for line in open(f, encoding="utf-8"):
        p = line.strip().split("\t")
        if len(p) == 2: M[p[0]] = p[1]
miss = []
for n in d["nodes"]:
    m = M.get(n["id"], "none")
    if m.startswith("box:"):
        b = B[int(m[4:])]; n["rect"] = [b["x"], b["y"], b["w"], b["h"]]
    elif m.startswith("xy:"):
        x, y = map(int, m[3:].split(",")); n["rect"] = [x, y, 300, 60]
    else:
        miss.append(n["id"])
    for k in ("r", "c", "hub", "summary"): n.pop(k, None)
d["nodes"] = [n for n in d["nodes"] if "rect" in n]
print("positioned", len(d["nodes"]), "missing", miss)
json.dump(d, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
