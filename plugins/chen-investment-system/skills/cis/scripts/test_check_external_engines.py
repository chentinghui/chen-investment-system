from __future__ import annotations

import unittest

from check_external_engines import check_external_engines


class ExternalEngineReadinessTests(unittest.TestCase):
    def by_id(self, result: dict) -> dict[str, dict]:
        return {item["engine"]: item for item in result["engines"]}

    def test_detects_python_engines_without_importing_them(self) -> None:
        detected_modules = {"openbb", "qlib", "rdagent"}
        result = check_external_engines(
            module_probe=lambda name: name in detected_modules,
            command_probe=lambda name: False,
        )
        engines = self.by_id(result)
        self.assertTrue(engines["openbb"]["executable_now"])
        self.assertTrue(engines["qlib"]["executable_now"])
        self.assertTrue(engines["rd_agent"]["executable_now"])
        self.assertFalse(engines["finrobot"]["executable_now"])
        self.assertEqual(engines["finrobot"]["status"], "not_detected")

    def test_lean_requires_cli_and_docker(self) -> None:
        result = check_external_engines(
            module_probe=lambda name: False,
            command_probe=lambda name: name == "lean",
        )
        lean = self.by_id(result)["lean"]
        self.assertEqual(lean["status"], "partial")
        self.assertFalse(lean["executable_now"])

        result = check_external_engines(
            module_probe=lambda name: False,
            command_probe=lambda name: name in {"lean", "docker"},
        )
        lean = self.by_id(result)["lean"]
        self.assertEqual(lean["status"], "detected")
        self.assertTrue(lean["executable_now"])

    def test_anthropic_skill_is_never_claimed_from_local_detection(self) -> None:
        result = check_external_engines(
            module_probe=lambda name: True,
            command_probe=lambda name: True,
        )
        anthropic = self.by_id(result)["anthropic_financial_services"]
        self.assertEqual(anthropic["status"], "context_check_required")
        self.assertFalse(anthropic["executable_now"])

    def test_readiness_is_informational_not_decision_authority(self) -> None:
        result = check_external_engines(
            module_probe=lambda name: False,
            command_probe=lambda name: False,
        )
        self.assertEqual(result["authority"]["runtime_detection"], "informational_only")
        self.assertEqual(result["authority"]["final_decision_authority"], "cis_control_layer")


if __name__ == "__main__":
    unittest.main()
