def check(trade, rules, equity, day_pnl):
    reasons = []
    markets = [m.upper() for m in rules.get("allowed_markets") or []]
    if trade["coin"] not in markets:
        reasons.append(f"{trade['coin']} is not in the allowed markets.")
    lev = trade.get("leverage") or 0
    if lev > float(rules.get("max_leverage") or 0):
        reasons.append(f"Leverage {lev:g}x is above the {rules.get('max_leverage')}x cap.")
    notional = float(trade.get("notional") or 0)
    cap = float(rules.get("max_position_usd") or 0)
    if notional > cap:
        reasons.append(f"Size ${notional:,.0f} is above the ${cap:,.0f} position cap.")
    if equity and day_pnl < 0:
        loss_pct = abs(day_pnl) / equity * 100
        limit = float(rules.get("daily_loss_stop_pct") or 0)
        if loss_pct >= limit:
            reasons.append(f"Today's loss is {loss_pct:.2f}%, at the {limit:g}% daily stop.")
    if trade.get("side") != "close" and not trade.get("stop") and trade.get("risk_pct"):
        reasons.append("A risk percent needs a stop, so the size can be worked out.")
    return reasons
