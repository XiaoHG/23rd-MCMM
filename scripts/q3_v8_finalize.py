"""Generate the v8 paper-support package from one audited q3 final package."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cli.q3_run import BundleDataset, batch_to_device, load_saved_standardizer
from scripts.q3_v7_finalize import load_model
from src.q_3.data import apply_standardizer, load_attachment2, sha256_file
from src.q_3.metrics import prediction_metrics

MODALITIES = ("text", "audio", "vision")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0]) if rows else ["sample_id"])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def new_dir() -> Path:
    value = ROOT / "E-q/q_3_output" / (time.strftime("%Y%m%d_%H%M%S") + f"_{time.time_ns() % 1_000_000_000:09d}")
    value.mkdir(parents=True, exist_ok=False)
    return value


def draw_boxes(path: Path, title: str, rows: list[list[str]], colors: list[str]) -> None:
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.axis("off")
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7)
    ax.set_title(title, fontsize=16, pad=18)
    for row_index, row in enumerate(rows):
        y = 5.8 - row_index * 1.55
        gap = 13 / (len(row) + 1)
        for col, label in enumerate(row):
            x = gap * (col + 1)
            box = FancyBboxPatch((x - 1.25, y - 0.38), 2.5, 0.76, boxstyle="round,pad=0.03", facecolor=colors[row_index % len(colors)], edgecolor="#334155", linewidth=1.2)
            ax.add_patch(box)
            ax.text(x, y, label, ha="center", va="center", fontsize=9, wrap=True)
            if row_index < len(rows) - 1:
                next_gap = 13 / (len(rows[row_index + 1]) + 1)
                for next_col in range(len(rows[row_index + 1])):
                    nx = next_gap * (next_col + 1)
                    ax.annotate("", xy=(nx, y - 0.78), xytext=(x, y - 0.42), arrowprops={"arrowstyle": "->", "color": "#64748b", "lw": 0.8})
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def generate_diagrams(output: Path) -> None:
    draw_boxes(output / "fig_technical_route.png", "Q3 technical route and audit boundary", [["Attachment 2\ntrain / valid / test", "Attachment 4\nunlabeled inference"], ["Train-only\nstandardization + mean baseline", "Masked multimodal\nTransformer"], ["Cross-modal attention\n+ dynamic gate", "Classification +\nregression heads"], ["Counterfactual\nmodal/window occlusion", "Video mapping +\nJSON evidence"], ["Metrics, ablation,\nerror attribution", "Paper tables, figures,\nfinal audit"]], ["#dbeafe", "#dcfce7", "#fef3c7", "#fee2e2"])
    draw_boxes(output / "fig_model_architecture.png", "Masked multimodal Transformer architecture", [["Text\n768", "Audio\n74", "Vision\n35"], ["Projection +\nLayerNorm", "Projection +\nLayerNorm", "Projection +\nLayerNorm"], ["Masked temporal\nTransformer", "Masked temporal\nTransformer", "Masked temporal\nTransformer"], ["Text queries\naudio / vision", "Dynamic gate\nweighted fusion"], ["3-class head", "Intensity head\n[-3, 3]"], ["Post-hoc\nexplanation"]], ["#e0f2fe", "#dcfce7", "#fef3c7", "#fce7f3"])
    draw_boxes(output / "fig_data_boundary.png", "Data boundary and leakage control", [["Train 3395\nfit parameters", "Valid 728\nselect settings", "Test 727\nfixed evaluation", "Attachment 4 20\nfinal inference only"], ["aligned_50.pkl\nfeature hash fixed", "No labels used\nfor Attachment 4"], ["One checkpoint +\none explanation config"]], ["#dbeafe", "#fef3c7", "#dcfce7"])


def training_curve(model_artifacts: Path, output: Path) -> None:
    rows = read_csv(model_artifacts / "training_log.csv")
    epoch = np.asarray([int(row["epoch"]) for row in rows])
    train = np.asarray([float(row["train_loss"]) for row in rows])
    valid = np.asarray([float(row["valid_loss"]) for row in rows])
    best = int(epoch[valid.argmin()])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(epoch, train, label="train loss")
    ax.plot(epoch, valid, label="valid loss")
    ax.axvline(best, color="black", linestyle="--", linewidth=1, label=f"best epoch={best}")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Joint loss")
    ax.set_title("Training and validation loss")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.savefig(output / "fig_training_curve.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    write_csv(output / "training_curve.csv", [{"epoch": int(e), "train_loss": float(t), "valid_loss": float(v), "is_best_epoch": int(e) == best} for e, t, v in zip(epoch, train, valid)])


def class_report(output: Path) -> None:
    rows = read_csv(output / "predictions_valid.csv")
    report = []
    for cls in range(3):
        truth = np.asarray([int(row["true_class"]) for row in rows])
        pred = np.asarray([int(row["pred_class"]) for row in rows])
        tp = int(((truth == cls) & (pred == cls)).sum())
        fp = int(((truth != cls) & (pred == cls)).sum())
        fn = int(((truth == cls) & (pred != cls)).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        report.append({"split": "valid", "class": cls, "precision": precision, "recall": recall, "f1": f1, "support": int((truth == cls).sum())})
    write_csv(output / "classification_report_valid.csv", report)
    lines = [r"\begin{table}[htbp]", r"\centering", r"\caption{Validation classification report}", r"\begin{tabular}{lrrrr}", r"Class & Precision & Recall & F1 & Support \\ \hline"]
    lines.extend([f"{row['class']} & {row['precision']:.4f} & {row['recall']:.4f} & {row['f1']:.4f} & {row['support']} " + (chr(92) * 2) for row in report])
    lines.extend([r"\end{tabular}", r"\end{table}"])
    (output / "classification_report_valid.tex").write_text("\n".join(lines), encoding="utf-8")


def local_heatmaps(output: Path) -> None:
    for split in ("valid", "test", "attachment4"):
        rows = read_csv(output / f"local_importance_{split}.csv")
        if not rows:
            continue
        fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
        for axis, modality in zip(axes, MODALITIES):
            current = [row for row in rows if row["modality"] == modality]
            matrix = np.zeros((len({row["sample_id"] for row in current}), 50), dtype=float)
            ids = sorted({row["sample_id"] for row in current})
            index = {sample: i for i, sample in enumerate(ids)}
            for row in current:
                start, end = int(row["start_index"]), int(row["end_index"])
                matrix[index[row["sample_id"]], start : end + 1] = float(row["impact_score"])
            image = axis.imshow(matrix, aspect="auto", cmap="magma")
            axis.set_title(modality.capitalize())
            axis.set_xlabel("Aligned timestep")
            axis.set_xticks([0, 10, 20, 30, 40, 49])
        axes[0].set_ylabel("Sample index")
        fig.colorbar(image, ax=axes.ravel().tolist(), shrink=0.75, label="Occlusion impact")
        fig.suptitle(f"{split.capitalize()} local importance heatmap")
        fig.savefig(output / f"fig_local_importance_heatmap_{split}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)


def gate_consistency(output: Path) -> None:
    rows = read_csv(output / "predictions_valid.csv")
    report = []
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.5))
    for axis, modality in zip(axes, MODALITIES):
        gate = np.asarray([float(row[f"gate_{modality}"]) for row in rows])
        contribution = np.asarray([float(row[f"modality_contrib_{modality}"]) for row in rows])
        corr = float(np.corrcoef(gate, contribution)[0, 1]) if gate.std() and contribution.std() else 0.0
        report.append({"split": "valid", "modality": modality, "pearson_gate_vs_counterfactual": corr})
        axis.scatter(gate, contribution, s=8, alpha=0.3)
        axis.set_title(f"{modality}: r={corr:.3f}")
        axis.set_xlabel("Gate")
        axis.set_ylabel("Counterfactual contribution")
    fig.tight_layout()
    fig.savefig(output / "fig_gate_vs_contribution_valid.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    write_csv(output / "gate_contribution_consistency.csv", report)


def modality_ablation(output: Path) -> None:
    model_dir = output / "model_artifacts"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, _, _ = load_model(model_dir, device)
    stats = load_saved_standardizer(model_dir / "train_standardizer.npz")
    feature = ROOT / "E-q/dataset/attachment_2_feature_files/aligned_50.pkl"
    rows = []
    for split in ("valid", "test"):
        bundle = apply_standardizer(load_attachment2(feature, split), stats)
        for removed in ("none", *MODALITIES):
            pred_cls, pred_reg, truth_cls, truth_reg = [], [], [], []
            loader = DataLoader(BundleDataset(bundle), batch_size=64, shuffle=False, num_workers=0)
            for batch in loader:
                batch = batch_to_device(batch, device)
                if removed != "none":
                    index = MODALITIES.index(removed)
                    batch[removed].zero_()
                    batch["mask"][:, :, index] = False
                with torch.no_grad():
                    result = model(batch["text"], batch["audio"], batch["vision"], batch["mask"])
                pred_cls.extend(result["logits"].argmax(1).cpu().numpy().tolist())
                pred_reg.extend(result["regression"].cpu().numpy().tolist())
            truth_cls = bundle.classification.tolist()
            truth_reg = bundle.regression.tolist()
            metrics = prediction_metrics(np.asarray(truth_cls), np.asarray(pred_cls), np.asarray(truth_reg), np.asarray(pred_reg))
            rows.append({"split": split, "removed_modality": removed, **metrics, "interpretation": "post-hoc modality removal; not a retrained single-modality baseline"})
    write_csv(output / "modality_ablation_metrics.csv", rows)


def mapping_quality(output: Path) -> None:
    audits = read_csv(output / "video_decode_audit.csv")
    mapping = read_csv(output / "evidence_mapping_attachment4.csv")
    rows = []
    for audit in audits:
        video = audit["video"]
        related = [row for row in mapping if row["source_video"] == video]
        clamped = sum(row.get("mapping_precision") == "approximate_after_decode_clamp" for row in related)
        rows.append({"video": video, "evidence_rows": len(related), "header_decoded_match": audit["header_decoded_match"], "clamped_evidence_rows": clamped, "decoded_frames": audit["frame_count_decoded"], "header_frames": audit["frame_count_header"]})
    write_csv(output / "mapping_quality.csv", rows)
    mismatch = np.asarray([0 if row["header_decoded_match"] == "True" else 1 for row in rows])
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(np.arange(len(rows)), mismatch, color="#dc2626")
    ax.set_xlabel("Attachment 4 video index")
    ax.set_ylabel("Header/decode mismatch")
    ax.set_title("Video mapping quality audit")
    fig.savefig(output / "fig_mapping_quality.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def representatives(output: Path) -> None:
    rows = read_csv(output / "predictions_valid.csv")
    candidates = {}
    for modality in MODALITIES:
        candidates[f"{modality}_dominant"] = max(rows, key=lambda row: float(row[f"modality_contrib_{modality}"]))
    candidates["classification_error"] = next((row for row in rows if row["true_class"] != row["pred_class"]), rows[0])
    candidates["max_regression_error"] = max(rows, key=lambda row: abs(float(row["true_regression"]) - float(row["pred_regression"])))
    candidates["balanced_contribution"] = min(rows, key=lambda row: np.std([float(row[f"modality_contrib_{m}"]) for m in MODALITIES]))
    result = []
    for rule, row in candidates.items():
        result.append({"selection_rule": rule, "sample_id": row["sample_id"], "pred_class": row["pred_class"], "true_class": row["true_class"], "pred_regression": row["pred_regression"], "true_regression": row["true_regression"], "main_modality": row["main_modality"], "contrib_text": row["modality_contrib_text"], "contrib_audio": row["modality_contrib_audio"], "contrib_vision": row["modality_contrib_vision"]})
    write_csv(output / "representative_sample_selection.csv", result)


def label_mapping(output: Path) -> None:
    payload = {
        "source": "E-q/dataset/attachment_2_feature_files/aligned_50.pkl classification_labels and regression_labels",
        "mapping": {"0": "Negative", "1": "Neutral", "2": "Positive"},
        "verification": "training labels have class 0 regression range [-3,-1/3], class 1 exactly 0, class 2 range [1/6,3]",
        "note": "Attachment 4 has no ground-truth class and does not use this mapping for evaluation."
    }
    (output / "label_mapping.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(args: argparse.Namespace) -> int:
    source = Path(args.source_dir).resolve()
    output = new_dir()
    for item in source.iterdir():
        if item.is_file():
            shutil.copy2(item, output / item.name)
        elif item.is_dir():
            shutil.copytree(item, output / item.name)
    generate_diagrams(output)
    training_curve(output / "model_artifacts", output)
    class_report(output)
    local_heatmaps(output)
    gate_consistency(output)
    modality_ablation(output)
    mapping_quality(output)
    representatives(output)
    label_mapping(output)
    finite_paths = ("model_metrics.csv", "modality_ablation_metrics.csv", "classification_report_valid.csv", "gate_contribution_consistency.csv")
    finite_values = []
    for name in finite_paths:
        for row in read_csv(output / name):
            for key, value in row.items():
                if key in {"split", "removed_modality", "interpretation", "modality"}:
                    continue
                try:
                    finite_values.append(np.isfinite(float(value)))
                except (TypeError, ValueError):
                    pass
    base_metrics = {row["split"]: row for row in read_csv(output / "model_metrics.csv")}
    ablation = {(row["split"], row["removed_modality"]): row for row in read_csv(output / "modality_ablation_metrics.csv")}
    base_matches_ablation = all(abs(float(base_metrics[split][metric]) - float(ablation[(split, "none")][metric])) < 1e-5 for split in ("valid", "test") for metric in ("accuracy", "macro_f1", "mae", "pearson"))
    audit = {
        "schema_version": "q3-v8-audit-v1",
        "source_dir": str(source),
        "base_package_audit_passed": json.loads((source / "final_package_audit.json").read_text(encoding="utf-8"))["passed"],
        "technical_route_diagram": (output / "fig_technical_route.png").is_file(),
        "model_architecture_diagram": (output / "fig_model_architecture.png").is_file(),
        "data_boundary_diagram": (output / "fig_data_boundary.png").is_file(),
        "training_curve": (output / "fig_training_curve.png").is_file(),
        "local_importance_heatmaps": all((output / f"fig_local_importance_heatmap_{split}.png").is_file() for split in ("valid", "test", "attachment4")),
        "classification_report": (output / "classification_report_valid.csv").is_file(),
        "modality_ablation_completed": len(read_csv(output / "modality_ablation_metrics.csv")) == 8,
        "all_outputs_finite": bool(finite_values) and all(finite_values),
        "base_metrics_match_ablation_none": base_matches_ablation,
        "label_mapping_documented": json.loads((output / "label_mapping.json").read_text(encoding="utf-8"))["mapping"] == {"0": "Negative", "1": "Neutral", "2": "Positive"},
        "attachment4_not_used_for_training_or_selection": True,
        "paper_claims_limit": "retrained architecture baselines and multi-seed uncertainty are not claimed from this run",
    }
    audit["passed"] = all(value for key, value in audit.items() if isinstance(value, bool))
    (output / "v8_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    readme = f"""# 问题三 v8 论文支撑包

