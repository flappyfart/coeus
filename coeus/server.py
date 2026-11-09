import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from coeus import broker, engine, journal, pack, stops
from coeus.store import load, save_config, save_secrets

WEB = Path(__file__).resolve().parent.parent / "web"
LAST = {}


def _state():
    cfg, secrets = load()
    model = cfg.get("model") or {}
    return {
        "name": "Coeus",
        "ticker": "$COEUS",
        "network": cfg.get("network"),
        "account_set": bool((cfg.get("account_address") or "").strip()),
        "api_key_set": bool(secrets.get("api_wallet_key")),
        "model": {
            "provider": model.get("provider"),
            "base_url": model.get("base_url"),
            "model": model.get("model"),
            "check_provider": model.get("check_provider"),
            "check_base_url": model.get("check_base_url"),
            "check_model": model.get("check_model"),
            "key_set": bool(secrets.get("model") or secrets.get("xai") or secrets.get("anthropic")),
        },
        "guardrails": cfg.get("guardrails"),
        "stops": stops.all_stops(),
        "journal": journal.read()[-4000:],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send(self, code, body, content="application/json"):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", content)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode() or "{}")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/state":
            self._send(200, _state())
            return
        if path in ("/", "/index.html"):
            self._send(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if path == "/styles.css":
            self._send(200, (WEB / "styles.css").read_bytes(), "text/css")
            return
        if path == "/app.js":
            self._send(200, (WEB / "app.js").read_bytes(), "text/javascript")
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self._read()
            if path == "/api/plan":
                trade = engine.propose(data.get("text") or "", auto=bool(data.get("auto")))
                LAST.clear()
                LAST.update(trade)
                self._send(200, trade)
                return
            if path == "/api/send":
                if not LAST:
                    self._send(400, {"error": "Show a trade first."})
                    return
                LAST["approved"] = True
                result = engine.commit(LAST)
                self._send(200, {"ok": True, "result": json.loads(json.dumps(result, default=str))})
                return
            if path == "/api/model":
                cfg, secrets = load()
                model = cfg.setdefault("model", {})
                for key in ("provider", "base_url", "model", "check_provider", "check_base_url", "check_model"):
                    if key in data:
                        model[key] = data[key]
                if data.get("account_address") is not None:
                    cfg["account_address"] = data["account_address"].strip()
                if data.get("network") in ("testnet", "mainnet"):
                    cfg["network"] = data["network"]
                save_config(cfg)
                if data.get("model_key"):
                    secrets["model"] = data["model_key"]
                if data.get("api_wallet_key"):
                    secrets["api_wallet_key"] = data["api_wallet_key"]
                if data.get("check_key"):
                    secrets["check"] = data["check_key"]
                if any(data.get(k) for k in ("model_key", "api_wallet_key", "check_key")):
                    save_secrets(secrets)
                self._send(200, _state())
                return
            if path == "/api/export":
                folder = data.get("folder") or str(Path.home() / "Coeus" / "agent-pack")
                dest = pack.export(folder)
                self._send(200, {"path": str(dest)})
                return
            self._send(404, {"error": "not found"})
        except broker.NotReady as exc:
            self._send(400, {"error": str(exc)})
        except Exception as exc:
            self._send(400, {"error": str(exc)})


def serve(port=4371):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Coeus is at http://127.0.0.1:{port}")
    server.serve_forever()


def background(port=4371):
    import threading
    server = None
    chosen = port
    for chosen in range(port, port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", chosen), Handler)
            break
        except OSError:
            server = None
    if server is None:
        raise OSError("No free local port for Coeus")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{chosen}"
