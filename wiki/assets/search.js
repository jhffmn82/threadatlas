
const S = JSON.parse(document.getElementById("settings").textContent);
const LIBRARY = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.5.1";
const loaded = {};
let words = null, library = null, embedder = null, tokenizer = null, reranker = null;
// the reranker runs on the graphics card when the browser offers one; the embedder runs on the processor, where its
// vectors match the store's exactly
const DEVICE = navigator.gpu ? "webgpu" : "wasm";

function status(text) { document.getElementById("status").textContent = text; }
function esc(s) { return String(s).split("&").join("&amp;").split("<").join("&lt;").split('"').join("&quot;"); }

// the words of a text, as the build split them: lower case, accents dropped, runs of letters or digits
function split(text) {
  const out = [];
  let word = "";
  const s = text.toLowerCase().normalize("NFD");
  for (let i = 0; i < s.length; i++) {
    const ch = s[i], code = s.charCodeAt(i);
    if (code >= 0x300 && code <= 0x36f) continue;
    if (ch.toLowerCase() !== ch.toUpperCase() || (ch >= "0" && ch <= "9")) word += ch;
    else if (word) { out.push(word); word = ""; }
  }
  if (word) out.push(word);
  return out;
}

async function loadShard(shard) {
  if (loaded[shard]) return;
  status("Loading " + shard + "...");
  const parts = await Promise.all([fetch("s/" + shard + ".json").then(function (r) { return r.json(); }),
                                   fetch("s/" + shard + ".bin").then(function (r) { return r.arrayBuffer(); })]);
  const data = parts[0], vectors = new Int8Array(parts[1]);
  let row = 0;
  for (const r of data.records) {
    r.row = row; r.vectors = vectors; row += r.n;
    r.work = r.w >= 0 ? data.docs[r.w] : null;
  }
  loaded[shard] = data;
}

// the records a search may return: every record of the chosen shards, a parent once; with the graph only, no chunk
function scopeOf(shards, records) {
  const scope = new Map();
  for (const shard of shards) for (const r of loaded[shard].records) {
    if (records === "graph" && r.k === "h") continue;
    if (!scope.has(r.i)) scope.set(r.i, r);
  }
  return scope;
}

// the records the two searches return: with chunks only, the chunks alone, as retrieval's chunks-only arm searches
function entriesOf(scope, records) {
  if (records !== "chunks") return scope;
  const only = new Map();
  for (const entry of scope) if (entry[1].k === "h") only.set(entry[0], entry[1]);
  return only;
}

async function embed(question) {
  if (!library) library = await import(LIBRARY);
  if (!embedder) { status("Loading the embedding model..."); embedder = await library.pipeline("feature-extraction", S.MODEL, { dtype: "fp16", device: "wasm" }); }
  const out = await embedder([question], { pooling: "cls", normalize: true });
  return out.data;
}

// step 1: every record's similarity, the best of its rows
function similarities(scope, q) {
  const score = new Map();
  for (const r of scope.values()) {
    let best = -Infinity;
    for (let j = 0; j < r.n; j++) {
      const at = (r.row + j) * 384;
      let d = 0;
      for (let k = 0; k < 384; k++) d += q[k] * r.vectors[at + k];
      if (d > best) best = d;
    }
    score.set(r.i, best / S.scale);
  }
  return score;
}

function bestFirst(ids, value) {
  const list = Array.from(ids);
  list.sort(function (a, b) { return (value.get(b) - value.get(a)) || (a - b); });
  return list;
}

// step 2: bm25 as FTS5 counts it, over the whole index, for the question's words joined by OR
function keywordHits(scope, question) {
  if (!words) return [];
  const terms = Array.from(new Set(split(question)));
  const score = new Map();
  const k1 = 1.2, b = 0.75;
  for (const r of scope.values()) {
    if (r.k === "p") continue;
    if (!r.split) { r.split = split(r.t || r.s); }
    let total = 0;
    for (const term of terms) {
      let tf = 0;
      for (const w of r.split) if (w === term) tf++;
      if (!tf) continue;
      const n = words.df[term] || 0;
      let idf = Math.log((words.N - n + 0.5) / (n + 0.5));
      if (idf <= 0) idf = 1e-6;
      total += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * r.split.length / words.avgdl));
    }
    if (total > 0) score.set(r.i, total);
  }
  return bestFirst(score.keys(), score).slice(0, S.K_ENTRY);
}

