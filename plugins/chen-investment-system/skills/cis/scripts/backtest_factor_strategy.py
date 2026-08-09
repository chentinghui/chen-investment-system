from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any


def parse_float(value: Any) -> float | None:
    try:
        text = str(value).strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def max_drawdown(returns: list[float]) -> float:
    equity = 1.0
    peak = 1.0
    worst = 0.0
    for r in returns:
        equity *= 1.0 + r
        peak = max(peak, equity)
        drawdown = equity / peak - 1.0
        worst = min(worst, drawdown)
    return worst


def annualized_metrics(returns: list[float], periods_per_year: int) -> dict[str, float | None]:
    if not returns:
        return {"cagr": None, "annualized_volatility": None, "sharpe": None, "max_drawdown": None}
    equity = 1.0
    for r in returns:
        equity *= 1.0 + r
    years = len(returns) / periods_per_year
    cagr = equity ** (1.0 / years) - 1.0 if years > 0 and equity > 0 else None
    if len(returns) >= 2:
        ann_vol = stdev(returns) * math.sqrt(periods_per_year)
        sharpe = (mean(returns) * periods_per_year / ann_vol) if ann_vol > 0 else None
    else:
        ann_vol = None
        sharpe = None
    return {
        "cagr": cagr,
        "annualized_volatility": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown(returns),
    }


def run_backtest(
    rows: list[dict[str, str]],
    top_fraction: float,
    top_n: int | None,
    cost_bps: float,
    periods_per_year: int,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        score = parse_float(row.get("score"))
        forward_return = parse_float(row.get("forward_return"))
        if not row.get("date") or not row.get("ticker") or score is None or forward_return is None:
            continue
        grouped[row["date"]].append(
            {
                "ticker": row["ticker"],
                "score": score,
                "forward_return": forward_return,
                "benchmark_return": parse_float(row.get("benchmark_return")),
            }
        )

    portfolio_returns: list[float] = []
    benchmark_returns: list[float] = []
    period_details: list[dict[str, Any]] = []
    one_way_cost = cost_bps / 10000.0

    for date in sorted(grouped):
        candidates = sorted(grouped[date], key=lambda item: item["score"], reverse=True)
        if not candidates:
            continue
        count = top_n if top_n is not None else max(1, math.ceil(len(candidates) * top_fraction))
        selected = candidates[: min(count, len(candidates))]
        gross_return = mean(item["forward_return"] for item in selected)
        net_return = gross_return - one_way_cost
        available_benchmarks = [item["benchmark_return"] for item in selected if item["benchmark_return"] is not None]
        benchmark_return = mean(available_benchmarks) if available_benchmarks else None

        portfolio_returns.append(net_return)
        if benchmark_return is not None:
            benchmark_returns.append(benchmark_return)
        period_details.append(
            {
                "date": date,
                "selected_count": len(selected),
                "selected_tickers": [item["ticker"] for item in selected],
                "gross_return": gross_return,
                "net_return": net_return,
                "benchmark_return": benchmark_return,
            }
        )

    metrics = annualized_metrics(portfolio_returns, periods_per_year)
    metrics["period_win_rate"] = (
        sum(1 for r in portfolio_returns if r > 0) / len(portfolio_returns) if portfolio_returns else None
    )
    if len(benchmark_returns) == len(portfolio_returns) and portfolio_returns:
        excess = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        metrics["mean_excess_return_per_period"] = mean(excess)
        metrics["excess_win_rate"] = sum(1 for r in excess if r > 0) / len(excess)
    else:
        metrics["mean_excess_return_per_period"] = None
        metrics["excess_win_rate"] = None

    return {
        "status": "experimental_baseline",
        "periods": len(portfolio_returns),
        "periods_per_year": periods_per_year,
        "transaction_cost_bps_per_rebalance": cost_bps,
        "selection": {"top_n": top_n, "top_fraction": top_fraction if top_n is None else None},
        "metrics": metrics,
        "period_details": period_details,
        "warning": "Input must be point-in-time and survivorship-bias-aware; this script does not create forward returns or historical universes.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CIS baseline cross-sectional factor backtest")
    parser.add_argument("input_csv", help="CSV: date,ticker,score,forward_return[,benchmark_return]")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--top-n", type=int)
    group.add_argument("--top-fraction", type=float, default=0.20)
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--periods-per-year", type=int, default=12)
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.top_n is not None and args.top_n <= 0:
        raise SystemExit("--top-n must be positive")
    if not 0 < args.top_fraction <= 1:
        raise SystemExit("--top-fraction must be in (0, 1]")
    if args.periods_per_year <= 0:
        raise SystemExit("--periods-per-year must be positive")

    with open(args.input_csv, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    required = {"date", "ticker", "score", "forward_return"}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit(f"input CSV must contain: {', '.join(sorted(required))}")

    payload = run_backtest(rows, args.top_fraction, args.top_n, args.cost_bps, args.periods_per_year)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
