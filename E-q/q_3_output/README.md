# 问题三输出目录说明

本目录保存 E 题问题三“可解释性多模态情感预测”的历次运行结果。每次运行必须新建时间戳子目录，格式为：

```text
YYYYMMDD_HHMMSS_microseconds
```

当前已核验的主要运行目录为：

```text
E-q/q_3_output/20260925_093119_520788600/  # 基线训练20轮 + 附件四推理
```

该次运行使用附件二 `aligned_50.pkl`：训练集 3395 条、验证集 728 条、测试集 727 条；附件四 20 条无标签样本只执行固定模型后的最终推理。模型直接使用题给 `text`、`audio`、`vision` 特征，不下载或微调额外预训练模型。完整建模见 [`E-q/modeling/q_3.md`](../modeling/q_3.md)，运行入口见 [`cli/q3_run.py`](../../cli/q3_run.py)。

## 一、如何选择运行目录

时间戳目录是一次独立、不可覆盖的运行记录，其中可能包括小样本冒烟测试和完整训练。判断是否为完整结果时，应先读取 `run_config.json`：

- `train_count=3395`、`valid_count=728`、`test_count=727`：使用附件二完整三划分；
- `max_train_samples`、`max_valid_samples`、`max_test_samples` 为 `null`：没有截取小样本；
- `run_attachment4=true`：完成附件四最终推理；训练模式下表示“训练后推理”，纯推理模式下表示“只推理”；
- `mode=attachment4_inference_only`：只加载已有 checkpoint，不训练、不计算 test 指标；
- `validation_audit.json` 的 `passed=true`：主键边界、标签和输出契约检查通过。

`20260925_093119_520788600` 是当前工作区中实际保留的、包含完整附件二训练/验证/测试、附件四推理、局部证据映射和忠实性诊断的基线完整运行。此前的类别加权调优和纯推理目录不在当前输出目录中，因此相关历史指标只能以项目其他记录为准，不能从当前目录复核。早期目录仅用于开发或冒烟验证，不应与完整运行的结果混合比较。

## 二、文件总览

| 文件 | 内容 | 用途 |
| --- | --- | --- |
| `run_config.json` | 数据版本、随机种子、超参数、设备和数据边界 | 复现实验条件 |
| `input_data_summary.json` | 实际加载数据的样本数、维度、mask 类型、标签分布和有限值检查 | 核验输入不是空数据或伪造摘要 |
| `run_summary.json` | 运行状态、最佳验证损失、验证/测试指标 | 快速读取本次结果 |
| `train_standardizer.npz` | 只由训练集拟合的三模态均值、标准差 | 防止标准化数据泄漏 |
| `best_model.pt` | 最佳验证损失对应的 PyTorch 权重和配置 | 固定模型推理/复现 |
| `training_log.csv` | 每轮训练损失和验证损失 | 检查收敛和模型选择 |
| `model_metrics.csv` | 验证集、测试集的分类和回归指标 | 性能比较 |
| `predictions_valid.csv` | 验证集逐样本真值、预测、内部门控 | 验证误差分析 |
| `predictions_test.csv` | 测试集逐样本真值、预测、内部门控 | 测试误差分析 |
| `explanations_valid.csv` | 验证集的反事实模态贡献和诊断 | 检查解释结果 |
| `evidence_mapping_valid.csv` | 验证集局部证据窗口及源素材映射状态 | 证据定位审计 |
| `fidelity_metrics.csv` | 高/低重要性窗口遮挡影响对比 | 解释忠实性诊断 |
| `predictions_attachment4.csv` | 附件四无标签样本预测和解释 | 最终专项推理 |
| `evidence_mapping_attachment4.csv` | 附件四证据到文本、秒数、帧区间的映射 | 回看附件四视频 |
| `anomalies.csv` | 特征、长度、映射异常 | 避免静默忽略异常 |
| `validation_audit.json` | 自动审计结果和检查项 | 核验数据边界与输出契约 |
| `output_checksums.json` | 输出文件 SHA-256 摘要 | 归档一致性核验 |

部分早期冒烟目录不含全部文件；正式分析应以完整运行目录为准。

