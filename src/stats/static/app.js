(() => {
  const tabs = [
    { btn: document.getElementById("tabSearch"), pane: document.getElementById("paneSearch") },
    { btn: document.getElementById("tabRag"), pane: document.getElementById("paneRag") },
  ];

  function select(index, focus = false) {
    tabs.forEach((t, i) => {
      const on = i === index;
      t.btn.setAttribute("aria-selected", String(on));
      t.btn.tabIndex = on ? 0 : -1;
      t.pane.hidden = !on;
    });
    if (focus) tabs[index].btn.focus();
    history.replaceState(null, "", index === 1 ? "#rag" : "#search");
  }

  tabs.forEach((t, i) => {
    t.btn.addEventListener("click", () => select(i));
    t.btn.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        e.preventDefault();
        select((i + 1) % tabs.length, true);
      }
    });
  });

  select(location.hash === "#rag" ? 1 : 0);
})();

(() => {
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

  function hitArticle(hit, rank) {
    const item = document.createElement("article");
    const meta = document.createElement("p");
    meta.className = "hint";
    meta.textContent =
      "#" + rank + " · min " + hit.minute + " · " +
      (hit.team || "unknown team") + " · " +
      (hit.player || "unknown player") + " · match " +
      (hit.match_id || "-");
    const body = document.createElement("p");
    body.textContent = hit.narrative;
    const score = document.createElement("p");
    score.className = "hint";
    score.textContent = "score " + Number(hit.score).toFixed(4);
    item.append(meta, body, score);
    return item;
  }

  function renderHits(payload, target, emptyText) {
    target.innerHTML = "";
    if (!payload.hits || payload.hits.length === 0) {
      const none = document.createElement("p");
      none.textContent = emptyText;
      target.appendChild(none);
      return;
    }
    payload.hits.forEach((hit, i) => {
      target.appendChild(hitArticle(hit, i + 1 + offset));
    });
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
      totalEl.textContent = payload.total + " hits · mode: " + payload.mode;
      renderHits(payload, resultsEl, "No results. Try a broader term.");
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
})();

(() => {
  const ragForm = document.getElementById("ragForm");
  const ragAnswer = document.getElementById("ragAnswer");
  const ragAnswerCard = document.getElementById("ragAnswerCard");
  const ragCitations = document.getElementById("ragCitations");
  const ragStatus = document.getElementById("ragStatus");
  const ragModel = document.getElementById("ragModel");

  async function runRag(event) {
    event.preventDefault();
    const question = document.getElementById("ragQ").value.trim();
    if (question === "") {
      return;
    }
    ragStatus.textContent = "Thinking...";
    ragAnswerCard.hidden = true;
    ragCitations.innerHTML = "";
    ragModel.textContent = "";
    try {
      const res = await fetch("/api/rag", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question: question, size: 10}),
      });
      if (!res.ok) {
        throw new Error("HTTP " + res.status);
      }
      const payload = await res.json();
      ragAnswer.textContent = payload.answer;
      ragAnswerCard.hidden = false;
      ragModel.textContent = payload.model;
      if (!payload.citations || payload.citations.length === 0) {
        const none = document.createElement("p");
        none.textContent = "No supporting events found.";
        ragCitations.appendChild(none);
      } else {
        payload.citations.forEach((hit, i) => {
          const item = document.createElement("article");
          const meta = document.createElement("p");
          meta.className = "hint";
          meta.textContent =
            "#" + (i + 1) + " · min " + hit.minute + " · " +
            (hit.team || "unknown team") + " · " +
            (hit.player || "unknown player");
          const body = document.createElement("p");
          body.textContent = hit.narrative;
          item.append(meta, body);
          ragCitations.appendChild(item);
        });
      }
      ragStatus.textContent = "Done.";
    } catch (err) {
      ragStatus.textContent = "RAG failed: " + err.message;
    }
  }

  ragForm.addEventListener("submit", runRag);
})();
