# 问题三最终结果包说明

本目录是问题三“可解释性多模态情感预测”的一次完整结果包。它由附件二的 `aligned_50.pkl` 训练得到的模型生成验证集、测试集结果，并使用同一模型对附件四进行最终推理和证据定位。

本 README 的目标是让每个文件都能被单独理解、复核和用于论文写作。论文中引用数值时，应以本目录的 CSV/JSON 为原始证据；图片用于展示，不能替代表格数据。

## 1. 结果边界与核心结论

### 1.1 数据使用边界

| 数据 | 样本数 | 用途 | 是否参与训练、调参或早停 |
|---|---:|---|---|
| 附件二 train | 3395 | 拟合模型参数、训练集标准化参数 | 是 |
| 附件二 valid | 728 | 选择最佳 checkpoint、解释参数和报告验证性能 | 用于验证/选择 |
| 附件二 test | 727 | 固定模型后的最终有标签测试评估 | 否 |
| 附件四 | 20 | 最终预测、模态贡献和证据展示 | 否，仅推理 |

附件四没有真实标签，因此 `predictions_attachment4.csv` 只能报告预测结果和解释结果，不能计算 Accuracy、F1、MAE、Pearson，也不能声称附件四预测正确。

### 1.2 标签映射

`label_mapping.json` 给出分类标签：`0=Negative`、`1=Neutral`、`2=Positive`。连续回归标签位于约 `[-3,3]`，分类标签由数据集提供的情感区间生成。附件四没有真实标签，不使用该映射做评估。

### 1.3 本次运行的主要有标签结果

来自 `model_metrics.csv`：

| 划分 | Accuracy | Macro-F1 | MAE | Pearson |
|---|---:|---:|---:|---:|
| valid | 0.607143 | 0.547565 | 0.652097 | 0.580993 |
| test | 0.672627 | 0.595023 | 0.679413 | 0.625911 |

这些是当前一次固定随机种子运行的结果，不是多随机种子均值，不应写成统计显著性结论或置信区间结论。

### 1.4 解释结果的正确含义

- `impact_score` 是对输入窗口进行反事实遮挡后，模型输出发生的变化，表示**模型敏感性**。
- 它不是因果效应、真实情绪成因，也不是人类可解释性的绝对量尺。
- 门控值表示模型内部融合权重，不能直接当作证据重要性；应结合 `modality_contrib_*` 和局部遮挡结果解释。
- 文本时间是对齐特征窗口映射出的相对时间，不是逐词的精确语音时间戳。
- 图片中的关键帧保留原始解码帧，不在视频内容上叠加文字；元数据分别保存在 `keyframes/keyframes.json` 和 `evidence_cards/evidence_cards.json`。

## 2. 目录结构

```text
20260925_225153_740084700/
├─ README.md                         本说明
├─ model_artifacts/                  模型、标准化器、训练日志和训练摘要
├─ evidence_cards/                   附件四每个样本的证据卡 PNG 和 JSON 元数据
├─ keyframes/                        附件四每个样本三种模态的关键帧 JPG 和 JSON 元数据
├─ *.csv                             预测、评估、解释、映射和审计明细
├─ *.json                            运行配置、数据清单、审计、校验和摘要
├─ *.png                             论文图表
├─ classification_report_valid.tex  验证集分类表的 LaTeX 片段
├─ table_evidence_examples.tex       附件四代表性证据表的 LaTeX 片段
└─ train_mean_baseline.npz           训练集均值反事实基线
```

文件名中的 `valid`、`test`、`attachment4` 分别表示验证集、测试集和附件四。`attachment4` 结果不能与有标签性能结果混用。

## 3. CSV 文件说明

### 3.1 性能结果与分类明细

#### `model_metrics.csv`

每行一个数据划分，是论文性能主表的数据源。

| 字段 | 含义 | 论文用法 |
|---|---|---|
| `split` | `valid` 或 `test` | 区分模型选择结果与最终有标签评估 |
| `accuracy` | 分类准确率，正确分类数/样本数 | 报告分类总体正确率 |
| `macro_f1` | 三个类别 F1 的宏平均 | 反映类别不均衡下的整体分类质量 |
| `mae` | 连续情感强度预测的平均绝对误差 | 回归性能，越小越好 |
| `pearson` | 预测强度与真实强度的 Pearson 相关系数 | 反映强度排序/线性相关程度 |

