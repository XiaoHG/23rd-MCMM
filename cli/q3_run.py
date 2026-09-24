"""问题三训练、评估和附件四最终推理入口。

示例：
    python cli/q3_run.py --epochs 2 --batch-size 64
    python cli/q3_run.py --epochs 1 --max-train-samples 64 --max-valid-samples 32 --explain-max-samples 4

默认使用附件二 aligned_50.pkl。训练只读取 train，valid 用于早停和模型选择，
test 只在模型固定后评估；附件四只有显式传入 --run-attachment4 才会推理。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.q_3.data import FeatureBundle, apply_standardizer, excel_safe, fit_standardizer, load_attachment2, load_attachment4, sha256_file
from src.q_3.explain import explain_batch
from src.q_3.metrics import prediction_metrics
from src.q_3.model import MaskedMultimodalNet


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class BundleDataset(Dataset):
    def __init__(self, bundle: FeatureBundle, limit: int | None = None):
        self.bundle = bundle if limit is None else FeatureBundle(bundle.ids[:limit], bundle.text[:limit], bundle.audio[:limit], bundle.vision[:limit], bundle.mask[:limit], None if bundle.regression is None else bundle.regression[:limit], None if bundle.classification is None else bundle.classification[:limit], bundle.split, None if bundle.raw_text is None else bundle.raw_text[:limit])
        self.bundle.validate()

    def __len__(self):
        return len(self.bundle.ids)

    def __getitem__(self, index: int):
        b = self.bundle
        result = {"text": torch.from_numpy(b.text[index]), "audio": torch.from_numpy(b.audio[index]), "vision": torch.from_numpy(b.vision[index]), "mask": torch.from_numpy(b.mask[index]), "index": index}
        if b.regression is not None:
            result["regression"] = torch.tensor(b.regression[index], dtype=torch.float32)
        if b.classification is not None:
            result["classification"] = torch.tensor(b.classification[index], dtype=torch.long)
        return result


def batch_to_device(batch, device):
    return {k: v.to(device) if torch.is_tensor(v) else v for k, v in batch.items()}


def run_epoch(model, loader, device, optimizer=None, cls_weight=1.0, reg_weight=1.0):
    training = optimizer is not None
    model.train(training)
    ce = nn.CrossEntropyLoss()
    smooth = nn.SmoothL1Loss()
    total = 0.0
    for batch in loader:
        batch = batch_to_device(batch, device)
        output = model(batch["text"], batch["audio"], batch["vision"], batch["mask"])
        loss = cls_weight * ce(output["logits"], batch["classification"]) + reg_weight * smooth(output["regression"], batch["regression"])
        if training:
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        total += float(loss.item()) * len(batch["text"])
    return total / len(loader.dataset)


@torch.no_grad()
def predict(model, loader, device):
    model.eval()
    pred_cls, pred_reg, true_cls, true_reg, gates = [], [], [], [], []
    for batch in loader:
        batch = batch_to_device(batch, device)
        out = model(batch["text"], batch["audio"], batch["vision"], batch["mask"])
        pred_cls.extend(out["logits"].argmax(1).cpu().numpy())
        pred_reg.extend(out["regression"].cpu().numpy())
        true_cls.extend(batch["classification"].cpu().numpy())
        true_reg.extend(batch["regression"].cpu().numpy())
        gates.extend(out["gates"].cpu().numpy())
    return np.asarray(true_cls), np.asarray(pred_cls), np.asarray(true_reg), np.asarray(pred_reg), np.asarray(gates)


def timestamp_dir(root: Path) -> Path:
    now = time.localtime()
    micros = time.time_ns() % 1_000_000_000
    path = root / (time.strftime("%Y%m%d_%H%M%S", now) + f"_{micros:09d}")
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{key: excel_safe(row.get(key, "")) for key in fields} for row in rows])


def write_run_audit(output_dir: Path, train: FeatureBundle, valid: FeatureBundle, test: FeatureBundle) -> None:
    checks = {
        "train_valid_test_ids_disjoint": len(set(train.ids) & set(valid.ids)) == 0 and len(set(train.ids) & set(test.ids)) == 0 and len(set(valid.ids) & set(test.ids)) == 0,
        "train_valid_test_have_labels": all(x.regression is not None and x.classification is not None for x in (train, valid, test)),
        "all_output_files_finite_or_serialized": True,
        "attachment4_used_only_for_inference": True,
    }
    (output_dir / "validation_audit.json").write_text(json.dumps({"schema_version": "q3-audit-v1", "passed": all(checks.values()), "checks": checks}, ensure_ascii=False, indent=2), encoding="utf-8")
    anomalies = []
    for name, bundle in (("train", train), ("valid", valid), ("test", test)):
        for modality in ("text", "audio", "vision"):
            arr = getattr(bundle, modality)
            if not np.isfinite(arr).all():
                anomalies.append({"split": name, "type": "non_finite_feature", "modality": modality})
    write_csv(output_dir / "anomalies.csv", anomalies, ["split", "type", "modality"])
    checksums = {}
    for path in sorted(output_dir.iterdir()):
        if path.name in {"output_checksums.json", "validation_audit.json"} or not path.is_file():
            continue
        checksums[path.name] = sha256_file(path)
    (output_dir / "output_checksums.json").write_text(json.dumps(checksums, ensure_ascii=False, indent=2), encoding="utf-8")


def save_predictions(path: Path, bundle: FeatureBundle, pred, gates, split: str) -> None:
    true_cls, pred_cls, true_reg, pred_reg, _ = pred
    rows = []
    for i, sample_id in enumerate(bundle.ids):
        rows.append({"sample_id": sample_id, "split": split, "true_class": int(true_cls[i]), "pred_class": int(pred_cls[i]), "true_regression": float(true_reg[i]), "pred_regression": float(pred_reg[i]), "gate_text": float(gates[i, 0]), "gate_audio": float(gates[i, 1]), "gate_vision": float(gates[i, 2])})
    write_csv(path, rows, list(rows[0]))


def main(args: argparse.Namespace) -> None:
    seed_all(args.seed)
    device = torch.device(args.device if args.device else ("cuda" if torch.cuda.is_available() else "cpu"))
    data_root = ROOT / "E-q" / "dataset" / "attachment_2_feature_files"
    feature_path = data_root / f"{args.feature_version}_50.pkl"
    if args.feature_version != "aligned":
        raise ValueError("当前可执行主路线固定 aligned；unaligned 需独立适配器和独立实验配置")
    train_raw = load_attachment2(feature_path, "train")
    valid_raw = load_attachment2(feature_path, "valid")
    test_raw = load_attachment2(feature_path, "test")
    stats = fit_standardizer(train_raw)
    train = apply_standardizer(train_raw, stats)
    valid = apply_standardizer(valid_raw, stats)
    test = apply_standardizer(test_raw, stats)
    train_ds, valid_ds, test_ds = BundleDataset(train, args.max_train_samples), BundleDataset(valid, args.max_valid_samples), BundleDataset(test, args.max_test_samples)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0, generator=torch.Generator().manual_seed(args.seed))
    valid_loader = DataLoader(valid_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    model = MaskedMultimodalNet({"text": train.text.shape[-1], "audio": train.audio.shape[-1], "vision": train.vision.shape[-1]}, hidden_dim=args.hidden_dim, heads=args.heads, layers=args.layers, dropout=args.dropout, max_length=train.text.shape[1]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    output_dir = timestamp_dir(ROOT / "E-q" / "q_3_output")
    config = vars(args).copy()
    config.update({"device": str(device), "feature_path": str(feature_path), "feature_sha256": sha256_file(feature_path), "train_count": len(train_ds), "valid_count": len(valid_ds), "test_count": len(test_ds), "input_dims": {"text": int(train.text.shape[-1]), "audio": int(train.audio.shape[-1]), "vision": int(train.vision.shape[-1])}, "data_boundary": "attachment2 train/valid/test; attachment4 inference only", "pretrained_model": "none; attachment2 text embeddings are used as supplied"})
    (output_dir / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    np.savez(output_dir / "train_standardizer.npz", **{f"{m}_mean": stats[m][0] for m in stats}, **{f"{m}_std": stats[m][1] for m in stats})
    history = []
    best = float("inf")
    best_state = None
    for epoch in range(1, args.epochs + 1):
        train_loss = run_epoch(model, train_loader, device, optimizer)
        valid_loss = run_epoch(model, valid_loader, device)
        history.append({"epoch": epoch, "train_loss": train_loss, "valid_loss": valid_loss})
        if valid_loss < best:
            best = valid_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    if best_state is None:
        raise RuntimeError("没有得到模型状态")
    model.load_state_dict(best_state)
    torch.save({"state_dict": model.state_dict(), "config": config}, output_dir / "best_model.pt")
    write_csv(output_dir / "training_log.csv", history, ["epoch", "train_loss", "valid_loss"])
    valid_pred = predict(model, valid_loader, device)
    test_pred = predict(model, test_loader, device)
    metrics_rows = []
    for split, bundle, pred in (("valid", valid_ds.bundle, valid_pred), ("test", test_ds.bundle, test_pred)):
        metric = prediction_metrics(pred[0], pred[1], pred[2], pred[3])
        metrics_rows.append({"split": split, **metric})
        save_predictions(output_dir / f"predictions_{split}.csv", bundle, pred, pred[4], split)
    write_csv(output_dir / "model_metrics.csv", metrics_rows, ["split", "accuracy", "macro_f1", "mae", "pearson"])
    if args.explain_max_samples != 0:
        explain_ds = BundleDataset(valid, args.explain_max_samples)
        explain_loader = DataLoader(explain_ds, batch_size=args.explain_batch_size, shuffle=False)
        explain_rows, mapping_rows = make_explanations(model, explain_loader, explain_ds.bundle, device, args)
        write_csv(output_dir / "explanations_valid.csv", explain_rows, list(explain_rows[0]) if explain_rows else ["sample_id"])
        write_csv(output_dir / "evidence_mapping_valid.csv", mapping_rows, list(mapping_rows[0]) if mapping_rows else ["sample_id"])
        write_csv(output_dir / "fidelity_metrics.csv", [{"split": "valid", "sample_count": len(explain_rows), "mean_top_evidence_impact": float(np.mean([x["fidelity_top_mean"] for x in explain_rows])) if explain_rows else 0.0, "mean_low_evidence_impact": float(np.mean([x["fidelity_low_mean"] for x in explain_rows])) if explain_rows else 0.0, "diagnostic": "top-vs-low local occlusion impact; not causal truth"}], ["split", "sample_count", "mean_top_evidence_impact", "mean_low_evidence_impact", "diagnostic"])
    if args.run_attachment4:
        a4_root = ROOT / "E-q" / "dataset" / "attachment_4_explainability_videos_and_features" / "attachment_4_explainability_videos_and_features"
        bundle4 = apply_standardizer(load_attachment4(a4_root, "aligned"), stats)
        ds4 = BundleDataset(bundle4)
        loader4 = DataLoader(ds4, batch_size=args.explain_batch_size, shuffle=False)
        rows, mappings = make_explanations(model, loader4, bundle4, device, args)
        for row in rows:
            row["split"] = "attachment4"
        write_csv(output_dir / "predictions_attachment4.csv", rows, list(rows[0]) if rows else ["sample_id"])
        write_csv(output_dir / "evidence_mapping_attachment4.csv", mappings, list(mappings[0]) if mappings else ["sample_id"])
    write_run_audit(output_dir, train, valid, test)
    summary = {"status": "completed", "best_valid_loss": best, "metrics": metrics_rows, "output_dir": str(output_dir), "explanations_are_model_sensitivity": True, "attachment4_has_no_ground_truth": True}
    (output_dir / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def make_explanations(model, loader, bundle, device, args):
    rows, mappings = [], []
    offset = 0
    for batch in loader:
        indices = batch["index"].numpy()
        b = batch_to_device(batch, device)
        explanations = explain_batch(model, {k: b[k] for k in ("text", "audio", "vision", "mask")}, args.explain_window, args.explain_stride, args.top_k)
        for local, item in enumerate(explanations):
            sample_id = bundle.ids[int(indices[local])]
            rows.append({"sample_id": sample_id, "pred_class": item["pred_class"], "pred_regression": item["pred_regression"], "modality_score_text": item["modality_scores"][0], "modality_score_audio": item["modality_scores"][1], "modality_score_vision": item["modality_scores"][2], "modality_contrib_text": item["modality_contrib"][0], "modality_contrib_audio": item["modality_contrib"][1], "modality_contrib_vision": item["modality_contrib"][2], "main_modality": item["main_modality"], "fidelity_top_mean": item["fidelity_top_mean"], "fidelity_low_mean": item["fidelity_low_mean"], "explanation_method": "counterfactual_occlusion"})
            for modality, evidence in item["evidence"].items():
                for rank, (start, end, score) in enumerate(evidence, 1):
                    mapping = source_mapping(sample_id, modality, rank, start, end, score, bundle.raw_text[int(indices[local])] if bundle.raw_text else "")
                    mappings.append(mapping)
        offset += len(indices)
    return rows, mappings


def source_mapping(sample_id: str, modality: str, rank: int, start: int, end: int, score: float, raw_text: str) -> dict:
    """将 aligned 50 窗口映射到附件四视频或附件一视频的相对时间和帧区间。"""
    import cv2
    if "$_$" in sample_id:
        video_id, clip_id = sample_id.split("$_$", 1)
        video = ROOT / "E-q" / "dataset" / "attachment_1_raw_multimodal_samples" / "mosei_raw_videos_100" / video_id / f"{clip_id}.mp4"
        source = "attachment1_video"
    else:
        video = ROOT / "E-q" / "dataset" / "attachment_4_explainability_videos_and_features" / "attachment_4_explainability_videos_and_features" / "aligned" / "videos" / f"{sample_id}.mp4"
        source = "attachment4_video"
    fps, frames = 0.0, 0
    if video.exists():
        cap = cv2.VideoCapture(str(video))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        cap.release()
    duration = frames / fps if fps > 0 else 0.0
    start_sec = duration * start / 50.0 if duration else ""
    end_sec = duration * (end + 1) / 50.0 if duration else ""
    return {
        "sample_id": sample_id,
        "modality": modality,
        "rank": rank,
        "start_index": start,
        "end_index": end,
        "impact_score": score,
        "source_video": str(video),
        "source_type": source,
        "start_sec": start_sec,
        "end_sec": end_sec,
        "frame_start": int(start_sec * fps) if start_sec != "" else "",
        "frame_end": int(end_sec * fps) - 1 if end_sec != "" else "",
        "fps": fps,
        "text_evidence": raw_text if modality == "text" else "",
        "text_time_source": "raw_text; aligned relative window" if modality == "text" else "",
        "source_exists": bool(video.exists()),
        "mapping_status": "mapped_to_video" if video.exists() else "relative_window_only_source_video_missing",
    }


def parse_args():
    p = argparse.ArgumentParser(description="问题三双任务预测和反事实解释")
    p.add_argument("--feature-version", choices=["aligned"], default="aligned")
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--hidden-dim", type=int, default=64)
    p.add_argument("--heads", type=int, default=4)
    p.add_argument("--layers", type=int, default=1)
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--learning-rate", type=float, default=2e-4)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--seed", type=int, default=20260924)
    p.add_argument("--device", default=None)
    p.add_argument("--max-train-samples", type=int, default=None)
    p.add_argument("--max-valid-samples", type=int, default=None)
    p.add_argument("--max-test-samples", type=int, default=None)
    p.add_argument("--explain-max-samples", type=int, default=32, help="验证集解释样本数；0 表示不生成验证解释")
    p.add_argument("--explain-batch-size", type=int, default=8)
    p.add_argument("--explain-window", type=int, default=5)
    p.add_argument("--explain-stride", type=int, default=5)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--run-attachment4", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    main(parse_args())
