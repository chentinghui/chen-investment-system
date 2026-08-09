from __future__ import annotations

import importlib.util
import json
import shutil
from dataclasses import asdict, dataclass
from typing import Callable

SCHEMA_VERSION = "cis.external-readiness.v1"


@dataclass(frozen=True)
class EngineReadiness:
    engine: str
    runtime_kind: str
    status: str
    detected_by: list[str]
    executable_now: bool
    notes: str


def _module_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _python_engine(
    engine: str,
    module_names: tuple[str, ...],
    *,
    notes: str,
    module_probe: Callable[[str], bool] = _module_exists,
) -> EngineReadiness:
    detected = [name for name in module_names if module_probe(name)]
    ready = bool(detected)
    return EngineReadiness(
        engine=engine,
        runtime_kind="python_package",
        status="detected" if ready else "not_detected",
        detected_by=[f"python:{name}" for name in detected],
        executable_now=ready,
        notes=notes,
    )


def check_external_engines(
    *,
    module_probe: Callable[[str], bool] = _module_exists,
    command_probe: Callable[[str], bool] = _command_exists,
) -> dict:
    engines: list[EngineReadiness] = []

    engines.append(
        _python_engine(
            "openbb",
            ("openbb",),
            notes="Detection only. Provider credentials/data entitlements are checked separately at execution time.",
            module_probe=module_probe,
        )
    )
    engines.append(
        _python_engine(
            "tradingagents",
            ("tradingagents",),
            notes="Original Python runtime detection only; CIS may still use its reviewed ChatGPT-native TradingAgents methodology when this package is absent.",
            module_probe=module_probe,
        )
    )
    engines.append(
        _python_engine(
            "finrobot",
            ("finrobot",),
            notes="Detection only. A real FinRobot task still requires the requested pipeline, data providers and model credentials to be usable.",
            module_probe=module_probe,
        )
    )
    engines.append(
        _python_engine(
            "qlib",
            ("qlib",),
            notes="Detection only. Qlib data initialization and point-in-time dataset readiness must be validated for each run.",
            module_probe=module_probe,
        )
    )
    engines.append(
        _python_engine(
            "rd_agent",
            ("rdagent",),
            notes="Detection only. RD-Agent scenarios may additionally require Docker, an LLM backend and scenario-specific configuration.",
            module_probe=module_probe,
        )
    )

    lean_cli = command_probe("lean")
    docker_cli = command_probe("docker")
    lean_detected_by = []
    if lean_cli:
        lean_detected_by.append("command:lean")
    if docker_cli:
        lean_detected_by.append("command:docker")
    lean_ready = lean_cli and docker_cli
    engines.append(
        EngineReadiness(
            engine="lean",
            runtime_kind="cli_plus_docker",
            status="detected" if lean_ready else ("partial" if lean_cli or docker_cli else "not_detected"),
            detected_by=lean_detected_by,
            executable_now=lean_ready,
            notes="CLI/Docker detection is only base runtime readiness. QuantConnect organization, project, data and credentials remain separate gates.",
        )
    )

    engines.append(
        EngineReadiness(
            engine="anthropic_financial_services",
            runtime_kind="context_managed_skill",
            status="context_check_required",
            detected_by=[],
            executable_now=False,
            notes="This capability is not a local Python package contract. The active environment must confirm the relevant skill is actually accessible before claiming use.",
        )
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "purpose": "non-invasive runtime detection; not proof of task execution or research quality",
        "engines": [asdict(item) for item in engines],
        "authority": {
            "runtime_detection": "informational_only",
            "final_decision_authority": "cis_control_layer",
        },
    }


def main() -> int:
    print(json.dumps(check_external_engines(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
