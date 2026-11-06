
(function () {
  function esc(s) { return String(s).split("&").join("&amp;").split("<").join("&lt;").split('"').join("&quot;"); }
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
