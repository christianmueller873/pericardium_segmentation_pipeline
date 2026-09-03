

from __future__ import annotations

import unittest

import numpy as np

from dual_agent_fusion_v1 import FusionConfig, fuse_pericardium


def circle(shape: tuple[int, int], center: tuple[int, int], radius: int) -> np.ndarray:
    xx, yy = np.ogrid[: shape[0], : shape[1]]
    return (xx - center[0]) ** 2 + (yy - center[1]) ** 2 <= radius**2


class DualAgentFusionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.shape = (64, 64, 10)
        self.agent1 = np.zeros(self.shape, dtype=np.uint8)
        self.probability = np.zeros(self.shape, dtype=np.float32)
        coarse = circle(self.shape[:2], (32, 32), 11)
        precise = circle(self.shape[:2], (32, 32), 9)
        for z in range(2, 8):
            self.agent1[:, :, z] = coarse
        for z in range(3, 7):
            self.probability[:, :, z][precise] = 0.8
        self.cfg = FusionConfig(
            end_band_mm=2.0,
            max_axial_extension_mm=2.0,
            spatial_bridge_mm=3.0,
            hard_fallback_bridge_mm=2.0,
            min_agent1_component_mm2=1.0,
            min_agent2_component_mm2=1.0,
        )

    def test_central_agent2_contour_is_unchanged(self) -> None:
        fused, diagnostics = fuse_pericardium(
            self.agent1, self.probability, (1.0, 1.0, 1.0), self.cfg
        )
        expected = self.probability[:, :, 5] >= self.cfg.agent2_threshold
        np.testing.assert_array_equal(fused[:, :, 5] > 0, expected)
        self.assertEqual(diagnostics["agent2_removed_voxels"], 0)

    def test_partial_end_recovery_requires_agent2_probability(self) -> None:
        support_ring = circle(self.shape[:2], (32, 32), 10)
        self.probability[:, :, 3][support_ring] = np.maximum(
            self.probability[:, :, 3][support_ring], 0.30
        )

        air = circle(self.shape[:2], (8, 8), 4)
        self.agent1[:, :, 3] |= air
        fused, diagnostics = fuse_pericardium(
            self.agent1, self.probability, (1.0, 1.0, 1.0), self.cfg
        )
        original = self.probability[:, :, 3] >= self.cfg.agent2_threshold
        self.assertGreater(int((fused[:, :, 3] & ~original).sum()), 0)
        self.assertFalse(fused[:, :, 3][air].any())
        self.assertTrue(any(row["mode"] == "partial_probability_supported" for row in diagnostics["recoveries"]))

    def test_complete_adjacent_end_miss_is_restored(self) -> None:
        support = circle(self.shape[:2], (32, 32), 8)
        self.probability[:, :, 2][support] = 0.18
        fused, diagnostics = fuse_pericardium(
            self.agent1, self.probability, (1.0, 1.0, 1.0), self.cfg
        )
        self.assertTrue(fused[:, :, 2].any())
        rows = [row for row in diagnostics["recoveries"] if row["z"] == 2]
        self.assertEqual(rows[0]["mode"], "complete_probability_supported")

    def test_hard_fallback_is_bounded_to_adjacent_end(self) -> None:
        fused, diagnostics = fuse_pericardium(
            self.agent1, self.probability, (1.0, 1.0, 1.0), self.cfg
        )
        self.assertTrue(fused[:, :, 2].any())
        self.assertTrue(fused[:, :, 7].any())
        fallback_rows = [
            row for row in diagnostics["recoveries"]
            if row["mode"] == "complete_bounded_agent1_fallback"
        ]
        self.assertEqual({row["z"] for row in fallback_rows}, {2, 7})

    def test_disconnected_internal_gap_uses_coherent_agent1_fallback(self) -> None:
        self.probability[:, :, 5] = 0.0
        fused, diagnostics = fuse_pericardium(
            self.agent1, self.probability, (1.0, 1.0, 1.0), self.cfg
        )
        self.assertTrue(fused[:, :, 5].any())
        self.assertEqual(
            diagnostics["fallback"],
            "agent2_fragmented_coherent_agent1_used",
        )

    def test_automatic_output_is_withheld_if_agent2_is_entirely_empty(self) -> None:
        fused, diagnostics = fuse_pericardium(
            self.agent1,
            np.zeros_like(self.probability),
            (1.0, 1.0, 1.0),
            self.cfg,
        )
        self.assertFalse(fused.any())
        self.assertEqual(diagnostics["fallback"], "agent2_empty_automatic_output_withheld")

    def test_unverified_total_agent1_fallback_requires_explicit_opt_in(self) -> None:
        cfg = FusionConfig(
            min_agent1_component_mm2=1.0,
            min_agent2_component_mm2=1.0,
            allow_unverified_total_agent1_fallback=True,
        )
        fused, diagnostics = fuse_pericardium(
            self.agent1, np.zeros_like(self.probability), (1.0, 1.0, 1.0), cfg
        )
        self.assertTrue(fused.any())
        self.assertEqual(diagnostics["fallback"], "agent2_empty_unverified_agent1_used")

    def test_incompatible_agent1_is_gated_off_without_changing_agent2(self) -> None:
        bad_agent1 = np.zeros_like(self.agent1)
        bad_agent1[2:5, 2:5, 4:6] = 1
        fused, diagnostics = fuse_pericardium(
            bad_agent1, self.probability, (1.0, 1.0, 1.0), self.cfg
        )
        expected = self.probability >= self.cfg.agent2_threshold
        np.testing.assert_array_equal(fused > 0, expected)
        self.assertFalse(diagnostics["agent1_agreement_gate"]["accepted"])
        self.assertEqual(
            diagnostics["fallback"],
            "agent1_rejected_by_agreement_gate_agent2_preserved",
        )

    def test_fragmented_agent2_falls_back_to_coherent_agent1(self) -> None:
        fragmented = self.probability.copy()

        fragmented[2:6, 2:6, 0] = 0.99
        fragmented[8:12, 50:54, 1] = 0.99
        fragmented[50:54, 8:12, 8] = 0.99
        fragmented[55:59, 55:59, 9] = 0.99
        cfg = FusionConfig(
            min_agent1_component_mm2=1.0,
            min_agent2_component_mm2=1.0,
            min_agent2_largest_component_fraction=0.99,
            min_agent1_largest_component_fraction_for_fallback=0.85,
        )
        fused, diagnostics = fuse_pericardium(
            self.agent1, fragmented, (1.0, 1.0, 1.0), cfg
        )
        self.assertEqual(
            diagnostics["fallback"],
            "agent2_fragmented_coherent_agent1_used",
        )
        labels, count = __import__("scipy").ndimage.label(
            fused, structure=np.ones((3, 3, 3), dtype=np.uint8)
        )
        self.assertEqual(count, 1)
        self.assertTrue(fused[:, :, 2:8].any())
        self.assertFalse(fused[:, :, 0].any())

    def test_fragmented_agent2_without_coherent_guide_is_withheld(self) -> None:
        bad_agent1 = np.zeros_like(self.agent1)
        bad_agent1[2:5, 2:5, 1] = 1
        bad_agent1[50:53, 50:53, 8] = 1
        fragmented = np.zeros_like(self.probability)
        fragmented[5:9, 5:9, 1] = 0.99
        fragmented[25:29, 25:29, 4] = 0.99
        fragmented[50:54, 50:54, 8] = 0.99
        cfg = FusionConfig(
            min_agent1_component_mm2=1.0,
            min_agent2_component_mm2=1.0,
            min_agent2_largest_component_fraction=0.90,
            min_agent1_largest_component_fraction_for_fallback=0.85,
        )
        fused, diagnostics = fuse_pericardium(
            bad_agent1, fragmented, (1.0, 1.0, 1.0), cfg
        )
        self.assertFalse(fused.any())
        self.assertEqual(
            diagnostics["fallback"],
            "agent2_fragmented_no_coherent_automatic_fallback",
        )

    def test_grid_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "grid mismatch"):
            fuse_pericardium(
                self.agent1,
                np.zeros((32, 32, 10), dtype=np.float32),
                (1.0, 1.0, 1.0),
                self.cfg,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
