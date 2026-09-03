from __future__ import annotations

import gc
import hashlib
import json
import logging
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np
import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from monai.inferers import SlidingWindowInferer
from monai.networks.nets import UNet
from monai.transforms import (
    Compose,
    EnsureChannelFirstd,
    LoadImaged,
    Orientationd,
    ScaleIntensityRanged,
    Spacingd,
)
from nibabel.processing import resample_from_to

from dual_agent_fusion_v1 import FusionConfig, fuse_pericardium
from dual_agent_paths_v1 import resolve_asset_path


HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "dual_agent_config_v1.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
AGENT1_MODEL_FOLDER = resolve_asset_path(
    CONFIG["agent1"]["model_folder"], "AGENT1_MODEL_DIR", HERE
)
AGENT1_LABEL = int(CONFIG["agent1"]["pericardium_label"])
AGENT2_CHECKPOINT = resolve_asset_path(
    CONFIG["agent2"]["checkpoint"], "AGENT2_CHECKPOINT", HERE
)
AGENT2_SPACING = tuple(float(value) for value in CONFIG["agent2"]["spacing_mm"])
AGENT2_PATCH_SIZE = tuple(int(value) for value in CONFIG["agent2"]["patch_size"])
AGENT2_HU_MIN, AGENT2_HU_MAX = (float(value) for value in CONFIG["agent2"]["hu_window"])
FUSION_CONFIG = FusionConfig(**CONFIG["fusion"])

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("pericardium-dual-agent-server")

