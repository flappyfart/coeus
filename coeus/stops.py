import json
import uuid
from coeus.store import HOME


def file():
    HOME.mkdir(parents=True, exist_ok=True)
    path = HOME / "stops.json"
    if not path.exists():
        path.write_text("[]")
    return path


def all_stops():
    try:
        return json.loads(file().read_text())
    except json.JSONDecodeError:
        return []


def save(items):
    file().write_text(json.dumps(items, indent=2))


def add(trade):
    items = all_stops()
    item = {
        "id": uuid.uuid4().hex[:8],
        "coin": trade["coin"],
        "side": trade["side"],
        "size": trade.get("size"),
        "stop": trade.get("stop"),
        "take_profit": trade.get("take_profit"),
        "entry": trade.get("entry"),
    }
    items.append(item)
    save(items)
    return item


def remove(stop_id):
    items = [item for item in all_stops() if item["id"] != stop_id]
    save(items)
