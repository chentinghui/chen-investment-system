from __future__ import annotations

import argparse
import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from prediction_ledger import DEFAULT_LEDGER, load_events, outcome_keys, prediction_map, record_outcome

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


@dataclass(frozen=True)
class DailyBar:
    session_date: date
    adjusted_close: float


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _unix_day(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp())


def fetch_yahoo_daily(symbol: str, start: date, end: date) -> list[DailyBar]:
    """Fetch adjusted daily closes from Yahoo's public chart endpoint.

    This is a best-effort, unauthenticated market-data source. Outcome events
    preserve the source name so production calibration can later be reconciled
    to a licensed provider without rewriting the original prediction snapshot.
    """
    encoded = urllib.parse.quote(symbol, safe="")
    params = urllib.parse.urlencode(
        {
            "period1": _unix_day(start),
            "period2": _unix_day(end + timedelta(days=1)),
            "interval": "1d",
            "events": "history",
            "includeAdjustedClose": "true",
        }
    )
    request = urllib.request.Request(
        f"{YAHOO_CHART.format(symbol=encoded)}?{params}",
        headers={"User-Agent": "chen-investment-system/0.5.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    chart = payload.get("chart", {})
    if chart.get("error"):
        raise RuntimeError(f"Yahoo error for {symbol}: {chart['error']}")
    results = chart.get("result") or []
    if not results:
        raise RuntimeError(f"Yahoo returned no history for {symbol}")
    result = results[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators", {})
    adjclose_blocks = indicators.get("adjclose") or []
    adjusted = (adjclose_blocks[0].get("adjclose") if adjclose_blocks else None) or []
    quote_blocks = indicators.get("quote") or []
    closes = (quote_blocks[0].get("close") if quote_blocks else None) or []

    bars: list[DailyBar] = []
    for index, timestamp in enumerate(timestamps):
        raw = adjusted[index] if index < len(adjusted) else None
        if raw is None and index < len(closes):
            raw = closes[index]
        if raw is None:
            continue
        value = float(raw)
        if not math.isfinite(value) or value <= 0:
            continue
        session = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).date()
        bars.append(DailyBar(session, value))
    if not bars:
        raise RuntimeError(f"Yahoo returned no usable closes for {symbol}")
    return bars


def _entry_index(bars: list[DailyBar], as_of: date) -> int | None:
    eligible = [index for index, bar in enumerate(bars) if bar.session_date <= as_of]
    if eligible:
        return eligible[-1]
    return 0 if bars else None


def _bar_on_or_before(bars: list[DailyBar], target: date) -> DailyBar | None:
    eligible = [bar for bar in bars if bar.session_date <= target]
    return eligible[-1] if eligible else None


def path_metrics(path: list[float]) -> dict[str, float]:
    if not path or path[0] <= 0:
        raise ValueError("price path must start with a positive value")
    entry = path[0]
    relative = [value / entry - 1 for value in path]
    peak = path[0]
    max_drawdown = 0.0
    for value in path:
        peak = max(peak, value)
        drawdown = value / peak - 1
        max_drawdown = min(max_drawdown, drawdown)
    return {
        "realized_return": path[-1] / entry - 1,
        "max_favorable_excursion": max(relative),
        "max_adverse_excursion": min(relative),
        "max_drawdown_during_horizon": max_drawdown,
    }


def _benchmark_return(bars: list[DailyBar], start: date, end: date) -> tuple[float, DailyBar, DailyBar]:
    entry = _bar_on_or_before(bars, start)
    exit_bar = _bar_on_or_before(bars, end)
    if entry is None or exit_bar is None or exit_bar.session_date < entry.session_date:
        raise ValueError("benchmark does not cover the evaluation window")
    return exit_bar.adjusted_close / entry.adjusted_close - 1, entry, exit_bar


def settle_prediction(
    prediction: dict[str, Any],
    already_settled: set[tuple[str, int]],
    *,
    today: date,
    fetcher: Callable[[str, date, date], list[DailyBar]] = fetch_yahoo_daily,
) -> tuple[list[dict[str, Any]], list[str]]:
    research_id = str(prediction["research_id"])
    as_of = date.fromisoformat(str(prediction["as_of"]))
    horizons = [int(value) for value in prediction.get("horizons_trading_days", [])]
    if not horizons and prediction.get("horizon_days"):
        horizons = [int(prediction["horizon_days"])]
    pending = [h for h in sorted(set(horizons)) if (research_id, h) not in already_settled]
    if not pending:
        return [], []

    start = as_of - timedelta(days=15)
    stock_bars = fetcher(str(prediction["ticker"]), start, today)
    entry_index = _entry_index(stock_bars, as_of)
    if entry_index is None:
        return [], [f"{research_id}: no entry session"]

    benchmark_symbol = str(prediction["benchmark"])
    benchmark_bars = fetcher(benchmark_symbol, start, today)
    sector_symbol = str(prediction.get("sector_benchmark") or "").strip()
    sector_bars = fetcher(sector_symbol, start, today) if sector_symbol else []

    outcomes: list[dict[str, Any]] = []
    warnings: list[str] = []
    for horizon in pending:
        target_index = entry_index + horizon
        if target_index >= len(stock_bars):
            continue
        path_bars = stock_bars[entry_index : target_index + 1]
        entry_bar = path_bars[0]
        exit_bar = path_bars[-1]
        metrics = path_metrics([bar.adjusted_close for bar in path_bars])
        try:
            benchmark_return, benchmark_entry, benchmark_exit = _benchmark_return(
                benchmark_bars, entry_bar.session_date, exit_bar.session_date
            )
        except ValueError as exc:
            warnings.append(f"{research_id}/{horizon}: {exc}")
            continue

        sector_return: float | None = None
        if sector_bars:
            try:
                sector_return, _, _ = _benchmark_return(
                    sector_bars, entry_bar.session_date, exit_bar.session_date
                )
            except ValueError as exc:
                warnings.append(f"{research_id}/{horizon}: sector benchmark: {exc}")

        snapshot_price = prediction.get("analysis_price")
        price_gap: float | None = None
        if snapshot_price not in (None, ""):
            try:
                snapshot = float(snapshot_price)
                if snapshot > 0:
                    price_gap = entry_bar.adjusted_close / snapshot - 1
                    if abs(price_gap) > 0.05:
                        warnings.append(
                            f"{research_id}/{horizon}: reconstructed entry differs from analysis_price by {price_gap:.2%}"
                        )
            except (TypeError, ValueError):
                warnings.append(f"{research_id}: invalid analysis_price ignored")

        outcome: dict[str, Any] = {
            "research_id": research_id,
            "horizon_trading_days": horizon,
            "evaluation_as_of": exit_bar.session_date.isoformat(),
            "entry_session_date": entry_bar.session_date.isoformat(),
            "exit_session_date": exit_bar.session_date.isoformat(),
            "entry_price": entry_bar.adjusted_close,
            "exit_price": exit_bar.adjusted_close,
            "realized_return": metrics["realized_return"],
            "benchmark_return": benchmark_return,
            "benchmark_entry_price": benchmark_entry.adjusted_close,
            "benchmark_exit_price": benchmark_exit.adjusted_close,
            "max_favorable_excursion": metrics["max_favorable_excursion"],
            "max_adverse_excursion": metrics["max_adverse_excursion"],
            "max_drawdown_during_horizon": metrics["max_drawdown_during_horizon"],
            "falsifier_triggered": None,
            "falsifier_status": "not_evaluated_automatically",
            "market_data_source": "Yahoo Finance chart API (best-effort, unauthenticated)",
            "market_data_retrieved_at": now_iso(),
            "analysis_price_gap_to_reconstructed_entry": price_gap,
        }
        if sector_return is not None:
            outcome["sector_benchmark_return"] = sector_return
        outcomes.append(outcome)
    return outcomes, warnings


def settle_due(
    ledger: Path,
    *,
    today: date,
    fetcher: Callable[[str, date, date], list[DailyBar]] = fetch_yahoo_daily,
    dry_run: bool = False,
) -> dict[str, Any]:
    events = load_events(ledger)
    predictions = prediction_map(events)
    settled = outcome_keys(events)
    created: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    for prediction in predictions.values():
        try:
            outcomes, item_warnings = settle_prediction(
                prediction, settled, today=today, fetcher=fetcher
            )
            warnings.extend(item_warnings)
            for outcome in outcomes:
                if not dry_run:
                    record_outcome(ledger, outcome)
                    settled.add((str(outcome["research_id"]), int(outcome["horizon_trading_days"])))
                created.append(outcome)
        except Exception as exc:
            errors.append(f"{prediction.get('research_id')}: {type(exc).__name__}: {exc}")

    status = "success"
    if errors and created:
        status = "partial"
    elif errors and not created:
        status = "provider_unavailable_or_no_settlement"
    return {
        "status": status,
        "prediction_count": len(predictions),
        "outcomes_created": len(created),
        "dry_run": dry_run,
        "outcomes": created,
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Settle due CIS prediction horizons using daily market data")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--today", help="Override current UTC date, YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args()

    today = date.fromisoformat(args.today) if args.today else datetime.now(timezone.utc).date()
    result = settle_due(args.ledger, today=today, dry_run=args.dry_run)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.summary_output:
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        args.summary_output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
