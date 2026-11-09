var last = null;
function textOf(trade) {
  if (!trade) return "";
  if (trade.error) return trade.error;
  var lines = [trade.side + " " + trade.coin + "   mark " + trade.entry, "orders: " + trade.network];
  if (trade.size) lines.push("size " + trade.size + "   $" + Math.round(trade.notional) + "   " + trade.leverage.toFixed(2) + "x");
  if (trade.size_note) lines.push(trade.size_note);
  if (trade.stop || trade.take_profit) lines.push("hidden stop " + trade.stop + "   hidden take-profit " + trade.take_profit);
  (trade.notes || []).forEach(function (n) { lines.push("· " + n); });
  if (trade.blocked && trade.blocked.length) {
    lines.push("Not sent.");
    trade.blocked.forEach(function (n) { lines.push("· " + n); });
  } else lines.push("Ready. Send places it. The tight stop stays on this computer.");
  return lines.join("\n");
}
function post(url, body) {
  return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(function (r) { return r.json(); });
}
document.getElementById("show").onclick = function () {
  post("/api/plan", { text: document.getElementById("plan").value, auto: document.getElementById("auto").checked }).then(function (trade) {
    last = trade;
    document.getElementById("out").textContent = textOf(trade);
    document.getElementById("send").disabled = !trade.ready;
  });
};
document.getElementById("send").onclick = function () {
  post("/api/send", {}).then(function (res) {
    document.getElementById("out").textContent = res.error || "Sent. The hidden stop, if any, is stored on this computer.";
    document.getElementById("send").disabled = true;
  });
};
document.getElementById("save").onclick = function () {
  post("/api/model", {
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
  }).then(function () {
    document.getElementById("model-key").value = "";
    document.getElementById("api-key").value = "";
    document.getElementById("setup").textContent = "Saved on this computer. Keys are not shown again.";
  });
};
document.getElementById("export").onclick = function () {
  post("/api/export", {}).then(function (res) {
    document.getElementById("setup").textContent = res.error || ("Pack written to " + res.path);
  });
};
fetch("/api/state").then(function (r) { return r.json(); }).then(function (s) {
  document.getElementById("provider").value = s.model.provider || "own";
  document.getElementById("base").value = s.model.base_url || "";
  document.getElementById("model").value = s.model.model || "";
  document.getElementById("check-provider").value = s.model.check_provider || "";
  document.getElementById("check-base").value = s.model.check_base_url || "";
  document.getElementById("check-model").value = s.model.check_model || "";
  document.getElementById("network").value = s.network || "testnet";
  document.getElementById("setup").textContent = "API wallet key: " + (s.api_key_set ? "saved" : "not set") + ". Model key: " + (s.model.key_set ? "saved" : "not set") + ".";
});
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
