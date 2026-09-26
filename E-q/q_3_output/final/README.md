# 问题三 v7 最终论文支撑包

本目录由 `D:\MCMM\23rd-MCMM\E-q\q_3_output\20260925_213047_006377600` 复制并补齐生成，所有预测、局部重要性、视频映射、关键帧和解释卡均来自同一 checkpoint、标准化文件和解释配置。

最终解释配置：baseline=`train_mean`，window=`7`，stride=`7`，top_k=`3`。附件四仅进行推理和证据展示，不参与训练、参数选择或真实性能统计。

核心论文材料：`predictions_attachment4.csv`、`evidence_mapping_attachment4.csv`、`local_importance_valid.csv`、`local_importance_test.csv`、`local_importance_attachment4.csv`、`error_attribution_valid.csv`、`model_metrics.csv`、`fidelity_metrics.json`、`table_evidence_examples.csv`、`table_evidence_examples.tex`、`fig_global_contribution.png`、`fig_fidelity_valid.png`、`fig_video_decode_audit.png`、`fig_confusion_matrix_valid.png`、`fig_confusion_matrix_test.png`、`fig_regression_diagnostics_valid.png`、`fig_regression_diagnostics_test.png`。

可回溯视频材料：`keyframes/` 保存未叠加文字的原始解码关键帧，`keyframes/keyframes.json` 按图片文件名记录样本、模态、窗口、影响分数、时间和帧号；`evidence_cards/` 保存由三模态原始关键帧组成的样本卡片，`evidence_cards/evidence_cards.json` 保存预测和证据参数。图像不承载解释文字，解释信息以 JSON 保存。

模型复现材料：`model_artifacts/best_model.pt`、`model_artifacts/train_standardizer.npz`、`model_artifacts/training_log.csv`、原始训练配置和训练摘要。审计文件：`final_package_audit.json`、`package_manifest.json`、`video_decode_audit.csv`、`anomalies.csv`、`output_checksums.json`。视频存在容器帧数与实际解码帧数不一致时，必须结合 `mapping_precision` 和审计结果人工复核；`impact_score` 表示模型反事实敏感性，不是因果真值。
