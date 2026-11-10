
(function () {
  function esc(s) { return String(s).split("&").join("&amp;").split("<").join("&lt;").split('"').join("&quot;"); }
  // the search's two models: their files fetched into the cache transformers.js reads, a moment after the page loads,
  // so a search finds them there; the search page loads its models itself
  var MODEL_FILES = ["https://huggingface.co/Xenova/bge-small-en-v1.5/resolve/main/config.json", "https://huggingface.co/Xenova/bge-small-en-v1.5/resolve/main/tokenizer_config.json", "https://huggingface.co/Xenova/bge-small-en-v1.5/resolve/main/tokenizer.json", "https://huggingface.co/Xenova/bge-small-en-v1.5/resolve/main/onnx/model_fp16.onnx", "https://huggingface.co/Xenova/ms-marco-MiniLM-L-6-v2/resolve/main/config.json", "https://huggingface.co/Xenova/ms-marco-MiniLM-L-6-v2/resolve/main/tokenizer_config.json", "https://huggingface.co/Xenova/ms-marco-MiniLM-L-6-v2/resolve/main/tokenizer.json", "https://huggingface.co/Xenova/ms-marco-MiniLM-L-6-v2/resolve/main/onnx/model.onnx"];
  function warm() {
    var line = navigator.connection;
    if (line && (line.saveData || line.effectiveType === "slow-2g" || line.effectiveType === "2g" || line.effectiveType === "3g")) return;
    caches.open("transformers-cache").then(function (cache) {
      return cache.keys().then(function (keys) {
        var have = {}, missing = [];
        for (var i = 0; i < keys.length; i++) have[keys[i].url] = true;
        for (var j = 0; j < MODEL_FILES.length; j++) if (!have[MODEL_FILES[j]]) missing.push(MODEL_FILES[j]);
        return cache.addAll(missing);
      });
    }).catch(function () {});
  }
  if (window.caches && !document.getElementById("settings")) window.addEventListener("load", function () { setTimeout(warm, 1000); });
  var data = document.getElementById("facts");
  if (!data) return;
  var facts = JSON.parse(data.textContent), pop = document.getElementById("pop"), cited = document.getElementById("cited");
  function spansOf(n) {
    var out = [], all = document.querySelectorAll(".q");
    for (var i = 0; i < all.length; i++) if ((" " + all[i].getAttribute("data-f") + " ").indexOf(" " + n + " ") >= 0) out.push(all[i]);
    return out;
  }
  // a link from a search result: #p-a-b marks the stretch from character a to character b of the text shown
  function passage() {
    var ends = location.hash.slice(3).split("-"), a = Number(ends[0]), b = Number(ends[1]);
    var walker = document.createTreeWalker(document.querySelector(".text"), NodeFilter.SHOW_TEXT);
    var range = document.createRange(), at = 0, node, last = null, started = false, ended = false;
    while ((node = walker.nextNode())) {
      var end = at + node.length;
      if (!started && a < end) { range.setStart(node, a - at); started = true; }
      if (started && b <= end) { range.setEnd(node, b - at); ended = true; break; }
      at = end;
      last = node;
    }
    if (!started) return;
    if (!ended) range.setEnd(last, last.length);
    if (window.CSS && CSS.highlights && window.Highlight) CSS.highlights.set("passage", new Highlight(range));
    cited.innerHTML = "<b>The passage this search result was read from, highlighted below.</b>";
    cited.hidden = false;
    window.scrollTo(0, window.scrollY + range.getBoundingClientRect().top - window.innerHeight / 3);
  }
  function highlight() {
    var id = decodeURIComponent(location.hash.slice(3));
    document.querySelectorAll(".q.hit").forEach(function (s) { s.classList.remove("hit"); });
    if (window.CSS && CSS.highlights) CSS.highlights.delete("passage");
    if (location.hash.indexOf("#p-") === 0) { passage(); return; }
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