论文写法：表格中同时报告 Accuracy、Macro-F1、MAE、Pearson，并明确 valid 用于选择、test 只在模型固定后评估。

#### `classification_report_valid.csv`

验证集的类别级结果，当前包括 Negative、Neutral、Positive 三行。

| 字段 | 含义 |
|---|---|
| `split` | 数据划分，此处为 `valid` |
| `class` | 数字类别，需按 `label_mapping.json` 翻译 |
| `precision` | 预测为该类的样本中真正属于该类的比例 |
| `recall` | 该类真实样本被识别出的比例 |
| `f1` | precision 与 recall 的调和平均 |
| `support` | 该类真实样本数量 |

本次 valid 的 Neutral Recall 约为 `0.2337`，可用于论文中讨论中性类别的识别困难，但不能仅凭该数字断言具体原因。

#### `classification_report_valid.tex`

`classification_report_valid.csv` 的 LaTeX 表格版本。论文需要直接插入验证集类别表格时使用；若重新生成结果，应以 CSV 为准并重新生成该文件。

#### `error_attribution_valid.csv`

验证集逐样本误差归因明细，用于错误分析，不是新的性能指标。

| 字段 | 含义 |
|---|---|
| `sample_id` | 样本唯一标识 |
| `true_class` / `pred_class` | 真实类别和预测类别 |
| `classification_error` | 是否分类错误，通常为 `0/1` |
| `true_regression` / `pred_regression` | 真实与预测连续情感强度 |
| `absolute_regression_error` | 两者绝对差 |
| `main_modality` | 该样本归一化反事实贡献最大的模态 |
| `error_group` | 如 `correct_classification` 或错误分组标签 |

论文用法：从该文件筛选分类正确但回归误差大、分类错误、文本/音频/视觉主导的案例，解释模型在哪些样本上失效。不要把 `main_modality` 写成真实情绪来源。

### 3.2 预测结果

#### `predictions_valid.csv`、`predictions_test.csv`

逐样本预测和解释字段。两者字段相同，且都有真实标签字段。

| 字段 | 含义 |
|---|---|
| `sample_id` | 样本唯一标识 |
| `split` | 数据划分 |
| `pred_class` | 预测类别，按 `label_mapping.json` 翻译 |
| `pred_regression` | 预测连续情感强度 |
| `gate_text`, `gate_audio`, `gate_vision` | 模型融合模块的内部门控值 |
| `modality_score_text/audio/vision` | 门控或模态评分的中间得分 |
| `modality_contrib_text/audio/vision` | 归一化反事实模态贡献，三者通常和为 1 |
| `main_modality` | 贡献最大的模态 |
| `fidelity_top_mean` | Top 证据窗口的平均遮挡影响 |
| `fidelity_low_mean` | 低重要性窗口的平均遮挡影响 |
| `explanation_method` | 解释方法，此处为 `counterfactual_occlusion` |
| `explanation_baseline` | 遮挡替换基线，此处为 `train_mean` |
| `explanation_window` | 一个解释窗口包含的对齐位置数，此处为 7 |
| `explanation_stride` | 窗口滑动步长，此处为 7 |
| `true_class` | 真实类别，仅 valid/test 有 |
| `true_regression` | 真实连续强度，仅 valid/test 有 |

论文用法：`predictions_valid.csv` 和 `predictions_test.csv` 用于误差分析、模态贡献统计和样例选择；主性能数值仍以 `model_metrics.csv` 为准。门控和反事实贡献必须分开讨论。

#### `predictions_attachment4.csv`

附件四的 20 条最终预测，字段与有标签预测文件基本相同，但没有 `true_class`、`true_regression`。其余字段的含义完全相同。

论文用法：报告附件四的预测类别、连续强度、主导模态、Top 证据和解释配置；不能报告附件四 Accuracy、F1、MAE 或 Pearson。

#### `explanation_summary.csv`