// step 3: the two lists fused by rank
function fuse(lists) {
  const rrf = new Map();
  for (const list of lists) for (let rank = 1; rank <= list.length; rank++) {
    const id = list[rank - 1];
    rrf.set(id, (rrf.get(id) || 0) + 1 / (S.RRF_K + rank));
  }
  return rrf;
}

function instanceAbstracts(scope, parent, skip) {
  const out = [];
  for (const pair of parent.x) if (pair[0] !== skip && scope.has(pair[1])) out.push(pair[1]);
  return out;
}

// step 4: the hits, and for each parent hit the abstracts of its instances
function makePool(scope, sim, rrf) {
  const pool = new Map();
  const entries = bestFirst(rrf.keys(), rrf);
  for (const id of entries) if (scope.get(id).k !== "p")
    pool.set(id, { hops: 0, edge: "entry", from: null, score: rrf.get(id) + 1e-12 * sim.get(id) });
  for (const id of entries) {
    const parent = scope.get(id);
    if (parent.k !== "p") continue;
    const candidates = Array.from(new Set(instanceAbstracts(scope, parent, null)));
    for (const a of bestFirst(candidates, sim).slice(0, S.PARENT_INSTANCES))
      if (!pool.has(a)) pool.set(a, { hops: 1, edge: "parent", from: id, score: rrf.get(id) + 1e-12 * sim.get(a) });
  }
  return pool;
}

function edgesOf(scope, r, parents) {
  const edges = {};
  for (const name in r.e) {
    const kept = [];
    for (const id of r.e[name]) if (scope.has(id)) kept.push(id);
    edges[name] = kept;
  }
  if (parents && r.p !== undefined && scope.has(r.p)) edges.parent = instanceAbstracts(scope, scope.get(r.p), r.m);
  return edges;
}

// step 5: hops steps out from the best-placed records; what they reach is a third ranked list
function walk(scope, sim, pool, hops, parents) {
  const placed = new Map();
  for (const entry of pool) placed.set(entry[0], entry[1].score);
  let frontier = bestFirst(pool.keys(), placed).slice(0, S.FRONTIER);
  const walked = new Map(), values = new Map();
  for (let hop = 1; hop <= hops; hop++) {
    const reached = new Map();
    for (const id of frontier) {
      const edges = edgesOf(scope, scope.get(id), parents);
      for (const edge in edges) {
        const candidates = new Set(edges[edge]);
        candidates.delete(id);
        for (const c of bestFirst(candidates, sim).slice(0, S.K_HOP)) {
          if (pool.has(c)) continue;
          const value = sim.get(c) * Math.pow(S.DISCOUNT, hop);
          if (values.has(c) && values.get(c) >= value) continue;
          walked.set(c, { hops: hop, edge: edge, from: id });
          values.set(c, value);
          reached.set(c, value);
        }
      }
    }
    frontier = bestFirst(reached.keys(), reached).slice(0, S.FRONTIER);
  }
  let rank = 1;
  for (const id of bestFirst(walked.keys(), values)) {
    const item = walked.get(id);
    item.score = 1 / (S.RRF_K + rank) + 1e-12 * sim.get(id);
    pool.set(id, item);
    rank++;
  }
}

function rerankText(r) { return r.q ? r.s + " " + r.q : r.s; }

// the cross-encoder's score of the question with every record of the pool, as retrieval reranks
async function rerank(question, scope, pool) {
  if (!library) library = await import(LIBRARY);
  if (!reranker) {
    status("Loading the reranker...");
    tokenizer = await library.AutoTokenizer.from_pretrained(S.RERANKER);
    reranker = await library.AutoModelForSequenceClassification.from_pretrained(S.RERANKER, { dtype: "fp32", device: DEVICE });
  }
  // scored shortest first, so each batch pads to texts of about its own length
  const top = Array.from(pool.keys());
  top.sort(function (a, b) { return rerankText(scope.get(a)).length - rerankText(scope.get(b)).length; });
  for (let at = 0; at < top.length; at += 16) {
    status("Reranking " + (at + 1) + " to " + Math.min(at + 16, top.length) + " of " + top.length + "...");
    const texts = [];
    for (const id of top.slice(at, at + 16)) texts.push(rerankText(scope.get(id)));
    const questions = [];
    for (let i = 0; i < texts.length; i++) questions.push(question);
    const inputs = tokenizer(questions, { text_pair: texts, padding: true, truncation: true });
    const out = await reranker(inputs);
    for (let i = 0; i < texts.length; i++) {
      const item = pool.get(top[at + i]);
      item.cross = out.logits.data[i];
      item.score = item.cross + 1e-9 * item.score;
    }
  }
}

