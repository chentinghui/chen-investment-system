from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from check_tradingagents_upstream import apply_check, should_check
from run_tradingagents_remote import NVIDIA_BASE_URL, validate_request


class TradingAgentsTTLTests(unittest.TestCase):
    def test_ttl_skips_before_seven_days(self) -> None:
        now = datetime(2026, 8, 9, tzinfo=timezone.utc)
        status = {"last_checked_at": (now - timedelta(days=6)).isoformat(), "check_ttl_days": 7}
        self.assertFalse(should_check(status, now))

    def test_ttl_checks_at_seven_days(self) -> None:
        now = datetime(2026, 8, 9, tzinfo=timezone.utc)
        status = {"last_checked_at": (now - timedelta(days=7)).isoformat(), "check_ttl_days": 7}
        self.assertTrue(should_check(status, now))

    def test_new_sha_marks_review_required(self) -> None:
        now = datetime(2026, 8, 9, tzinfo=timezone.utc)
        status = {"reviewed_sha": "old", "review_status": "reviewed", "check_ttl_days": 7}
        result = apply_check(status, "new", now)
        self.assertEqual(result["review_status"], "review_required")
        self.assertEqual(result["upstream_check"], "change_detected")


class TradingAgentsAdapterTests(unittest.TestCase):
    def test_manual_request_contract_normalizes_ticker(self) -> None:
        result = validate_request({
            "request_id": "x1",
            "ticker": "mu",
            "analysis_date": "2026-08-09",
            "backend": "ollama",
            "provider_profile": "local_ollama",
            "selected_analysts": ["market"],
            "max_debate_rounds": 0,
            "max_risk_rounds": 0,
        })
        self.assertEqual(result["ticker"], "MU")
        self.assertEqual(result["backend"], "ollama")
        self.assertEqual(result["provider_profile"], "local_ollama")
        self.assertIsNone(result["credential_env"])

    def test_openai_compatible_requires_model(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires deep_model"):
            validate_request({
                "request_id": "x2",
                "ticker": "MU",
                "analysis_date": "2026-08-09",
                "backend": "openai_compatible",
                "provider_profile": "custom",
                "backend_url": "https://example.com/v1",
                "selected_analysts": ["market"],
            })

    def test_nvidia_profile_is_pinned_to_nvidia_endpoint_and_key(self) -> None:
        result = validate_request({
            "request_id": "x3",
            "ticker": "MU",
            "analysis_date": "2026-08-09",
            "backend": "openai_compatible",
            "provider_profile": "nvidia",
            "backend_url": NVIDIA_BASE_URL,
            "deep_model": "nvidia/model",
            "selected_analysts": ["market"],
        })
        self.assertEqual(result["backend_url"], NVIDIA_BASE_URL)
        self.assertEqual(result["credential_env"], "NVIDIA_API_KEY")

    def test_nvidia_key_cannot_be_routed_to_arbitrary_endpoint(self) -> None:
        with self.assertRaisesRegex(ValueError, "nvidia provider_profile requires"):
            validate_request({
                "request_id": "x4",
                "ticker": "MU",
                "analysis_date": "2026-08-09",
                "backend": "openai_compatible",
                "provider_profile": "nvidia",
                "backend_url": "https://attacker.example/v1",
                "deep_model": "nvidia/model",
                "selected_analysts": ["market"],
            })

    def test_custom_endpoint_uses_only_generic_compatible_key(self) -> None:
        result = validate_request({
            "request_id": "x5",
            "ticker": "MU",
            "analysis_date": "2026-08-09",
            "backend": "openai_compatible",
            "provider_profile": "custom",
            "backend_url": "https://models.example.com/v1",
            "deep_model": "custom-model",
            "selected_analysts": ["market"],
        })
        self.assertEqual(result["credential_env"], "OPENAI_COMPATIBLE_API_KEY")

    def test_unknown_request_fields_are_rejected_to_avoid_secret_echo(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown or forbidden request fields"):
            validate_request({
                "request_id": "x6",
                "ticker": "MU",
                "analysis_date": "2026-08-09",
                "backend": "ollama",
                "selected_analysts": ["market"],
                "api_key": "must-not-be-accepted",
            })


if __name__ == "__main__":
    unittest.main()
