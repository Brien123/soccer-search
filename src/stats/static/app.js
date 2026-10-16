const form = document.getElementById("searchForm");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");
const totalEl = document.getElementById("total");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");

let offset = 0;

function currentParams() {
  const data = new FormData(form);
  const params = new URLSearchParams();
  for (const [key, value] of data.entries()) {
    const text = String(value).trim();
    if (text !== "") {
      params.set(key, text);
    }
  }
  params.set("offset", String(offset));
  return params;
}

function renderHits(payload) {
  resultsEl.innerHTML = "";
  totalEl.textContent = payload.total + " hits · mode: " + payload.mode;
  if (!payload.hits || payload.hits.length === 0) {
    resultsEl.innerHTML = '<div class="card">No results. Try a broader term.</div>';
    return;
  }
  for (const hit of payload.hits) {
    const card = document.createElement("div");
    card.className = "card";
    const top = document.createElement("div");
    top.className = "card-top";
    const minute = document.createElement("span");
    minute.className = "pill";
    minute.textContent = "min " + hit.minute;
    const team = document.createElement("span");
    team.className = "pill";
    team.textContent = hit.team || "unknown team";
    const player = document.createElement("span");
    player.className = "pill";
    player.textContent = hit.player || "unknown player";
    const match = document.createElement("span");
    match.className = "pill";
    match.textContent = "match " + (hit.match_id || "-");
    top.append(minute, team, player, match);
    const body = document.createElement("div");
    body.className = "narrative";
    body.textContent = hit.narrative;
    const score = document.createElement("div");
    score.className = "score";
    score.textContent = "score " + Number(hit.score).toFixed(4);
    card.append(top, body, score);
    resultsEl.appendChild(card);
  }
}

async function runSearch() {
  const params = currentParams();
  statusEl.textContent = "Searching...";
  try {
    const res = await fetch("/api/search?" + params.toString());
    if (!res.ok) {
      throw new Error("HTTP " + res.status);
    }
    const payload = await res.json();
    renderHits(payload);
    statusEl.textContent = "Done.";
  } catch (err) {
    statusEl.textContent = "Search failed: " + err.message;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  offset = 0;
  runSearch();
});

prevBtn.addEventListener("click", () => {
  const size = Number(document.getElementById("size").value || "10");
  offset = Math.max(0, offset - size);
  runSearch();
});

nextBtn.addEventListener("click", () => {
  const size = Number(document.getElementById("size").value || "10");
  offset = offset + size;
  runSearch();
});

runSearch();