const KINDS = { f: "fact", c: "cell", a: "abstract", h: "chunk", p: "parent" };

function short(text, n) { return text.length <= n ? text : text.slice(0, n).split(" ").slice(0, -1).join(" ") + "..."; }

function how(scope, item, ranks) {
  if (item.edge === "entry") {
    const parts = [];
    if (ranks.meaning.has(item.id)) parts.push("meaning #" + ranks.meaning.get(item.id));
    if (ranks.keyword.has(item.id)) parts.push("keywords #" + ranks.keyword.get(item.id));
    return "a hit: " + parts.join(", ");
  }
  const from = scope.get(item.from);
  const where = KINDS[from.k] + ' <a href="' + esc(from.u) + '">' + esc(short(from.k === "p" || from.k === "f" ? from.s : from.l, 70)) + "</a>";
  if (item.edge === "parent" && item.hops === 1 && from.k === "p") return "brought in by the hit on " + where;
  return item.hops + (item.hops === 1 ? " hop" : " hops") + " along " + item.edge + " from the " + where;
}

function show(scope, pool, ranks, seconds) {
  const placed = new Map();
  for (const entry of pool) { entry[1].id = entry[0]; placed.set(entry[0], entry[1].score); }
  const order = bestFirst(pool.keys(), placed).slice(0, S.SHOWN);
  let html = "";
  for (const id of order) {
    const r = scope.get(id), item = pool.get(id);
    let text = "<p>" + esc(r.s) + "</p>";
    if (r.q) text += '<blockquote>' + esc(r.q) + "</blockquote>";
    const cross = item.cross === undefined ? "" : " &middot; reranker " + item.cross.toFixed(2);
    html += '<li class="result"><div class="where"><span class="tag">' + KINDS[r.k] + '</span> <a href="' + esc(r.u) + '">' + esc(r.l) + "</a></div>"
         + text + '<div class="found">' + how(scope, item, ranks) + cross + "</div></li>";
  }
  document.getElementById("results").innerHTML = html;
  status(pool.size + " records in the pool, the first " + order.length + " shown, in " + seconds.toFixed(1) + " s.");
}

async function search(e) {
  e.preventDefault();
  const question = document.getElementById("question").value.trim();
  const button = document.querySelector("#ask button");
  if (!question || button.disabled) return;
  button.disabled = true;
  try { await run(question); } finally { button.disabled = false; }
}

async function run(question) {
  const started = performance.now();
  const chosen = document.getElementById("scope").value;
  const shards = chosen === "all" ? S.shards : [chosen];
  const mode = document.getElementById("how").value;
  const hops = Number(document.querySelector("input[name=hops]:checked").value);
  const records = document.getElementById("records").value;
  if (!words) words = await fetch("s/words.json").then(function (r) { return r.json(); });
  for (const shard of shards) await loadShard(shard);
  const scope = scopeOf(shards, records);
  const searched = entriesOf(scope, records);
  status("Embedding the question...");
  const q = await embed(question);
  status("Searching " + scope.size.toLocaleString() + " records...");
  const sim = similarities(scope, q);
  const meaning = mode === "keyword" ? [] : bestFirst(searched.keys(), sim).slice(0, S.K_ENTRY).slice(0, S.HITS);
  const keyword = mode === "meaning" ? [] : keywordHits(searched, question).slice(0, S.HITS);
  const ranks = { meaning: new Map(), keyword: new Map() };
  for (let i = 0; i < meaning.length; i++) ranks.meaning.set(meaning[i], i + 1);
  for (let i = 0; i < keyword.length; i++) ranks.keyword.set(keyword[i], i + 1);
  const pool = makePool(scope, sim, fuse([meaning, keyword]));
  if (hops > 0) walk(scope, sim, pool, hops, records !== "chunks");
  if (document.getElementById("rerank").checked && pool.size) await rerank(question, scope, pool);
  show(scope, pool, ranks, (performance.now() - started) / 1000);
}

document.getElementById("ask").addEventListener("submit", search);

// a question from a search box on another page: searched at once over every work, the other settings as the page opens
const asked = new URLSearchParams(location.search).get("q");
if (asked && asked.trim()) {
  document.getElementById("question").value = asked.trim();
  document.getElementById("scope").value = "all";
  document.getElementById("ask").requestSubmit();
}