附件四解释结果的简要索引，每行对应一个附件四样本，适合快速生成样本清单或检查证据卡是否齐全。

| 字段 | 含义 |
|---|---|
| `sample_id` | 附件四样本编号 |
| `pred_class` | 预测类别 |
| `pred_regression` | 预测连续情感强度 |
| `source_video` | 对应原始视频路径 |
| `top_evidence_count` | 该样本保存的 Top 证据数量 |
| `main_modality` | 归一化反事实贡献最大的模态 |
| `card_path` | 证据卡相对路径，如 `evidence_cards/01.png` |
| `mapping_status` | 证据是否成功映射到视频 |

论文用法：用于正文附件四结果概览和证据卡索引；若需要具体窗口、秒、帧号和文本，应继续查 `evidence_mapping_attachment4.csv`，不能只依据本摘要表。

### 3.3 模态贡献与消融

#### `modality_contribution_summary.csv`

对每个划分、每种模态汇总反事实贡献。

| 字段 | 含义 |
|---|---|
| `split` | `valid`、`test` 或 `attachment4` |
| `modality` | `text`、`audio`、`vision` |
| `sample_count` | 参与统计的样本数 |
| `mean_contribution` | 平均归一化反事实贡献 |
| `std_contribution` | 贡献标准差 |
| `median_contribution` | 贡献中位数 |

论文用法：制作模态贡献柱状图和汇总表。当前有标签数据中，文本平均贡献约 `0.565--0.572`，音频约 `0.242--0.245`，视觉约 `0.183--0.194`。这说明模型对文本输入更敏感，不等于文本在真实情绪形成中必然最重要。

#### `modality_ablation_metrics.csv`

固定模型的后验模态移除诊断。`removed_modality=none` 是完整模型；其余行把某模态替换/遮挡后直接推理。

| 字段 | 含义 |
|---|---|
| `split` | valid 或 test |
| `removed_modality` | 移除的模态，`none/text/audio/vision` |
| `accuracy`, `macro_f1`, `mae`, `pearson` | 移除后重新计算的指标 |
| `interpretation` | 对该行统计性质的说明 |

重要：这不是重新训练的单模态基线。论文中应称为“固定模型的后验模态移除诊断”，用于判断当前融合模型对某模态的依赖程度，不能写成单模态模型性能比较。

#### `gate_contribution_consistency.csv`

比较门控值与反事实贡献的一致性。

| 字段 | 含义 |
|---|---|
| `split` | 当前为 valid |
| `modality` | 被比较的模态 |
| `pearson_gate_vs_counterfactual` | 门控值与反事实贡献的 Pearson 相关系数 |

本次 text/audio/vision 相关系数分别约为 `0.1050/0.0349/0.0061`，相关性较弱。因此论文必须说明：门控值不能替代反事实贡献解释。

### 3.4 局部证据与时间映射

#### `local_importance_valid.csv`、`local_importance_test.csv`、`local_importance_attachment4.csv`

逐样本、逐模态、逐窗口的遮挡影响，是热力图和证据排序的原始数据。

| 字段 | 含义 |
|---|---|
| `sample_id` | 样本标识 |
| `split` | 所属划分 |
| `modality` | 文本、音频或视觉 |
| `start_index`, `end_index` | 对齐序列窗口的起止位置，不是视频帧号 |
| `impact_score` | 遮挡窗口后模型输出变化的非负影响分数 |
| `is_top_k` | 是否属于该样本的 Top-k 证据窗口 |

论文用法：绘制三模态局部重要性热力图，或筛选 `is_top_k=True` 的窗口进入证据表。解释分数描述模型敏感性，不应解释成因果贡献。

#### `evidence_mapping_valid.csv`、`evidence_mapping_test.csv`、`evidence_mapping_attachment4.csv`

将 Top 证据窗口映射回原始视频和文本证据。

