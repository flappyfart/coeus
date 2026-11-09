import unittest
from coeus import guard, plan


class PlanTests(unittest.TestCase):
    def test_example(self):
        parsed = plan.parse("short ETH if funding turns negative and it loses 3,200. risk 1%. max 3x.")
        self.assertEqual(parsed["side"], "short")
        self.assertEqual(parsed["coin"], "ETH")
        self.assertTrue(parsed["funding_negative"])
        self.assertEqual(parsed["price_below"], 3200)
        self.assertEqual(parsed["risk_pct"], 1)
        self.assertEqual(parsed["max_leverage"], 3)

    def test_long_levels(self):
        parsed = plan.parse("Long BTC if it reclaims 98,000. Stop at 96,500, take profit at 102,000, risk 0.5%.")
        self.assertEqual(parsed["side"], "long")
        self.assertEqual(parsed["price_above"], 98000)
        self.assertEqual(parsed["stop"], 96500)
        self.assertEqual(parsed["take_profit"], 102000)
        self.assertEqual(parsed["risk_pct"], 0.5)

    def test_unclear(self):
        with self.assertRaises(ValueError):
            plan.parse("buy the dip")


class GuardTests(unittest.TestCase):
    def test_blocks_leverage_and_market(self):
        rules = {"max_leverage": 3, "max_position_usd": 5000, "daily_loss_stop_pct": 2, "allowed_markets": ["ETH"]}
        trade = {"coin": "DOGE", "side": "long", "leverage": 10, "notional": 9000, "stop": 1, "risk_pct": 1}
        reasons = guard.check(trade, rules, 1000, 0)
        self.assertTrue(any("DOGE" in r for r in reasons))
        self.assertTrue(any("Leverage" in r for r in reasons))
        self.assertTrue(any("position cap" in r for r in reasons))


if __name__ == "__main__":
    unittest.main()
