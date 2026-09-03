from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "dual_agent_config_v1.json"


class DualAgentConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    def test_schema_and_default_output(self) -> None:
        self.assertEqual(self.config["schema_version"], 1)
        self.assertEqual(self.config["default_output"], "fused")

    def test_model_defaults_are_repository_relative(self) -> None:
        for value in (
            self.config["agent1"]["model_folder"],
            self.config["agent2"]["checkpoint"],
        ):
            self.assertFalse(Path(value).is_absolute(), value)
            self.assertNotRegex(value, re.compile(r"[A-Za-z]:[\\/]"))

    def test_checkpoint_hashes_are_sha256(self) -> None:
        for agent in ("agent1", "agent2"):
            digest = self.config[agent]["checkpoint_sha256"]
            self.assertRegex(digest, re.compile(r"^[0-9a-f]{64}$"))

    def test_frontend_contract_exposes_all_outputs(self) -> None:
        contract = self.config["frontend_contract"]
        self.assertEqual(contract["automatic_default"], "fused")
        self.assertEqual(contract["available_outputs"], ["fused", "agent1", "agent2"])
        self.assertTrue(contract["allow_user_selection"])


if __name__ == "__main__":
    unittest.main()