app = FastAPI(title="Pericardium Dual-Agent Segmentation API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_frozen_assets(check_hashes: bool = False) -> dict[str, Any]:
    agent1_checkpoint = (
        AGENT1_MODEL_FOLDER
        / "fold_0"
        / str(CONFIG["agent1"]["checkpoint_name"])
    )
    missing = [str(path) for path in (CONFIG_PATH, agent1_checkpoint, AGENT2_CHECKPOINT) if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing frozen dual-agent assets: {missing}")
    result: dict[str, Any] = {
        "agent1_checkpoint": str(agent1_checkpoint),
        "agent2_checkpoint": str(AGENT2_CHECKPOINT),
        "hashes_checked": check_hashes,
    }
    if check_hashes:
        actual1, actual2 = sha256(agent1_checkpoint), sha256(AGENT2_CHECKPOINT)
        expected1 = str(CONFIG["agent1"]["checkpoint_sha256"]).lower()
        expected2 = str(CONFIG["agent2"]["checkpoint_sha256"]).lower()
        if actual1.lower() != expected1 or actual2.lower() != expected2:
            raise RuntimeError(
                "Frozen checkpoint hash mismatch: "
                f"Agent1 expected={expected1} actual={actual1}; "
                f"Agent2 expected={expected2} actual={actual2}"
            )
        result.update({"agent1_sha256": actual1, "agent2_sha256": actual2})
    return result


def _release_cuda() -> None:
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def run_agent1(input_nii_path: Path, output_dir: Path) -> tuple[np.ndarray, nib.Nifti1Image]:
    from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    predictor = nnUNetPredictor(
        tile_step_size=0.5,
        use_gaussian=True,
        use_mirroring=True,
        perform_everything_on_device=torch.cuda.is_available(),
        device=device,
        verbose=False,
        verbose_preprocessing=False,
        allow_tqdm=True,
    )
    predictor.initialize_from_trained_model_folder(
        str(AGENT1_MODEL_FOLDER),
        use_folds=tuple(int(value) for value in CONFIG["agent1"]["folds"]),
        checkpoint_name=str(CONFIG["agent1"]["checkpoint_name"]),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    predictor.predict_from_files(
        [[str(input_nii_path)]],
        str(output_dir),
        save_probabilities=False,
        overwrite=True,
        num_processes_preprocessing=1,
        num_processes_segmentation_export=1,
    )
    outputs = sorted(output_dir.glob("*.nii.gz"))
    if not outputs:
        raise RuntimeError("Agent 1 produced no NIfTI output")
    image = nib.load(str(outputs[0]))
    labels = np.asanyarray(image.dataobj)
    if labels.ndim == 4 and labels.shape[-1] == 1:
        labels = labels[..., 0]
    if labels.ndim != 3:
        raise RuntimeError(f"Unexpected Agent 1 output shape: {labels.shape}")
    pericardium = labels == AGENT1_LABEL
    del predictor, labels
    _release_cuda()
    return pericardium.astype(np.uint8), image


def build_agent2_model(device: torch.device) -> UNet:
    return UNet(
        spatial_dims=3,
        in_channels=1,
        out_channels=1,
        channels=(32, 64, 128, 256, 320),
        strides=(2, 2, 2, 2),
        num_res_units=2,
    ).to(device)


def run_agent2(input_nii_path: Path, native_target: nib.Nifti1Image) -> np.ndarray:
    transform = Compose([
        LoadImaged(keys=["image"]),
        EnsureChannelFirstd(keys=["image"]),
        Orientationd(keys=["image"], axcodes="RAS"),
        Spacingd(keys=["image"], pixdim=AGENT2_SPACING, mode=("bilinear",)),
        ScaleIntensityRanged(
            keys=["image"],
            a_min=AGENT2_HU_MIN,
            a_max=AGENT2_HU_MAX,
            b_min=0.0,
            b_max=1.0,
            clip=True,
        ),
    ])
    data = transform({"image": str(input_nii_path)})
    image = data["image"]
    model_affine = np.asarray(image.affine.cpu())
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_agent2_model(device)
    state = torch.load(AGENT2_CHECKPOINT, map_location=device)
    loaded = model.load_state_dict(state["model_state"], strict=True)
    if loaded.missing_keys or loaded.unexpected_keys:
        raise RuntimeError(f"Agent 2 checkpoint mismatch: {loaded}")
    inferer = SlidingWindowInferer(
        roi_size=AGENT2_PATCH_SIZE,
        sw_batch_size=1,
        overlap=0.25,
        mode="gaussian",
    )
    model.eval()
    autocast_enabled = device.type == "cuda"
    with torch.no_grad(), torch.amp.autocast(device_type=device.type, enabled=autocast_enabled):
        logits = inferer(image.unsqueeze(0).to(device), model)
    probability_model = torch.sigmoid(logits)[0, 0].float().cpu().numpy()
    probability_image = nib.Nifti1Image(probability_model, model_affine)
    probability_native = np.asanyarray(
        resample_from_to(probability_image, native_target, order=1).dataobj,
        dtype=np.float32,
    )
    del model, logits, probability_model, probability_image, image, data
    _release_cuda()
    return np.clip(probability_native, 0.0, 1.0)


def _native_3d_image(path: Path) -> nib.Nifti1Image:
    image = nib.load(str(path))
    if len(image.shape) != 3:
        raise ValueError(f"Only 3D NIfTI CT volumes are supported, got {image.shape}")
    return image


def run_dual_inference(input_nii_path: Path, work_dir: Path) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    verify_frozen_assets(check_hashes=False)
    native = _native_3d_image(input_nii_path)
    log.info("Running Agent 1 coarse pericardium prediction")
    agent1, agent1_image = run_agent1(input_nii_path, work_dir / "agent1")
    if agent1.shape != native.shape or not np.allclose(agent1_image.affine, native.affine, atol=1e-4):
        agent1_native_image = resample_from_to(
            nib.Nifti1Image(agent1.astype(np.uint8), agent1_image.affine), native, order=0
        )
        agent1 = np.asanyarray(agent1_native_image.dataobj) > 0
    log.info("Running Agent 2 precise pericardium prediction")
    probability = run_agent2(input_nii_path, native)
    agent2 = probability >= FUSION_CONFIG.agent2_threshold
    spacing = tuple(float(value) for value in native.header.get_zooms()[:3])
    fused, diagnostics = fuse_pericardium(agent1, probability, spacing, FUSION_CONFIG)
    outputs = {
        "fused": fused.astype(np.uint8),
        "agent1": np.asarray(agent1, dtype=np.uint8),
        "agent2": np.asarray(agent2, dtype=np.uint8),
    }
    return outputs, diagnostics


def _flat_slices(mask_xyz: np.ndarray) -> dict[str, list[int]]:
    slices: dict[str, list[int]] = {}
    for z in range(mask_xyz.shape[2]):
        plane = np.asarray(mask_xyz[:, :, z], dtype=np.uint8).T
        if plane.any():
            slices[str(z)] = plane.ravel().tolist()
    return slices


def _rle_slices(mask_xyz: np.ndarray) -> dict[str, dict[str, Any]]:
    slices: dict[str, dict[str, Any]] = {}
    for z in range(mask_xyz.shape[2]):
        flat = np.asarray(mask_xyz[:, :, z], dtype=np.uint8).T.ravel()
        foreground = np.flatnonzero(flat)
        if not len(foreground):
            continue
        breaks = np.flatnonzero(np.diff(foreground) > 1)
        starts = np.r_[0, breaks + 1]
        stops = np.r_[breaks, len(foreground) - 1]
        runs: list[int] = []
        for start_index, stop_index in zip(starts, stops):
            start = int(foreground[start_index])
            length = int(foreground[stop_index] - foreground[start_index] + 1)
            runs.extend((start, length))
        slices[str(z)] = {"runs": runs, "foreground": int(len(foreground))}
    return slices


def _save_upload(file: UploadFile, temp_dir: Path) -> Path:
    filename = file.filename or "scan.nii.gz"
    if not (filename.lower().endswith(".nii") or filename.lower().endswith(".nii.gz")):
        raise ValueError("Upload must be a .nii or .nii.gz NIfTI CT volume")
    suffix = ".nii.gz" if filename.lower().endswith(".nii.gz") else ".nii"
    input_dir = temp_dir / "input"
    input_dir.mkdir(parents=True)
    input_path = input_dir / f"dual_{uuid.uuid4().hex[:8]}_0000{suffix}"
    with input_path.open("wb") as handle:
        shutil.copyfileobj(file.file, handle)
    return input_path


async def _segment_request(file: UploadFile) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    temp_dir = Path(tempfile.mkdtemp(prefix="pericardium_dual_"))
    try:
        input_path = _save_upload(file, temp_dir)
        return run_dual_inference(input_path, temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/health")
def health(check_hashes: bool = False):
    try:
        assets = verify_frozen_assets(check_hashes=check_hashes)
        return {
            "status": "ok",
            "system": "pericardium-dual-agent-v1",
            "default_output": "fused",
            "available_outputs": ["fused", "agent1", "agent2"],
            "cuda_available": torch.cuda.is_available(),
            "assets": assets,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/segment")
async def segment(file: UploadFile = File(...)):
    try:
        outputs, diagnostics = await _segment_request(file)
        fused = outputs["fused"]
        return JSONResponse(content={
            "shape": list(fused.shape),
            "slices": _flat_slices(fused),
            "labels": [1] if fused.any() else [],
            "selected_output": "fused",
            "available_outputs": ["fused", "agent1", "agent2"],
            "fusion_summary": {
                "fallback": diagnostics["fallback"],
                "restored_voxels": diagnostics["restored_voxels"],
                "recovery_count": len(diagnostics["recoveries"]),
                "agent1_accepted": diagnostics["agent1_agreement_gate"]["accepted"],
                "agent1_gate_reasons": diagnostics["agent1_agreement_gate"]["reasons"],
            },
        })
    except Exception as exc:
        log.exception("Dual-agent inference failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/segment/compare")
async def segment_compare(file: UploadFile = File(...)):
    try:
        outputs, diagnostics = await _segment_request(file)
        return JSONResponse(content={
            "shape": list(outputs["fused"].shape),
            "encoding": "per-slice-foreground-rle-v1",
            "slice_flattening": "transpose_xy_then_C_order",
            "default_output": "fused",
            "available_outputs": ["fused", "agent1", "agent2"],
            "outputs": {
                name: {"slices": _rle_slices(mask), "nonzero_voxels": int(mask.sum())}
                for name, mask in outputs.items()
            },
            "fusion_diagnostics": diagnostics,
        })
    except Exception as exc:
        log.exception("Dual-agent comparison inference failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