| 字段 | 含义 |
|---|---|
| `sample_id` | 样本标识 |
| `modality` | 证据所属模态 |
| `rank` | 该模态证据排序名次 |
| `start_index`, `end_index` | 对齐特征窗口位置 |
| `impact_score` | 对应窗口的模型敏感性 |
| `source_video` | 原始视频路径 |
| `source_type` | 视频来源类型，如附件一或附件四视频 |
| `start_sec`, `end_sec` | 映射后的相对时间，秒 |
| `frame_start`, `frame_end` | 映射到视频的起止帧 |
| `fps` | 用于帧/时间换算的帧率 |
| `text_evidence` | 对齐到该样本的原始文本证据；音频/视觉可能为空 |
| `text_time_source` | 文本时间来源说明，当前为原始文本加对齐相对窗口 |
| `source_exists` | 视频源文件是否存在 |
| `mapping_precision` | 当前主要为 `decoded_frame_range` |
| `mapping_status` | 如 `mapped_to_video`、`relative_window_only_source_video_missing` |

论文用法：该文件是从数值证据回到视频/文本的关键桥梁。正文可引用样例的时间段、帧号和文本；必须同时披露 `mapping_status`，不能把缺少源视频的相对窗口说成已精确定位。

#### `mapping_quality.csv`

逐视频的映射质量审计。

| 字段 | 含义 |
|---|---|
| `video` | 视频路径 |
| `evidence_rows` | 该视频对应的证据行数 |
| `header_decoded_match` | 容器声明帧数是否等于实际解码帧数 |
| `clamped_evidence_rows` | 因超出实际帧范围而被截断的证据行数 |
| `decoded_frames` | 实际解码帧数 |
| `header_frames` | 视频容器声明帧数 |

#### `anomalies.csv`

证据帧异常记录，字段为 `sample_id`、`modality`、`type`、`requested_frame`、`used_frame`、`source_video`。本次文件仅有表头，表示没有被记录的帧替换异常；这不等于所有视频容器帧数都一致，容器/解码差异仍看 `video_decode_audit.csv`。

#### `video_decode_audit.csv`

附件四视频解码审计。

| 字段 | 含义 |
|---|---|
| `video` | 视频路径 |
| `source_exists` | 文件是否存在 |
| `fps_header` | 容器声明帧率 |
| `frame_count_header` | 容器声明帧数 |
| `frame_count_decoded` | 实际成功解码帧数 |
| `width`, `height` | 视频分辨率 |
| `header_decoded_match` | 两种帧数是否一致 |
| `decode_status` | 解码状态，如 `ok` |

本次有 16 个视频的声明帧数与实际解码帧数不一致。论文应说明实际证据映射以成功解码帧为准，并将该现象作为数据质量审计结果，而不是模型性能结果。

### 3.5 证据样例与训练过程

#### `representative_sample_selection.csv`

代表性有标签样本选择表。

| 字段 | 含义 |
|---|---|
| `selection_rule` | 样本选择规则，如 text/audio/vision dominant 或错误案例 |
| `sample_id` | 样本标识 |
| `pred_class`, `true_class` | 预测和真实类别 |
| `pred_regression`, `true_regression` | 预测和真实强度 |
| `main_modality` | 反事实贡献最大的模态 |
| `contrib_text/audio/vision` | 三模态归一化贡献 |

论文用法：选择“主导模态正确案例”和“主导模态导致的失败案例”，构造定性分析表。不要把样本选择结果当成总体统计。

#### `table_evidence_examples.csv`

附件四论文表格的精选证据样例。

| 字段 | 含义 |
|---|---|
| `sample_id` | 附件四样本编号 |
| `pred_class` | 预测类别 |
| `pred_regression` | 预测强度 |
| `main_modality` | 全局主导模态 |
| `evidence_modality` | 当前展示的证据模态 |
| `impact_score` | 证据窗口影响 |
| `start_sec`, `end_sec` | 证据时间段 |
| `frame_start`, `frame_end` | 对应视频帧范围 |
| `text_evidence` | 可读文本证据 |

#### `table_evidence_examples.tex`

`table_evidence_examples.csv` 的 LaTeX 表格片段，可直接复制进论文表格环境；正式提交前检查字体、列宽和长文本换行。

#### `training_curve.csv`

训练过程逐 epoch 日志。

| 字段 | 含义 |
|---|---|
| `epoch` | 训练轮次 |
| `train_loss` | 训练集联合损失 |
| `valid_loss` | 验证集联合损失 |
| `is_best_epoch` | 是否为验证损失最优轮次 |

