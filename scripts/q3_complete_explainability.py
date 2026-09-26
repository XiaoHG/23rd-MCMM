"""完成问题三剩余解释性检查与附件四视频解释卡。

输入：已有问题三运行目录中的 ``best_model.pt`` 和 ``train_standardizer.npz``。
输出：在 ``E-q/q_3_output`` 新建时间戳目录，包含验证集解释参数诊断、
OpenCV 视频解码审计、关键帧、附件四样本解释卡和可追溯清单。

示例：
    python scripts/q3_complete_explainability.py \
      --run-dir E-q/q_3_output/20260925_100021_726334600 \
      --valid-max-samples 0
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cli.q3_run import BundleDataset, batch_to_device, load_saved_standardizer
from src.q_3.data import apply_standardizer, load_attachment2, load_attachment4, sha256_file
from src.q_3.explain import explain_batch
from src.q_3.model import MaskedMultimodalNet

MODALITIES = ("text", "audio", "vision")
MODALITY_LABELS = {"text": "Text", "audio": "Audio", "vision": "Vision"}


def timestamp_dir(parent: Path) -> Path:
    now = time.localtime()
    value = parent / (time.strftime("%Y%m%d_%H%M%S", now) + f"_{time.time_ns() % 1_000_000_000:09d}")
    value.mkdir(parents=True, exist_ok=False)
    return value


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fields} for row in rows)


def latex_escape(value: object) -> str:
    text = str(value)
    for old, new in (("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")):
        text = text.replace(old, new)
    return text


def save_figure(path: Path) -> None:
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


def make_global_contribution_figure(predictions: list[dict[str, str]], path: Path) -> None:
    values = np.asarray([[float(row[f"modality_contrib_{name}"]) for name in MODALITIES] for row in predictions])
    means, stds = values.mean(axis=0), values.std(axis=0)
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    ax.bar([MODALITY_LABELS[x] for x in MODALITIES], means, yerr=stds, capsize=5, color=["#2563eb", "#ea580c", "#16a34a"], alpha=0.85)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Mean normalized counterfactual contribution")
    ax.set_title("Attachment 4 modality sensitivity (unlabeled)")
    ax.grid(axis="y", alpha=0.25)
    save_figure(path)


def make_fidelity_figure(source_run: Path, path: Path) -> None:
    csv_path = source_run / "fidelity_metrics.csv"
    json_path = source_run / "fidelity_metrics.json"
    if csv_path.exists():
        rows = read_csv(csv_path)
        top = float(rows[0]["mean_top_evidence_impact"])
        low = float(rows[0]["mean_low_evidence_impact"])
        count = rows[0]["sample_count"]
    elif json_path.exists():
        payload = read_json(json_path)
        values = payload["valid"]
        top = float(values["mean_top_evidence_impact"])
        low = float(values["mean_low_evidence_impact"])
        count = values["sample_count"]
    else:
        raise FileNotFoundError(f"missing fidelity metrics in {source_run}")
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.bar(["Top evidence", "Low evidence"], [top, low], color=["#0f766e", "#94a3b8"])
    ax.set_ylabel("Mean occlusion impact")
    ax.set_title(f"Validation explanation fidelity (n={count}; sensitivity diagnostic)")
    ax.grid(axis="y", alpha=0.25)
    save_figure(path)


def make_decode_figure(audits: list[dict], path: Path) -> None:
    labels = [Path(row["video"]).stem for row in audits]
    header = np.asarray([int(row["frame_count_header"]) for row in audits])
    decoded = np.asarray([int(row["frame_count_decoded"]) for row in audits])
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.bar(x - 0.18, header, width=0.36, label="Container frame count", color="#64748b")
    ax.bar(x + 0.18, decoded, width=0.36, label="Decoded frame count", color="#2563eb")
    ax.set_xticks(x, labels, rotation=45, ha="right")
    ax.set_ylabel("Frames")
    ax.set_title("Attachment 4 video decode audit")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    save_figure(path)


def write_evidence_tables(run_dir: Path, summary: list[dict], output: Path) -> None:
    mapping = read_csv(run_dir / "evidence_mapping_attachment4.csv")
    grouped = {}
    for row in mapping:
        grouped.setdefault(row["sample_id"].lstrip("'"), []).append(row)
    rows = []
    for item in summary:
        sample = item["sample_id"]
        candidates = [row for row in grouped.get(sample, []) if row.get("rank") == "1"]
        candidates.sort(key=lambda row: (MODALITIES.index(row["modality"]), row["modality"]))
        if not candidates:
            continue
        top = candidates[0]
        rows.append({
            "sample_id": sample,
            "pred_class": item["pred_class"],
            "pred_regression": item["pred_regression"],
            "main_modality": item["main_modality"],
            "evidence_modality": top["modality"],
            "impact_score": top["impact_score"],
            "start_sec": top["start_sec"],
            "end_sec": top["end_sec"],
            "frame_start": top["frame_start"],
            "frame_end": top["frame_end"],
            "text_evidence": top.get("text_evidence", ""),
        })
    fields = list(rows[0]) if rows else ["sample_id"]
    write_csv(output / "table_evidence_examples.csv", rows, fields)
    selected = rows[:6]
    lines = [r"\begin{table}[htbp]", r"\centering", r"\small", r"\caption{Attachment 4 evidence examples}", r"\label{tab:q3_evidence_examples}", r"\begin{tabular}{lrrrrrr}", r"\toprule", r"ID & Class & Regression & Modality & Impact & Time (s) & Frames \\", r"\midrule"]
    for row in selected:
        lines.append(" & ".join(latex_escape(row[key]) for key in ("sample_id", "pred_class", "pred_regression", "evidence_modality", "impact_score", "start_sec")) + "--" + latex_escape(row["end_sec"]) + " & " + latex_escape(row["frame_start"]) + "--" + latex_escape(row["frame_end"]) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    (output / "table_evidence_examples.tex").write_text("\n".join(lines), encoding="utf-8")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "sample"


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


def validation_diagnostics(model, valid, train, stats, device, batch_size: int, limit: int | None):
    """在验证集比较窗口长度和两种遮挡基线，参数只由有标签 valid 诊断。"""
    dataset = BundleDataset(valid, limit)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    means = {
        name: torch.from_numpy(np.asarray(getattr(apply_standardizer(train, stats), name), dtype=np.float32).mean(axis=(0, 1)))
        for name in MODALITIES
    }
    rows = []
    for baseline in ("zero_invalid", "train_mean"):
        for window in (3, 5, 7):
            items = []
            for batch in loader:
                batch = batch_to_device(batch, device)
                items.extend(explain_batch(model, {k: batch[k] for k in ("text", "audio", "vision", "mask")}, window=window, stride=window, top_k=3, baseline=baseline, modality_means=means))
            top = np.asarray([x["fidelity_top_mean"] for x in items], dtype=float)
            low = np.asarray([x["fidelity_low_mean"] for x in items], dtype=float)
            contrib = np.asarray([x["modality_contrib"] for x in items], dtype=float)
            rows.append({
                "baseline": baseline,
                "window": window,
                "stride": window,
                "sample_count": len(items),
                "mean_top_impact": float(top.mean()) if len(top) else 0.0,
                "mean_low_impact": float(low.mean()) if len(low) else 0.0,
                "top_minus_low": float((top - low).mean()) if len(top) else 0.0,
                "top_to_low_ratio": float(top.mean() / max(low.mean(), 1e-8)) if len(top) else 0.0,
                "mean_contrib_text": float(contrib[:, 0].mean()) if len(contrib) else 0.0,
                "mean_contrib_audio": float(contrib[:, 1].mean()) if len(contrib) else 0.0,
                "mean_contrib_vision": float(contrib[:, 2].mean()) if len(contrib) else 0.0,
            })
    selected = max(rows, key=lambda row: (row["top_minus_low"], -row["window"], row["baseline"] == "zero_invalid"))
    return rows, selected


def decode_video(path: Path) -> tuple[dict, dict[int, np.ndarray]]:
    cap = cv2.VideoCapture(str(path))
    fps_header = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    header_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    selected: dict[int, np.ndarray] = {}
    decoded = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        decoded += 1
        selected[decoded - 1] = frame
    cap.release()
    audit = {
        "video": str(path),
        "source_exists": path.exists(),
        "fps_header": fps_header,
        "frame_count_header": header_frames,
        "frame_count_decoded": decoded,
        "width": width,
        "height": height,
        "header_decoded_match": header_frames == decoded,
        "decode_status": "ok" if decoded else "read_failed",
    }
    return audit, selected


def put_label(image: np.ndarray, lines: list[str]) -> np.ndarray:
    """兼容旧接口：现在不在图像中绘制任何标签，直接返回原始帧。"""
    return image.copy()


def make_video_artifacts(run_dir: Path, output: Path) -> tuple[list[dict], list[dict], list[dict]]:
    mapping = read_csv(run_dir / "evidence_mapping_attachment4.csv")
    predictions = {row["sample_id"].lstrip("'"): row for row in read_csv(run_dir / "predictions_attachment4.csv")}
    grouped: dict[str, list[dict]] = {}
    for row in mapping:
        grouped.setdefault(row["sample_id"].lstrip("'"), []).append(row)
    keyframe_dir = output / "keyframes"
    card_dir = output / "evidence_cards"
    keyframe_dir.mkdir()
    card_dir.mkdir()
    audits: dict[str, dict] = {}
    decoded_frames: dict[str, dict[int, np.ndarray]] = {}
    anomalies: list[dict] = []
    keyframe_metadata: dict[str, dict] = {}
    card_metadata: dict[str, dict] = {}
    for rows in grouped.values():
        if rows and rows[0]["source_video"]:
            source = Path(rows[0]["source_video"])
            key = str(source)
            if key not in audits:
                audit, frames = decode_video(source)
                audits[key] = audit
                decoded_frames[key] = frames
    summary = []
    for sample_id, rows in sorted(grouped.items()):
        panels = []
        top_rows = []
        for modality in MODALITIES:
            candidates = [row for row in rows if row["modality"] == modality]
            candidates.sort(key=lambda row: int(row.get("rank", "999")))
            if not candidates:
                continue
            row = candidates[0]
            top_rows.append(row)
            source = str(row["source_video"])
            frame_start = int(float(row["frame_start"])) if row["frame_start"] else -1
            frame_end = int(float(row["frame_end"])) if row["frame_end"] else -1
            center = (frame_start + frame_end) // 2 if frame_start >= 0 and frame_end >= frame_start else -1
            available = decoded_frames.get(source, {})
            audit = audits.get(source, {})
            decoded_count = int(audit.get("frame_count_decoded", 0))
            original_center = center
            if decoded_count and center >= decoded_count:
                center = decoded_count - 1
                anomalies.append({"sample_id": sample_id, "modality": modality, "type": "frame_index_clamped_to_decoded_range", "requested_frame": original_center, "used_frame": center, "source_video": source})
            if center < 0:
                anomalies.append({"sample_id": sample_id, "modality": modality, "type": "invalid_frame_mapping", "requested_frame": original_center, "used_frame": "", "source_video": source})
            frame = available.get(center)
            if frame is None:
                anomalies.append({"sample_id": sample_id, "modality": modality, "type": "decoded_frame_unavailable", "requested_frame": original_center, "used_frame": center, "source_video": source})
                continue
            # 关键帧和解释卡只保存原始视频画面，所有解释参数进入同目录 JSON。
            frame_path = keyframe_dir / f"{safe_name(sample_id)}_{modality}_rank1.jpg"
            cv2.imwrite(str(frame_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            keyframe_metadata[frame_path.name] = {
                "sample_id": sample_id,
                "modality": modality,
                "rank": int(row.get("rank", "1")),
                "impact_score": float(row["impact_score"]),
                "start_index": int(row["start_index"]),
                "end_index": int(row["end_index"]),
                "start_sec": float(row["start_sec"]) if row["start_sec"] else None,
                "end_sec": float(row["end_sec"]) if row["end_sec"] else None,
                "requested_frame_start": frame_start,
                "requested_frame_end": frame_end,
                "used_center_frame": center,
                "fps": float(row["fps"]) if row["fps"] else None,
                "source_video": source,
                "source_type": row.get("source_type", ""),
                "text_evidence": row.get("text_evidence", ""),
                "text_time_source": row.get("text_time_source", ""),
                "mapping_status": row.get("mapping_status", ""),
                "frame_content": "original_decoded_frame_without_overlay",
            }
            resized = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
            panels.append(resized)
        if panels:
            while len(panels) < 3:
                panels.append(np.zeros_like(panels[0]))
            card_body = cv2.hconcat(panels[:3])
        else:
            card_body = np.zeros((270, 1440, 3), dtype=np.uint8)
        pred = predictions.get(sample_id, {})
        card = card_body
        card_path = card_dir / f"{safe_name(sample_id)}.png"
        cv2.imwrite(str(card_path), card)
        card_metadata[card_path.name] = {
            "sample_id": sample_id,
            "pred_class": int(pred["pred_class"]) if pred.get("pred_class") else None,
            "pred_regression": float(pred["pred_regression"]) if pred.get("pred_regression") else None,
            "main_modality": pred.get("main_modality", ""),
            "explanation_method": pred.get("explanation_method", "counterfactual_occlusion"),
            "source_video": top_rows[0]["source_video"] if top_rows else "",
            "component_keyframes": [f"{safe_name(sample_id)}_{row['modality']}_rank1.jpg" for row in top_rows],
            "evidence": [
                {
                    "modality": row["modality"],
                    "rank": int(row.get("rank", "1")),
                    "impact_score": float(row["impact_score"]),
                    "start_index": int(row["start_index"]),
                    "end_index": int(row["end_index"]),
                    "start_sec": float(row["start_sec"]) if row["start_sec"] else None,
                    "end_sec": float(row["end_sec"]) if row["end_sec"] else None,
                    "frame_start": int(float(row["frame_start"])) if row["frame_start"] else None,
                    "frame_end": int(float(row["frame_end"])) if row["frame_end"] else None,
                    "mapping_status": row.get("mapping_status", ""),
                }
                for row in top_rows
            ],
            "frame_content": "original_decoded_frames_without_overlay",
        }
        summary.append({
            "sample_id": sample_id,
            "pred_class": pred.get("pred_class", ""),
            "pred_regression": pred.get("pred_regression", ""),
            "source_video": top_rows[0]["source_video"] if top_rows else "",
            "top_evidence_count": len(top_rows),
            "main_modality": pred.get("main_modality", ""),
            "card_path": str(card_path.relative_to(output)),
            "mapping_status": ";".join(sorted(set(row.get("mapping_status", "") for row in rows))),
        })
    (keyframe_dir / "keyframes.json").write_text(json.dumps(keyframe_metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (card_dir / "evidence_cards.json").write_text(json.dumps(card_metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return list(audits.values()), summary, anomalies


def main(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    output = timestamp_dir(ROOT / "E-q" / "q_3_output")
    device = torch.device(args.device if args.device else ("cuda" if torch.cuda.is_available() else "cpu"))
    model, model_config, checkpoint_path = load_model(run_dir, device)
    stats = load_saved_standardizer(run_dir / "train_standardizer.npz")
    feature_path = ROOT / "E-q" / "dataset" / "attachment_2_feature_files" / "aligned_50.pkl"
    train = apply_standardizer(load_attachment2(feature_path, "train"), stats)
    valid = apply_standardizer(load_attachment2(feature_path, "valid"), stats)
    diagnostic_rows, selected = validation_diagnostics(model, valid, train, stats, device, args.batch_size, None if args.valid_max_samples == 0 else args.valid_max_samples)
    write_csv(output / "explanation_parameter_selection.csv", diagnostic_rows, list(diagnostic_rows[0]))
    (output / "explanation_selection.json").write_text(json.dumps({"selected": selected, "selection_rule": "maximize mean top-minus-low occlusion impact on valid; tie prefers smaller window then zero_invalid", "valid_max_samples": args.valid_max_samples}, ensure_ascii=False, indent=2), encoding="utf-8")
    audits, summary, anomalies = make_video_artifacts(run_dir, output)
    write_csv(output / "video_decode_audit.csv", audits, list(audits[0]) if audits else ["video"])
    write_csv(output / "explanation_summary.csv", summary, list(summary[0]) if summary else ["sample_id"])
    write_csv(output / "anomalies.csv", anomalies, list(anomalies[0]) if anomalies else ["sample_id", "modality", "type", "requested_frame", "used_frame", "source_video"])
    attachment4_predictions = read_csv(run_dir / "predictions_attachment4.csv")
    make_global_contribution_figure(attachment4_predictions, output / "fig_global_contribution.png")
    make_fidelity_figure(run_dir, output / "fig_fidelity_valid.png")
    make_decode_figure(audits, output / "fig_video_decode_audit.png")
    write_evidence_tables(run_dir, summary, output)
    (output / "run_config.json").write_text(json.dumps({
        "source_run_dir": str(run_dir),
        "feature_version": model_config.get("feature_version", "aligned"),
        "seed": model_config.get("seed"),
        "valid_max_samples": args.valid_max_samples,
        "batch_size": args.batch_size,
        "device": str(device),
        "video_frame_rule": "center of mapped interval, clamped to actual decoded frame range",
        "selection_rule": "maximize valid mean top-minus-low occlusion impact",
        "selected_explanation": selected,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    source_files = [checkpoint_path, run_dir / "train_standardizer.npz", run_dir / "run_config.json", run_dir / "evidence_mapping_attachment4.csv", run_dir / "predictions_attachment4.csv", feature_path]
    manifest = {
        "source_run_dir": str(run_dir),
        "source_files": {str(path): {"exists": path.exists(), "sha256": sha256_file(path) if path.exists() else ""} for path in source_files},
        "generator": str(Path(__file__).resolve()),
        "python": platform.python_version(),
        "opencv": cv2.__version__,
        "torch": torch.__version__,
        "device": str(device),
        "selected_explanation": selected,
        "video_sample_count": len(summary),
    }
    (output / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    readme = f"""# 问题三可解释性完成材料

