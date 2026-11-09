import json
import urllib.request

MAINNET = "https://api.hyperliquid.xyz"
TESTNET = "https://api.hyperliquid-testnet.xyz"


def base_url(network):
    return TESTNET if network == "testnet" else MAINNET


def info(body, network="mainnet"):
    req = urllib.request.Request(
        base_url(network) + "/info",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.loads(res.read().decode())


def snapshot(coin, network="mainnet"):
    meta, ctxs = info({"type": "metaAndAssetCtxs"}, network)
    names = [asset["name"] for asset in meta["universe"]]
    if coin not in names:
        raise ValueError(f"{coin} is not a perp on this book")
    i = names.index(coin)
    asset = meta["universe"][i]
    ctx = ctxs[i]
    mark = float(ctx.get("markPx") or ctx.get("midPx") or 0)
    return {
        "coin": coin,
        "mark": mark,
        "funding": float(ctx.get("funding") or 0),
        "open_interest": float(ctx.get("openInterest") or 0),
        "max_leverage": int(asset.get("maxLeverage") or 1),
        "sz_decimals": int(asset.get("szDecimals") or 4),
    }


def candles(coin, interval, start_ms, network="mainnet"):
    return info({
        "type": "candleSnapshot",
        "req": {"coin": coin, "interval": interval, "startTime": start_ms, "endTime": 0},
    }, network)


def open_orders(address, network):
    rows = info({"type": "openOrders", "user": address}, network)
    return rows if isinstance(rows, list) else []


def account(address, network):
    state = info({"type": "clearinghouseState", "user": address}, network)
    equity = float(state.get("marginSummary", {}).get("accountValue") or 0)
    positions = []
    for item in state.get("assetPositions") or []:
        pos = item.get("position") or {}
        positions.append({
            "coin": pos.get("coin"),
            "size": float(pos.get("szi") or 0),
            "entry": float(pos.get("entryPx") or 0),
            "upnl": float(pos.get("unrealizedPnl") or 0),
        })
    return {"equity": equity, "positions": positions}
