import time

from coeus import broker, guard, journal, market, models, plan, stops
from coeus.store import load, secret


def _keys(cfg, secrets):
    model = cfg.get("model") or {}
    provider = model.get("provider") or "own"

    def key_for(name):
        if name == "spacexai":
            return secret(secrets, "xai", "XAI_API_KEY")
        if name == "claude":
            return secret(secrets, "anthropic", "ANTHROPIC_API_KEY")
        if name == "own":
            return secret(secrets, "model", "COEUS_MODEL_KEY")
        return ""

    return provider, key_for(provider), model


def _conditions_met(parsed, snap, network):
    notes = []
    met = True
    if parsed["funding_negative"]:
        ok = snap["funding"] < 0
        met = met and ok
        notes.append(f"funding {snap['funding']:.6f} {'is' if ok else 'is not'} negative")
    if parsed["price_below"] is not None:
        ok = snap["mark"] <= parsed["price_below"]
        met = met and ok
        notes.append(f"mark {snap['mark']:g} {'is at or below' if ok else 'is above'} {parsed['price_below']:g}")
    if parsed["price_above"] is not None:
        ok = snap["mark"] >= parsed["price_above"]
        met = met and ok
        notes.append(f"mark {snap['mark']:g} {'is at or above' if ok else 'is below'} {parsed['price_above']:g}")
    if parsed["four_hour_low"]:
        start = int(time.time() * 1000) - 5 * 4 * 60 * 60 * 1000
        rows = market.candles(parsed["coin"], "4h", start, network)
        if len(rows) < 2:
            met = False
            notes.append("not enough 4-hour candles")
        else:
            low = float(rows[-2]["l"])
            ok = snap["mark"] < low
            met = met and ok
            notes.append(f"mark {snap['mark']:g} {'lost' if ok else 'has not lost'} the 4-hour low {low:g}")
    if not parsed["conditions"] and parsed["side"] != "close":
        notes.append("no extra condition; the plan can be sent once you approve it")
    return met, notes


def _size(parsed, snap, equity, rules):
    if parsed["side"] == "close":
        return None, None
    if not equity:
        return None, "Connect an account before a size is chosen. No size was invented."
    risk = parsed.get("risk_pct")
    stop = parsed.get("stop")
    if risk and stop:
        risk_usd = equity * risk / 100
        distance = abs(snap["mark"] - stop) / snap["mark"]
        if distance <= 0:
            return None, "The stop is on the wrong side of the price."
        notional = risk_usd / distance
    elif risk:
        return None, "Add a stop so the risk percent can set a size."
    else:
        return None, "Add a risk percent, for example risk 1%."
    lev_cap = float(rules.get("max_leverage") or 1)
    if parsed.get("max_leverage"):
        lev_cap = min(lev_cap, float(parsed["max_leverage"]))
    lev_cap = min(lev_cap, float(snap["max_leverage"]))
    max_notional = min(float(rules.get("max_position_usd") or notional), equity * lev_cap)
    notional = min(notional, max_notional)
    size = plan.round_size(notional / snap["mark"], snap["sz_decimals"])
    leverage = notional / equity if equity else None
    return {"size": size, "notional": notional, "leverage": leverage}, None


def propose(text, auto=False):
    cfg, secrets = load()
    rules = cfg.get("guardrails") or {}
    parsed = plan.parse(text)
    snap = market.snapshot(parsed["coin"], "mainnet")
    met, notes = _conditions_met(parsed, snap, "mainnet")
    address = (cfg.get("account_address") or "").strip()
    equity = None
    if address:
        equity = market.account(address, cfg.get("network") or "testnet")["equity"]
    sized, size_note = _size(parsed, snap, equity, rules)
    trade = {
        "text": parsed["text"],
        "side": parsed["side"],
        "coin": parsed["coin"],
        "entry": snap["mark"],
        "stop": parsed.get("stop"),
        "take_profit": parsed.get("take_profit"),
        "risk_pct": parsed.get("risk_pct"),
        "conditions": parsed["conditions"],
        "conditions_met": met,
        "notes": notes,
        "market": snap,
        "equity": equity,
        "size": sized["size"] if sized else None,
        "notional": sized["notional"] if sized else None,
        "leverage": sized["leverage"] if sized else None,
        "size_note": size_note,
        "network": cfg.get("network") or "testnet",
        "auto": auto,
    }
    reasons = []
    if not met:
        reasons.append("The conditions are not met, so nothing is ready to send.")
    if size_note and parsed["side"] != "close":
        reasons.append(size_note)
    if sized or parsed["side"] == "close":
        reasons.extend(guard.check(trade, rules, equity or 0, journal.day_pnl()))
    if auto:
        model = cfg.get("model") or {}
        provider = model.get("check_provider") or ""
        if not provider:
            reasons.append("Auto mode needs a second model. Approve the trade yourself, or set a check model.")
        else:
            key = secret(secrets, "check", "COEUS_CHECK_KEY")
            if provider == "spacexai":
                key = secret(secrets, "xai", "XAI_API_KEY")
            if provider == "claude":
                key = secret(secrets, "anthropic", "ANTHROPIC_API_KEY")
            allowed, why = models.allow(
                text, provider, model.get("check_model"), model.get("check_base_url"), key
            )
            if not allowed:
                reasons.append(why or "The second model said no.")
    if cfg.get("halted"):
        reasons.append("Sends are paused. Arm Coeus before a new order.")
    trade["passed"] = guard.passed(trade, rules, equity or 0, journal.day_pnl())
    trade["blocked"] = reasons
    trade["ready"] = not reasons
    return trade


