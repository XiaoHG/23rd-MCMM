# 问题三论文素材包

本目录由 `scripts/generate_q3_report_artifacts.py` 从 `D:\MCMM\23rd-MCMM\E-q\q_3_output\20260925_093119_520788600` 自动生成。所有指标、表格和数据图均来自该运行目录；外部论文仅用于模型结构和写作框架参考，不提供本项目数值。

## 结果边界

- 特征版本：`aligned`，输入文件哈希：`66e867aa74bc70a844e806e5571e371c9abb4a35f9e2887ce9b4d97ff2cb8fcd`。
- 数据划分：train/valid/test=3395/728/727。
- 当前模型选择依据：最低 `valid_loss`；test 仅用于固定模型后的报告。
- 解释结果是反事实遮挡敏感性，不等同于人工标注的情感原因。
- 附件四无标签，只能报告预测和证据映射，不能报告真实性能。

## 表格

- `table_data_summary.csv/.tex`：数据划分、维度、mask 和类别分布。
- `table_metrics.csv/.tex`：valid/test 的 Accuracy、Macro-F1、MAE、Pearson。
- `table_confusion_valid.csv/.tex`：验证集混淆矩阵和各类召回率。
- `table_modality_fusion.csv/.tex`：test 内部门控均值与 valid 反事实贡献均值。

## 图表

- `fig_model_framework.png`：问题三模型框架，可用于论文模型总览图。
- `fig_training_convergence.png`：训练/验证损失和最佳 epoch。
- `fig_confusion_matrix_valid.png`：验证集三分类混淆矩阵。
- `fig_regression_scatter_test.png`：test 回归真实值与预测值散点图。
- `fig_modality_contribution_valid.png`：验证集三模态反事实贡献均值及标准差。
- `fig_gate_distribution_test.png`：test 内部门控权重分布。
- `fig_explanation_fidelity_valid.png`：高/低证据窗口遮挡影响诊断。

## 写作建议

正文应按“数据契约与切分 -> 掩码时序编码 -> 跨模态交互 -> 动态融合双任务头 -> 反事实解释 -> 评价与局限性”的顺序组织。表格中的 test 指标只在模型和超参数固定后引用；不要把 `gate_*` 直接称为模态因果贡献，也不要把附件四预测写成有标签准确率。

`source_manifest.json` 保存了生成输入文件的哈希，可用于论文结果复核。
