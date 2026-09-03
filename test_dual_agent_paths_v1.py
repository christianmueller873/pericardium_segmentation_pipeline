from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dual_agent_paths_v1 import resolve_asset_path


class ResolveAssetPathTests(unittest.TestCase):
    def test_relative_default_is_resolved_from_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = resolve_asset_path(
                "models/agent.pt", "MODEL_PATH", root, environ={}
            )
            self.assertEqual(actual, (root / "models" / "agent.pt").resolve())

    def test_environment_variable_overrides_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = resolve_asset_path(
                "models/default.pt",
                "MODEL_PATH",
                root,
                environ={"MODEL_PATH": "external/override.pt"},
            )
            self.assertEqual(actual, (root / "external" / "override.pt").resolve())

    def test_absolute_path_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            absolute = root / "models" / "agent.pt"
            actual = resolve_asset_path(
                str(absolute), "MODEL_PATH", root / "other", environ={}
            )
            self.assertEqual(actual, absolute.resolve())

    def test_empty_environment_override_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "MODEL_PATH is set but empty"):
                resolve_asset_path(
                    "models/agent.pt",
                    "MODEL_PATH",
                    Path(directory),
                    environ={"MODEL_PATH": "   "},
                )


if __name__ == "__main__":
    unittest.main()
