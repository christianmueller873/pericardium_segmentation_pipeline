from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from dual_agent_paths_v1 import resolve_asset_path


HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "dual_agent_config_v1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", type=Path)
    parser.add_argument("--skip-hashes", action="store_true")
    args = parser.parse_args()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    agent1_model = resolve_asset_path(
        config["agent1"]["model_folder"], "AGENT1_MODEL_DIR", HERE
    )
    agent1_checkpoint = agent1_model / "fold_0" / config["agent1"]["checkpoint_name"]
    agent2_checkpoint = resolve_asset_path(
        config["agent2"]["checkpoint"], "AGENT2_CHECKPOINT", HERE
    )
    dataset_json = agent1_model / "dataset.json"

    report = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "config": str(CONFIG_PATH),
        "checks": {},
    }
    checks = report["checks"]
    required_modules = (
        "fastapi", "nibabel", "numpy", "scipy", "torch", "monai", "nnunetv2", "multipart", "uvicorn"
    )
    checks["dependencies"] = {
        module: importlib.util.find_spec(module) is not None for module in required_modules
    }
    checks["files"] = {
        "agent1_checkpoint": agent1_checkpoint.is_file(),
        "agent1_dataset_json": dataset_json.is_file(),
        "agent2_checkpoint": agent2_checkpoint.is_file(),
        "fusion_module": (HERE / "dual_agent_fusion_v1.py").is_file(),
        "server_module": (HERE / "server_dual_agent_v1.py").is_file(),
    }
    if dataset_json.is_file():
        labels = json.loads(dataset_json.read_text(encoding="utf-8"))["labels"]
        checks["agent1_label7_is_pericardium"] = labels.get("pericardium") == 7
    else:
        checks["agent1_label7_is_pericardium"] = False

    if not args.skip_hashes and agent1_checkpoint.is_file() and agent2_checkpoint.is_file():
        actual1, actual2 = sha256(agent1_checkpoint), sha256(agent2_checkpoint)
        checks["checkpoint_hashes"] = {
            "agent1_expected": config["agent1"]["checkpoint_sha256"],
            "agent1_actual": actual1,
            "agent1_match": actual1.lower() == config["agent1"]["checkpoint_sha256"].lower(),
            "agent2_expected": config["agent2"]["checkpoint_sha256"],
            "agent2_actual": actual2,
            "agent2_match": actual2.lower() == config["agent2"]["checkpoint_sha256"].lower(),
        }

    boolean_checks = list(checks["dependencies"].values()) + list(checks["files"].values())
    boolean_checks.append(bool(checks["agent1_label7_is_pericardium"]))
    if "checkpoint_hashes" in checks:
        boolean_checks.extend((
            checks["checkpoint_hashes"]["agent1_match"],
            checks["checkpoint_hashes"]["agent2_match"],
        ))
    report["status"] = "PASS" if all(boolean_checks) else "FAIL"
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