## 三、配置、模型和训练文件

### 1. `run_config.json`

关键字段说明如下：

| 字段 | 含义 |
| --- | --- |
| `feature_version` | 特征版本；当前为 `aligned`，三模态均有 50 个时间位置 |
| `feature_path` / `feature_sha256` | 附件二输入路径及 SHA-256，保证数据版本可核验 |
| `epochs`、`batch_size` | 训练轮数与批大小 |
| `hidden_dim`、`heads`、`layers`、`dropout` | 时序编码器隐层维度、注意力头数、层数和 dropout |
| `learning_rate`、`weight_decay` | AdamW 优化器参数 |
| `cls_weight`、`reg_weight` | 总损失中分类损失和回归损失的权重；当前默认均为 `1.0` |
| `class_weighted` | 是否启用按训练集类别频数计算的加权交叉熵；只使用 train 标签计算 |
| `seed`、`device` | 固定随机种子与实际计算设备 |
| `train_count`、`valid_count`、`test_count` | 实际使用的附件二三划分样本数 |
| `input_dims` | 三模态维度；当前文本 768、音频 74、视觉 35 |
| `explain_window`、`explain_stride`、`top_k` | 局部遮挡窗口长度、步长和保留证据数 |
| `run_attachment4` | 是否对附件四执行最终推理 |
| `data_boundary` | 数据边界说明；附件四只能推理 |
| `pretrained_model` | 预训练模型使用记录；当前为 `none` |

训练模式还会记录：

```json
{
  "max_train_samples": null,
  "max_valid_samples": null,
  "max_test_samples": null,
  "run_attachment4": true,
  "checkpoint": null,
  "standardizer": null
}
```

其中 `null` 表示使用完整划分；如果是冒烟测试，限制字段会记录实际截取规模。`checkpoint=null` 表示本次从随机初始化模型开始训练；纯推理模式则会记录已有 `best_model.pt` 的路径和哈希。

### 2. `train_standardizer.npz`

数组如下：

```text
text_mean, text_std
audio_mean, audio_std
vision_mean, vision_std
```

所有均值、标准差仅由附件二训练集计算。验证集、测试集和附件四使用同一组参数，避免测试或无标签专项集统计量进入训练流程。

纯推理模式不会重新拟合标准化参数，而是从 checkpoint 同目录读取该文件；也可以通过 `--standardizer` 显式指定。若缺少该文件，不能直接对附件四推理，否则会产生不可追溯的尺度变化。

### 3. `best_model.pt`

这是 PyTorch checkpoint，不是只包含裸权重的文件，主要包含：

| 键 | 含义 |
| --- | --- |
| `state_dict` | 模型所有可训练参数；对应验证损失最低的 epoch |
| `config` | 保存模型结构、输入维度、训练超参数、数据文件哈希和运行边界 |

当前 `config.input_dims` 为文本 768、音频 74、视觉 35；`hidden_dim`、`heads`、`layers`、`dropout` 用于恢复网络结构。纯推理入口会从这些配置恢复模型，使用 `strict=True` 加载权重，结构不匹配时直接报错，不会静默忽略参数。

### 4. `training_log.csv`

| 字段 | 含义 |
| --- | --- |
| `epoch` | 从 1 开始的训练轮次 |
| `train_loss` | 本轮训练集分类交叉熵与回归 Smooth L1 的组合损失 |
| `valid_loss` | 验证集相同损失；最低值对应 `best_model.pt` |
| `train_batches`、`valid_batches` | 本轮实际处理的训练/验证 batch 数，用于核验数据是否真正遍历 |
| `optimizer_steps` | 本轮实际执行的参数更新次数；正常训练时等于 `train_batches` |
| `epoch_seconds` | 本轮训练和验证耗时 |
| `parameter_l2_norm` | 本轮结束时模型参数的 L2 范数，用于确认参数确实发生变化 |

损失仅用于训练期模型选择，不能替代题目评价指标。

### 5. `model_metrics.csv`

每行对应有标签的 `valid` 或 `test` 划分：

