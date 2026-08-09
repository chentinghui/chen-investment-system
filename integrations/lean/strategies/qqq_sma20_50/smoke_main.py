from AlgorithmImports import *
from datetime import datetime, timedelta
import os

from strategy_logic import BUY, SELL, DrawdownTracker, cash_interest_amount, crossover_signal


class QqqDaily(PythonData):
    """Synthetic daily QQQ OHLC + cash-rate feed used only for engine CI testing."""

    def get_source(self, config, date, is_live_mode):
        path = os.path.join(Globals.data_folder, "custom", "qqq_sma20_50.csv")
        return SubscriptionDataSource(path, SubscriptionTransportMedium.LOCAL_FILE)

    def reader(self, config, line, date, is_live_mode):
        if not line or line.startswith("date,"):
            return None
        parts = line.split(",")
        if len(parts) < 6:
            return None

        point = QqqDaily()
        point.symbol = config.symbol
        point.time = datetime.strptime(parts[0], "%Y-%m-%d")
        point.end_time = point.time + timedelta(days=1)
        point.open = float(parts[1])
        point.high = float(parts[2])
        point.low = float(parts[3])
        point.close = float(parts[4])
        point.cash_rate = float(parts[5])
        # Custom securities trade at Value. Set it to the adjusted open so a
        # pending signal from the prior close executes at the next session open.
        point.value = point.open
        return point


class QqqSma20Sma50SmokeAlgorithm(QCAlgorithm):
    """Actual LEAN-engine test harness for the production crossover logic.

    It uses public Yahoo/FRED data converted into a local custom security. This
    deliberately avoids claiming native QuantConnect QQQ data entitlement while
    still exercising LEAN's event loop, portfolio, fills, fees, slippage,
    statistics, and CIS result adapter end-to-end.
    """

    def initialize(self):
        self.set_start_date(2020, 1, 2)
        self.set_end_date(2026, 8, 7)
        self.set_cash(100_000)

        security = self.add_data(QqqDaily, "QQQ_CIS", Resolution.DAILY)
        self._symbol = security.symbol
        security.set_fee_model(ConstantFeeModel(0.0))
        security.set_slippage_model(ConstantSlippageModel(0.0001))

        self._fast = SimpleMovingAverage(20)
        self._slow = SimpleMovingAverage(50)
        self.set_warm_up(60, Resolution.DAILY)

        self._previous_fast = None
        self._previous_slow = None
        self._pending = None
        self._last_cash_accrual_date = None
        self._cash_interest_credited = 0.0
        self._drawdown = DrawdownTracker()
        self._signals = []

    def on_warmup_finished(self):
        if self._fast.is_ready and self._slow.is_ready:
            self._previous_fast = float(self._fast.current.value)
            self._previous_slow = float(self._slow.current.value)

    def on_data(self, data):
        if not data.contains_key(self._symbol):
            return
        point = data[self._symbol]

        if not self.is_warming_up:
            self._accrue_idle_cash(point)
            self._execute_pending_at_open(point)
            self._update_intraday_proxy(point)

        self._fast.update(point.end_time, point.close)
        self._slow.update(point.end_time, point.close)

        if self.is_warming_up or not (self._fast.is_ready and self._slow.is_ready):
            return

        current_fast = float(self._fast.current.value)
        current_slow = float(self._slow.current.value)
        signal = crossover_signal(
            self._previous_fast,
            self._previous_slow,
            current_fast,
            current_slow,
        )
        if signal is not None:
            self._pending = {
                "action": signal,
                "signal_date": self.time.strftime("%Y-%m-%d"),
            }

        self._previous_fast = current_fast
        self._previous_slow = current_slow

    def _execute_pending_at_open(self, point):
        if self._pending is None:
            return
        action = self._pending["action"]
        signal_date = self._pending["signal_date"]
        self._pending = None

        if action == BUY and not self.portfolio[self._symbol].invested:
            self.set_holdings(self._symbol, 1.0)
            self._signals.append(("BUY", signal_date, self.time.strftime("%Y-%m-%d"), float(point.open)))
        elif action == SELL and self.portfolio[self._symbol].invested:
            self.liquidate(self._symbol)
            self._signals.append(("SELL", signal_date, self.time.strftime("%Y-%m-%d"), float(point.open)))

    def _accrue_idle_cash(self, point):
        current_date = self.time.date()
        if self._last_cash_accrual_date is None:
            self._last_cash_accrual_date = current_date
            return
        days = (current_date - self._last_cash_accrual_date).days
        self._last_cash_accrual_date = current_date
        if self.portfolio.invested or days <= 0:
            return
        usd = self.portfolio.cash_book["USD"]
        rate = max(0.0, float(point.cash_rate))
        interest = cash_interest_amount(float(usd.amount), rate, days)
        if interest > 0:
            usd.add_amount(interest)
            self._cash_interest_credited += interest

    def _update_intraday_proxy(self, point):
        holdings = self.portfolio[self._symbol]
        if holdings.invested:
            proxy = float(self.portfolio.cash + holdings.quantity * point.low)
        else:
            proxy = float(self.portfolio.total_portfolio_value)
        self._drawdown.update(proxy)

    def on_end_of_algorithm(self):
        first_buy = next((x for x in self._signals if x[0] == "BUY"), None)
        last_signal = self._signals[-1] if self._signals else None
        self.set_summary_statistic("CIS Engine Harness", "QuantConnect LEAN custom-data smoke")
        self.set_summary_statistic("CIS Strict Cross Executions", str(len(self._signals)))
        self.set_summary_statistic("CIS Cash Interest Credited", f"{self._cash_interest_credited:.2f}")
        self.set_summary_statistic("CIS Intraday Proxy Max Drawdown", f"{self._drawdown.max_drawdown:.6%}")
        if first_buy:
            self.set_summary_statistic("CIS First Buy Signal Date", first_buy[1])
            self.set_summary_statistic("CIS First Buy Execution Date", first_buy[2])
        if last_signal:
            self.set_summary_statistic("CIS Last Execution", "|".join(map(str, last_signal[:3])))
