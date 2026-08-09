from __future__ import annotations

import unittest

from route_cis import build_route


class RouteCISTests(unittest.TestCase):
    def engine_ids(self, result: dict) -> list[str]:
        return [item["engine"] for item in result["selected_engines"]]

    def test_general_research_uses_openbb_and_tradingagents(self) -> None:
        result = build_route({"intent": "general_research", "asset_type": "equity", "mode": "standard"})
        self.assertEqual(self.engine_ids(result), ["openbb", "tradingagents"])
        self.assertEqual(result["final_decision_authority"], "cis_control_layer")

    def test_valuation_routes_finrobot_and_deep_secondary(self) -> None:
        result = build_route({"intent": "valuation", "asset_type": "equity", "mode": "deep"})
        ids = self.engine_ids(result)
        self.assertEqual(ids[:3], ["openbb", "tradingagents", "finrobot"])
        self.assertIn("anthropic_financial_services", ids)

    def test_factor_discovery_requires_rdagent_qlib_and_lean(self) -> None:
        result = build_route({"intent": "factor_discovery", "asset_type": "equity", "mode": "standard"})
        ids = self.engine_ids(result)
        self.assertEqual(ids, ["openbb", "rd_agent", "qlib", "lean"])
        self.assertTrue(any("experimental" in warning for warning in result["warnings"]))

    def test_explicit_lean_never_disappears_in_fast_mode(self) -> None:
        result = build_route(
            {
                "intent": "general_research",
                "asset_type": "equity",
                "mode": "fast",
                "explicit_lean": True,
            }
        )
        self.assertIn("lean", self.engine_ids(result))
        self.assertTrue(any("do not substitute" in warning for warning in result["warnings"]))

    def test_etf_route_keeps_cis_product_gate(self) -> None:
        result = build_route({"intent": "etf_review", "asset_type": "etf", "mode": "standard"})
        self.assertIn("etf_qdii_gate", result["cis_gates"])

    def test_tactical_route_keeps_price_and_rr_gates(self) -> None:
        result = build_route({"intent": "tactical_trade", "asset_type": "equity", "mode": "standard"})
        self.assertIn("price_session_guard", result["cis_gates"])
        self.assertIn("tactical_rr_gate", result["cis_gates"])
        self.assertIn("four_layer_trading_gate", result["cis_gates"])

    def test_boolean_fields_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            build_route(
                {
                    "intent": "general_research",
                    "asset_type": "equity",
                    "mode": "standard",
                    "needs_backtest": "yes",
                }
            )

    def test_unknown_intent_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            build_route({"intent": "guess", "asset_type": "equity", "mode": "standard"})


if __name__ == "__main__":
    unittest.main()
