"""生成问题三论文表格、模型框架图和结果图。

使用：
    python scripts/generate_q3_report_artifacts.py \
        --run-dir E-q/q_3_output/20260925_093119_520788600

输入：指定问题三运行目录中的 JSON/CSV 输出。
输出：E-q/q_3_output/<新时间戳>/ 下的论文表格、PNG 图、来源清单和说明文档。
该脚本只读取运行结果，不读取 test 之外的数据，也不修改原始输出目录。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODALITIES = ("text", "audio", "vision")
COLORS = {"text": "#2563eb", "audio": "#ea580c", "vision": "#16a34a"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def timestamp_dir(parent: Path) -> Path:
    now = time.localtime()
    micros = time.time_ns() % 1_000_000_000
    path = parent / (time.strftime("%Y%m%d_%H%M%S", now) + f"_{micros:09d}")
    path.mkdir(parents=True, exist_ok=False)
    return path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def latex_escape(value: object) -> str:
    text = str(value)
    replacements = {"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#", "{": r"\{", "}": r"\}"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def write_latex_table(path: Path, headers: list[str], rows: list[list[object]], caption: str, label: str) -> None:
    alignment = "l" + "r" * (len(headers) - 1)
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        rf"\caption{{{latex_escape(caption)}}}",
        rf"\label{{tab:{label}}}",
        rf"\begin{{tabular}}{{{alignment}}}",
        r"\toprule",
        " & ".join(latex_escape(x) for x in headers) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(latex_escape(x) for x in row) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def save_figure(path: Path) -> None:
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


def make_training_figure(log: list[dict[str, str]], path: Path) -> None:
    epochs = np.array([int(x["epoch"]) for x in log])
    train = np.array([float(x["train_loss"]) for x in log])
    valid = np.array([float(x["valid_loss"]) for x in log])
    best = int(epochs[np.argmin(valid)])
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.plot(epochs, train, marker="o", ms=3, lw=2, label="Train loss", color="#2563eb")
    ax.plot(epochs, valid, marker="o", ms=3, lw=2, label="Validation loss", color="#dc2626")
    ax.axvline(best, ls="--", lw=1.2, color="#111827", label=f"Best validation epoch = {best}")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Joint loss")
    ax.set_title("Training convergence and model selection")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    save_figure(path)


def confusion_matrix(rows: list[dict[str, str]]) -> np.ndarray:
    matrix = np.zeros((3, 3), dtype=int)
    for row in rows:
        matrix[int(row["true_class"]), int(row["pred_class"])] += 1
    return matrix


def make_confusion_figure(rows: list[dict[str, str]], path: Path) -> None:
    matrix = confusion_matrix(rows)
    row_percent = matrix / np.maximum(matrix.sum(axis=1, keepdims=True), 1) * 100
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    image = ax.imshow(row_percent, cmap="Blues", vmin=0, vmax=100)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{matrix[i, j]}\n({row_percent[i, j]:.1f}%)", ha="center", va="center", color="white" if row_percent[i, j] > 55 else "#111827", fontsize=9)
    ax.set_xticks(range(3), ["0", "1", "2"])
    ax.set_yticks(range(3), ["0", "1", "2"])
    ax.set_xlabel("Predicted class")
    ax.set_ylabel("True class")
    ax.set_title("Validation confusion matrix")
    fig.colorbar(image, ax=ax, label="Row percentage (%)", fraction=0.046)
    save_figure(path)


def make_regression_figure(rows: list[dict[str, str]], path: Path) -> None:
    y = np.array([float(x["true_regression"]) for x in rows])
    pred = np.array([float(x["pred_regression"]) for x in rows])
    fig, ax = plt.subplots(figsize=(5.8, 4.8))
    ax.scatter(y, pred, s=13, alpha=0.35, color="#7c3aed", edgecolors="none")
    ax.plot([-3, 3], [-3, 3], "--", color="#111827", lw=1.2, label="Ideal prediction")
    ax.set_xlim(-3.05, 3.05)
    ax.set_ylim(-3.05, 3.05)
    ax.set_xlabel("True intensity")
    ax.set_ylabel("Predicted intensity")
    ax.set_title("Test-set regression calibration")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    save_figure(path)


def make_modality_figure(rows: list[dict[str, str]], path: Path) -> None:
    values = np.array([[float(x[f"modality_contrib_{m}"]) for m in MODALITIES] for x in rows])
    means = values.mean(axis=0)
    stds = values.std(axis=0)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.bar(["Text", "Audio", "Vision"], means, yerr=stds, capsize=4, color=[COLORS[m] for m in MODALITIES], alpha=0.85)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Mean normalized counterfactual contribution")
    ax.set_title("Validation modality contribution")
    ax.grid(axis="y", alpha=0.25)
    save_figure(path)


def make_gate_figure(rows: list[dict[str, str]], path: Path) -> None:
    values = np.array([[float(x[f"gate_{m}"]) for m in MODALITIES] for x in rows])
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    ax.boxplot([values[:, i] for i in range(3)], tick_labels=["Text", "Audio", "Vision"], patch_artist=True, boxprops={"facecolor": "#dbeafe"}, medianprops={"color": "#111827"})
    ax.set_ylabel("Internal gate weight")
    ax.set_title("Test-set dynamic gate distribution")
    ax.grid(axis="y", alpha=0.25)
    save_figure(path)


def make_fidelity_figure(rows: list[dict[str, str]], path: Path) -> None:
    top = np.array([float(x["fidelity_top_mean"]) for x in rows])
    low = np.array([float(x["fidelity_low_mean"]) for x in rows])
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.bar(["Top evidence windows", "Low evidence windows"], [top.mean(), low.mean()], yerr=[top.std(), low.std()], capsize=4, color=["#0f766e", "#94a3b8"])
    ax.set_ylabel("Mean occlusion impact")
    ax.set_title("Explanation fidelity diagnostic on validation subset")
    ax.grid(axis="y", alpha=0.25)
    save_figure(path)


def make_framework_figure(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")
    boxes = [
        (0.4, 5.3, 2.0, 0.9, "Aligned input\ntext / audio / vision", "#dbeafe"),
        (0.4, 3.7, 2.0, 0.9, "Validity mask\n[ N, 50, 3 ]", "#ffedd5"),
        (3.0, 5.2, 2.1, 1.1, "Modality projection\nLinear + LayerNorm", "#dcfce7"),
        (3.0, 3.6, 2.1, 1.1, "Mask-aware temporal\nTransformer encoders", "#dcfce7"),
        (5.9, 4.4, 2.1, 1.1, "Cross-modal response\nText <- Audio/Vision", "#fef3c7"),
        (8.7, 5.2, 2.2, 1.1, "Dynamic gated fusion\nmasked modality weights", "#fce7f3"),
        (8.7, 3.6, 2.2, 1.1, "Dual-task heads\nclass + regression", "#fce7f3"),
        (5.9, 1.4, 2.1, 1.1, "Counterfactual occlusion\nmodality / local windows", "#ede9fe"),
        (8.7, 1.4, 2.2, 1.1, "Evidence mapping\ntext / seconds / frames", "#ede9fe"),
    ]
    for x, y, w, h, label, color in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, fc=color, ec="#334155", lw=1.2, joinstyle="round"))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=9, color="#111827")
    arrows = [((2.4, 5.75), (3.0, 5.75)), ((2.4, 4.15), (3.0, 4.15)), ((5.1, 5.75), (5.9, 4.95)), ((5.1, 4.15), (5.9, 4.95)), ((8.0, 4.95), (8.7, 5.75)), ((9.8, 5.2), (9.8, 4.7)), ((8.7, 4.15), (8.0, 2.0)), ((8.0, 2.0), (8.7, 1.95))]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.5, "color": "#475569"})
    ax.text(6.0, 6.65, "Question 3: Mask-aware multimodal sentiment prediction and explanation", ha="center", fontsize=14, weight="bold")
    ax.text(6.0, 0.45, "Outputs: polarity, intensity, modality contribution, local evidence and fidelity diagnostics", ha="center", fontsize=10, color="#475569")
    save_figure(path)


def build_tables(config: dict, summary: dict, input_summary: dict, metrics: list[dict[str, str]], valid_rows: list[dict[str, str]], test_rows: list[dict[str, str]], output: Path) -> None:
    data_rows = []
    splits = input_summary.get("splits", {})
    for name in ("train", "valid", "test"):
        item = splits[name]
        data_rows.append({"split": name, "samples": item["sample_count"], "text_shape": str(item["feature_shapes"]["text"]), "audio_shape": str(item["feature_shapes"]["audio"]), "vision_shape": str(item["feature_shapes"]["vision"]), "mask_dtype": item["mask_dtype"], "class_distribution": json.dumps(item["classification_distribution"], ensure_ascii=False)})
    fields = ["split", "samples", "text_shape", "audio_shape", "vision_shape", "mask_dtype", "class_distribution"]
    write_csv(output / "table_data_summary.csv", data_rows, fields)
    write_latex_table(output / "table_data_summary.tex", ["Split", "Samples", "Text shape", "Audio shape", "Vision shape", "Mask", "Class counts"], [[r[x] for x in fields] for r in data_rows], "Data split and feature shape summary", "q3_data_summary")

    metric_rows = []
    for row in metrics:
        metric_rows.append({"split": row["split"], "accuracy": f"{float(row['accuracy']):.4f}", "macro_f1": f"{float(row['macro_f1']):.4f}", "mae": f"{float(row['mae']):.4f}", "pearson": f"{float(row['pearson']):.4f}"})
    mf = ["split", "accuracy", "macro_f1", "mae", "pearson"]
    write_csv(output / "table_metrics.csv", metric_rows, mf)
    write_latex_table(output / "table_metrics.tex", ["Split", "Accuracy", "Macro-F1", "MAE", "Pearson"], [[r[x] for x in mf] for r in metric_rows], "Question 3 prediction metrics", "q3_metrics")

    matrix = confusion_matrix(valid_rows)
    cm_rows = [{"true_class": i, "pred_0": matrix[i, 0], "pred_1": matrix[i, 1], "pred_2": matrix[i, 2], "recall": f"{matrix[i, i] / max(matrix[i].sum(), 1):.4f}"} for i in range(3)]
    cf = ["true_class", "pred_0", "pred_1", "pred_2", "recall"]
    write_csv(output / "table_confusion_valid.csv", cm_rows, cf)
    write_latex_table(output / "table_confusion_valid.tex", ["True class", "Pred 0", "Pred 1", "Pred 2", "Recall"], [[r[x] for x in cf] for r in cm_rows], "Validation confusion matrix and class recall", "q3_confusion_valid")

    gate_values = {m: float(np.mean([float(r[f"gate_{m}"]) for r in test_rows])) for m in MODALITIES}
    contrib_values = {m: float(np.mean([float(r[f"modality_contrib_{m}"]) for r in read_csv(Path(config["_explanations_path"]))])) for m in MODALITIES}
    fusion_rows = [{"quantity": "Mean test gate", **{m: f"{gate_values[m]:.4f}" for m in MODALITIES}}, {"quantity": "Mean valid counterfactual contribution", **{m: f"{contrib_values[m]:.4f}" for m in MODALITIES}}]
    ff = ["quantity", *MODALITIES]
    write_csv(output / "table_modality_fusion.csv", fusion_rows, ff)
    write_latex_table(output / "table_modality_fusion.tex", ["Quantity", "Text", "Audio", "Vision"], [[r[x] for x in ff] for r in fusion_rows], "Internal gates and counterfactual contributions", "q3_modality_fusion")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    required = ["run_config.json", "run_summary.json", "input_data_summary.json", "model_metrics.csv", "training_log.csv", "predictions_valid.csv", "predictions_test.csv", "explanations_valid.csv", "fidelity_metrics.csv"]
    missing = [name for name in required if not (run_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"运行目录缺少文件：{missing}")
    config = read_json(run_dir / "run_config.json")
    summary = read_json(run_dir / "run_summary.json")
    input_summary = read_json(run_dir / "input_data_summary.json")
    metrics = read_csv(run_dir / "model_metrics.csv")
    log = read_csv(run_dir / "training_log.csv")
    valid_rows = read_csv(run_dir / "predictions_valid.csv")
    test_rows = read_csv(run_dir / "predictions_test.csv")
    explanations = read_csv(run_dir / "explanations_valid.csv")
    output_root = args.output_root.resolve() if args.output_root else run_dir.parent
    output = timestamp_dir(output_root)
    config["_explanations_path"] = str(run_dir / "explanations_valid.csv")
    build_tables(config, summary, input_summary, metrics, valid_rows, test_rows, output)
    make_training_figure(log, output / "fig_training_convergence.png")
    make_confusion_figure(valid_rows, output / "fig_confusion_matrix_valid.png")
    make_regression_figure(test_rows, output / "fig_regression_scatter_test.png")
    make_modality_figure(explanations, output / "fig_modality_contribution_valid.png")
    make_gate_figure(test_rows, output / "fig_gate_distribution_test.png")
    make_fidelity_figure(explanations, output / "fig_explanation_fidelity_valid.png")
    make_framework_figure(output / "fig_model_framework.png")
    source_files = [run_dir / name for name in required if (run_dir / name).exists()]
    manifest = {"source_run_dir": str(run_dir), "source_files": {path.name: {"sha256": sha256_file(path), "bytes": path.stat().st_size} for path in source_files}, "generator": str(Path(__file__).resolve()), "feature_sha256": config.get("feature_sha256"), "metrics_are_from": "specified run directory only"}
    (output / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    report = f"""# 问题三论文素材包\n\n本目录由 `scripts/generate_q3_report_artifacts.py` 从 `{run_dir}` 自动生成。所有指标、表格和数据图均来自该运行目录；外部论文仅用于模型结构和写作框架参考，不提供本项目数值。\n\n## 结果边界\n\n- 特征版本：`{config.get('feature_version')}`，输入文件哈希：`{config.get('feature_sha256')}`。\n- 数据划分：train/valid/test={config.get('train_count')}/{config.get('valid_count')}/{config.get('test_count')}。\n- 当前模型选择依据：最低 `valid_loss`；test 仅用于固定模型后的报告。\n- 解释结果是反事实遮挡敏感性，不等同于人工标注的情感原因。\n- 附件四无标签，只能报告预测和证据映射，不能报告真实性能。\n\n## 表格\n\n- `table_data_summary.csv/.tex`：数据划分、维度、mask 和类别分布。\n- `table_metrics.csv/.tex`：valid/test 的 Accuracy、Macro-F1、MAE、Pearson。\n- `table_confusion_valid.csv/.tex`：验证集混淆矩阵和各类召回率。\n- `table_modality_fusion.csv/.tex`：test 内部门控均值与 valid 反事实贡献均值。\n\n## 图表\n\n- `fig_model_framework.png`：问题三模型框架，可用于论文模型总览图。\n- `fig_training_convergence.png`：训练/验证损失和最佳 epoch。\n- `fig_confusion_matrix_valid.png`：验证集三分类混淆矩阵。\n- `fig_regression_scatter_test.png`：test 回归真实值与预测值散点图。\n- `fig_modality_contribution_valid.png`：验证集三模态反事实贡献均值及标准差。\n- `fig_gate_distribution_test.png`：test 内部门控权重分布。\n- `fig_explanation_fidelity_valid.png`：高/低证据窗口遮挡影响诊断。\n\n## 写作建议\n\n正文应按“数据契约与切分 -> 掩码时序编码 -> 跨模态交互 -> 动态融合双任务头 -> 反事实解释 -> 评价与局限性”的顺序组织。表格中的 test 指标只在模型和超参数固定后引用；不要把 `gate_*` 直接称为模态因果贡献，也不要把附件四预测写成有标签准确率。\n\n`source_manifest.json` 保存了生成输入文件的哈希，可用于论文结果复核。\n"""
    (output / "README.md").write_text(report, encoding="utf-8")
    print(json.dumps({"status": "completed", "output_dir": str(output), "source_run_dir": str(run_dir), "figures": 7, "table_files": 8}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