| 字段 | 含义 |
| --- | --- |
| `split` | 数据划分 |
| `accuracy` | 三分类预测正确比例 |
| `macro_f1` | 三个类别 F1 的算术平均，降低类别不平衡影响 |
| `mae` | 连续情感强度预测平均绝对误差，越小越好 |
| `pearson` | 预测强度与真实强度的 Pearson 相关系数，越大越好 |

附件四没有真实标签，禁止为它计算或报告 Accuracy、F1、MAE、Pearson。

### 6. `input_data_summary.json`

该文件是对实际进入本次运行的数据摘要，不是手工填写的说明。训练模式下包含 `train`、`valid`、`test` 三个对象；纯推理模式下包含 `attachment4` 对象。

| 字段 | 含义 |
| --- | --- |
| `feature_sha256` | 附件二特征 pickle 的 SHA-256；纯推理模式对应 `checkpoint_sha256` 和 `standardizer_sha256` |
| `split` | 当前数据划分名称 |
| `sample_count` | 实际加载样本数量 |
| `unique_sample_ids` | 去重后的样本主键数量，应与 `sample_count` 相等 |
| `feature_shapes.text/audio/vision` | 三模态数组形状 `[N,L,D]` |
| `feature_shapes.mask` | mask 形状 `[N,L,3]` |
| `mask_dtype` | 当前为 `bool`；`True` 表示有效位置 |
| `classification_distribution` | 各分类标签的样本数；无标签附件四为 `null` |
| `regression_min/max` | 回归标签最小/最大值；无标签附件四为 `null` |
| `feature_finite` | 三模态特征是否全部为有限数值 |

当前完整附件二输入摘要为：

```text
train: 3395 条，text [3395,50,768]，audio [3395,50,74]，vision [3395,50,35]
valid:  728 条，text [728,50,768]， audio [728,50,74]， vision [728,50,35]
test:   727 条，text [727,50,768]， audio [727,50,74]，  vision [727,50,35]
```

该文件应与 `run_config.json` 和输入文件哈希一起查看，不能只根据 CSV 行数判断运行是否完整。

## 四、逐样本预测文件

### 1. `predictions_valid.csv` 与 `predictions_test.csv`

字段完全相同：

| 字段 | 含义 |
| --- | --- |
| `sample_id` | 稳定样本主键，通常为 `video_id$_$clip_id` |
| `split` | `valid` 或 `test` |
| `true_class` | 题给三分类真值，当前编码为 `0/1/2` |
| `pred_class` | 模型预测类别 `0/1/2` |
| `true_regression` | 题给连续情感强度真值，范围 `[-3,3]` |
| `pred_regression` | 模型预测强度，模型输出被限制在 `[-3,3]` |
| `gate_text` | 动态融合层的文本内部门控权重 |
| `gate_audio` | 动态融合层的音频内部门控权重 |
| `gate_vision` | 动态融合层的视觉内部门控权重 |

同一行三个 `gate_*` 之和约为 1。它们仅表示模型内部融合比例，**不是最终模态贡献**；最终解释应使用 `explanations_valid.csv` 中的 `modality_contrib_*`。

`predictions_valid.csv` 用于分析模型选择阶段的逐样本表现；`predictions_test.csv` 只能在模型和超参数固定后读取和报告。不要用 test 结果反向选择 epoch、类别权重、损失权重或解释参数。

### 2. `predictions_attachment4.csv`

附件四无标签样本的最终预测和反事实解释。它包含 `sample_id`、`pred_class`、`pred_regression`、三类 `modality_score_*`、三类 `modality_contrib_*`、`main_modality`、`fidelity_top_mean`、`fidelity_low_mean`、`explanation_method` 和 `split`。

`split` 固定为 `attachment4`。该文件没有 `true_class`、`true_regression`，因此所有预测都只是模型输出，不能表述为附件四上的真实性能。

附件四共有两种输出来源：

1. 训练模式加 `--run-attachment4`：先训练附件二模型，再用本次验证损失最优权重推理附件四；该目录同时有 `training_log.csv`、`model_metrics.csv` 和附件四文件。
2. 纯推理模式加 `--checkpoint`：加载已有权重和 `train_standardizer.npz`，跳过附件二训练/验证/测试，只生成附件四预测与解释。此时 `run_summary.json` 中 `epochs_requested=0`、`epochs_completed=0`、`optimizer_steps=0`，且没有训练日志和有标签指标。

