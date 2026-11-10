
// Block 12's search, run in a worker so the page never waits on it: the shards, both searches, the walk, the two
// models. The page sends a question and its settings; the worker sends back its progress and the results.
const LIBRARY = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.5.1";
const KINDS = { f: "fact", c: "cell", a: "abstract", h: "chunk", p: "parent" };
// whose words a result is: a model's, or the source's
const WHOSE = { f: '<span class="by">claim worded by a model, its quotation the source&rsquo;s</span>', c: '<span class="by">written by a model</span>',
                a: '<span class="by">written by a model</span>', h: '<span class="by source">the source&rsquo;s own words</span>' };
let S = null, base = "";
const shards = {};
let words = null, library = null, embedder = null, tokenizer = null, reranker = null;
let embedderLoading = null, rerankerLoading = null;
// the reranker runs on the graphics card when the browser offers one that works, else on the processor; the embedder
// runs on the processor, where its vectors match the store's exactly
let device = self.navigator && self.navigator.gpu ? "webgpu" : "wasm";
const loading = { embedder: "", reranker: "" };

function status(text) { self.postMessage({ type: "status", text: text }); }
function esc(s) { return String(s).split("&").join("&amp;").split("<").join("&lt;").split('"').join("&quot;"); }
function short(text, n) { return text.length <= n ? text : text.slice(0, n).split(" ").slice(0, -1).join(" ") + "..."; }

async function json(path) {
  const response = await fetch(base + path);
  if (!response.ok) throw new Error("could not load " + path);
  return response.json();
}

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

// the keyword file a word sits in, the same hash the build used
function bucketOf(term, buckets) {
  let h = 0;
  for (const ch of term) h = (h * 31 + ch.codePointAt(0)) % 4294967296;
  return h % buckets;
}

// a shard: its index and its vectors; the words and the keyword files come later, only as needed
async function loadShard(name, k, total) {
  if (shards[name]) return;
  status("Loading " + S.names[name] + " (" + k + " of " + total + ")...");
  const parts = await Promise.all([json(name + ".json"), fetch(base + name + ".bin").then(function (r) { return r.arrayBuffer(); })]);
  const meta = parts[0], vectors = new Int8Array(parts[1]);
  const recs = [];
  let row = 0;
  for (let li = 0; li < meta.i.length; li++) {
    recs.push({ i: meta.i[li], k: meta.k[li], n: meta.n[li], row: row, vectors: vectors, shard: name, li: li, dl: meta.dl[li],
                w: meta.w[li], p: meta.p[li], m: meta.m[li], e: meta.e[li] || {}, x: meta.x[li] || null });
    row += meta.n[li];
  }
  shards[name] = { meta: meta, recs: recs, postings: {} };
}

