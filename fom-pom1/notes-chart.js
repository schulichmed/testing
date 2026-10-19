/* Interactive note charts for one block: the lecture's tables and flowcharts, word for word
   from the portal's notes data, with Look / Walk / Test. D = {course, block, lectures} is set
   by the page. */
(function () {
var SPINE = /caus|etiolog|risk|path|mechan|present|clinical|feature|symptom|sign|exam|diagnos|\bdx\b|investig|work.?up|\blab|imaging|treat|\btx\b|manag|therap|prognos|\bpx\b|complic|epidem|defin|course|histo|finding|onset|location|\bage\b|incidence|prevalence|indication|adverse|side effect|contraind|monitor|dose|example|class|action|function|origin|innervat|supply|cell|morpholog/i;
var MODE = "look", lec = null, MERMAID = null;
var $ = function (s, r) { return (r || document).querySelector(s); };
function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
function text(h) { var d = document.createElement("div"); d.innerHTML = h || ""; return (d.textContent || "").replace(/\s+/g, " ").trim(); }
function blank(h) { var t = text(h); return !t || /^[\/—–-]$/.test(t); }

/* ---------- lecture picker ---------- */
var pick = $("#pick"), body = $("#body"), bar = $("#bar");
var byId = {};
D.lectures.forEach(function (l) { byId[l.id] = l; });
var weeks = {};
D.lectures.forEach(function (l) { (weeks[l.week] = weeks[l.week] || []).push(l); });
Object.keys(weeks).forEach(function (w) {
  var g = el("optgroup"); g.label = weeks[w][0].weekLabel;
  weeks[w].forEach(function (l) { var o = el("option", null, l.num + " - " + l.name); o.value = l.id; g.appendChild(o); });
  pick.appendChild(g);
});
pick.addEventListener("change", function () { location.hash = pick.value; });
function step(d) { var i = D.lectures.indexOf(lec) + d; if (i >= 0 && i < D.lectures.length) location.hash = D.lectures[i].id; }
$("#prev").addEventListener("click", function () { step(-1); });
$("#next").addEventListener("click", function () { step(1); });

/* ---------- tables ---------- */
function shape(b) {
  var rows = b.rows, n = (b.cols || []).length || (rows[0] || []).length;
  var label = rows.length > 1 && rows.every(function (r) { var t = text(r[0]); return t && t.length <= 45; });
  var spine = label && rows.filter(function (r) { return SPINE.test(text(r[0])); }).length >= rows.length / 2;
  if (spine && n >= 3) return { unit: "col", first: 1 };
  return { unit: "row", first: label ? 1 : 0 };
}
function tableBlock(b) {
  var box = el("div", "tblock"), sh = shape(b);
  if (b.lead) { var ld = el("div", "lead"); ld.innerHTML = b.lead; box.appendChild(ld); }
  var wrap = el("div", "tscroll"), t = el("table", "nt");
  if (b.cols && b.cols.length) {
    var hr = el("tr");
    b.cols.forEach(function (c, i) { var th = el("th"); th.innerHTML = c; if (sh.unit === "col" && i >= sh.first) th.dataset.u = i; hr.appendChild(th); });
    var th = el("thead"); th.appendChild(hr); t.appendChild(th);
  }
  var tb = el("tbody");
  b.rows.forEach(function (r, ri) {
    var tr = el("tr");
    r.forEach(function (c, ci) {
      var td = el(ci < sh.first ? "th" : "td"); td.innerHTML = c;
      if (ci < sh.first) td.scope = "row";
      var u = sh.unit === "col" ? ci : ri;
      if (ci >= sh.first || sh.unit === "col" && ci >= sh.first) td.dataset.u = u;
      if (sh.unit === "row" && ci < sh.first) td.dataset.u = u;
      if (ci >= sh.first && !blank(c)) td.classList.add("rv");
      tr.appendChild(td);
    });
    tb.appendChild(tr);
  });
  t.appendChild(tb); wrap.appendChild(t); box.appendChild(wrap);
  box.dataset.unit = sh.unit;
  t.addEventListener("click", function (e) {
    var c = e.target.closest("[data-u]"); if (!c) return;
    var u = c.dataset.u, cells = t.querySelectorAll('[data-u="' + u + '"]');
    if (MODE === "look") {
      var on = t.classList.contains("focus") && t.dataset.f === u;
      t.classList.toggle("focus", !on); t.dataset.f = on ? "" : u;
      t.querySelectorAll(".on").forEach(function (x) { x.classList.remove("on"); });
      if (!on) cells.forEach(function (x) { x.classList.add("on"); });
    } else if (MODE === "test") {
      var nxt = t.querySelector('.hid[data-u="' + u + '"]'); if (!nxt) return;
      nxt.classList.remove("hid", "next");
      var n2 = t.querySelector('.hid[data-u="' + u + '"]'); if (n2) n2.classList.add("next");
    }
  });
  return box;
}

/* ---------- flowcharts ---------- */
function loadMermaid() {
  if (MERMAID) return MERMAID;
  MERMAID = new Promise(function (res, rej) {
    var s = document.createElement("script");
    s.src = "https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js";
    s.onload = function () {
      window.mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "base",
        themeVariables: { primaryColor: "#efe8f6", primaryBorderColor: "#7a3fb0", primaryTextColor: "#201436", lineColor: "#6b6380", fontFamily: "Inter, sans-serif", fontSize: "14px" },
        flowchart: { htmlLabels: true, useMaxWidth: true } });
      res(window.mermaid);
    };
    s.onerror = rej; document.head.appendChild(s);
  });
  return MERMAID;
}
var seq = 0;
function pathBlock(b) {
  var box = el("div", "pblock"), fig = el("div", "pfig"), walk = el("div", "pwalk");
  box.appendChild(fig); box.appendChild(walk);
  loadMermaid().then(function (m) {
    var id = "pw" + (++seq);
    return m.render(id, b.mermaid).then(function (r) {
      fig.innerHTML = r.svg;
      return m.mermaidAPI.getDiagramFromText(b.mermaid);
    }).then(function (dg) { graph(dg, fig, walk, box); });
  }).catch(function () { fig.textContent = "This flowchart could not be drawn."; });
  return box;
}
function graph(dg, fig, walk, box) {
  var V = dg.db.getVertices(), E = dg.db.getEdges();
  var verts = V instanceof Map ? Object.fromEntries(V) : V;
  var out = {}, inc = {};
  E.forEach(function (e) { (out[e.start] = out[e.start] || []).push(e); inc[e.end] = 1; });
  var ids = Object.keys(verts);
  var branching = ids.some(function (k) { return (out[k] || []).length > 1; });
  if (!branching) return;           // a straight chain has nothing to ask
  box.classList.add("can-walk");
  var start = ids.filter(function (k) { return !inc[k]; })[0] || ids[0];
  var svg = fig.querySelector("svg");
  function nodeEl(k) { return svg && svg.querySelector('g.node[id^="flowchart-' + k + '-"]'); }
  var trail = [];
  function at(k) {
    walk.innerHTML = "";
    if (svg) { svg.classList.add("walking"); svg.querySelectorAll(".on").forEach(function (x) { x.classList.remove("on"); }); }
    trail.concat([k]).forEach(function (x) { var n = nodeEl(x); if (n) n.classList.add("on"); });
    var n = nodeEl(k); if (n) n.scrollIntoView({ block: "nearest", behavior: "smooth" });
    walk.appendChild(el("p", "q", text(verts[k].text)));
    var a = el("div", "ans"); walk.appendChild(a);
    var outs = out[k] || [];
    if (!outs.length) walk.insertBefore(el("p", "qh", "End of this branch."), a);
    outs.forEach(function (e) {
      var lab = text(e.text) || (outs.length === 1 ? "Next →" : text(verts[e.end].text));
      var btn = el("button", null, lab); a.appendChild(btn);
      btn.addEventListener("click", function () { trail.push(k); at(e.end); });
    });
    var r = el("button", "ghost", "Start again"); a.appendChild(r);
    r.addEventListener("click", function () { trail = []; at(start); });
  }
  box.walkStart = function () { trail = []; at(start); };
  box.walkStop = function () { walk.innerHTML = ""; if (svg) { svg.classList.remove("walking"); svg.querySelectorAll(".on").forEach(function (x) { x.classList.remove("on"); }); } };
  if (MODE === "walk") box.walkStart();
}

