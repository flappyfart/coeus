var last = null;

function post(url, body) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {})
  }).then(function (r) { return r.json(); });
}

function fillList(id, items, bad) {
  var ul = document.getElementById(id);
  ul.replaceChildren();
  (items || []).forEach(function (text) {
    var li = document.createElement("li");
    if (bad) li.className = "bad";
    li.textContent = text;
    ul.appendChild(li);
  });
  if (!items || !items.length) {
    var li = document.createElement("li");
    li.textContent = bad ? "Nothing is holding this send." : "No rule line yet.";
    ul.appendChild(li);
  }
}

function money(n) {
  if (n == null || isNaN(n)) return "—";
  return "$" + Math.round(n).toLocaleString("en-US");
}

function showTrade(trade) {
  last = trade;
  var empty = document.getElementById("empty");
  var card = document.getElementById("receipt");
  if (!trade || trade.error) {
    card.hidden = true;
    empty.hidden = false;
    empty.textContent = (trade && trade.error) || "Tell Coeus the plan.";
    document.getElementById("send").disabled = true;
    return;
  }
  empty.hidden = true;
  card.hidden = false;
  document.getElementById("r-net").textContent = trade.network === "mainnet" ? "Mainnet · real orders" : "Testnet";
  document.getElementById("r-side").textContent = (trade.side || "").toUpperCase();
  document.getElementById("r-coin").textContent = trade.coin || "";
  document.getElementById("r-size").textContent = trade.size ? String(trade.size) + " · " + money(trade.notional) : (trade.size_note || "—");
  document.getElementById("r-lev").textContent = trade.leverage ? trade.leverage.toFixed(2) + "x" : "—";
  document.getElementById("r-stop").textContent = trade.stop != null ? String(trade.stop) : "None on this computer";
  document.getElementById("r-tp").textContent = trade.take_profit != null ? String(trade.take_profit) : "—";
  document.getElementById("r-risk").textContent = trade.risk_pct != null ? trade.risk_pct + "% of equity" : "—";
  document.getElementById("r-mark").textContent = trade.entry != null ? String(trade.entry) : "—";
  var notes = (trade.notes || []).slice();
  fillList("r-rules", (trade.passed || []).concat(notes), false);
  fillList("r-blocks", trade.blocked || [], true);
  document.getElementById("send").disabled = !trade.ready;
}

function setPaused(on) {
  document.getElementById("paused").hidden = !on;
  document.getElementById("stop").hidden = on;
  document.getElementById("arm").hidden = !on;
  document.body.classList.toggle("is-paused", on);
}

function saveAll() {
  return post("/api/model", {
    provider: document.getElementById("provider").value,
    base_url: document.getElementById("base").value,
    model: document.getElementById("model").value,
    model_key: document.getElementById("model-key").value,
    check_provider: document.getElementById("check-provider").value,
    check_base_url: document.getElementById("check-base").value,
    check_model: document.getElementById("check-model").value,
    account_address: document.getElementById("account").value,
    api_wallet_key: document.getElementById("api-key").value,
    network: document.getElementById("network").value
  }).then(function (state) {
    document.getElementById("model-key").value = "";
    document.getElementById("api-key").value = "";
    if (state && state.error) {
      document.getElementById("setup").textContent = state.error;
      return;
    }
    document.getElementById("setup").textContent = "Saved on this computer. Keys are not shown again.";
    if (state && state.version) applyState(state);
  });
}

function applyState(s) {
  document.getElementById("ver").textContent = s.version || "0.2.0";
  document.getElementById("provider").value = s.model.provider || "own";
  document.getElementById("base").value = s.model.base_url || "";
  document.getElementById("model").value = s.model.model || "";
  document.getElementById("check-provider").value = s.model.check_provider || "";
  document.getElementById("check-base").value = s.model.check_base_url || "";
  document.getElementById("check-model").value = s.model.check_model || "";
  document.getElementById("network").value = s.network || "testnet";
  document.body.setAttribute("data-net", s.network || "testnet");
  document.getElementById("setup").textContent = "API wallet key: " + (s.api_key_set ? "saved" : "not set") + ". Model key: " + (s.model.key_set ? "saved" : "not set") + ".";
  setPaused(!!s.halted);
}

document.getElementById("composer").addEventListener("submit", function (e) { e.preventDefault(); });
document.getElementById("show").onclick = function () {
  post("/api/plan", {
    text: document.getElementById("plan").value,
    auto: document.getElementById("auto").checked
  }).then(showTrade);
};
document.getElementById("send").onclick = function () {
  if ((document.getElementById("network").value || "testnet") === "mainnet") {
    document.getElementById("gate-word").value = "";
    document.getElementById("gate").hidden = false;
    document.getElementById("gate-word").focus();
    return;
  }
  sendNow("");
};
function sendNow(confirm) {
  post("/api/send", { confirm: confirm }).then(function (res) {
    document.getElementById("gate").hidden = true;
    if (res.error) {
      document.getElementById("empty").hidden = false;
      document.getElementById("empty").textContent = res.error;
      return;
    }
    document.getElementById("empty").hidden = false;
    document.getElementById("empty").textContent = "Sent. The receipt is in the journal on this computer. A hidden stop, if you set one, fires only while Coeus is open.";
    document.getElementById("receipt").hidden = true;
    document.getElementById("send").disabled = true;
    last = null;
  });
}
document.getElementById("gate-form").addEventListener("submit", function (e) {
  e.preventDefault();
  sendNow(document.getElementById("gate-word").value.trim());
});
document.getElementById("gate-no").onclick = function () { document.getElementById("gate").hidden = true; };
document.getElementById("save").onclick = saveAll;
document.getElementById("export").onclick = function () {
  post("/api/export", {}).then(function (res) {
    document.getElementById("setup").textContent = res.error || ("Pack written to " + res.path);
  });
};
document.getElementById("network").addEventListener("change", function () {
  document.body.setAttribute("data-net", document.getElementById("network").value);
  post("/api/model", { network: document.getElementById("network").value });
});
document.getElementById("stop").onclick = function () { document.getElementById("stop-ask").hidden = false; };
document.getElementById("stop-no").onclick = function () { document.getElementById("stop-ask").hidden = true; };
document.getElementById("stop-yes").onclick = function () {
  post("/api/halt", {}).then(function (res) {
    document.getElementById("stop-ask").hidden = true;
    setPaused(true);
    document.getElementById("send").disabled = true;
    document.getElementById("empty").hidden = false;
    document.getElementById("empty").textContent = res.error || res.note || "Paused.";
  });
};
document.getElementById("arm").onclick = function () {
  post("/api/arm", {}).then(function (res) {
    if (res.error) return;
    setPaused(false);
    document.getElementById("empty").hidden = false;
    document.getElementById("empty").textContent = "Armed. Testnet is still the safe place to try a plan. Mainnet asks for the word MAINNET.";
  });
};
document.querySelectorAll("[data-save-proxy]").forEach(function (btn) {
  btn.addEventListener("click", function () { document.getElementById("save").click(); });
});
document.querySelectorAll("[data-pane]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var name = btn.getAttribute("data-pane");
    document.querySelectorAll("[data-pane]").forEach(function (b) { b.classList.toggle("on", b === btn); });
    document.querySelectorAll("[data-panel]").forEach(function (p) { p.hidden = p.getAttribute("data-panel") !== name; });
  });
});
fetch("/api/state").then(function (r) { return r.json(); }).then(applyState);