纯推理目录的典型文件为：

```text
run_config.json
input_data_summary.json
predictions_attachment4.csv
evidence_mapping_attachment4.csv
run_summary.json
output_checksums.json
```

如果要复核某次调优或纯推理运行，必须确认其时间戳子目录实际存在，再读取该目录中的 `run_config.json` 和 `run_summary.json`；README 不替代运行目录本身。

## 五、反事实解释和证据定位

### 1. 解释分数的含义

对完整输入得到分类概率 (p_i) 与回归输出 (hat y_i)。分别遮挡文本、音频、视觉后得到 (p_i^{-m})、(hat y_i^{-m})，影响分数为：

\[
r_{i,m}=0.5D_{KL}(p_i\Vert p_i^{-m})+0.5|\hat y_i-\hat y_i^{-m}|.
\]

对三个正影响分数归一化，得到各模态贡献。局部证据使用同样逻辑遮挡单模态的滑动时间窗。因此分数描述的是“当前模型预测对输入的敏感程度”，不是人工标注的真实情感原因，也不是严格因果效应。

当前代码实现中的零/无效遮挡规则是：被遮挡模态的特征置零，同时对应 mask 置为无效；分类影响使用 KL 散度，回归影响使用绝对预测差，二者各占 0.5。`modality_score_*` 是未归一化影响，`modality_contrib_*` 是按三模态归一化后的比例。

### 2. `explanations_valid.csv`

每行对应一条执行反事实解释的验证集样本。当前完整运行使用 `explain_max_samples=32`，因此包含 32 条样本。

| 字段 | 含义 |
| --- | --- |
| `sample_id` | 稳定样本主键 |
| `pred_class`、`pred_regression` | 当前模型的分类和强度预测 |
| `modality_score_text` / `audio` / `vision` | 遮挡完整模态后的未归一化影响分数 (r_{i,m}) |
| `modality_contrib_text` / `audio` / `vision` | 归一化模态贡献；同一行三者和约为 1 |
| `main_modality` | 贡献最大的模态；并列时可用分号分隔多个模态 |
| `fidelity_top_mean` | 高重要性局部窗口的平均遮挡影响 |
| `fidelity_low_mean` | 低重要性局部窗口的平均遮挡影响 |
| `explanation_method` | 当前固定为 `counterfactual_occlusion` |

若 `fidelity_top_mean` 大于 `fidelity_low_mean`，说明高排名窗口的遮挡通常比低排名窗口更能改变模型预测，是忠实性诊断证据，不是人工解释真值。

### 3. `evidence_mapping_valid.csv` 与 `evidence_mapping_attachment4.csv`

每行表示一段模态局部证据；`rank=1` 是同模态内影响最高的保留窗口，之后是非重叠的次高窗口。

| 字段 | 含义 |
| --- | --- |
| `sample_id` | 样本主键；若原 ID 以 `-` 开头，CSV 可能加 Excel 安全前缀 `'` |
| `modality` | `text`、`audio` 或 `vision` |
| `rank` | 同一模态内的证据影响排名 |
| `start_index`、`end_index` | aligned 50 时间轴上的闭区间索引，范围 `0` 至 `49` |
| `impact_score` | 遮挡该局部时间窗导致的预测变化，越大表示模型越依赖该窗口 |
| `source_video` | 供回看的预期或实际 MP4 路径 |
| `source_type` | `attachment4_video` 或 `attachment1_video` |
| `start_sec`、`end_sec` | 按 50 窗口比例换算的起止秒数；只在源视频存在时写出 |
| `frame_start`、`frame_end` | 对应视频帧闭区间；只在源视频存在时写出 |
| `fps` | 视频帧率；只在源视频存在时写出 |
| `text_evidence` | 文本模态时保存原始转写，音频/视觉行为空 |
| `text_time_source` | 文本时间来源；当前为 `raw_text; aligned relative window`，不是观测的逐词时间戳 |
| `source_exists` | 本地是否实际存在对应源视频 |
| `mapping_status` | `mapped_to_video` 表示已映射秒数和帧号；`relative_window_only_source_video_missing` 表示仅保留相对窗口 |