该文件用于绘制训练曲线、说明收敛和选择 checkpoint。详细训练批次数、耗时和参数范数见 `model_artifacts/training_log.csv`。

## 4. JSON、模型和校验文件

### 4.1 顶层运行配置与数据清单

#### `run_config.json`

记录本次解释打包使用的模型、数据和解释参数。主要字段为：`mode`（运行模式）、`source_run_dir`（源运行目录）、`checkpoint_sha256`（模型权重哈希）、`standardizer_sha256`（标准化器哈希）、`feature_path/feature_sha256`（输入特征路径和哈希）、`feature_version`（此处为 aligned）、`seed`、`device`、`baseline`、`baseline_space`、`window`、`stride`、`top_k`、各划分样本数，以及 `attachment4_used_for`。其中 `baseline=train_mean` 表示用训练集均值替换被遮挡窗口。

论文用法：说明解释参数在 valid 上确定后固定用于 test 和附件四；附件四没有参与参数选择。

#### `input_manifest.json`

记录关键输入文件是否存在、字节数和 SHA-256。用于证明模型权重、标准化器、运行配置和 `aligned_50.pkl` 的具体版本。

#### `label_mapping.json`

记录类别映射、标签来源和验证规则。论文中的类别名称、混淆矩阵坐标和分类报告必须按此文件解释。

#### `environment.json`

记录 Python、Windows、PyTorch、NumPy、OpenCV、Matplotlib 和计算设备版本。论文方法部分可据此写软件环境。

### 4.2 解释参数和审计

#### `explanation_parameter_selection.json`

记录解释窗口候选方案及选择过程。候选项含 `baseline`、`window`、`stride`、`sample_count`、`mean_top_impact`、`mean_low_impact`、`top_minus_low`、`top_to_low_ratio`；`selected` 是最终配置，`selection_rule` 说明以验证集 Top 与 low 窗口影响差最大为选择原则。

#### `fidelity_metrics.json`

记录最终解释配置和验证集忠实性指标：`mean_top_evidence_impact`、`mean_low_evidence_impact`、`top_minus_low`。它说明解释排序具有模型行为层面的区分度，不构成因果验证。

#### `validation_audit.json`

记录训练/验证/测试 ID 是否互斥、样本数是否正确、附件四是否完整预测、贡献是否归一化、证据索引是否越界、附件四是否无标签、解释配置是否一致，以及视频解码帧数差异数量。

#### `v8_audit.json`

记录技术路线图、模型结构图、数据边界图、训练曲线、热力图、分类报告、模态消融、有限值检查、标签映射和附件四边界是否完成。`paper_claims_limit` 明确本结果没有声称重新训练架构基线或多随机种子不确定性。

#### `final_package_audit.json`

最终材料包完整性审计。重要字段包括附件四预测数、样本 ID 唯一性、关键帧和证据卡数量及 JSON 匹配、模型文件是否存在、视频帧数差异数量、附件四是否仅推理、`impact_score` 的语义和总体验证结果 `passed`。

#### `package_manifest.json`

记录材料包的来源目录、模型材料来源目录、生成脚本、模型文件哈希、解释参数和源预测/映射文件哈希。部分路径是生成材料时的历史绝对路径；判断当前文件应结合 `output_checksums.json` 和目录实际文件。

#### `output_checksums.json`

记录本目录所有结果文件、模型文件、关键帧和证据卡的 SHA-256。用于传输、提交或重新生成后的完整性核验。任何手工编辑都会使对应原哈希失效。

### 4.3 `model_artifacts/` 模型复现材料

| 文件 | 作用 |
|---|---|
| `best_model.pt` | 验证损失最优的 PyTorch 模型权重，用于重新推理 |
| `train_standardizer.npz` | 训练集拟合得到的标准化参数，推理时必须复用 |
| `run_config.json` | 原始训练运行的超参数和输入配置 |
| `run_summary.json` | 训练状态、epoch、优化步数、最优验证损失和 valid/test 指标 |
| `training_log.csv` | 每个 epoch 的损失、批次数、优化步数、耗时和参数 L2 范数 |
| `input_data_summary.json` | 样本数、特征形状、类别分布、回归范围和有限值检查 |

