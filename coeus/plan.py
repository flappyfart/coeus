import re

MARKETS = ("BTC", "ETH", "SOL", "HYPE")
NUM = r"([0-9][0-9,]*(?:\.[0-9]+)?)"


def _num(match):
    return float(match.group(1).replace(",", "")) if match else None


def parse(text):
    raw = " ".join((text or "").split())
    if not raw:
        raise ValueError("Write a plan first.")
    side_m = re.search(r"\b(long|short|close)\b", raw, re.I)
    coin_m = re.search(r"\b(" + "|".join(MARKETS) + r")\b", raw, re.I)
    if not side_m or not coin_m:
        raise ValueError("Name a side (long, short, or close) and a market: BTC, ETH, SOL, or HYPE.")
    side = side_m.group(1).lower()
    coin = coin_m.group(1).upper()
    loses = _num(re.search(r"\b(?:loses|below|under)\s+\$?" + NUM, raw, re.I))
    reclaim = _num(re.search(r"\b(?:reclaims|above|over|breaks)\s+\$?" + NUM, raw, re.I))
    stop = _num(re.search(r"\bstop(?:\s+at)?\s+\$?" + NUM, raw, re.I))
    take = _num(re.search(r"\btake[\s-]?profit(?:\s+at)?\s+\$?" + NUM, raw, re.I))
    risk = _num(re.search(r"\brisk\s+" + NUM + r"\s*%", raw, re.I))
    lev = _num(re.search(r"\b(?:max(?:imum)?\s+)?" + NUM + r"\s*x\b", raw, re.I))
    if lev and not re.search(r"\bmax", raw, re.I) and not re.search(NUM + r"\s*x\b", raw, re.I):
        lev = None
    funding_negative = bool(re.search(r"funding", raw, re.I) and re.search(r"negative", raw, re.I))
    four_hour_low = bool(re.search(r"4[\s-]?hour low|4h low", raw, re.I))
    close_fraction = 0.5 if re.search(r"\bhalf\b", raw, re.I) else 1.0
    conditions = []
    if funding_negative:
        conditions.append("funding is negative")
    if loses is not None:
        conditions.append(f"price at or below {loses:g}")
    if reclaim is not None:
        conditions.append(f"price at or above {reclaim:g}")
    if four_hour_low:
        conditions.append("price loses the 4-hour low")
    return {
        "text": raw,
        "side": side,
        "coin": coin,
        "price_below": loses,
        "price_above": reclaim,
        "stop": stop,
        "take_profit": take,
        "risk_pct": risk,
        "max_leverage": lev,
        "funding_negative": funding_negative,
        "four_hour_low": four_hour_low,
        "close_fraction": close_fraction,
        "conditions": conditions,
    }


def round_size(size, decimals):
    factor = 10 ** decimals
    return int(size * factor) / factor