附件四的 20 条样本拥有对应 MP4，应优先从 `evidence_mapping_attachment4.csv` 回看 `start_sec` 至 `end_sec`。附件二样本不保证属于附件一的 100 条视频；当 `source_exists=false` 时，只能解释到特征窗口和原始文本，不能伪造视频帧映射。

### 4. `fidelity_metrics.csv`

| 字段 | 含义 |
| --- | --- |
| `split` | 执行忠实性诊断的有标签划分，当前为 `valid` |
| `sample_count` | 参与局部遮挡解释的样本数 |
| `mean_top_evidence_impact` | 高重要性局部证据的平均遮挡影响 |
| `mean_low_evidence_impact` | 低重要性局部窗口的平均遮挡影响 |
| `diagnostic` | 指标计算说明和边界 |

当前完整运行中该指标用于比较高、低排名窗口的敏感性。具体数值必须以对应运行目录的 `fidelity_metrics.csv` 为准，不应把某一次运行的数值复制到其他运行。高排名窗口影响更大只能支持“模型对其更敏感”，不表示已证明真实因果关系或人工解释正确率。

## 六、审计与完整性文件

### 0. `run_summary.json`

训练模式字段：

| 字段 | 含义 |
| --- | --- |
| `status` | `completed` 表示流程正常结束，不代表指标一定理想 |
| `epochs_requested` / `epochs_completed` | 请求训练轮数和实际完成轮数 |
| `total_optimizer_steps` | 全部 epoch 的参数更新次数 |
| `best_valid_loss` | 保存 `best_model.pt` 时使用的最低验证损失 |
| `metrics` | valid/test 指标列表，包含 Accuracy、Macro-F1、MAE、Pearson |
| `output_dir` | 当前运行目录绝对路径 |
| `explanations_are_model_sensitivity` | 说明解释是模型敏感性分析，而非真实因果证明 |
| `attachment4_has_no_ground_truth` | 说明附件四无标签 |

纯推理模式的摘要不同：`mode` 为 `attachment4_inference_only`，`epochs_requested`、`epochs_completed`、`optimizer_steps` 均为 0，`ground_truth_available=false`，`metrics=null`。这组字段用于证明该目录没有重新训练，也没有对附件四计算真实性能。

### 1. `validation_audit.json`

| 字段 | 含义 |
| --- | --- |
| `train_valid_test_ids_disjoint` | 训练、验证、测试主键无交集 |
| `train_valid_test_have_labels` | 三个附件二划分均有分类和回归标签 |
| `all_output_files_finite_or_serialized` | 输出数值可用或已按规定序列化 |
| `attachment4_used_only_for_inference` | 附件四未进入训练、调参或性能统计 |
| `passed` | 上述检查是否全部通过 |

### 2. `anomalies.csv`

| 字段 | 含义 |
| --- | --- |
| `split` | 异常所在数据划分 |
| `type` | 异常类型，例如 `non_finite_feature` |
| `modality` | 对应模态 |

只有表头表示未检测到该类异常。视频映射是否可用不写入此表，而是逐条记录在 `evidence_mapping_*.csv` 的 `source_exists`、`mapping_status` 中。

### 3. `output_checksums.json`

键为运行目录内输出文件名，值为 SHA-256。重新传输、归档或提交后可重新计算并核对。该文件自身不列入哈希表，避免自引用变化。

### 4. `anomalies.csv` 的边界

该文件只记录当前 CLI 自动检查到的非有限特征等异常。当前无异常时通常只有表头。视频源是否存在、解释窗口是否能映射到秒数和帧号，分别通过 `evidence_mapping_*.csv` 的 `source_exists` 与 `mapping_status` 检查，不能因为 `anomalies.csv` 为空就断言所有解释已经人工验证。

## 七、CSV、主键与人工复核

所有 CSV 使用 UTF-8 BOM。为避免 Excel 把 `-`、`=`、`+`、`@` 开头的 `sample_id` 解释为公式，文本型字段会增加 Excel 安全前缀 `'`：

