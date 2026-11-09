import argparse
import json

from coeus import broker, engine, journal, market, pack
from coeus.store import load


def _print_trade(trade):
    print(f"{trade['side']} {trade['coin']}  mark {trade['entry']}")
    print(f"network for orders: {trade['network']}")
    if trade.get("size"):
        print(f"size {trade['size']}  about ${trade['notional']:,.0f}  {trade['leverage']:.2f}x")
    elif trade.get("size_note"):
        print(trade["size_note"])
    if trade.get("stop") or trade.get("take_profit"):
        print(f"hidden stop {trade.get('stop')}   hidden take-profit {trade.get('take_profit')}")
    for note in trade.get("notes") or []:
        print(" ·", note)
    if trade.get("blocked"):
        print("Not sent.")
        for reason in trade["blocked"]:
            print(" ·", reason)
    else:
        print("Ready. It is not sent until you pass --send.")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="coeus", description="Coeus, a local Hyperliquid perp assistant.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    plan = sub.add_parser("plan", help="Read a plan and show the trade")
    plan.add_argument("text")
    plan.add_argument("--send", action="store_true", help="Place the order after the checks pass")
    plan.add_argument("--auto", action="store_true", help="Also ask the second model")
    plan.add_argument("--i-mean-mainnet", action="store_true", help="Required with --send when orders are set to mainnet")

    sub.add_parser("doctor", help="Check the market and the local setup")
    sub.add_parser("journal", help="Print the journal")
    sub.add_parser("watch", help="Fire hidden stops that the market has reached")
    sub.add_parser("desktop", help="Open the Mac or Windows window")
    serve = sub.add_parser("serve", help="Run the local page")
    serve.add_argument("--port", type=int, default=4371)

    export = sub.add_parser("export", help="Write a pack you can import into your own model")
    export.add_argument("folder")

    args = parser.parse_args(argv)
    if args.cmd == "plan":
        trade = engine.propose(args.text, auto=args.auto)
        _print_trade(trade)
        if args.send:
            trade["approved"] = True
            if args.i_mean_mainnet:
                trade["mainnet_confirm"] = "MAINNET"
            try:
                result = engine.commit(trade)
            except broker.NotReady as exc:
                print(exc)
                return 1
            print(json.dumps(result["exchange"], default=str)[:2000])
        return 0
    if args.cmd == "doctor":
        cfg, secrets = load()
        snap = market.snapshot("ETH")
        print(f"ETH mark {snap['mark']}  funding {snap['funding']}  open interest {snap['open_interest']}")
        print(f"orders go to {cfg.get('network')}")
        print("account address:", cfg.get("account_address") or "(not set)")
        print("api wallet key:", "saved" if secrets.get("api_wallet_key") else "not set")
        model = cfg.get("model") or {}
        print("model:", model.get("provider"), model.get("model") or "(name not set)")
        return 0
    if args.cmd == "journal":
        print(journal.read())
        return 0
    if args.cmd == "export":
        print(pack.export(args.folder))
        return 0
    if args.cmd == "watch":
        return _watch()
    if args.cmd == "desktop":
        from coeus.desktop import main as open_window
        open_window()
        return 0
    if args.cmd == "serve":
        from coeus.server import serve
        serve(args.port)
        return 0
    return 1


def _watch():
    try:
        for line in engine.watch_once():
            print(line)
    except broker.NotReady as exc:
        print(exc)
        return 1
    return 0
