from __future__ import annotations

import unittest

from strategy_logic import BUY, SELL, DrawdownTracker, cash_interest_amount, crossover_signal


class CrossoverSignalTests(unittest.TestCase):
    def test_no_initial_regime_entry_without_cross(self) -> None:
        self.assertIsNone(crossover_signal(None, None, 110.0, 100.0))

    def test_bullish_regime_without_new_cross_does_not_rebuy(self) -> None:
        self.assertIsNone(crossover_signal(105.0, 100.0, 106.0, 101.0))

    def test_strict_golden_cross(self) -> None:
        self.assertEqual(crossover_signal(99.0, 100.0, 101.0, 100.0), BUY)

    def test_equality_to_above_counts_as_golden_cross(self) -> None:
        self.assertEqual(crossover_signal(100.0, 100.0, 100.01, 100.0), BUY)

    def test_strict_death_cross(self) -> None:
        self.assertEqual(crossover_signal(101.0, 100.0, 99.0, 100.0), SELL)

    def test_equality_to_below_counts_as_death_cross(self) -> None:
        self.assertEqual(crossover_signal(100.0, 100.0, 99.99, 100.0), SELL)


class CashInterestTests(unittest.TestCase):
    def test_cash_interest_uses_act_365(self) -> None:
        self.assertAlmostEqual(cash_interest_amount(100_000, 0.05, 7), 95.8904109589, places=6)

    def test_cash_interest_rejects_nonpositive_inputs(self) -> None:
        self.assertEqual(cash_interest_amount(100_000, 0.0, 7), 0.0)
        self.assertEqual(cash_interest_amount(100_000, 0.05, 0), 0.0)
        self.assertEqual(cash_interest_amount(0.0, 0.05, 7), 0.0)


class DrawdownTrackerTests(unittest.TestCase):
    def test_tracks_worst_drawdown(self) -> None:
        tracker = DrawdownTracker()
        tracker.update(100)
        tracker.update(120)
        tracker.update(90)
        tracker.update(110)
        self.assertAlmostEqual(tracker.max_drawdown, -0.25)


if __name__ == "__main__":
    unittest.main()