`input_data_summary.json` 中的特征形状为 text `(N,50,768)`、audio `(N,50,74)`、vision `(N,50,35)`，mask 为 `(N,50,3)`；50 是对齐序列长度，不是视频帧数。

`train_mean_baseline.npz` 是解释模块的训练集均值替换基线，不是新的模型权重，也不是标签均值。

## 5. 图表文件说明与论文用途

所有图表均为本目录实际数据生成的 PNG；图表用于展示，精确数值应回查 CSV/JSON。

| 图表 | 内容和论文用途 |
|---|---|
| `fig_technical_route.png` | 输入特征、训练、预测到解释证据的技术路线；用于方法总览 |
| `fig_model_architecture.png` | 掩码时序编码、跨模态交互、动态门控、分类/回归双头和解释模块；用于模型结构 |
| `fig_data_boundary.png` | train/valid/test 与附件四的使用边界；强调附件四仅推理 |
| `fig_training_curve.png` | train/valid loss 随 epoch 变化；说明训练收敛 |
| `fig_confusion_matrix_valid.png` | valid 三分类混淆矩阵；分析类别错误结构 |
| `fig_confusion_matrix_test.png` | test 三分类混淆矩阵；展示最终有标签分类结果 |
| `fig_regression_diagnostics_valid.png` | valid 真实/预测强度散点及残差；分析回归误差 |
| `fig_regression_diagnostics_test.png` | test 真实/预测强度散点及残差；分析最终回归结果 |
| `fig_global_contribution.png` | 三模态平均反事实贡献及波动；对应 `modality_contribution_summary.csv` |
| `fig_modality_contribution_valid.png` | valid 样本级模态贡献分布；展示贡献异质性 |
| `fig_gate_vs_contribution_valid.png` | 门控值与反事实贡献的比较；说明二者不可直接等同 |
| `fig_local_importance_heatmap_valid.png` | valid 窗口级影响热力图；结合 `local_importance_valid.csv` |
| `fig_local_importance_heatmap_test.png` | test 窗口级影响热力图；固定模型后的解释 |
| `fig_local_importance_heatmap_attachment4.png` | 附件四窗口级影响热力图；无标签推理解释 |
| `fig_fidelity_valid.png` | Top 与 low 证据窗口影响对比；解释忠实性诊断 |
| `fig_mapping_quality.png` | 证据映射质量统计；说明视频源和映射状态 |
| `fig_video_decode_audit.png` | 容器帧数与实际解码帧数对比；数据质量审计 |

推荐论文顺序：技术路线图/模型图/数据边界图 -> 训练曲线和性能图 -> 模态贡献和消融 -> 局部热力图与证据映射 -> 附件四关键帧和解码审计。

## 6. `evidence_cards/` 和 `keyframes/`

### 6.1 `evidence_cards/`

包含 `01.png` 至 `20.png` 共 20 张附件四证据卡，以及 `evidence_cards.json`。每张卡对应一个样本，通常包含预测类别、预测强度、主导模态、三个模态的 Top 证据和关键帧引用。

`evidence_cards.json` 的外层键是 PNG 文件名。每项字段包括：`sample_id`（样本编号）、`pred_class/pred_regression`（预测类别和强度）、`main_modality`（最大反事实贡献模态）、`explanation_method`、`source_video`、`component_keyframes`（引用的三张关键帧）、`evidence`（三模态证据数组）和 `frame_content`（未叠加文字的原始解码帧）。`evidence` 数组中的模态、排序、影响、窗口位置、秒、帧范围和映射状态与 `evidence_mapping_attachment4.csv` 对应。

论文用法：证据卡用于附件四定性展示和附录；必须同时引用 CSV/JSON 和映射状态，不能将卡片外观当成性能证明。

### 6.2 `keyframes/`

包含 20 个样本 × 3 个模态的 60 张 JPG，以及 `keyframes.json`。文件名格式为：

```text
<sample_id>_<modality>_rank1.jpg
```

