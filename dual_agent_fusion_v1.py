"""Conservative fusion for coarse and precise pericardial-sac predictions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from scipy import ndimage


@dataclass(frozen=True)
class FusionConfig:
    """Validated thresholds and safety policies for automatic fusion."""

    agent2_threshold: float = 0.50
    partial_recovery_probability: float = 0.20
    complete_recovery_probability: float = 0.12
    end_band_mm: float = 15.0
    max_axial_extension_mm: float = 9.0
    spatial_bridge_mm: float = 8.0
    hard_fallback_bridge_mm: float = 5.0
    max_restored_area_fraction_of_anchor: float = 1.05
    min_agent1_component_mm2: float = 20.0
    min_agent2_component_mm2: float = 10.0
    min_agent1_agent2_dice: float = 0.10
    min_agent1_overlap_fraction: float = 0.30
    min_agent1_volume_ratio_to_agent2: float = 0.15
    max_agent1_volume_ratio_to_agent2: float = 6.0
    min_shared_nonempty_slices: int = 3
    min_agent2_largest_component_fraction: float = 0.90
    min_agent1_largest_component_fraction_for_fallback: float = 0.85
    fallback_to_agent1_on_fragmented_agent2: bool = True
    enforce_single_connected_output: bool = True
    allow_hard_agent1_end_fallback: bool = True
    allow_unverified_total_agent1_fallback: bool = False
    allow_internal_gap_recovery: bool = False
    restrict_agent2_to_agent1_envelope: bool = False
    agent1_envelope_mm: float = 10.0

    def validate(self) -> None:
        for name in (
            "agent2_threshold",
            "partial_recovery_probability",
            "complete_recovery_probability",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value}")
        if self.complete_recovery_probability > self.partial_recovery_probability:
            raise ValueError("complete recovery threshold must not exceed partial threshold")
        for name in (
            "end_band_mm",
            "max_axial_extension_mm",
            "spatial_bridge_mm",
            "hard_fallback_bridge_mm",
            "min_agent1_component_mm2",
            "min_agent2_component_mm2",
            "agent1_envelope_mm",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.max_restored_area_fraction_of_anchor <= 0:
            raise ValueError("max_restored_area_fraction_of_anchor must be positive")
        for name in (
            "min_agent1_agent2_dice",
            "min_agent1_overlap_fraction",
            "min_agent2_largest_component_fraction",
            "min_agent1_largest_component_fraction_for_fallback",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value}")
        if self.min_agent1_volume_ratio_to_agent2 < 0:
            raise ValueError("min_agent1_volume_ratio_to_agent2 must be non-negative")
        if self.max_agent1_volume_ratio_to_agent2 < self.min_agent1_volume_ratio_to_agent2:
            raise ValueError("maximum Agent 1 volume ratio must be at least the minimum")
        if self.min_shared_nonempty_slices < 1:
            raise ValueError("min_shared_nonempty_slices must be at least 1")


def _disk(radius_pixels: int) -> np.ndarray:
    radius_pixels = max(int(radius_pixels), 0)
    yy, xx = np.ogrid[-radius_pixels : radius_pixels + 1, -radius_pixels : radius_pixels + 1]
    return (xx * xx + yy * yy) <= radius_pixels * radius_pixels


def _largest_component(mask: np.ndarray, min_pixels: int = 1) -> np.ndarray:
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return np.zeros_like(mask)
    labels, count = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    if count == 0:
        return np.zeros_like(mask)
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    selected = int(np.argmax(sizes))
    if sizes[selected] < min_pixels:
        return np.zeros_like(mask)
    return labels == selected


def _clean_slices(mask: np.ndarray, min_pixels: int) -> np.ndarray:
    clean = np.zeros_like(mask, dtype=bool)
    for z in range(mask.shape[2]):
        component = _largest_component(mask[:, :, z], min_pixels=min_pixels)
        if component.any():
            component = ndimage.binary_fill_holes(component)
        clean[:, :, z] = component
    return clean


def _component_quality_3d(mask: np.ndarray) -> tuple[np.ndarray, int, int, float]:
    """Return the largest component and summary connectedness statistics."""

    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return np.zeros_like(mask), 0, 0, 0.0
    labels, count = ndimage.label(mask, structure=np.ones((3, 3, 3), dtype=np.uint8))
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    selected = int(np.argmax(sizes))
    largest = int(sizes[selected])
    total = int(mask.sum())
    return labels == selected, int(count), largest, largest / max(total, 1)


def _filled_largest_component_3d(mask: np.ndarray) -> np.ndarray:
    """Keep one 3D component and fill its holes independently by axial slice."""

    component, _, _, _ = _component_quality_3d(mask)
    for z in np.flatnonzero(component.any(axis=(0, 1))):
        component[:, :, z] = ndimage.binary_fill_holes(component[:, :, z])
    return component


def _keep_component_touching_seed(mask: np.ndarray, seed: np.ndarray) -> np.ndarray:
    """Keep only candidate components that touch the supplied seed mask."""

    mask = np.asarray(mask, dtype=bool)
    seed = np.asarray(seed, dtype=bool)
    if not mask.any() or not seed.any():
        return np.zeros_like(mask)
    labels, count = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    touching = np.unique(labels[seed & mask])
    touching = touching[touching != 0]
    if not len(touching):
        return np.zeros_like(mask)
    return np.isin(labels, touching)


def _cap_added_area(
    base: np.ndarray,
    proposed: np.ndarray,
    probability: np.ndarray,
    maximum_total_area: int,
) -> np.ndarray:
    """Cap proposed foreground additions while favoring higher probability."""

    base = np.asarray(base, dtype=bool)
    proposed = np.asarray(proposed, dtype=bool)
    maximum_total_area = max(int(maximum_total_area), int(base.sum()))
    allowance = maximum_total_area - int(base.sum())
    additions = proposed & ~base
    if additions.sum() <= allowance:
        return base | additions
    if allowance <= 0:
        return base.copy()
    coords = np.flatnonzero(additions)
    scores = np.asarray(probability, dtype=np.float32).ravel()[coords]
    selected = coords[np.argpartition(scores, -allowance)[-allowance:]]
    result = base.copy().ravel()
    result[selected] = True
    return result.reshape(base.shape)


def _nearest_nonempty_index(nonempty: np.ndarray, z: int) -> int | None:
    indices = np.flatnonzero(nonempty)
    if not len(indices):
        return None
    return int(indices[np.argmin(np.abs(indices - z))])


def _slice_spacing(spacing_xyz: tuple[float, float, float]) -> tuple[float, float, float]:
    if len(spacing_xyz) != 3 or any(float(value) <= 0 for value in spacing_xyz):
        raise ValueError(f"spacing_xyz must contain three positive values, got {spacing_xyz}")
    return tuple(float(value) for value in spacing_xyz)


def fuse_pericardium(
    agent1_mask_xyz: np.ndarray,
    agent2_probability_xyz: np.ndarray,
    spacing_xyz: tuple[float, float, float],
    config: FusionConfig | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Fuse Agent 1 and Agent 2 without weakening a coherent precise mask."""

    cfg = config or FusionConfig()
    cfg.validate()
    spacing_x, spacing_y, spacing_z = _slice_spacing(spacing_xyz)
    agent1 = np.asarray(agent1_mask_xyz, dtype=bool)
    probability = np.asarray(agent2_probability_xyz, dtype=np.float32)
    if agent1.ndim != 3 or probability.ndim != 3:
        raise ValueError("Agent 1 mask and Agent 2 probability must both be 3D")
    if agent1.shape != probability.shape:
        raise ValueError(f"grid mismatch: Agent 1 {agent1.shape}, Agent 2 {probability.shape}")
    if not np.isfinite(probability).all():
        raise ValueError("Agent 2 probability contains NaN or infinity")
    probability = np.clip(probability, 0.0, 1.0)

    pixel_area = spacing_x * spacing_y
    min_agent1_pixels = max(1, int(np.ceil(cfg.min_agent1_component_mm2 / pixel_area)))
    min_agent2_pixels = max(1, int(np.ceil(cfg.min_agent2_component_mm2 / pixel_area)))
    coarse = _clean_slices(agent1, min_agent1_pixels)


    precise = probability >= cfg.agent2_threshold
    precise_anchors = _clean_slices(precise, min_agent2_pixels)
    fused = precise.copy()
    agent1_nonempty = coarse.any(axis=(0, 1))
    agent2_nonempty = precise_anchors.any(axis=(0, 1))
    raw_agent2_nonempty = precise.any(axis=(0, 1))

    intersection = int((coarse & precise).sum())
    agent1_voxels = int(coarse.sum())
    agent2_voxels = int(precise.sum())
    agreement_dice = 2.0 * intersection / max(agent1_voxels + agent2_voxels, 1)
    agent1_overlap_fraction = intersection / max(agent1_voxels, 1)
    volume_ratio = agent1_voxels / max(agent2_voxels, 1)
    shared_slices = int(np.logical_and(agent1_nonempty, raw_agent2_nonempty).sum())
    agent2_largest, agent2_component_count, agent2_largest_voxels, agent2_largest_fraction = (
        _component_quality_3d(precise)
    )
    agent1_largest, agent1_component_count, agent1_largest_voxels, agent1_largest_fraction = (
        _component_quality_3d(coarse)
    )
    agreement_reasons: list[str] = []
    if agent1_voxels == 0:
        agreement_reasons.append("agent1_empty")
    if agreement_dice < cfg.min_agent1_agent2_dice:
        agreement_reasons.append("low_agent1_agent2_dice")
    if agent1_overlap_fraction < cfg.min_agent1_overlap_fraction:
        agreement_reasons.append("low_agent1_overlap_fraction")
    if volume_ratio < cfg.min_agent1_volume_ratio_to_agent2:
        agreement_reasons.append("agent1_too_small_relative_to_agent2")
    if volume_ratio > cfg.max_agent1_volume_ratio_to_agent2:
        agreement_reasons.append("agent1_too_large_relative_to_agent2")
    if shared_slices < cfg.min_shared_nonempty_slices:
        agreement_reasons.append("too_few_shared_nonempty_slices")

    diagnostics: dict[str, Any] = {
        "policy": "agent2-primary_conservative-agent1-range-end-recovery",
        "config": asdict(cfg),
        "spacing_xyz_mm": list(spacing_xyz),
        "shape_xyz": list(agent1.shape),
        "agent1_nonempty_slices": np.flatnonzero(agent1_nonempty).astype(int).tolist(),
        "agent2_nonempty_slices": np.flatnonzero(raw_agent2_nonempty).astype(int).tolist(),
        "agent1_agreement_gate": {
            "accepted": not agreement_reasons,
            "reasons": agreement_reasons,
            "agent1_cleaned_voxels": agent1_voxels,
            "agent2_voxels": agent2_voxels,
            "intersection_voxels": intersection,
            "dice": agreement_dice,
            "agent1_overlap_fraction": agent1_overlap_fraction,
            "agent1_to_agent2_volume_ratio": volume_ratio,
            "shared_nonempty_slices": shared_slices,
        },
        "connectedness_gate": {
            "agent2_components_3d": agent2_component_count,
            "agent2_largest_component_voxels": agent2_largest_voxels,
            "agent2_largest_component_fraction": agent2_largest_fraction,
            "agent2_minimum_largest_component_fraction": cfg.min_agent2_largest_component_fraction,
            "agent1_components_3d": agent1_component_count,
            "agent1_largest_component_voxels": agent1_largest_voxels,
            "agent1_largest_component_fraction": agent1_largest_fraction,
            "agent1_minimum_largest_component_fraction_for_fallback": (
                cfg.min_agent1_largest_component_fraction_for_fallback
            ),
        },
        "recoveries": [],
        "fallback": None,
    }


    if not agent2_nonempty.any():
        if cfg.allow_unverified_total_agent1_fallback:
            fused = coarse.copy()
            diagnostics["fallback"] = "agent2_empty_unverified_agent1_used"
        else:
            fused = np.zeros_like(coarse)
            diagnostics["fallback"] = "agent2_empty_automatic_output_withheld"
        diagnostics["fused_nonempty_slices"] = np.flatnonzero(fused.any(axis=(0, 1))).astype(int).tolist()
        diagnostics["restored_voxels"] = int(fused.sum())
        return fused.astype(np.uint8), diagnostics


    if agent2_largest_fraction < cfg.min_agent2_largest_component_fraction:
        coherent_agent1 = (
            agent1_largest_voxels >= min_agent1_pixels
            and agent1_largest_fraction
            >= cfg.min_agent1_largest_component_fraction_for_fallback
        )
        if cfg.fallback_to_agent1_on_fragmented_agent2 and coherent_agent1:
            fused = _filled_largest_component_3d(agent1_largest)
            diagnostics["fallback"] = "agent2_fragmented_coherent_agent1_used"
            diagnostics["fused_nonempty_slices"] = (
                np.flatnonzero(fused.any(axis=(0, 1))).astype(int).tolist()
            )
            diagnostics["restored_voxels"] = int((fused & ~precise).sum())
            diagnostics["agent2_preserved_voxels"] = int((fused & precise).sum())
            diagnostics["agent2_removed_voxels"] = int((precise & ~fused).sum())
            return fused.astype(np.uint8), diagnostics
        diagnostics["fallback"] = "agent2_fragmented_no_coherent_automatic_fallback"
        fused = np.zeros_like(coarse)
        diagnostics["fused_nonempty_slices"] = []
        diagnostics["restored_voxels"] = 0
        diagnostics["agent2_preserved_voxels"] = 0
        diagnostics["agent2_removed_voxels"] = int(precise.sum())
        return fused.astype(np.uint8), diagnostics


    if agreement_reasons:
        diagnostics["fallback"] = "agent1_rejected_by_agreement_gate_agent2_preserved"
        diagnostics["restored_voxels"] = 0
        pre_connectivity_voxels = int(fused.sum())
        if cfg.enforce_single_connected_output:
            fused = _filled_largest_component_3d(fused)
        diagnostics["connectivity_cleanup_removed_voxels"] = (
            pre_connectivity_voxels - int(fused.sum())
        )
        diagnostics["fused_nonempty_slices"] = (
            np.flatnonzero(fused.any(axis=(0, 1))).astype(int).tolist()
        )
        diagnostics["agent2_preserved_voxels"] = int((fused & precise).sum())
        diagnostics["agent2_removed_voxels"] = int((precise & ~fused).sum())
        return fused.astype(np.uint8), diagnostics

    z2 = np.flatnonzero(agent2_nonempty)
    first2, last2 = int(z2[0]), int(z2[-1])
    end_band_slices = max(1, int(np.ceil(cfg.end_band_mm / spacing_z)))
    max_extension_slices = max(0, int(np.floor(cfg.max_axial_extension_mm / spacing_z)))
    bridge_pixels = max(1, int(np.ceil(cfg.spatial_bridge_mm / min(spacing_x, spacing_y))))
    hard_bridge_pixels = max(1, int(np.ceil(cfg.hard_fallback_bridge_mm / min(spacing_x, spacing_y))))
    bridge_structure = _disk(bridge_pixels)

    if cfg.restrict_agent2_to_agent1_envelope:
        envelope_pixels = max(1, int(np.ceil(cfg.agent1_envelope_mm / min(spacing_x, spacing_y))))
        envelope_structure = _disk(envelope_pixels)
        for z in range(agent1.shape[2]):
            if coarse[:, :, z].any() and fused[:, :, z].any():
                envelope = ndimage.binary_dilation(coarse[:, :, z], structure=envelope_structure)
                restricted = fused[:, :, z] & envelope
                if restricted.any():
                    fused[:, :, z] = _largest_component(restricted)


    for z in range(first2, last2 + 1):
        if z > first2 + end_band_slices and z < last2 - end_band_slices:
            continue
        base = fused[:, :, z]
        if not base.any() or not coarse[:, :, z].any():
            continue
        seed_envelope = ndimage.binary_dilation(base, structure=bridge_structure)
        supported = coarse[:, :, z] & (probability[:, :, z] >= cfg.partial_recovery_probability)
        proposed = base | (supported & seed_envelope)
        proposed = _keep_component_touching_seed(proposed, base)
        anchor_area = int(base.sum())
        capped = _cap_added_area(
            base,
            proposed,
            probability[:, :, z],
            int(np.ceil(anchor_area * cfg.max_restored_area_fraction_of_anchor)),
        )


        added_mask = capped & ~base
        added = int(added_mask.sum())
        if added:
            fused[:, :, z] = ndimage.binary_fill_holes(capped)
            diagnostics["recoveries"].append({
                "z": z,
                "mode": "partial_probability_supported",
                "added_voxels": added,
                "agent2_probability_max_added": float(probability[:, :, z][added_mask].max()),
            })


    candidates: list[tuple[int, int]] = []
    for distance in range(1, max_extension_slices + 1):
        candidates.extend(((first2 - distance, distance), (last2 + distance, distance)))
    if cfg.allow_internal_gap_recovery:
        for z in range(first2 + 1, last2):
            if not agent2_nonempty[z]:
                nearest = _nearest_nonempty_index(agent2_nonempty, z)
                if nearest is not None:
                    candidates.append((z, abs(z - nearest)))

    for z, distance in candidates:
        if z < 0 or z >= agent1.shape[2] or fused[:, :, z].any() or not coarse[:, :, z].any():
            continue
        anchor_z = _nearest_nonempty_index(fused.any(axis=(0, 1)), z)
        if anchor_z is None or abs(anchor_z - z) > max_extension_slices:
            continue

        start, stop = sorted((anchor_z, z))
        if not agent1_nonempty[start : stop + 1].all():
            continue
        anchor = fused[:, :, anchor_z]
        bridge = _disk(hard_bridge_pixels * max(1, distance))
        continuity_envelope = ndimage.binary_dilation(anchor, structure=bridge)
        supported = (
            coarse[:, :, z]
            & continuity_envelope
            & (probability[:, :, z] >= cfg.complete_recovery_probability)
        )
        mode = "complete_probability_supported"
        if not supported.any() and cfg.allow_hard_agent1_end_fallback and distance == 1:
            supported = coarse[:, :, z] & continuity_envelope
            mode = "complete_bounded_agent1_fallback"
        supported = _largest_component(supported, min_pixels=min_agent1_pixels)
        if not supported.any():
            continue
        cap = int(np.ceil(anchor.sum() * cfg.max_restored_area_fraction_of_anchor))
        restored = _cap_added_area(
            np.zeros_like(supported), supported, probability[:, :, z], cap
        )
        restored = _largest_component(restored, min_pixels=min_agent1_pixels)
        if restored.any():
            fused[:, :, z] = ndimage.binary_fill_holes(restored)
            diagnostics["recoveries"].append({
                "z": z,
                "mode": mode,
                "anchor_z": anchor_z,
                "axial_distance_slices": distance,
                "added_voxels": int(restored.sum()),
                "agent2_probability_max": float(probability[:, :, z][restored].max()),
            })

    pre_connectivity_voxels = int(fused.sum())
    if cfg.enforce_single_connected_output:
        fused = _filled_largest_component_3d(fused)
    diagnostics["connectivity_cleanup_removed_voxels"] = pre_connectivity_voxels - int(fused.sum())
    fused_nonempty = fused.any(axis=(0, 1))
    diagnostics["fused_nonempty_slices"] = np.flatnonzero(fused_nonempty).astype(int).tolist()
    diagnostics["restored_voxels"] = int((fused & ~precise).sum())
    diagnostics["agent2_preserved_voxels"] = int((fused & precise).sum())
    diagnostics["agent2_removed_voxels"] = int((precise & ~fused).sum())
    return fused.astype(np.uint8), diagnostics
