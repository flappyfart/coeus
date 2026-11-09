from coeus.market import MAINNET, TESTNET


class NotReady(Exception):
    pass


def _exchange(cfg, secrets):
    key = secrets.get("api_wallet_key") or ""
    account = (cfg.get("account_address") or "").strip()
    if not key or not account:
        raise NotReady("Add an API wallet key and your account address. Nothing was sent.")
    import eth_account
    from hyperliquid.exchange import Exchange
    wallet = eth_account.Account.from_key(key)
    url = TESTNET if cfg.get("network") == "testnet" else MAINNET
    return Exchange(wallet, url, account_address=account)


def send_open(cfg, secrets, trade):
    exchange = _exchange(cfg, secrets)
    is_buy = trade["side"] == "long"
    return exchange.market_open(trade["coin"], is_buy, float(trade["size"]), None, 0.01)


def send_close(cfg, secrets, coin, size):
    exchange = _exchange(cfg, secrets)
    return exchange.market_close(coin, float(size) if size else None)


def cancel_open(cfg, secrets):
    exchange = _exchange(cfg, secrets)
    address = (cfg.get("account_address") or "").strip()
    network = cfg.get("network") or "testnet"
    from coeus.market import open_orders
    orders = open_orders(address, network)
    reqs = []
    for order in orders:
        coin = order.get("coin")
        oid = order.get("oid")
        if coin and oid is not None:
            reqs.append({"coin": coin, "oid": int(oid)})
    if not reqs:
        return {"cancelled": 0}
    return {"cancelled": len(reqs), "exchange": exchange.bulk_cancel(reqs)}
