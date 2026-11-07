
// the search page: the form and the results; the search itself runs in a worker (search-worker.js), so the page
// never waits on it
const S = JSON.parse(document.getElementById("settings").textContent);
const button = document.querySelector("#ask button");
const worker = new Worker(new URL("search-worker.js", import.meta.url), { type: "module" });

function status(text) { document.getElementById("status").textContent = text; }
function finish() { button.disabled = false; }

worker.onmessage = function (e) {
  const m = e.data;
  if (m.type === "status") status(m.text);
  if (m.type === "done") { document.getElementById("results").innerHTML = m.html; status(m.text); finish(); }
  if (m.type === "error") { status("The search stopped: " + m.text + ". Search again to retry."); finish(); }
};
worker.onerror = function (e) { status("The search stopped: " + (e.message || "the search could not run") + ". Search again to retry."); finish(); };
worker.postMessage({ type: "init", settings: S, base: new URL("s/", location.href).href });

function search(e) {
  e.preventDefault();
  const question = document.getElementById("question").value.trim();
  if (!question || button.disabled) return;
  button.disabled = true;
  status("Searching...");
  worker.postMessage({
    type: "search",
    question: question,
    scope: document.getElementById("scope").value,
    mode: document.getElementById("how").value,
    records: document.getElementById("records").value,
    hops: Number(document.querySelector("input[name=hops]:checked").value),
    rerank: document.getElementById("rerank").checked
  });
}

document.getElementById("ask").addEventListener("submit", search);

// a question from a search box on another page: searched at once over every work, the other settings as the page opens
const asked = new URLSearchParams(location.search).get("q");
if (asked && asked.trim()) {
  document.getElementById("question").value = asked.trim();
  document.getElementById("scope").value = "all";
  document.getElementById("ask").requestSubmit();
}
