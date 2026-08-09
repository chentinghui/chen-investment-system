from AlgorithmImports import *

from strategy_logic import BUY, SELL, DrawdownTracker, cash_interest_amount, crossover_signal


class QqqSma20Sma50Algorithm(QCAlgorithm):
    """Strict 20/50-day QQQ moving-average crossover strategy for LEAN.

    Rules:
      * start in cash;
      * BUY only on an actual SMA20 cross from <= SMA50 to > SMA50;
      * SELL only on an actual SMA20 cross from >= SMA50 to < SMA50;
      * signal is confirmed on the daily close and executed with a Market-On-Open
        order for the next trading session;
      * QQQ uses adjusted data so splits/dividends are normalized consistently;
      * idle USD cash is credited using LEAN's historical risk-free-rate model;
      * fee and slippage assumptions are parameters, not hidden constants.
    """

    def initialize(self) -> None:
        self.set_start_date(2020, 1, 2)
        self.set_end_date(2026, 8, 7)
        self.set_cash(100_000)
        self.set_benchmark("QQQ")

        self._fast_period = int(self.get_parameter("fast_period") or 20)
        self._slow_period = int(self.get_parameter("slow_period") or 50)
        self._fee_per_order = float(self.get_parameter("fee_per_order") or 0.0)
        self._slippage_bps = float(self.get_parameter("slippage_bps") or 1.0)
        self._credit_cash_yield = (self.get_parameter("credit_cash_yield") or "true").lower() == "true"

        security = self.add_equity(
            "QQQ",
            Resolution.DAILY,
            data_normalization_mode=DataNormalizationMode.ADJUSTED,
        )
        self._symbol = security.symbol
        security.set_fee_model(ConstantFeeModel(self._fee_per_order))
        security.set_slippage_model(ConstantSlippageModel(self._slippage_bps / 10_000.0))

        # LEAN's InterestRateProvider is used for historical risk-free-rate-aware
        # statistics and, when enabled, for explicit idle-cash accrual below.
        self.set_risk_free_interest_rate_model(InterestRateProvider())

        self._fast = self.sma(self._symbol, self._fast_period, Resolution.DAILY)
        self._slow = self.sma(self._symbol, self._slow_period, Resolution.DAILY)
        self.set_warm_up(self._slow_period + 1, Resolution.DAILY)

        self._previous_fast = None
        self._previous_slow = None
        self._last_cash_accrual_date = None
        self._cash_interest_credited = 0.0
        self._cross_count = 0
        self._intraday_drawdown = DrawdownTracker()

    def on_warmup_finished(self) -> None:
        # Seed only the previous indicator values. Do not seed a position. This
        # prevents the old bug where a pre-existing bullish regime caused an
        # automatic buy on the first backtest day without a fresh golden cross.
        if self._fast.is_ready and self._slow.is_ready:
            self._previous_fast = float(self._fast.current.value)
            self._previous_slow = float(self._slow.current.value)

    def on_data(self, data: Slice) -> None:
        bar = data.bars.get(self._symbol)
        if bar is None:
            return

        self._accrue_idle_cash()
        self._update_intraday_proxy_drawdown(bar)

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

        if signal is not None and not self.transactions.get_open_orders(self._symbol):
            if signal == BUY and not self.portfolio[self._symbol].invested:
                quantity = self.calculate_order_quantity(self._symbol, 1.0)
                if quantity > 0:
                    self.market_on_open_order(
                        self._symbol,
                        quantity,
                        tag=f"SMA{self._fast_period} crossed above SMA{self._slow_period}",
                    )
                    self._cross_count += 1
            elif signal == SELL and self.portfolio[self._symbol].invested:
                quantity = -self.portfolio[self._symbol].quantity
                if quantity != 0:
                    self.market_on_open_order(
                        self._symbol,
                        quantity,
                        tag=f"SMA{self._fast_period} crossed below SMA{self._slow_period}",
                    )
                    self._cross_count += 1

        self._previous_fast = current_fast
        self._previous_slow = current_slow

    def _accrue_idle_cash(self) -> None:
        current_date = self.time.date()
        if self._last_cash_accrual_date is None:
            self._last_cash_accrual_date = current_date
            return

        calendar_days = (current_date - self._last_cash_accrual_date).days
        self._last_cash_accrual_date = current_date
        if not self._credit_cash_yield or self.portfolio.invested or calendar_days <= 0:
            return

        usd = self.portfolio.cash_book["USD"]
        annual_rate = float(self.risk_free_interest_rate_model.get_interest_rate(self.time))
        interest = cash_interest_amount(float(usd.amount), annual_rate, calendar_days)
        if interest > 0:
            usd.add_amount(interest)
            self._cash_interest_credited += interest

    def _update_intraday_proxy_drawdown(self, bar: TradeBar) -> None:
        holdings = self.portfolio[self._symbol]
        if holdings.invested:
            # Daily-low proxy: conservative within each daily bar. It is more
            # informative than close-only drawdown while remaining auditable at
            # daily resolution.
            proxy_equity = float(self.portfolio.cash + holdings.quantity * bar.low)
        else:
            proxy_equity = float(self.portfolio.total_portfolio_value)
        self._intraday_drawdown.update(proxy_equity)

    def on_end_of_algorithm(self) -> None:
        self.set_summary_statistic(
            "CIS Intraday Proxy Max Drawdown",
            f"{self._intraday_drawdown.max_drawdown:.6%}",
        )
        self.set_summary_statistic("CIS Strict Cross Orders", str(self._cross_count))
        self.set_summary_statistic(
            "CIS Cash Interest Credited",
            f"{self._cash_interest_credited:.2f}",
        )
        self.set_summary_statistic(
            "CIS Execution Rule",
            "strict crossover at close; next-session Market-On-Open",
        )