`keyframes.json` 的外层键是图片文件名，字段包括：`sample_id`、`modality`、`rank`、`impact_score`、`start_index`、`end_index`、`start_sec`、`end_sec`、`requested_frame_start`、`requested_frame_end`、`used_center_frame`、`fps`、`source_video`、`source_type`、`text_evidence`、`text_time_source`、`mapping_status` 和 `frame_content`。

- `requested_frame_start/end` 是按时间窗口和 FPS 换算的目标范围。
- `used_center_frame` 是实际展示的中心帧。
- `frame_content=original_decoded_frame_without_overlay` 表示图片保留原视频内容，没有把参数文字画到视频帧上。
- `text_evidence` 通常只在文本证据中非空，音频和视觉关键帧可以为空。

论文用法：关键帧用于把局部重要性数值映射回原始视觉材料；时间、帧号和影响值应从 JSON/CSV 读取，不要人工从图片推测。

## 7. 推荐的论文引用链路

1. 用 `run_config.json`、`input_data_summary.json` 和 `fig_data_boundary.png` 说明输入特征、对齐长度、划分边界和附件四仅推理。
2. 用 `fig_technical_route.png`、`fig_model_architecture.png` 和模型公式说明结构、分类/回归双任务及动态融合。
3. 用 `training_curve.csv`、`fig_training_curve.png` 和 `model_artifacts/training_log.csv` 说明训练过程和 checkpoint。
4. 用 `model_metrics.csv`、`classification_report_valid.csv`、混淆矩阵和回归诊断图报告有标签性能。
5. 用 `modality_contribution_summary.csv`、`modality_ablation_metrics.csv` 和 `gate_contribution_consistency.csv` 讨论模态依赖，并明确后验移除与重新训练基线的区别。
6. 用 `local_importance_*.csv`、`evidence_mapping_*.csv`、`fig_fidelity_valid.png` 和热力图说明局部反事实解释及其忠实性。
7. 用 `predictions_attachment4.csv`、`table_evidence_examples.csv`、`evidence_cards/`、`keyframes/` 和 `video_decode_audit.csv` 展示附件四最终预测和可回溯证据。
8. 用 `validation_audit.json`、`final_package_audit.json`、`output_checksums.json` 和环境文件说明可复现性与数据质量边界。

## 8. 必须在论文中说明的限制

- 本目录只对应一次随机种子 `20260924`，没有多种子均值、置信区间或显著性检验。
- `modality_ablation_metrics.csv` 是固定模型的后验模态移除诊断，不是重新训练的单模态模型结果。
- `impact_score`、模态贡献和门控值都是模型行为解释，不是因果证据。
- 附件四没有标签，只能报告预测和解释，不能报告真实性能。
- 文本时间是对齐窗口的相对映射，不是逐词人工标注时间戳。
- 16 个附件四视频存在容器帧数与实际解码帧数不一致，应以实际解码帧和审计字段为准。
- `source_video`、`package_manifest.json` 中可能保留生成材料时的历史绝对路径；跨机器复现时应根据项目根目录重定位路径，并用哈希核对版本。
- 当前结果没有声称重新训练的架构基线、外部数据集增益或多随机种子稳定性。

## 9. 完整性检查与复现核验

1. 检查 `validation_audit.json` 和 `final_package_audit.json` 的 `passed` 是否为 `true`。
2. 检查 train/valid/test 样本数和特征形状是否与 `model_artifacts/input_data_summary.json` 一致。
3. 检查 `predictions_attachment4.csv` 是否有 20 个唯一 `sample_id`。
4. 检查 `keyframes/keyframes.json` 与 60 个 JPG、`evidence_cards/evidence_cards.json` 与 20 个 PNG 是否一一对应。
5. 用 `output_checksums.json` 对需要交付的文件做 SHA-256 校验。
6. 重新推理时必须同时加载 `model_artifacts/best_model.pt` 和 `model_artifacts/train_standardizer.npz`，使用 `run_config.json` 中的 aligned 特征、seed、窗口、步长和训练集均值基线。

本目录是结果证据包，不应手工修改预测 CSV、审计 JSON、关键帧元数据或哈希文件。若重新运行产生新结果，应在新的时间戳输出目录保存，不能覆盖本目录。