def send_block(network, confirm, halted):
    if halted:
        return "Sends are paused. Press Arm to allow them again. Nothing was sent."
    if (network or "testnet") == "mainnet" and confirm != "MAINNET":
        return "Mainnet needs the word MAINNET. Nothing was sent."
    return ""


def commit(trade):
    cfg, secrets = load()
    reason = send_block(cfg.get("network"), trade.get("mainnet_confirm"), cfg.get("halted"))
    if reason:
        raise broker.NotReady(reason)
    if trade.get("blocked"):
        raise broker.NotReady(" ".join(trade["blocked"]))
    if (cfg.get("guardrails") or {}).get("require_approval", True) and not trade.get("approved"):
        raise broker.NotReady("This trade is not approved. Nothing was sent.")
    if trade["side"] == "close":
        result = broker.send_close(cfg, secrets, trade["coin"], trade.get("size"))
    else:
        result = broker.send_open(cfg, secrets, trade)
    hidden = None
    if trade.get("stop") or trade.get("take_profit"):
        hidden = stops.add(trade)
    lev = trade.get("leverage")
    lines = [
        f"{trade['side']} {trade['coin']}",
        f"network: {cfg.get('network') or 'testnet'}",
        f"entry: {trade.get('entry')}",
        f"size: {trade.get('size')}",
        f"leverage: {f'{lev:.2f}x' if isinstance(lev, (int, float)) else lev}",
        f"stop on this computer: {trade.get('stop')}",
        f"take profit on this computer: {trade.get('take_profit')}",
        f"risk percent: {trade.get('risk_pct')}",
        "The stop was not placed on the public order list. It fires only while Coeus is open.",
    ]
    for rule in trade.get("passed") or []:
        lines.append(f"rule passed: {rule}")
    lines.append(f"exchange: {result}")
    journal.add(trade["coin"], "\n".join(lines))
    return {"exchange": result, "hidden_stop": hidden}


def halt():
    from coeus.store import save_config
    cfg, secrets = load()
    cfg["halted"] = True
    save_config(cfg)
    try:
        result = broker.cancel_open(cfg, secrets)
        note = f"Cancelled {result.get('cancelled', 0)} open orders."
    except broker.NotReady as exc:
        result = {"cancelled": 0}
        note = str(exc)
    journal.add("Stop", f"Sends are paused. {note}")
    return {"halted": True, "cancelled": result.get("cancelled", 0), "note": note}


def arm():
    from coeus.store import save_config
    cfg, _secrets = load()
    cfg["halted"] = False
    save_config(cfg)
    journal.add("Arm", "Sends are allowed again. Mainnet still needs the word MAINNET.")
    return {"halted": False}


def watch_once():
    cfg, secrets = load()
    if cfg.get("halted"):
        return ["Sends are paused. Hidden stops are not firing."]
    notes = []
    for item in list(stops.all_stops()):
        snap = market.snapshot(item["coin"])
        mark = snap["mark"]
        hit = None
        if item.get("stop") and item["side"] == "long" and mark <= float(item["stop"]):
            hit = "stop"
        elif item.get("stop") and item["side"] == "short" and mark >= float(item["stop"]):
            hit = "stop"
        elif item.get("take_profit") and item["side"] == "long" and mark >= float(item["take_profit"]):
            hit = "take profit"
        elif item.get("take_profit") and item["side"] == "short" and mark <= float(item["take_profit"]):
            hit = "take profit"
        if not hit:
            notes.append(f"{item['coin']} mark {mark:g} still waiting")
            continue
        result = broker.send_close(cfg, secrets, item["coin"], item.get("size"))
        journal.add(item["coin"], f"Hidden {hit} reached at {mark}.\nexchange: {result}\npnl: 0")
        stops.remove(item["id"])
        notes.append(f"Closed {item['coin']} on a hidden {hit}.")
    if not notes:
        notes.append("No hidden stops.")
    return notes
