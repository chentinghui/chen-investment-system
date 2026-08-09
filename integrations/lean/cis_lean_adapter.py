from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "cis.lean.backtest.v1"
ENGINE_NAME = "QuantConnect LEAN"
ENGINE_ROLE = "external_quant_validation"

_DISPLAY_STAT_KEYS = {
    "Compounding Annual Return",
    "Drawdown",
    "Sharpe Ratio",
    "Sortino Ratio",
    "Net Profit",
    "Win Rate",
    "Loss Rate",
    "Profit-Loss Ratio",
    "Annual Standard Deviation",
    "Total Orders",
    "Total Trades",
}

_CAMEL_STAT_KEYS = {
    "compoundingAnnualReturn",
    "drawdown",
    "sharpeRatio",
    "sortinoRatio",
    "totalNetProfit",
    "winRate",
    "lossRate",
    "profitLossRatio",
    "annualStandardDeviation",
}

_EXCLUDED_RESULT_NAMES = (
    "-alpha-results.json",
    "-order-events.json",
    "data-monitor-report-",
)


def _finite_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None

    text = str(value).strip()
    if not text:
        return None

    negative_parentheses = text.startswith("(") and text.endswith(")")
    if negative_parentheses:
        text = text[1:-1].strip()

    is_percent = text.endswith("%")
    if is_percent:
        text = text[:-1].strip()

    for token in ("$", "€", "£", "¥", ","):
        text = text.replace(token, "")

    try:
        number = float(text)
    except ValueError:
        return None

    if not math.isfinite(number):
        return None
    if negative_parentheses:
        number = -number
    if is_percent:
        number /= 100.0
    return number


def _extract_dict(payload: Mapping[str, Any], *keys: str) -> Mapping[str, Any] | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, Mapping):
            return value
    return None


def _looks_like_statistics(candidate: Mapping[str, Any]) -> bool:
    keys = set(candidate.keys())
    return len(keys & _DISPLAY_STAT_KEYS) >= 2 or len(keys & _CAMEL_STAT_KEYS) >= 2