// the records a search may return: every record of the chosen shards, a parent once; with the graph only, no chunk
function scopeOf(names, records) {
  const scope = new Map();
  for (const name of names) for (const r of shards[name].recs) {
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

// the words, label and link of these records, fetched in blocks
async function withText(recs) {
  const wanted = new Map();
  for (const r of recs) {
    if (r.s !== undefined) continue;
    const key = r.shard + "/t" + Math.floor(r.li / S.block);
    if (!wanted.has(key)) wanted.set(key, []);
    wanted.get(key).push(r);
  }
  const keys = Array.from(wanted.keys());
  await Promise.all(keys.map(function (key) {
    return json(key + ".json").then(function (block) {
      for (const r of wanted.get(key)) {
        const t = block[r.li % S.block];
        r.l = t.l; r.s = t.s; r.u = t.u; r.q = t.q || "";
      }
    });
  }));
}

function progress(which) {
  return function (event) {
    if (event.status === "progress" && event.file && event.file.indexOf(".onnx") >= 0) loading[which] = " " + Math.round(event.progress) + "%";
  };
}
function loadEmbedder() {
  if (!embedderLoading) embedderLoading = (async function () {
    if (!library) library = await import(LIBRARY);
    embedder = await library.pipeline("feature-extraction", S.MODEL, { dtype: "fp16", device: "wasm", progress_callback: progress("embedder") });
  })();
  // a load that fails is tried again by the next search
  embedderLoading.catch(function () { embedderLoading = null; });
  return embedderLoading;
}
function loadReranker() {
  if (!rerankerLoading) rerankerLoading = (async function () {
    if (!library) library = await import(LIBRARY);
    tokenizer = await library.AutoTokenizer.from_pretrained(S.RERANKER);
    if (device === "webgpu") {
      // a browser can offer a graphics card the model cannot use: then the processor runs it
      const adapter = await self.navigator.gpu.requestAdapter().catch(function () { return null; });
      if (!adapter) device = "wasm";
    }
    try {
      reranker = await library.AutoModelForSequenceClassification.from_pretrained(S.RERANKER, { dtype: "fp32", device: device, progress_callback: progress("reranker") });
    } catch (error) {
      if (device !== "webgpu") throw error;
      device = "wasm";
      reranker = await library.AutoModelForSequenceClassification.from_pretrained(S.RERANKER, { dtype: "fp32", device: device, progress_callback: progress("reranker") });
    }
  })();
  rerankerLoading.catch(function () { rerankerLoading = null; });
  return rerankerLoading;
}
async function waitFor(which, load, label) {
  const timer = setInterval(function () { status("Loading " + label + "..." + loading[which]); }, 500);
  try { await load(); } finally { clearInterval(timer); }
}

async function embed(question) {
  if (!embedder) { status("Loading the embedding model..."); await waitFor("embedder", loadEmbedder, "the embedding model"); }
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

// step 2: bm25 as FTS5 counts it, over the whole index, for the question's words joined by OR; each word's records
// come from its keyword file
async function keywordHits(names, searched, question) {
  if (!words) words = await json("words.json");
  const terms = Array.from(new Set(split(question)));
  const score = new Map();
  const k1 = 1.2, b = 0.75;
  for (const name of names) {
    const sh = shards[name];
    const files = Array.from(new Set(terms.map(function (term) { return bucketOf(term, sh.meta.buckets); })));
    await Promise.all(files.map(function (bucket) {
      if (sh.postings[bucket]) return null;
      return json(name + "/k" + bucket + ".json").then(function (data) { sh.postings[bucket] = data; });
    }));
    for (const term of terms) {
      const list = sh.postings[bucketOf(term, sh.meta.buckets)][term];
      if (!list) continue;
      const n = words.df[term] || 0;
      let idf = Math.log((words.N - n + 0.5) / (n + 0.5));
      if (idf <= 0) idf = 1e-6;
      for (let j = 0; j < list.length; j += 2) {
        const r = sh.recs[list[j]], tf = list[j + 1];
        if (!searched.has(r.i)) continue;
        score.set(r.i, (score.get(r.i) || 0) + idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * r.dl / words.avgdl)));
      }
    }
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
  for (const pair of parent.x || []) if (pair[0] !== skip && scope.has(pair[1])) out.push(pair[1]);
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
  if (parents && r.p >= 0 && scope.has(r.p)) edges.parent = instanceAbstracts(scope, scope.get(r.p), r.m);
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
  if (!reranker) { status("Loading the reranker..."); await waitFor("reranker", loadReranker, "the reranker"); }
  const recs = [];
  for (const id of pool.keys()) recs.push(scope.get(id));
  await withText(recs);
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

async function show(scope, pool, ranks, started) {
  const placed = new Map();
  for (const entry of pool) { entry[1].id = entry[0]; placed.set(entry[0], entry[1].score); }
  const order = bestFirst(pool.keys(), placed).slice(0, S.SHOWN);
  const recs = [];
  for (const id of order) {
    recs.push(scope.get(id));
    if (pool.get(id).from !== null) recs.push(scope.get(pool.get(id).from));
  }
  await withText(recs);
  let html = "";
  for (const id of order) {
    const r = scope.get(id), item = pool.get(id);
    let text = "<p>" + esc(r.s) + "</p>";
    if (r.q) text += "<blockquote>" + esc(r.q) + "</blockquote>";
    const cross = item.cross === undefined ? "" : " &middot; reranker " + item.cross.toFixed(2);
    html += '<li class="result"><div class="where"><span class="tag">' + KINDS[r.k] + '</span> <a href="' + esc(r.u) + '">' + esc(r.l) + "</a> " + (WHOSE[r.k] || "") + "</div>"
         + text + '<div class="found">' + how(scope, item, ranks) + cross + "</div></li>";
  }
  const seconds = (performance.now() - started) / 1000;
  return { html: html, text: pool.size + " records in the pool, the first " + order.length + " shown, in " + seconds.toFixed(1) + " s." };
}

async function run(ask) {
  const started = performance.now();
  const names = ask.scope === "all" ? S.shards : [ask.scope];
  for (let k = 0; k < names.length; k++) await loadShard(names[k], k + 1, names.length);
  const scope = scopeOf(names, ask.records);
  const searched = entriesOf(scope, ask.records);
  status("Embedding the question...");
  const q = await embed(ask.question);
  status("Searching " + scope.size.toLocaleString() + " records...");
  const sim = similarities(scope, q);
  const meaning = ask.mode === "keyword" ? [] : bestFirst(searched.keys(), sim).slice(0, S.K_ENTRY).slice(0, S.HITS);
  const keyword = ask.mode === "meaning" ? [] : (await keywordHits(names, searched, ask.question)).slice(0, S.HITS);
  const ranks = { meaning: new Map(), keyword: new Map() };
  for (let i = 0; i < meaning.length; i++) ranks.meaning.set(meaning[i], i + 1);
  for (let i = 0; i < keyword.length; i++) ranks.keyword.set(keyword[i], i + 1);
  const pool = makePool(scope, sim, fuse([meaning, keyword]));
  if (ask.hops > 0) walk(scope, sim, pool, ask.hops, ask.records !== "chunks");
  if (ask.rerank && pool.size) await rerank(ask.question, scope, pool);
  return show(scope, pool, ranks, started);
}

self.onmessage = async function (e) {
  const m = e.data;
  if (m.type === "init") {
    S = m.settings;
    base = m.base;
    // both models start loading as the page opens; a search waits only for what is not loaded yet
    loadEmbedder().catch(function () {});
    loadReranker().catch(function () {});
    return;
  }
  try {
    const out = await run(m);
    self.postMessage({ type: "done", html: out.html, text: out.text });
  } catch (error) {
    self.postMessage({ type: "error", text: error && error.message ? error.message : String(error) });
  }
};
