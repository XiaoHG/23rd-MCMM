"""Package the v7 prediction run and all paper-supporting explainability artifacts.

Usage:
    python scripts/q3_v7_package.py \
      --source-dir E-q/q_3_output/20260925_213047_006377600

The source run is copied into a new timestamp directory. Video frames and cards
are regenerated from the source run's final attachment-4 mapping and predictions.
No model training, parameter selection, or attachment-4 evaluation is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import q3_complete_explainability as explainability


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def timestamp_dir(parent: Path) -> Path:
    import time

    value = parent / (time.strftime("%Y%m%d_%H%M%S") + f"_{time.time_ns() % 1_000_000_000:09d}")
    value.mkdir(parents=True, exist_ok=False)
    return value


def main(args: argparse.Namespace) -> int:
    source = Path(args.source_dir).resolve()
    required = ("predictions_attachment4.csv", "evidence_mapping_attachment4.csv", "run_config.json", "validation_audit.json")
    missing = [name for name in required if not (source / name).is_file()]
    if missing:
        raise FileNotFoundError(f"source run is incomplete: {missing}")

    output = timestamp_dir(ROOT / "E-q/q_3_output")
    for item in source.iterdir():
        if item.is_file():
            shutil.copy2(item, output / item.name)

    source_config = json.loads((source / "run_config.json").read_text(encoding="utf-8"))
    model_source = Path(source_config.get("source_run_dir", source)).resolve()
    model_output = output / "model_artifacts"
    model_output.mkdir()
    model_files = ("best_model.pt", "train_standardizer.npz", "training_log.csv", "run_config.json", "run_summary.json", "input_data_summary.json")
    copied_model_files = []
    for name in model_files:
        candidate = model_source / name
        if candidate.is_file():
            shutil.copy2(candidate, model_output / name)
            copied_model_files.append(name)

    audits, summary, anomalies = explainability.make_video_artifacts(source, output)
    explainability.write_csv(output / "video_decode_audit.csv", audits, list(audits[0]) if audits else ["video"])
    explainability.write_csv(output / "explanation_summary.csv", summary, list(summary[0]) if summary else ["sample_id"])
    anomaly_fields = list(anomalies[0]) if anomalies else ["sample_id", "modality", "type", "requested_frame", "used_frame", "source_video"]
    explainability.write_csv(output / "anomalies.csv", anomalies, anomaly_fields)
    predictions = explainability.read_csv(source / "predictions_attachment4.csv")
    explainability.make_global_contribution_figure(predictions, output / "fig_global_contribution.png")
    explainability.make_fidelity_figure(source, output / "fig_fidelity_valid.png")
    explainability.make_decode_figure(audits, output / "fig_video_decode_audit.png")
    explainability.write_evidence_tables(source, summary, output)

    selected = json.loads((source / "explanation_parameter_selection.json").read_text(encoding="utf-8"))["selected"]
    keyframe_json = json.loads((output / "keyframes/keyframes.json").read_text(encoding="utf-8"))
    card_json = json.loads((output / "evidence_cards/evidence_cards.json").read_text(encoding="utf-8"))
    frame_files = sorted(path.name for path in (output / "keyframes").glob("*.jpg"))
    card_files = sorted(path.name for path in (output / "evidence_cards").glob("*.png"))
    audit = {
        "schema_version": "q3-v7-final-package-v1",
        "source_dir": str(source),
        "base_audit_passed": json.loads((source / "validation_audit.json").read_text(encoding="utf-8"))["passed"],
        "selected_explanation": selected,
        "attachment4_prediction_count": len(predictions),
        "attachment4_sample_ids_unique": len({row["sample_id"].lstrip("'") for row in predictions}) == len(predictions),
        "keyframe_count": len(frame_files),
        "keyframe_metadata_count": len(keyframe_json),
        "card_count": len(card_files),
        "card_metadata_count": len(card_json),
        "keyframe_files_match_json": set(frame_files) == set(keyframe_json),
        "card_files_match_json": set(card_files) == set(card_json),
        "all_cards_have_three_or_fewer_component_frames": all(len(item.get("component_keyframes", [])) <= 3 for item in card_json.values()),
        "model_artifacts_present": all((model_output / name).is_file() for name in ("best_model.pt", "train_standardizer.npz", "training_log.csv")),
        "video_decode_mismatch_count": sum(not item["header_decoded_match"] for item in audits),
        "attachment4_is_inference_only": True,
        "impact_score_semantics": "model_sensitivity_not_causal_truth",
    }
    audit["passed"] = all(value for key, value in audit.items() if isinstance(value, bool))
    (output / "final_package_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "package_manifest.json").write_text(json.dumps({
        "source_dir": str(source),
        "source_validation_audit": str(source / "validation_audit.json"),
        "model_source_dir": str(model_source),
        "model_artifacts": {name: {"path": str(model_output / name), "sha256": sha256(model_output / name)} for name in copied_model_files},
        "generator": str(Path(__file__).resolve()),
        "selected_explanation": selected,
        "source_prediction_sha256": sha256(source / "predictions_attachment4.csv"),
        "source_mapping_sha256": sha256(source / "evidence_mapping_attachment4.csv"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    readme = f"""# 问题三 v7 最终论文支撑包

本目录由 `{source}` 复制并补齐生成，所有预测、局部重要性、视频映射、关键帧和解释卡均来自同一 checkpoint、标准化文件和解释配置。

最终解释配置：baseline=`{selected['baseline']}`，window=`{selected['window']}`，stride=`{selected['stride']}`，top_k=`{selected.get('top_k', 3)}`。附件四仅进行推理和证据展示，不参与训练、参数选择或真实性能统计。

核心论文材料：`predictions_attachment4.csv`、`evidence_mapping_attachment4.csv`、`local_importance_valid.csv`、`local_importance_test.csv`、`local_importance_attachment4.csv`、`error_attribution_valid.csv`、`model_metrics.csv`、`fidelity_metrics.json`、`table_evidence_examples.csv`、`table_evidence_examples.tex`、`fig_global_contribution.png`、`fig_fidelity_valid.png`、`fig_video_decode_audit.png`、`fig_confusion_matrix_valid.png`、`fig_confusion_matrix_test.png`、`fig_regression_diagnostics_valid.png`、`fig_regression_diagnostics_test.png`。

可回溯视频材料：`keyframes/` 保存未叠加文字的原始解码关键帧，`keyframes/keyframes.json` 按图片文件名记录样本、模态、窗口、影响分数、时间和帧号；`evidence_cards/` 保存由三模态原始关键帧组成的样本卡片，`evidence_cards/evidence_cards.json` 保存预测和证据参数。图像不承载解释文字，解释信息以 JSON 保存。

模型复现材料：`model_artifacts/best_model.pt`、`model_artifacts/train_standardizer.npz`、`model_artifacts/training_log.csv`、原始训练配置和训练摘要。审计文件：`final_package_audit.json`、`package_manifest.json`、`video_decode_audit.csv`、`anomalies.csv`、`output_checksums.json`。视频存在容器帧数与实际解码帧数不一致时，必须结合 `mapping_precision` 和审计结果人工复核；`impact_score` 表示模型反事实敏感性，不是因果真值。
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    checksums = {str(path.relative_to(output)): sha256(path) for path in output.rglob("*") if path.is_file() and path.name != "output_checksums.json"}
    (output / "output_checksums.json").write_text(json.dumps(checksums, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "output_dir": str(output), "audit_passed": audit["passed"], "keyframes": len(frame_files), "evidence_cards": len(card_files)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    raise SystemExit(main(parser.parse_args()))
