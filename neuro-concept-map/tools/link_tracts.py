import json, re
T = r"C:/Users/nsims/projects/testing/"

# 1. spinal-tracts: deep links (#dcml, #stt, #sct, #lcst, #cbt; #syn-ant/post/cent/bs)
p = T + "spinal-tracts/index.html"; s = open(p, encoding="utf-8").read()
if "function fromHash" not in s:
    n = s.count('pick("grac")'); assert n >= 1, n
    s = s.replace('pick("grac")', '(fromHash()||pick("grac"))', 1)
    hook = '''
function fromHash(){const h=decodeURIComponent(location.hash.slice(1));if(!h||!MAP)return false;
 if(h.startsWith("syn-")&&SYN[h.slice(4)]){showSyn(h.slice(4));return true}
 if(S[h]){const xs=Object.keys(XS).find(k=>XS[k][0]===h);if(xs)pick(xs);else{SYNCUR=null;synOn(null);showStage(h,"")}
  document.querySelector(".play").scrollIntoView({behavior:"auto",block:"start"});return true}
 return false}
addEventListener("hashchange",fromHash);
'''
    i = s.rindex("</script>")
    s = s[:i] + hook + s[i:]
    open(p, "w", encoding="utf-8", newline="\n").write(s)

# 2. concept map: an extra button on the tract and cord-syndrome boxes
EX = {
 "dorsal-column": "dcml", "spinothalamic-tract": "stt", "lateral-corticospinal-tract": "lcst", "spinal-cord-tracts": "",
 "anterior-cord-syndrome": "syn-ant", "posterior-cord-syndrome": "syn-post", "central-cord-syndrome": "syn-cent",
 "brown-s-quard-syndrome": "syn-bs", "sensory-ataxia-proprioceptive": "dcml", "spinal-cord": "",
}
p = T + "neuro-concept-map/nodes.json"; d = json.load(open(p, encoding="utf-8"))
hit = 0
for n in d["nodes"]:
    if n["id"] in EX:
        h = EX[n["id"]]
        n["extras"] = [{"name": "Spinal tracts, animated", "url": "https://schulichmed.github.io/testing/spinal-tracts/" + ("#" + h if h else ""),
                        "what": ("this syndrome" if h.startswith("syn-") else "this tract") if h else "all five tracts"}]
        hit += 1
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

p = T + "neuro-concept-map/index.html"; s = open(p, encoding="utf-8").read()
a = "  const charts = (n.charts || []).map(c => '<button class=\"chartbtn\" data-url=\"' + c.url + '\" data-name=\"' + esc(c.name) + '\">Open the ' + esc(c.name) + ' chart<span>' + (c.col ? \"this diagnosis lit\" : \"whole chart\") + ' ›</span></button>').join(\"\");"
assert a in s
s = s.replace(a, a + "\n  const extras = (n.extras || []).map(x => '<button class=\"chartbtn\" data-url=\"' + x.url + '\" data-name=\"' + esc(x.name) + '\">' + esc(x.name) + '<span>' + esc(x.what) + ' ›</span></button>').join(\"\");", 1)
b = "    (charts ? '<h3>In the portal</h3>' + charts : '') +"
assert b in s
s = s.replace(b, "    (charts || extras ? '<h3>In the portal</h3>' + charts + extras : '') +", 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("linked", hit, "boxes")