def extract_statistics(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    direct = _extract_dict(payload, "statistics", "Statistics")
    if direct and _looks_like_statistics(direct):
        return direct

    total_performance = _extract_dict(payload, "totalPerformance", "TotalPerformance")
    if total_performance:
        portfolio = _extract_dict(total_performance, "portfolioStatistics", "PortfolioStatistics")
        if portfolio and _looks_like_statistics(portfolio):
            return portfolio

    for value in payload.values():
        if isinstance(value, Mapping):
            if _looks_like_statistics(value):
                return value
            nested = extract_statistics(value)
            if nested:
                return nested
    return None


def extract_runtime_statistics(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    direct = _extract_dict(payload, "runtimeStatistics", "RuntimeStatistics")
    if direct:
        return direct
    for value in payload.values():
        if isinstance(value, Mapping):
            nested = extract_runtime_statistics(value)
            if nested:
                return nested
    return None


def _first(stats: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in stats:
            return stats[key]
    return None


def normalize_statistics(stats: Mapping[str, Any]) -> dict[str, Any]:
    metrics: dict[str, Any] = {}

    numeric_map = {
        "cagr": ("Compounding Annual Return", "compoundingAnnualReturn"),
        "max_drawdown": ("Drawdown", "drawdown"),
        "sharpe_ratio": ("Sharpe Ratio", "sharpeRatio"),
        "sortino_ratio": ("Sortino Ratio", "sortinoRatio"),
        "net_profit": ("Net Profit", "totalNetProfit"),
        "win_rate": ("Win Rate", "winRate"),
        "loss_rate": ("Loss Rate", "lossRate"),
        "profit_loss_ratio": ("Profit-Loss Ratio", "profitLossRatio"),
        "expectancy": ("Expectancy", "expectancy"),
        "annual_volatility": ("Annual Standard Deviation", "annualStandardDeviation"),
        "alpha": ("Alpha", "alpha"),
        "beta": ("Beta", "beta"),
        "information_ratio": ("Information Ratio", "informationRatio"),
        "tracking_error": ("Tracking Error", "trackingError"),
        "treynor_ratio": ("Treynor Ratio", "treynorRatio"),
        "portfolio_turnover": ("Portfolio Turnover", "portfolioTurnover"),
    }

    for output_key, input_keys in numeric_map.items():
        number = _finite_number(_first(stats, *input_keys))
        if number is not None:
            metrics[output_key] = number

    total_orders = _finite_number(_first(stats, "Total Orders", "totalOrders"))
    if total_orders is not None:
        metrics["total_orders"] = int(total_orders)

    total_trades = _finite_number(_first(stats, "Total Trades", "totalTrades"))
    if total_trades is not None:
        metrics["total_trades"] = int(total_trades)

    for output_key, input_keys in {
        "total_fees_raw": ("Total Fees", "totalFees"),
        "estimated_strategy_capacity_raw": ("Estimated Strategy Capacity", "estimatedStrategyCapacity"),
        "lowest_capacity_asset": ("Lowest Capacity Asset", "lowestCapacityAsset"),
    }.items():
        value = _first(stats, *input_keys)
        if value not in (None, ""):
            metrics[output_key] = value

    return metrics


def parse_result_payload(payload: Mapping[str, Any], *, result_file: str | None = None) -> dict[str, Any]:
    statistics = extract_statistics(payload)
    if not statistics:
        raise ValueError("LEAN result JSON does not contain recognizable backtest statistics")

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "engine": ENGINE_NAME,
        "engine_role": ENGINE_ROLE,
        "decision_authority": "none",
        "execution_status": "success",
        "research_quality": "unreviewed",
        "metrics": normalize_statistics(statistics),
        "statistics_raw": dict(statistics),
    }
    if result_file:
        result["result_file"] = result_file

    runtime_statistics = extract_runtime_statistics(payload)
    if runtime_statistics:
        result["runtime_statistics_raw"] = dict(runtime_statistics)

    return result


def parse_result_file(path: Path | str) -> dict[str, Any]:
    result_path = Path(path).expanduser().resolve()
    if not result_path.is_file():
        raise FileNotFoundError(f"LEAN result file not found: {result_path}")
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("LEAN result JSON root must be an object")
    return parse_result_payload(payload, result_file=str(result_path))


def discover_result_file(output_dir: Path | str) -> Path:
    root = Path(output_dir).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"LEAN output directory not found: {root}")

    candidates = []
    for path in root.rglob("*.json"):
        name = path.name
        if any(name.endswith(suffix) for suffix in _EXCLUDED_RESULT_NAMES[:2]):
            continue
        if name.startswith(_EXCLUDED_RESULT_NAMES[2]):
            continue
        candidates.append(path)

    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(payload, Mapping) and extract_statistics(payload):
            return path

    raise FileNotFoundError(f"no recognizable LEAN backtest result JSON found under: {root}")


def check_readiness(
    *,
    lean_executable: str = "lean",
    docker_executable: str = "docker",
    runner: Any = subprocess.run,
) -> dict[str, Any]:
    lean_path = shutil.which(lean_executable)
    docker_path = shutil.which(docker_executable)

    readiness = "ready"
    missing: list[str] = []
    if not lean_path:
        missing.append("lean_cli")
    if not docker_path:
        missing.append("docker")
    if missing:
        readiness = "unavailable"

    result: dict[str, Any] = {
        "engine": ENGINE_NAME,
        "engine_role": ENGINE_ROLE,
        "runtime_readiness": readiness,
        "missing": missing,
        "lean_executable": lean_path,
        "docker_executable": docker_path,
        "account_entitlement": "not_checked",
    }

    if lean_path:
        try:
            completed = runner(
                [lean_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            version_text = (completed.stdout or completed.stderr or "").strip()
            if version_text:
                result["lean_version"] = version_text.splitlines()[-1]
        except (OSError, subprocess.TimeoutExpired):
            result["runtime_readiness"] = "unavailable"
            if "lean_cli_runtime" not in result["missing"]:
                result["missing"].append("lean_cli_runtime")

    if docker_path:
        try:
            completed = runner(
                [docker_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            version_text = (completed.stdout or completed.stderr or "").strip()
            if version_text:
                result["docker_version"] = version_text.splitlines()[-1]
        except (OSError, subprocess.TimeoutExpired):
            result["runtime_readiness"] = "unavailable"
            if "docker_runtime" not in result["missing"]:
                result["missing"].append("docker_runtime")

    return result


def build_backtest_command(
    project: Path | str,
    output_dir: Path | str,
    *,
    lean_executable: str = "lean",
    update_image: bool = False,
) -> list[str]:
    command = [
        lean_executable,
        "backtest",
        str(Path(project).expanduser()),
        "--output",
        str(Path(output_dir).expanduser()),
    ]
    if update_image:
        command.append("--update")
    return command


def _tail(text: str | None, limit: int = 6000) -> str:
    value = text or ""
    if len(value) <= limit:
        return value
    return value[-limit:]


def run_backtest(
    project: Path | str,
    output_dir: Path | str,
    *,
    lean_executable: str = "lean",
    update_image: bool = False,
    timeout_seconds: int | None = None,
    runner: Any = subprocess.run,
) -> dict[str, Any]:
    project_path = Path(project).expanduser().resolve()
    output_path = Path(output_dir).expanduser().resolve()

    if not project_path.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "engine": ENGINE_NAME,
            "engine_role": ENGINE_ROLE,
            "decision_authority": "none",
            "execution_status": "invalid_input",
            "error": f"LEAN project not found: {project_path}",
        }

    lean_path = shutil.which(lean_executable)
    if not lean_path:
        return {
            "schema_version": SCHEMA_VERSION,
            "engine": ENGINE_NAME,
            "engine_role": ENGINE_ROLE,
            "decision_authority": "none",
            "execution_status": "unavailable",
            "runtime_readiness": "lean_cli_missing",
            "error": "Lean CLI executable is not available on PATH",
        }

    docker_path = shutil.which("docker")
    if not docker_path:
        return {
            "schema_version": SCHEMA_VERSION,
            "engine": ENGINE_NAME,
            "engine_role": ENGINE_ROLE,
            "decision_authority": "none",
            "execution_status": "unavailable",
            "runtime_readiness": "docker_missing",
            "error": "Docker is required for local Lean CLI backtests but is not available on PATH",
        }

    output_path.mkdir(parents=True, exist_ok=True)
    command = build_backtest_command(
        project_path,
        output_path,
        lean_executable=lean_path,
        update_image=update_image,
    )

    try:
        completed = runner(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "engine": ENGINE_NAME,
            "engine_role": ENGINE_ROLE,
            "decision_authority": "none",
            "execution_status": "error",
            "error_type": "timeout",
            "error": f"LEAN backtest timed out after {timeout_seconds} seconds",
            "stdout_tail": _tail(exc.stdout if isinstance(exc.stdout, str) else None),
            "stderr_tail": _tail(exc.stderr if isinstance(exc.stderr, str) else None),
        }
    except OSError as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "engine": ENGINE_NAME,
            "engine_role": ENGINE_ROLE,
            "decision_authority": "none",
            "execution_status": "error",
            "error_type": "spawn_error",
            "error": str(exc),
        }

    if completed.returncode != 0:
        return {
            "schema_version": SCHEMA_VERSION,
            "engine": ENGINE_NAME,
            "engine_role": ENGINE_ROLE,
            "decision_authority": "none",
            "execution_status": "error",
            "error_type": "lean_nonzero_exit",
            "returncode": completed.returncode,
            "command": command,
            "stdout_tail": _tail(completed.stdout),
            "stderr_tail": _tail(completed.stderr),
        }

    try:
        result_file = discover_result_file(output_path)
        parsed = parse_result_file(result_file)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "engine": ENGINE_NAME,
            "engine_role": ENGINE_ROLE,
            "decision_authority": "none",
            "execution_status": "error",
            "error_type": "result_parse_error",
            "error": str(exc),
            "command": command,
            "stdout_tail": _tail(completed.stdout),
            "stderr_tail": _tail(completed.stderr),
        }

    parsed["command"] = command
    parsed["output_dir"] = str(output_path)
    parsed["stdout_tail"] = _tail(completed.stdout)
    parsed["stderr_tail"] = _tail(completed.stderr)
    return parsed


def _print_json(payload: Mapping[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CIS adapter for the external QuantConnect LEAN engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    readiness = subparsers.add_parser("readiness", help="Check local Lean CLI and Docker availability")
    readiness.add_argument("--lean-executable", default="lean")
    readiness.add_argument("--docker-executable", default="docker")

    parse = subparsers.add_parser("parse", help="Parse an existing LEAN backtest result JSON")
    parse.add_argument("--result", required=True)

    backtest = subparsers.add_parser("backtest", help="Run a local LEAN backtest through Lean CLI")
    backtest.add_argument("--project", required=True)
    backtest.add_argument("--output", required=True)
    backtest.add_argument("--lean-executable", default="lean")
    backtest.add_argument("--update-image", action="store_true")
    backtest.add_argument("--timeout-seconds", type=int, default=None)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.command == "readiness":
            payload = check_readiness(
                lean_executable=args.lean_executable,
                docker_executable=args.docker_executable,
            )
            _print_json(payload)
            return 0 if payload["runtime_readiness"] == "ready" else 2

        if args.command == "parse":
            payload = parse_result_file(args.result)
            _print_json(payload)
            return 0

        payload = run_backtest(
            args.project,
            args.output,
            lean_executable=args.lean_executable,
            update_image=args.update_image,
            timeout_seconds=args.timeout_seconds,
        )
        _print_json(payload)
        return 0 if payload.get("execution_status") == "success" else 2
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        _print_json({
            "schema_version": SCHEMA_VERSION,
            "engine": ENGINE_NAME,
            "engine_role": ENGINE_ROLE,
            "decision_authority": "none",
            "execution_status": "invalid_input",
            "error": str(exc),
        })
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