```text
'-UacrmKiTn4$_$7
```

程序读取主键时，只需对文本 ID 去除开头的一个单引号；不要对数值标签、贡献、秒数或帧号添加/去除前缀。

完整复现命令：

```powershell
python cli/q3_run.py --epochs 2 --batch-size 64 --explain-max-samples 32 --explain-batch-size 8 --device cuda --run-attachment4
```

类别均衡调优命令：

```powershell
python cli/q3_run.py `
  --epochs 8 --batch-size 64 --hidden-dim 64 --heads 4 --layers 1 `
  --learning-rate 2e-4 --weight-decay 1e-4 `
  --class-weighted --cls-weight 1.0 --reg-weight 1.0 `
  --seed 20260924 --device cuda
```

已有权重的附件四纯推理命令：

```powershell
python cli/q3_run.py `
  --checkpoint E-q/q_3_output/<训练运行目录>/best_model.pt `
  --run-attachment4 --explain-batch-size 8 `
  --explain-window 5 --explain-stride 5 --top-k 3 `
  --seed 20260924 --device cuda
```

该命令默认从 checkpoint 同目录读取 `train_standardizer.npz`；若文件位置不同，增加 `--standardizer path/to/train_standardizer.npz`。纯推理输出只包含附件四预测和证据映射，不包含 `model_metrics.csv`。

运行后可检查：

```powershell
$latest = Get-ChildItem E-q/q_3_output -Directory | Sort-Object Name -Descending | Select-Object -First 1
Get-Content (Join-Path $latest.FullName 'validation_audit.json')
Get-Content (Join-Path $latest.FullName 'model_metrics.csv')
Get-Content (Join-Path $latest.FullName 'fidelity_metrics.csv')
Get-Content (Join-Path $latest.FullName 'run_summary.json')
```

人工复核附件四解释时，依据 `evidence_mapping_attachment4.csv` 的 `source_video` 打开视频，跳转到 `start_sec` 至 `end_sec`，并结合 `text_evidence`、`impact_score` 以及 `predictions_attachment4.csv` 的模态贡献判断。论文中应表述为模型预测证据或敏感片段，而不是未经人工标注验证的真实情感原因。

## 八、视频级解释完成材料

使用 `scripts/q3_complete_explainability.py` 可在完整验证集上比较 `zero_invalid` 与 `train_mean` 遮挡基线、窗口长度 3/5/7，并读取附件四 MP4 生成 `keyframes/` 和 `evidence_cards/`。每次运行新建时间戳目录，另含 `video_decode_audit.csv`、`anomalies.csv`、`explanation_summary.csv`、`run_config.json`、`source_manifest.json` 和递归输出校验。

OpenCV 容器帧数与实际解码帧数不一致时，关键帧会截断到实际可解码范围，并在 `anomalies.csv` 中记录请求帧号和实际使用帧号；不能把截断后的画面描述为原始映射完全准确。

`keyframes/` 和 `evidence_cards/` 内的图片不再绘制标签或参数，保证视频帧内容完整。`keyframes/keyframes.json` 以关键帧文件名为键，记录模态、rank、影响分数、时间区间、请求帧号、实际使用帧号、源视频和文本证据；`evidence_cards/evidence_cards.json` 以解释卡文件名为键，记录预测结果、主导模态、组成关键帧和各模态证据参数。两个 JSON 与各自目录内的图片文件一一对应。
## v7 最终论文支撑包

`20260925_213047_006377600` 是统一预测与审计源目录；包含关键帧、解释卡、模型权重和论文图表的完整归档为 `20260925_215043_145160100`。该目录由 `scripts/q3_v7_package.py` 从源目录复制后生成，确保预测、证据映射、关键帧和解释卡来自同一 checkpoint 与解释配置。

完整归档必须同时检查 `final_package_audit.json`（应为 `passed=true`）、`package_manifest.json`、`keyframes/keyframes.json`、`evidence_cards/evidence_cards.json` 和 `output_checksums.json`。当前归档包含 20 条附件四预测、60 张原始关键帧和 20 张解释卡；附件四仍然只用于推理和证据展示，不用于训练、调参或真实性能统计。