/* ---------- modes ---------- */
function apply() {
  body.classList.toggle("is-look", MODE === "look");
  body.classList.toggle("is-test", MODE === "test");
  body.querySelectorAll("table.nt").forEach(function (t) {
    t.classList.remove("focus"); t.dataset.f = "";
    t.querySelectorAll(".on").forEach(function (x) { x.classList.remove("on"); });
    t.querySelectorAll(".hid").forEach(function (x) { x.classList.remove("hid", "next"); });
    if (MODE === "test") {
      var us = {};
      t.querySelectorAll(".rv").forEach(function (c) { c.classList.add("hid"); if (!us[c.dataset.u]) { us[c.dataset.u] = 1; c.classList.add("next"); } });
    }
  });
  body.querySelectorAll(".pblock.can-walk").forEach(function (p) { if (MODE === "walk") p.walkStart(); else p.walkStop(); });
  var tips = {
    look: "Click a column (or row) of any table to focus it and fade the rest. Click it again to see everything.",
    walk: "Every flowchart that branches asks its questions here: answer them from the top and the route lights up.",
    test: "Each table starts with only its labels showing. Recall the next box, then tap that column (or row) to check it; each tap reveals one more, in order."
  };
  bar.textContent = tips[MODE];
  var nP = body.querySelectorAll(".pblock.can-walk").length, nT = body.querySelectorAll("table.nt").length;
  if (MODE === "walk" && !nP) bar.textContent = "This lecture has no branching flowchart to walk. Try Look or Test.";
  if (MODE !== "walk" && !nT) bar.textContent = "This lecture has no table. Try Walk.";
}
document.querySelectorAll("#modes .chip").forEach(function (b) {
  b.addEventListener("click", function () {
    MODE = b.dataset.mode;
    document.querySelectorAll("#modes .chip").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
    apply();
  });
});

/* ---------- render a lecture ---------- */
function show() {
  var id = decodeURIComponent(location.hash.slice(1));
  lec = byId[id] || D.lectures[0];
  pick.value = lec.id;
  body.innerHTML = "";
  body.appendChild(el("h2", "ltitle", lec.title || lec.name));
  if (lec.framing) { var f = el("div", "framing"); f.innerHTML = lec.framing; body.appendChild(f); }
  lec.items.forEach(function (b) {
    if (b.t === "table") body.appendChild(tableBlock(b));
    else if (b.t === "pathway") body.appendChild(pathBlock(b));
    else if (b.t === "head") { var h = el("div", "shead"); h.innerHTML = b.html; body.appendChild(h); }
  });
  $("#prev").disabled = D.lectures.indexOf(lec) === 0;
  $("#next").disabled = D.lectures.indexOf(lec) === D.lectures.length - 1;
  apply();
  window.scrollTo({ top: 0 });
}
window.addEventListener("hashchange", show);
show();
})();