本目录由 `scripts/q3_complete_explainability.py` 生成，来源运行目录为 `{run_dir}`。原运行目录和原始 MP4 未修改。

## 解释边界

- `modality_contrib_*` 和局部 `impact_score` 是反事实遮挡敏感性，不是人工情感原因或严格因果效应。
- 附件四无标签，本目录不报告附件四准确率、F1、MAE 或 Pearson。
- 文本的时间是 aligned 窗口的相对时间代理，不是逐词观测时间戳。
- 验证集参数选择仅使用有标签 valid；附件四只用于固定模型后的推理和视频映射。

## 文件

- `explanation_parameter_selection.csv`：窗口 3/5/7 与零无效、训练集均值两种基线的验证集诊断。
- `explanation_selection.json`：按 valid 的 top-minus-low 遮挡影响选择的固定解释参数。
- `video_decode_audit.csv`：OpenCV 实际解码 FPS、容器帧数、解码帧数和尺寸。
- `anomalies.csv`：容器帧数与实际解码范围不一致、帧号截断等异常；异常不会被静默忽略。
- `keyframes/`：每个附件四样本每个可用模态的 rank-1 原始中心关键帧；`keyframes.json` 以图片文件名为键保存全部参数。
- `evidence_cards/`：由原始关键帧组成的样本级画面；`evidence_cards.json` 以卡片文件名为键保存预测和证据参数。图片不叠加文字。
- `explanation_summary.csv`：样本卡与证据映射索引。
- `fig_global_contribution.png`：附件四三模态贡献分布，只表示模型敏感性。
- `fig_fidelity_valid.png`：有标签验证集高低证据遮挡诊断。
- `fig_video_decode_audit.png`：20 个附件四视频的容器帧数与实际解码帧数。
- `table_evidence_examples.csv/.tex`：固定顺序的证据示例及论文表格。
- `source_manifest.json`：输入文件哈希、环境版本和生成参数。
- `run_config.json`：本次解释参数、窗口选择规则和视频帧处理规则。

当前自动选择结果：baseline=`{selected['baseline']}`，window=`{selected['window']}`，stride=`{selected['stride']}`，valid 样本数=`{selected['sample_count']}`。
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    checksums = {str(path.relative_to(output)): sha256_file(path) for path in output.rglob("*") if path.is_file() and path.name != "output_checksums.json"}
    (output / "output_checksums.json").write_text(json.dumps(checksums, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "output_dir": str(output), "selected": selected, "video_samples": len(summary)}, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--valid-max-samples", type=int, default=0, help="0 表示使用完整验证集")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main(parse_args()))
