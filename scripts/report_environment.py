from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
from pathlib import Path


DISTRIBUTIONS = (
    "fastapi",
    "monai",
    "nibabel",
    "nnunetv2",
    "numpy",
    "python-multipart",
    "scipy",
    "torch",
    "uvicorn",
)


def build_report() -> dict[str, object]:
    packages: dict[str, str | None] = {}
    for name in DISTRIBUTIONS:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "packages": packages,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(build_report(), indent=2) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
