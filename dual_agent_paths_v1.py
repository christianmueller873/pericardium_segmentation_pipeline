"""Portable path resolution for the dual-agent runtime."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path


def resolve_asset_path(
    configured_path: str,
    env_var: str,
    repository_root: Path,
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Resolve an environment override or a repository-relative default path."""
    environment = os.environ if environ is None else environ
    if env_var in environment:
        raw_path = environment[env_var].strip()
        if not raw_path:
            raise ValueError(f"{env_var} is set but empty")
    else:
        raw_path = str(configured_path).strip()
        if not raw_path:
            raise ValueError(f"No path configured for {env_var}")

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = repository_root / path
    return path.resolve(strict=False)
