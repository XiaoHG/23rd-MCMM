"""问题三 v7 统一审计、解释和论文材料生成入口。

该脚本从固定 checkpoint 重新生成 valid/test/附件四的同配置解释，修复
旧流程中 train_mean 双重标准化和附件四解释参数不一致的问题。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cli.q3_run import BundleDataset, batch_to_device, load_saved_standardizer
from src.q_3.data import apply_standardizer, load_attachment2, load_attachment4, sha256_file
from src.q_3.explain import MODALITIES, _kl, train_means_from_standardized
from src.q_3.model import MaskedMultimodalNet


def timestamp_dir(parent: Path) -> Path:
    now = time.localtime()
    result = parent / (time.strftime("%Y%m%d_%H%M%S", now) + f"_{time.time_ns() % 1_000_000_000:09d}")
    result.mkdir(parents=True, exist_ok=False)
    return result


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else ["sample_id"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def sha256(path: Path) -> str:
    return sha256_file(path) if path.is_file() else ""


def load_model(run_dir: Path, device: torch.device):
    checkpoint_path = run_dir / "best_model.pt"
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    config = checkpoint["config"]
    model = MaskedMultimodalNet(
        input_dims={name: int(config["input_dims"][name]) for name in MODALITIES},
        hidden_dim=int(config.get("hidden_dim", 64)),
        heads=int(config.get("heads", 4)),
        layers=int(config.get("layers", 1)),
        dropout=float(config.get("dropout", 0.1)),
        max_length=50,
    ).to(device)
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.eval()
    return model, config, checkpoint_path


@torch.no_grad()
def model_outputs(model, batch):
    output = model(batch["text"], batch["audio"], batch["vision"], batch["mask"])
    return torch.softmax(output["logits"], dim=-1), output["regression"], output["gates"]


def intervene(batch, name: str, start: int | None, end: int | None, baseline: str, means: dict[str, torch.Tensor]):
    result = {key: value.clone() for key, value in batch.items()}
    index = MODALITIES.index(name)
    begin = 0 if start is None else start
    finish = result[name].shape[1] if end is None else end
    if baseline == "train_mean":
        result[name][:, begin:finish] = means[name].to(result[name].device, dtype=result[name].dtype)
    else:
        result[name][:, begin:finish] = 0.0
        result["mask"][:, begin:finish, index] = False
    return result


@torch.no_grad()
def explain_detailed(model, batch, window: int, stride: int, top_k: int, baseline: str, means: dict[str, torch.Tensor]):
    full_p, full_y, gates = model_outputs(model, batch)
    n, length = batch["text"].shape[:2]
    scores = torch.zeros((n, 3), device=full_p.device)
    all_windows = [[[] for _ in MODALITIES] for _ in range(n)]
    for index, name in enumerate(MODALITIES):
        removed = intervene(batch, name, None, None, baseline, means)
        p_removed, y_removed, _ = model_outputs(model, removed)
        scores[:, index] = 0.5 * _kl(full_p, p_removed) + 0.5 * (full_y - y_removed).abs()
        for start in range(0, length, stride):
            end = min(start + window, length)
            local = intervene(batch, name, start, end, baseline, means)
            p_local, y_local, _ = model_outputs(model, local)
            impact = 0.5 * _kl(full_p, p_local) + 0.5 * (full_y - y_local).abs()
            for row in range(n):
                if bool(batch["mask"][row, start:end, index].any()):
                    all_windows[row][index].append((start, end - 1, float(impact[row].item())))
    contribution = scores.clamp_min(0) / scores.clamp_min(0).sum(1, keepdim=True).clamp_min(1e-8)
    result = []
    for row in range(n):
        evidence = {}
        for index, name in enumerate(MODALITIES):
            candidates = sorted(all_windows[row][index], key=lambda item: item[2], reverse=True)
            selected = []
            for item in candidates:
                if all(item[1] < old[0] - 1 or item[0] > old[1] + 1 for old in selected):
                    selected.append(item)
                if len(selected) >= top_k:
                    break
            evidence[name] = selected
        flat = [item[2] for values in all_windows[row] for item in values]
        result.append({
            "pred_class": int(full_p[row].argmax().item()),
            "pred_regression": float(full_y[row].item()),
            "gates": [float(x) for x in gates[row].cpu()],
            "modality_scores": [float(x) for x in scores[row].cpu()],
            "modality_contrib": [float(x) for x in contribution[row].cpu()],
            "main_modality": MODALITIES[int(contribution[row].argmax().item())],
            "evidence": evidence,
            "all_windows": {name: values for name, values in zip(MODALITIES, all_windows[row])},
            "fidelity_top_mean": float(np.mean(sorted(flat, reverse=True)[:3])) if flat else 0.0,
            "fidelity_low_mean": float(np.mean(sorted(flat)[:3])) if flat else 0.0,
        })
    return result


def video_mapping(sample_id: str, modality: str, rank: int, start: int, end: int, impact: float, raw_text: str, video_audit: dict[str, dict]):
    if "$_$" in sample_id:
        video_id, clip_id = sample_id.split("$_$", 1)
        video = ROOT / "E-q/dataset/attachment_1_raw_multimodal_samples/mosei_raw_videos_100" / video_id / f"{clip_id}.mp4"
        source_type = "attachment1_video"
    else:
        video = ROOT / "E-q/dataset/attachment_4_explainability_videos_and_features/attachment_4_explainability_videos_and_features/aligned/videos" / f"{sample_id}.mp4"
        source_type = "attachment4_video"
    audit = video_audit.get(str(video), {})
    fps = float(audit.get("fps_header", 0.0))
    decoded = int(audit.get("frame_count_decoded", 0))
    duration = decoded / fps if fps > 0 and decoded else 0.0
    start_sec = duration * start / 50.0 if duration else ""
    end_sec = duration * (end + 1) / 50.0 if duration else ""
    frame_start = int(start_sec * fps) if start_sec != "" else ""
    frame_end = int(end_sec * fps) - 1 if end_sec != "" else ""
    clamped = bool(decoded and frame_end >= decoded)
    return {
        "sample_id": sample_id, "modality": modality, "rank": rank,
        "start_index": start, "end_index": end, "impact_score": impact,
        "source_video": str(video), "source_type": source_type,
        "start_sec": start_sec, "end_sec": end_sec,
        "frame_start": frame_start, "frame_end": frame_end, "fps": fps,
        "text_evidence": raw_text if modality == "text" else "",
        "text_time_source": "raw_text; aligned relative window" if modality == "text" else "",
        "source_exists": video.exists(),
        "mapping_precision": "approximate_after_decode_clamp" if clamped else "decoded_frame_range",
        "mapping_status": "mapped_to_video" if video.exists() else "relative_window_only_source_video_missing",
    }


def decode_audits(paths: list[Path]) -> dict[str, dict]:
    audits = {}
    for path in paths:
        cap = cv2.VideoCapture(str(path))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        header = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        decoded = 0
        while True:
            ok, _ = cap.read()
            if not ok:
                break
            decoded += 1
        cap.release()
        audits[str(path)] = {"video": str(path), "source_exists": path.exists(), "fps_header": fps, "frame_count_header": header, "frame_count_decoded": decoded, "width": width, "height": height, "header_decoded_match": header == decoded, "decode_status": "ok" if decoded else "read_failed"}
    return audits


def summarize_predictions(bundle, detailed, split: str, baseline: str, window: int, stride: int):
    rows = []
    for sample_id, item, index in zip(bundle.ids, detailed, range(len(bundle.ids))):
        row = {"sample_id": sample_id, "split": split, "pred_class": item["pred_class"], "pred_regression": item["pred_regression"], "gate_text": item["gates"][0], "gate_audio": item["gates"][1], "gate_vision": item["gates"][2], "modality_score_text": item["modality_scores"][0], "modality_score_audio": item["modality_scores"][1], "modality_score_vision": item["modality_scores"][2], "modality_contrib_text": item["modality_contrib"][0], "modality_contrib_audio": item["modality_contrib"][1], "modality_contrib_vision": item["modality_contrib"][2], "main_modality": item["main_modality"], "fidelity_top_mean": item["fidelity_top_mean"], "fidelity_low_mean": item["fidelity_low_mean"], "explanation_method": "counterfactual_occlusion", "explanation_baseline": baseline, "explanation_window": window, "explanation_stride": stride}
        if bundle.classification is not None:
            row.update({"true_class": int(bundle.classification[index]), "true_regression": float(bundle.regression[index])})
        rows.append(row)
    return rows


def build_outputs(bundle, detailed, split, audits, baseline: str, window: int, stride: int):
    predictions = summarize_predictions(bundle, detailed, split, baseline, window, stride)
    mappings, local_rows = [], []
    for sample_id, item, index in zip(bundle.ids, detailed, range(len(bundle.ids))):
        raw = bundle.raw_text[index] if bundle.raw_text else ""
        for modality in MODALITIES:
            for rank, (start, end, impact) in enumerate(item["evidence"][modality], 1):
                mappings.append(video_mapping(sample_id, modality, rank, start, end, impact, raw, audits))
            for start, end, impact in item["all_windows"][modality]:
                local_rows.append({"sample_id": sample_id, "split": split, "modality": modality, "start_index": start, "end_index": end, "impact_score": impact, "is_top_k": any(start == x[0] and end == x[1] for x in item["evidence"][modality])})
    return predictions, mappings, local_rows


def plot_metrics(rows: list[dict], output: Path):
    if not rows:
        return
    values = np.asarray([[float(row[f"modality_contrib_{m}"]) for m in MODALITIES] for row in rows])
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.boxplot([values[:, i] for i in range(3)], tick_labels=["Text", "Audio", "Vision"], patch_artist=True)
    ax.set_ylabel("Normalized counterfactual contribution")
    ax.set_title("Validation modality contribution distribution")
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(output / "fig_modality_contribution_valid.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_evaluation_artifacts(rows: list[dict], output: Path) -> None:
    """Create paper-ready diagnostics from the same final valid/test rows."""
    for split in ("valid", "test"):
        current = [row for row in rows if row["split"] == split]
        if not current:
            continue
        true_cls = np.asarray([int(row["true_class"]) for row in current])
        pred_cls = np.asarray([int(row["pred_class"]) for row in current])
        confusion = np.zeros((3, 3), dtype=int)
        for truth, prediction in zip(true_cls, pred_cls):
            confusion[truth, prediction] += 1
        fig, ax = plt.subplots(figsize=(5.2, 4.4))
        image = ax.imshow(confusion, cmap="Blues")
        for i in range(3):
            for j in range(3):
                ax.text(j, i, str(confusion[i, j]), ha="center", va="center")
        ax.set_xlabel("Predicted class")
        ax.set_ylabel("True class")
        ax.set_title(f"{split.capitalize()} confusion matrix")
        fig.colorbar(image, ax=ax, shrink=0.82)
        fig.savefig(output / f"fig_confusion_matrix_{split}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

        truth_reg = np.asarray([float(row["true_regression"]) for row in current])
        pred_reg = np.asarray([float(row["pred_regression"]) for row in current])
        residual = pred_reg - truth_reg
        fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
        axes[0].scatter(truth_reg, pred_reg, s=10, alpha=0.45)
        axes[0].plot([-3, 3], [-3, 3], "k--", linewidth=1)
        axes[0].set_xlabel("True intensity")
        axes[0].set_ylabel("Predicted intensity")
        axes[0].set_title(f"{split.capitalize()} regression")
        axes[1].hist(residual, bins=24, color="#4c78a8", alpha=0.85)
        axes[1].axvline(0, color="k", linestyle="--", linewidth=1)
        axes[1].set_xlabel("Prediction residual")
        axes[1].set_ylabel("Count")
        axes[1].set_title(f"{split.capitalize()} residuals")
        fig.tight_layout()
        fig.savefig(output / f"fig_regression_diagnostics_{split}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    stats = []
    for split in ("valid", "test", "attachment4"):
        current = [row for row in rows if row["split"] == split]
        if not current:
            continue
        for modality in MODALITIES:
            values = np.asarray([float(row[f"modality_contrib_{modality}"]) for row in current])
            stats.append({"split": split, "modality": modality, "sample_count": len(values), "mean_contribution": float(values.mean()), "std_contribution": float(values.std()), "median_contribution": float(np.median(values))})
    write_csv(output / "modality_contribution_summary.csv", stats)


def select_explanation_config(model, valid, means, device, batch_size: int):
    rows = []
    for baseline in ("zero_invalid", "train_mean"):
        for window in (3, 5, 7):
            items = []
            loader = DataLoader(BundleDataset(valid), batch_size=batch_size, shuffle=False, num_workers=0)
            for batch in loader:
                batch = batch_to_device(batch, device)
                items.extend(explain_detailed(model, {key: batch[key] for key in ("text", "audio", "vision", "mask")}, window, window, 3, baseline, means))
            top = np.asarray([x["fidelity_top_mean"] for x in items])
            low = np.asarray([x["fidelity_low_mean"] for x in items])
            rows.append({"baseline": baseline, "window": window, "stride": window, "sample_count": len(items), "mean_top_impact": float(top.mean()), "mean_low_impact": float(low.mean()), "top_minus_low": float((top - low).mean()), "top_to_low_ratio": float(top.mean() / max(low.mean(), 1e-8))})
    selected = max(rows, key=lambda row: (row["top_minus_low"], -row["window"], row["baseline"] == "zero_invalid"))
    return rows, selected


def main(args):
    run_dir = Path(args.run_dir).resolve()
    output = timestamp_dir(ROOT / "E-q/q_3_output")
    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    model, model_config, checkpoint_path = load_model(run_dir, device)
    stats = load_saved_standardizer(run_dir / "train_standardizer.npz")
    feature_path = ROOT / "E-q/dataset/attachment_2_feature_files/aligned_50.pkl"
    train_raw = load_attachment2(feature_path, "train")
    valid_raw = load_attachment2(feature_path, "valid")
    test_raw = load_attachment2(feature_path, "test")
    train = apply_standardizer(train_raw, stats)
    valid = apply_standardizer(valid_raw, stats)
    test = apply_standardizer(test_raw, stats)
    means_np = train_means_from_standardized(train)
    means = {name: torch.from_numpy(value) for name, value in means_np.items()}
    a4_root = ROOT / "E-q/dataset/attachment_4_explainability_videos_and_features/attachment_4_explainability_videos_and_features"
    a4 = apply_standardizer(load_attachment4(a4_root, "aligned"), stats)
    all_videos = [Path(f) for f in sorted((a4_root / "aligned/videos").glob("*.mp4"))]
    audits = decode_audits(all_videos)
    selection_rows, selected = select_explanation_config(model, valid, means, device, args.batch_size)
    args.window = int(selected["window"])
    args.stride = int(selected["stride"])
    args.baseline = selected["baseline"]
    (output / "explanation_parameter_selection.json").write_text(json.dumps({"candidates": selection_rows, "selected": selected, "selection_rule": "maximize corrected valid top-minus-low impact; ties prefer smaller window then zero_invalid"}, ensure_ascii=False, indent=2), encoding="utf-8")
    detailed_by_split = {}
    for split, bundle in (("valid", valid), ("test", test), ("attachment4", a4)):
        loader = DataLoader(BundleDataset(bundle), batch_size=args.batch_size, shuffle=False, num_workers=0)
        detailed = []
        for batch in loader:
            batch = batch_to_device(batch, device)
            detailed.extend(explain_detailed(model, {key: batch[key] for key in ("text", "audio", "vision", "mask")}, args.window, args.stride, args.top_k, args.baseline, means))
        detailed_by_split[split] = detailed
    pred_valid, map_valid, local_valid = build_outputs(valid, detailed_by_split["valid"], "valid", audits, args.baseline, args.window, args.stride)
    pred_test, map_test, local_test = build_outputs(test, detailed_by_split["test"], "test", audits, args.baseline, args.window, args.stride)
    pred_a4, map_a4, local_a4 = build_outputs(a4, detailed_by_split["attachment4"], "attachment4", audits, args.baseline, args.window, args.stride)
    write_csv(output / "predictions_valid.csv", pred_valid)
    write_csv(output / "predictions_test.csv", pred_test)
    write_csv(output / "predictions_attachment4.csv", pred_a4)
    write_csv(output / "evidence_mapping_valid.csv", map_valid)
    write_csv(output / "evidence_mapping_test.csv", map_test)
    write_csv(output / "evidence_mapping_attachment4.csv", map_a4)
    write_csv(output / "local_importance_valid.csv", local_valid)
    write_csv(output / "local_importance_test.csv", local_test)
    write_csv(output / "local_importance_attachment4.csv", local_a4)
    metric_rows = []
    for split, bundle, rows in (("valid", valid, pred_valid), ("test", test, pred_test)):
        y_cls = np.asarray([row["true_class"] for row in rows]); p_cls = np.asarray([row["pred_class"] for row in rows])
        y_reg = np.asarray([row["true_regression"] for row in rows]); p_reg = np.asarray([row["pred_regression"] for row in rows])
        from src.q_3.metrics import prediction_metrics
        metric_rows.append({"split": split, **prediction_metrics(y_cls, p_cls, y_reg, p_reg)})
    write_csv(output / "model_metrics.csv", metric_rows)
    fidelity = {"selection": selected, "final_config": {"baseline": args.baseline, "window": args.window, "stride": args.stride, "top_k": args.top_k}, "valid": {"sample_count": len(pred_valid), "mean_top_evidence_impact": float(np.mean([x["fidelity_top_mean"] for x in pred_valid])), "mean_low_evidence_impact": float(np.mean([x["fidelity_low_mean"] for x in pred_valid])), "top_minus_low": float(np.mean([float(x["fidelity_top_mean"]) - float(x["fidelity_low_mean"]) for x in pred_valid]))}}
    (output / "fidelity_metrics.json").write_text(json.dumps(fidelity, ensure_ascii=False, indent=2), encoding="utf-8")
    error_rows = []
    for row in pred_valid:
        error_rows.append({"sample_id": row["sample_id"], "true_class": row["true_class"], "pred_class": row["pred_class"], "classification_error": int(row["true_class"] != row["pred_class"]), "true_regression": row["true_regression"], "pred_regression": row["pred_regression"], "absolute_regression_error": abs(float(row["true_regression"]) - float(row["pred_regression"])), "main_modality": row["main_modality"], "error_group": "classification_error" if row["true_class"] != row["pred_class"] else "correct_classification"})
    write_csv(output / "error_attribution_valid.csv", error_rows)
    plot_metrics(pred_valid, output)
    plot_evaluation_artifacts(pred_valid + pred_test + pred_a4, output)
    write_csv(output / "video_decode_audit.csv", list(audits.values()))
    np.savez(output / "train_mean_baseline.npz", **means_np)
    manifest_paths = [checkpoint_path, run_dir / "train_standardizer.npz", run_dir / "run_config.json", feature_path]
    (output / "run_config.json").write_text(json.dumps({"mode": "v7_unified_explanation_finalize", "source_run_dir": str(run_dir), "checkpoint_sha256": sha256(checkpoint_path), "standardizer_sha256": sha256(run_dir / "train_standardizer.npz"), "feature_path": str(feature_path), "feature_sha256": sha256(feature_path), "feature_version": "aligned", "seed": model_config.get("seed"), "device": str(device), "baseline": args.baseline, "baseline_space": "standardized_train_features_once", "window": args.window, "stride": args.stride, "top_k": args.top_k, "train_count": len(train.ids), "valid_count": len(valid.ids), "test_count": len(test.ids), "attachment4_count": len(a4.ids), "attachment4_used_for": "inference_only"}, ensure_ascii=False, indent=2), encoding="utf-8")
    environment = {"python": platform.python_version(), "platform": platform.platform(), "torch": torch.__version__, "numpy": np.__version__, "opencv": cv2.__version__, "matplotlib": matplotlib.__version__, "device": str(device)}
    (output / "environment.json").write_text(json.dumps(environment, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "input_manifest.json").write_text(json.dumps({str(path): {"exists": path.exists(), "sha256": sha256(path), "bytes": path.stat().st_size if path.exists() else 0} for path in manifest_paths}, ensure_ascii=False, indent=2), encoding="utf-8")
    all_predictions = pred_valid + pred_test + pred_a4
    all_mappings = map_valid + map_test + map_a4
    checks = {"train_valid_test_ids_disjoint": not (set(train.ids) & set(valid.ids) or set(train.ids) & set(test.ids) or set(valid.ids) & set(test.ids)), "train_valid_test_counts": [len(train.ids), len(valid.ids), len(test.ids)] == [3395, 728, 727], "attachment4_full_prediction": len(pred_a4) == len(a4.ids), "contributions_sum_to_one": all(abs(sum(float(row[f"modality_contrib_{m}"]) for m in MODALITIES) - 1) < 1e-4 for row in all_predictions), "evidence_indices_in_range": all(0 <= int(row["start_index"]) <= int(row["end_index"]) < 50 for row in all_mappings), "attachment4_unlabeled": all("true_class" not in row for row in pred_a4), "explanation_config_consistent": all(row["explanation_baseline"] == args.baseline and int(row["explanation_window"]) == args.window and int(row["explanation_stride"]) == args.stride for row in all_predictions)}
    (output / "validation_audit.json").write_text(json.dumps({"schema_version": "q3-v7-audit-v1", "passed": all(checks.values()), "checks": checks, "video_decode_mismatch_count": sum(not x["header_decoded_match"] for x in audits.values())}, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "README.md").write_text(f"# 问题三 v7 统一结果\n\n来源 checkpoint：`{checkpoint_path}`。本目录统一使用 `{args.baseline}`（标准化训练特征只计算一次）、window={args.window}、stride={args.stride}、top_k={args.top_k} 生成 valid/test/附件四解释。附件四仅推理，无真实性能标签。\n\n主要文件：`predictions_valid.csv`、`predictions_test.csv`、`predictions_attachment4.csv`、三份 `local_importance_*.csv`、三份证据映射、`error_attribution_valid.csv`、`modality_contribution_summary.csv`、valid/test 混淆矩阵、回归诊断图、`video_decode_audit.csv`、`validation_audit.json`、`environment.json`、`input_manifest.json`、`output_checksums.json`。\n\n`impact_score` 是模型反事实敏感性，不是因果真值；`mapping_precision=approximate_after_decode_clamp` 表示视频容器帧数与实际解码范围不一致，需人工复核。\n", encoding="utf-8")
    checksums = {}
    for path in output.rglob("*"):
        if path.is_file() and path.name != "output_checksums.json":
            checksums[str(path.relative_to(output))] = sha256(path)
    (output / "output_checksums.json").write_text(json.dumps(checksums, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "output_dir": str(output), "audit_passed": all(checks.values()), "metrics": metric_rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--window", type=int, default=7)
    parser.add_argument("--stride", type=int, default=7)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--device", default=None)
    main(parser.parse_args())
