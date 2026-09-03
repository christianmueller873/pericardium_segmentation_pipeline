from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    ".gitignore",
    "CITATION.cff",
    "LICENSE",
    "PUBLICATION_MANIFEST.md",
    "README.md",
    "ct_viewer.html",
    "dual_agent_config_v1.json",
    "dual_agent_fusion_v1.py",
    "dual_agent_paths_v1.py",
    "poetry.lock",
    "preflight_dual_agent_v1.py",
    "pyproject.toml",
    "requirements-ci.txt",
    "requirements_dual_agent_v1.txt",
    "server_dual_agent_v1.py",
    "test_ct_viewer_smoothing.js",
    "test_dual_agent_config_v1.py",
    "test_dual_agent_fusion_v1.py",
    "test_dual_agent_paths_v1.py",
    "test_static_demo.js",
}
PUBLIC_DIRECTORIES = (".github", "demo", "docs", "models", "results", "scripts")
PROHIBITED_SUFFIXES = (
    ".nii", ".nii.gz", ".dcm", ".bmp", ".npy", ".npz", ".pkl", ".b2nd",
    ".pt", ".pth", ".ckpt", ".zip",
)
TEXT_SUFFIXES = {
    "", ".cff", ".csv", ".html", ".js", ".json", ".lock", ".md", ".ps1",
    ".py", ".toml", ".txt", ".yml", ".yaml",
}
REQUIRED_IGNORE_RULES = (
    "/data/", "/gold_standard_20/", "/nnUNet_training/",
    "/agent2_finetune_runs/", "/safe to remove/", "/uncertain/", ".Rhistory",
)
CONTENT_RULES = {
    "personal Windows user path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.I),
    "internal patient alias": re.compile(
        r"\b(?:" + "|".join(("V" + "Mar", "D" + "Sil")) + r")\b"
    ),
    "likely embedded credential": re.compile(
        r"(?:api[_-]?key|access[_-]?token|secret[_-]?key|password)\s*[:=]\s*['\"][^'\"]+",
        re.I,
    ),
}
APPROVED_BINARY_FILES = {
    "demo/assets/full_pipeline_demo.mp4":
        "9ac53ddbfecc1b59fb3fbad543e736cf7fb03d69a198c776c79791ca0b0b60d6",
}


def public_files() -> list[Path]:
    files = [ROOT / name for name in sorted(ROOT_FILES)]
    for directory in PUBLIC_DIRECTORIES:
        base = ROOT / directory
        if base.is_dir():
            files.extend(path for path in base.rglob("*") if path.is_file())
    return sorted(set(files))


def audit() -> dict[str, object]:
    errors: list[str] = []
    files = public_files()
    for required in sorted(ROOT_FILES):
        if not (ROOT / required).is_file():
            errors.append(f"missing required public file: {required}")

    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        lower = relative.lower()
        if any(lower.endswith(suffix) for suffix in PROHIBITED_SUFFIXES):
            errors.append(f"prohibited medical/model/archive extension: {relative}")
        if path.stat().st_size > 10 * 1024 * 1024:
            errors.append(f"public file exceeds 10 MiB audit limit: {relative}")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            expected_hash = APPROVED_BINARY_FILES.get(relative)
            if expected_hash is None:
                errors.append(f"unapproved public binary file: {relative}")
            else:
                actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                if actual_hash != expected_hash:
                    errors.append(f"approved binary hash mismatch: {relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"expected UTF-8 text file is not decodable: {relative}")
            continue
        for label, pattern in CONTENT_RULES.items():
            if pattern.search(text):
                errors.append(f"{label}: {relative}")

    ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for rule in REQUIRED_IGNORE_RULES:
        if rule not in ignore_text:
            errors.append(f"missing required ignore rule: {rule}")

    for relative in APPROVED_BINARY_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing approved public binary: {relative}")

    relative_files = [path.relative_to(ROOT).as_posix() for path in files]
    return {
        "status": "PASS" if not errors else "FAIL",
        "public_file_count": len(relative_files),
        "public_files": relative_files,
        "errors": errors,
    }


def main() -> int:
    report = audit()
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
