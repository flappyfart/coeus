import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home() / ".coeus"

DEFAULT = {
    "network": "testnet",
    "account_address": "",
    "guardrails": {
        "max_leverage": 3,
        "max_position_usd": 5000,
        "daily_loss_stop_pct": 2.0,
        "allowed_markets": ["BTC", "ETH", "SOL", "HYPE"],
        "require_approval": True,
    },
    "model": {
        "provider": "own",
        "base_url": "",
        "model": "",
        "check_provider": "",
        "check_base_url": "",
        "check_model": "",
    },
}


def _toml(data, indent=0):
    lines = []
    pad = "  " * indent
    tables = []
    for key, value in data.items():
        if isinstance(value, dict):
            tables.append((key, value))
            continue
        if isinstance(value, bool):
            shown = "true" if value else "false"
        elif isinstance(value, (int, float)):
            shown = str(value)
        elif isinstance(value, list):
            inner = ", ".join(json.dumps(item) for item in value)
            shown = "[" + inner + "]"
        else:
            shown = json.dumps(str(value))
        lines.append(f"{pad}{key} = {shown}")
    text = "\n".join(lines)
    for key, value in tables:
        block = _toml(value, 0)
        text += f"\n\n[{key}]\n{block}"
    return text


def load():
    HOME.mkdir(parents=True, exist_ok=True)
    path = HOME / "config.toml"
    if not path.exists():
        path.write_text(ROOT.joinpath("config.example.toml").read_text())
    try:
        import tomllib
        data = tomllib.loads(path.read_text())
    except Exception:
        data = {}
    cfg = json.loads(json.dumps(DEFAULT))
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(cfg.get(key), dict):
            cfg[key].update(value)
        else:
            cfg[key] = value
    secrets = {}
    secret_path = HOME / "secrets.json"
    if secret_path.exists():
        try:
            secrets = json.loads(secret_path.read_text())
        except json.JSONDecodeError:
            secrets = {}
    return cfg, secrets


def save_config(cfg):
    HOME.mkdir(parents=True, exist_ok=True)
    path = HOME / "config.toml"
    path.write_text(_toml(cfg) + "\n")
    return path


def save_secrets(secrets):
    HOME.mkdir(parents=True, exist_ok=True)
    path = HOME / "secrets.json"
    path.write_text(json.dumps(secrets))
    os.chmod(path, 0o600)
    return path


def secret(secrets, name, env):
    return os.environ.get(env) or secrets.get(name) or ""
