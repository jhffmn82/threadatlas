
(function () {
  var up = document.body.getAttribute("data-up") || "";
  var index = null;
  function load(then) {
    if (index) { then(); return; }
    fetch(up + "search.json").then(function (r) { return r.json(); }).then(function (rows) { index = rows; then(); });
  }
  function find(query) {
    var q = query.toLowerCase().trim(), found = [];
    if (!q) return [];
    function tier(name) {
      name = name.toLowerCase();
      if (name === q) return 3;
      if (name.indexOf(q) === 0 || name.indexOf(" " + q) >= 0) return 2;
      if (name.indexOf(q) > 0) return 1;
      return 0;
    }
    for (var i = 0; i < index.length; i++) {
      var best = tier(index[i][0]), names = index[i][4] || [];
      for (var k = 0; k < names.length; k++) best = Math.max(best, tier(names[k]));
      if (best) found.push([best, index[i]]);
    }
    function byTier(a, b) { return (b[0] - a[0]) || (b[1][3] - a[1][3]); }
    found.sort(byTier);
    var out = [];
    for (var j = 0; j < found.length && j < 12; j++) out.push(found[j][1]);
    return out;
  }
  function esc(s) { return String(s).split("&").join("&amp;").split("<").join("&lt;").split('"').join("&quot;"); }
  document.querySelectorAll(".search").forEach(function (box) {
    var input = box.querySelector("input"), hits = box.querySelector(".hits");
    input.addEventListener("input", function () {
      load(function () {
        var rows = find(input.value), html = "";
        for (var i = 0; i < rows.length; i++) html += '<a href="' + up + rows[i][2] + '">' + esc(rows[i][0]) + "<small>" + esc(rows[i][1]) + "</small></a>";
        hits.innerHTML = html;
      });
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { var first = hits.querySelector("a"); if (first) location.href = first.href; }
    });
    document.addEventListener("click", function (e) { if (!box.contains(e.target)) hits.innerHTML = ""; });
  });
  var data = document.getElementById("facts");
  if (!data) return;
  var facts = JSON.parse(data.textContent), pop = document.getElementById("pop"), cited = document.getElementById("cited");
  function spansOf(n) {
    var out = [], all = document.querySelectorAll(".q");
    for (var i = 0; i < all.length; i++) if ((" " + all[i].getAttribute("data-f") + " ").indexOf(" " + n + " ") >= 0) out.push(all[i]);
    return out;
  }
  function highlight() {
    var id = decodeURIComponent(location.hash.slice(3));
    document.querySelectorAll(".q.hit").forEach(function (s) { s.classList.remove("hit"); });
    if (location.hash.indexOf("#f-") !== 0) { cited.hidden = true; return; }
    for (var n = 0; n < facts.length; n++) {
      if (facts[n][0] === id) {
        var spans = spansOf(n);
        spans.forEach(function (s) { s.classList.add("hit"); });
        cited.innerHTML = "<b>Cited quote, highlighted below.</b> " + esc(facts[n][1]) + (facts[n][2] ? ' &middot; <a href="' + facts[n][2] + '">back to the entity</a>' : "");
        cited.hidden = false;
        if (spans.length) spans[0].scrollIntoView({ block: "center" });
        return;
      }
    }
  }
  window.addEventListener("hashchange", highlight);
  highlight();
  document.querySelector(".text").addEventListener("click", function (e) {
    var span = e.target.closest(".q");
    if (!span) { pop.hidden = true; return; }
    var list = span.getAttribute("data-f").split(" "), html = "<b>Facts quoting this passage</b><ul>";
    for (var i = 0; i < list.length; i++) {
      var f = facts[Number(list[i])];
      html += "<li>" + (f[2] ? '<a href="' + f[2] + '">' + esc(f[1]) + "</a>" : esc(f[1])) + "</li>";
    }
    pop.innerHTML = html + "</ul>";
    pop.style.left = Math.min(e.pageX, window.innerWidth - 420) + "px";
    pop.style.top = (e.pageY + 14) + "px";
    pop.hidden = false;
    e.stopPropagation();
  });
  document.addEventListener("click", function (e) { if (!pop.contains(e.target)) pop.hidden = true; });
})();