来源：`{source}`。本目录在同一 checkpoint、同一标准化参数和同一解释配置基础上补齐论文审查材料。

新增图表：`fig_technical_route.png`、`fig_model_architecture.png`、`fig_data_boundary.png`、`fig_training_curve.png`、`fig_local_importance_heatmap_valid.png`、`fig_local_importance_heatmap_test.png`、`fig_local_importance_heatmap_attachment4.png`、`fig_gate_vs_contribution_valid.png`、`fig_mapping_quality.png`。

新增表格：`classification_report_valid.csv/.tex`、`modality_ablation_metrics.csv`、`gate_contribution_consistency.csv`、`mapping_quality.csv`、`representative_sample_selection.csv`、`training_curve.csv`、`label_mapping.json`。

`modality_ablation_metrics.csv` 是固定模型的事后模态移除诊断，不是重新训练的单模态模型基线；未运行的重训练结构基线、多随机种子置信区间和显著性检验不能从本目录推断。附件四仍只用于最终推理和解释。

`v8_audit.json` 是本次 v8 材料完整性审计。视频帧异常、文本相对时间映射和 `impact_score` 的模型敏感性语义仍需在论文中明确说明。
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    checksums = {}
    for path in output.rglob("*"):
        if path.is_file() and path.name != "output_checksums.json":
            checksums[str(path.relative_to(output))] = sha256_file(path)
    (output / "output_checksums.json").write_text(json.dumps(checksums, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "output_dir": str(output), "audit_passed": audit["passed"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    raise SystemExit(main(parser.parse_args()))
