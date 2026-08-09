from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev
from typing import Any


def parse_float(value: Any) -> float | None:
    try:
        if value is None or isinstance(value, bool):
            return None
        text = str(value).strip()
        number = float(text) if text else None
        if number is None or not math.isfinite(number):
            return None
        return number
    except (TypeError, ValueError):
        return None


def parse_period(value: str) -> datetime:
    text = value.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError(f"date must be YYYY-MM or YYYY-MM-DD: {value}")


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


def equal_weights(tickers: list[str]) -> dict[str, float]:
    if not tickers:
        return {}
    if len(set(tickers)) != len(tickers):
        raise ValueError("tickers must be unique when constructing portfolio weights")
    w = 1.0 / len(tickers)
    return {ticker: w for ticker in tickers}


def one_way_turnover(previous: dict[str, float], current: dict[str, float]) -> float:
    if not previous:
        return 1.0 if current else 0.0
    names = set(previous) | set(current)
    turnover = 0.5 * sum(abs(current.get(k, 0.0) - previous.get(k, 0.0)) for k in names)
    return min(max(turnover, 0.0), 1.0)


def segment_name(date_text: str, train_end: str | None, validation_end: str | None) -> str:
    current = parse_period(date_text)
    if train_end and current <= parse_period(train_end):
        return "train"
    if validation_end and current <= parse_period(validation_end):
        return "validation"
    return "out_of_sample" if train_end or validation_end else "all"


def summarize_returns(returns: list[float], benchmarks: list[float | None], periods_per_year: int) -> dict[str, Any]:
    metrics: dict[str, Any] = annualized_metrics(returns, periods_per_year)
    metrics["period_win_rate"] = sum(1 for r in returns if r > 0) / len(returns) if returns else None
    valid_pairs = [(p, b) for p, b in zip(returns, benchmarks) if b is not None]
    if valid_pairs and len(valid_pairs) == len(returns):
        excess = [p - float(b) for p, b in valid_pairs]
        metrics["mean_excess_return_per_period"] = mean(excess)
        metrics["excess_win_rate"] = sum(1 for r in excess if r > 0) / len(excess)
    else:
        metrics["mean_excess_return_per_period"] = None
        metrics["excess_win_rate"] = None
    return metrics


def run_backtest(
    rows: list[dict[str, str]],
    top_fraction: float,
    top_n: int | None,
    cost_bps: float,
    periods_per_year: int,
    train_end: str | None = None,
    validation_end: str | None = None,
) -> dict[str, Any]:
    if top_n is not None and top_n <= 0:
        raise ValueError("top_n must be positive")
    if not 0 < top_fraction <= 1:
        raise ValueError("top_fraction must be in (0, 1]")
    if not math.isfinite(cost_bps) or cost_bps < 0:
        raise ValueError("cost_bps must be a finite non-negative number")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if train_end and validation_end and parse_period(validation_end) <= parse_period(train_end):
        raise ValueError("validation_end must be after train_end")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_period_tickers: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        score = parse_float(row.get("score"))
        forward_return = parse_float(row.get("forward_return"))
        raw_date = str(row.get("date") or "").strip()
        ticker = str(row.get("ticker") or "").strip().upper()
        if not raw_date or not ticker or score is None or forward_return is None:
            continue
        parse_period(raw_date)
        if forward_return < -1.0:
            raise ValueError(f"forward_return cannot be below -100% at row {index}")
        key = (raw_date, ticker)
        if key in seen_period_tickers:
            raise ValueError(f"duplicate ticker within period: {raw_date}/{ticker}")
        seen_period_tickers.add(key)
        benchmark_return = parse_float(row.get("benchmark_return"))
        if benchmark_return is not None and benchmark_return < -1.0:
            raise ValueError(f"benchmark_return cannot be below -100% at row {index}")
        grouped[raw_date].append({
            "ticker": ticker,
            "score": score,
            "forward_return": forward_return,
            "benchmark_return": benchmark_return,
        })

    portfolio_returns: list[float] = []
    benchmark_returns: list[float | None] = []
    period_details: list[dict[str, Any]] = []
    previous_weights: dict[str, float] = {}
    cost_rate = cost_bps / 10000.0

    for period in sorted(grouped, key=parse_period):
        candidates = sorted(grouped[period], key=lambda item: item["score"], reverse=True)
        count = top_n if top_n is not None else max(1, math.ceil(len(candidates) * top_fraction))
        selected = candidates[: min(count, len(candidates))]
        tickers = [item["ticker"] for item in selected]
        current_weights = equal_weights(tickers)
        turnover = one_way_turnover(previous_weights, current_weights)
        transaction_cost = turnover * cost_rate
        gross_return = mean(item["forward_return"] for item in selected)
        net_return = gross_return - transaction_cost

        available_benchmarks = [item["benchmark_return"] for item in selected if item["benchmark_return"] is not None]
        benchmark_return = None
        if available_benchmarks:
            first = available_benchmarks[0]
            if any(abs(float(x) - float(first)) > 1e-12 for x in available_benchmarks[1:]):
                raise ValueError(f"benchmark_return must be identical within period {period}")
            benchmark_return = float(first)

        segment = segment_name(period, train_end, validation_end)
        portfolio_returns.append(net_return)
        benchmark_returns.append(benchmark_return)
        period_details.append({
            "date": period,
            "segment": segment,
            "selected_count": len(selected),
            "selected_tickers": tickers,
            "gross_return": gross_return,
            "turnover": turnover,
            "transaction_cost": transaction_cost,
            "net_return": net_return,
            "benchmark_return": benchmark_return,
        })
        previous_weights = current_weights

    metrics = summarize_returns(portfolio_returns, benchmark_returns, periods_per_year)
    metrics["average_turnover"] = mean([p["turnover"] for p in period_details]) if period_details else None
    metrics["total_transaction_cost"] = sum(p["transaction_cost"] for p in period_details)

    metrics_by_segment: dict[str, Any] = {}
    for segment in ("train", "validation", "out_of_sample", "all"):
        subset = [p for p in period_details if p["segment"] == segment]
        if not subset:
            continue
        metrics_by_segment[segment] = {
            "periods": len(subset),
            **summarize_returns([p["net_return"] for p in subset], [p["benchmark_return"] for p in subset], periods_per_year),
        }

    return {
        "status": "experimental_baseline_optional_extension",
        "periods": len(portfolio_returns),
        "periods_per_year": periods_per_year,
        "transaction_cost_bps_per_one_way_turnover": cost_bps,
        "selection": {"top_n": top_n, "top_fraction": top_fraction if top_n is None else None},
        "split": {"train_end": train_end, "validation_end": validation_end},
        "metrics": metrics,
        "metrics_by_segment": metrics_by_segment,
        "period_details": period_details,
        "warning": "Input must be point-in-time, unique by (date,ticker), and survivorship-bias-aware. This optional extension never changes CIS production rules automatically.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional CIS baseline cross-sectional factor backtest")
    parser.add_argument("input_csv", help="CSV: date,ticker,score,forward_return[,benchmark_return]")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--top-n", type=int)
    group.add_argument("--top-fraction", type=float, default=0.20)
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--periods-per-year", type=int, default=12)
    parser.add_argument("--train-end")
    parser.add_argument("--validation-end")
    parser.add_argument("--output")
    args = parser.parse_args()
    with open(args.input_csv, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    required = {"date", "ticker", "score", "forward_return"}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit(f"input CSV must contain: {', '.join(sorted(required))}")
    try:
        payload = run_backtest(rows, args.top_fraction, args.top_n, args.cost_bps, args.periods_per_year, args.train_end, args.validation_end)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
