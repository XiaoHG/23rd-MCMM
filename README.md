# 23rd-MCMM

2026 年第二十三届中国研究生数学建模竞赛 E 题项目。当前题目为“复杂场景下多模态情感预测的数学建模与算法设计”，项目使用 Python 完成资料整理、数据审计、三模态特征提取、时序对齐、后续鲁棒预测和可解释性分析。

## 项目状态

当前已经完成：

- E 题原始题面和附件的工作副本整理；
- CMU-MOSEI 相关论文、模型和 GitHub 工程资料分析；
- 问题一透明基线特征提取和时间对齐脚本；
- 100 条原始视频的特征、掩码、时间映射、异常清单和典型样本输出；
- 问题三的 masked Transformer 双任务预测、反事实模态贡献和局部时间证据原型；
- 问题三的单元测试、训练/验证/测试评估入口，以及附件 4 最终推理入口；
- 本地论文与源码知识库索引。

当前尚未完成：

- 问题二的局部模态缺失鲁棒预测模型；
- 问题二的可执行鲁棒预测入口；
- 问题三的系统消融实验、正式实验表和最终论文结论。

未经运行日志、验证集结果或题面核验支持的内容，只能视为候选方案或待确认事项。

## 目录结构

```text
23rd-MCMM/
├── AGENTS.md                         # 项目边界、合规约束和工作流程
├── 26-tq/                            # 2026 年原始赛题和附件，只读核验来源
├── E-q/                              # E 题工作目录
│   ├── dataset/                       # E 题数据副本，只读使用
│   ├── modeling/                      # q_1.md、q_2.md、q_3.md 建模文档
│   ├── q_1_output/                    # 问题一历次运行输出，每次运行一个时间戳子目录
│   ├── q_2_output/                    # 问题二历次模型输出，每次运行一个时间戳子目录
│   └── q_3_output/                    # 问题三历次模型输出，每次运行一个时间戳子目录
├── CMU-MOSEI/                         # 论文资料、方法分析和 GitHub 工程
├── research/                          # 外部资料索引、阅读卡片和 SQLite 检索库
├── references/                        # 按需缓存的往届论文资料
├── scripts/                           # 可重复运行的脚本入口
├── src/                               # 可复用数据、模型、指标和解释逻辑
│   └── q_3/                            # 问题三核心模块
├── cli/                               # 命令行运行入口
│   └── q3_run.py                       # 问题三训练、评估、解释和附件4推理
├── test/                              # 单元测试
├── draft/                             # 草稿材料，不代表最终结论
└── versions/                          # 项目版本分析和迭代记录
```

## E 题数据边界

原始题面唯一核验来源为：

```text
26-tq/第二十三届中国研究生数学建模竞赛 - 中文题目/中文题目/E题/
```

E 题工作数据位于：

```text
E-q/dataset/
├── attachment_1_raw_multimodal_samples/
│   └── mosei_raw_videos_100/           # 100 条原始视频和 label-100.xlsx
├── attachment_2_feature_files/        # aligned_50.pkl、unaligned_50.pkl、label.xlsx
├── attachment_3_missing_modality_features/
│   ├── aligned/                        # 局部模态缺失专项数据
│   └── unaligned/
└── attachment_4_explainability_videos_and_features/
    ├── aligned/                        # 可解释性专项视频和特征
    └── unaligned/
```

必须遵守：

1. 只能使用赛题提供的 CMU-MOSEI 系列数据进行训练、微调、调参、阈值选择和结果统计。
2. 附件 1 的视频和标签只读，不能替换、增补、删除或手工修改。
3. 附件 2 的 train、valid、test 边界不能混用；参数只在训练集拟合，结构、超参数和阈值在验证集选择。
4. 附件 3、附件 4 无标签，只能用于最终专项推理，不能用于训练、调参、早停或真实性能统计。
5. `aligned_50.pkl` 与 `unaligned_50.pkl` 只能选择一个，并在训练、验证和专项测试中保持一致；`text` 与 `text_bert` 也只能二选一。
6. 分类至少报告 Accuracy、F1；回归至少报告 MAE、Pearson 相关系数。
7. 解释结果必须能回溯到文本片段、音频时间段或视觉关键帧。

## 环境安装

### 推荐环境

建议使用独立 Conda 环境，Python 3.11 或 3.12。当前机器已核验的运行环境为 Python 3.13.5、pip 26.2.1；问题一脚本可以运行，但深度学习相关依赖在 Python 3.13 下可能存在版本兼容问题。

Windows PowerShell 安装示例：

```powershell
conda create -n mcmm-e python=3.11 -y
conda activate mcmm-e

python -m pip install --upgrade pip
python -m pip install numpy==1.26.4 pandas openpyxl opencv-python==4.10.0.84 matplotlib pymupdf

# 问题三需要 PyTorch；下列版本组合已在 Windows + CUDA 11.8 环境验证
python -m pip install torch==2.0.1+cu118 --index-url https://download.pytorch.org/whl/cu118

# 可选：用于阅读或扩展预训练模型的工具
python -m pip install transformers
```

如果本机 CUDA 版本不同，应按照 PyTorch 官方渠道选择匹配版本；不要将 CUDA 11.8 的 wheel 与其他 CUDA 运行时混装。当前项目已验证的环境组合为 Python 3.11.16、NumPy 1.26.4、PyTorch 2.0.1+cu118。安装后执行：

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

若输出 `False`，问题三仍可使用 CPU 运行，但训练速度会明显降低。

Windows 下若同时使用 Conda MKL 和 PyTorch wheel，可能出现 `OMP: Error #15`。`cli/q3_run.py` 已在导入 PyTorch 前固定单线程并设置 `KMP_DUPLICATE_LIB_OK=TRUE`，用于兼容当前环境；若直接在其他脚本中先导入 PyTorch，应在导入前执行：

```powershell
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
```

该变量是 Windows 多 OpenMP runtime 的兼容性开关，若改用完全统一的 Conda/PyTorch 安装来源，可去掉它并重新验证运行时。

### FFmpeg

问题一脚本使用 FFmpeg 从 MP4 中解码单声道 16 kHz 音频。安装后必须确认 `ffmpeg` 和 `ffprobe` 可以被 PowerShell 找到：

```powershell
ffmpeg -version
ffprobe -version
```

Windows 可使用已有包管理器安装，例如：

```powershell
winget install Gyan.FFmpeg.Shared
```

安装后重启终端，确保 FFmpeg 目录已加入 `PATH`。当前已核验到 `ffmpeg.exe` 和 `ffprobe.exe` 可用。

### 环境核验

```powershell
python --version
python -c "import numpy, pandas, openpyxl, cv2, matplotlib; print('科学计算依赖：ok')"
python -c "import fitz; print('PyMuPDF：ok')"
python -c "import torch; print('PyTorch:', torch.__version__, 'CUDA:', torch.cuda.is_available())"
ffmpeg -version
```

当前项目没有单独的 `requirements.txt`；安装依赖时应结合实际任务和 PyTorch 官方兼容矩阵记录环境版本。运行记录必须保存 Python 版本、操作系统、依赖版本、设备、随机种子和数据文件清单。

## 问题一：特征提取与时序对齐

问题一脚本为：

```text
scripts/q1_extract_features.py
```

运行完整的 100 条样本：

```powershell
python scripts/q1_extract_features.py
```

仅处理前 `N` 条进行冒烟测试：

```powershell
python scripts/q1_extract_features.py --max-samples 2
```

修改公共时间窗数量时显式指定，并在正式实验中固定配置：

```powershell
python scripts/q1_extract_features.py --steps 50 --seed 20260923
```

### 当前问题一基线

脚本从附件 1 的原始视频和 `label-100.xlsx` 读取数据，以 `video_id_clip_id` 建立稳定主键，并将每条视频的有效时长划分为 50 个公共时间窗。

- 文本：英文词元切分，使用 SHA-256 稳定哈希生成 64 维词元向量，再加入 8 个词法统计量，最终维度为 72。
- 音频：FFmpeg 单声道 16 kHz 解码；每个窗口提取 12 个对数频带能量和 8 个时域/频域统计量，最终维度为 20。
- 视觉：OpenCV 逐帧读取并缩放到 `64 x 36`，提取 RGB、灰度、边缘、运动和空间差异统计量，最终维度为 20。
- 时间：三模态组织为 50 个公共时间窗；文本因附件 1 没有逐词时间戳，采用按视频时长均匀分配词元的明确推断规则。
- 掩码：输出文本、音频和视觉的有效窗口掩码，区分真实特征、缺失和 padding。

这是一套可审计、可复现的透明基线，不等同于 BERT、COVAERP、Facet 或其他预训练特征。替换特征提取器时，必须保留 `sample_id`、时间映射、有效掩码和输出接口。

### 问题一输出

输出目录为：

```text
E-q/
├── q_1_output/<YYYYMMDD_HHMMSS_microseconds>/  # 问题一
├── q_2_output/<YYYYMMDD_HHMMSS_microseconds>/  # 问题二
└── q_3_output/<YYYYMMDD_HHMMSS_microseconds>/  # 问题三
```

主要文件：

| 文件 | 内容 |
| --- | --- |
| `q1_aligned_features.npz` | `text`、`audio`、`vision`、`modality_mask`、`valid_lengths`、`sample_ids` |
| `labels.csv` | 原始标签表的核对副本 |
| `sample_manifest.csv` | 样本状态、时长、特征维度和有效窗口 |
| `video_metadata.csv` | 帧率、分辨率、容器帧数、实际解码帧数和音频状态 |
| `time_mapping.csv` | 公共窗口到音频采样点、视频帧和有效掩码的映射 |
| `text_token_mapping.csv` | 词元到推断时间区间的映射 |
| `anomalies.csv` | 异常和元数据不一致清单 |
| `typical_sample.json` | 典型样本摘要 |
| `typical_sample_timeline.png` | 典型样本三模态时间轴图 |
| `run_config.json` | 参数、维度、工具和数据边界 |
| `run_summary.json` | 样本覆盖、输出形状和异常计数 |

当前已经完成一次完整运行：100/100 样本、100 个唯一主键，特征形状为文本 `(100,50,72)`、音频 `(100,50,20)`、视觉 `(100,50,20)`，时间映射 5000 行。输出中的 90 条视频容器帧数与实际解码帧数不一致、1 条音频窗口覆盖不足已写入本次运行目录的 `anomalies.csv`，没有被静默忽略。每次运行都会新建时间戳目录，不覆盖已有结果。

### CSV 的 Excel 兼容性

输出 CSV 使用 UTF-8 BOM。由于部分 `video_id` 和 `sample_id` 以 `-` 开头，Excel 可能将它们误解析为公式并显示 `#NAME?`。脚本会对以 `=、+、-、@` 开头的文本字段添加 Excel 安全前缀 `'`；Excel 显示时仍为原始文本，程序读取时如需恢复机器主键，可去除字段开头的单个 `'`。

## 建模文档

- [问题一建模](E-q/modeling/q_1.md)：特征提取、公共时间窗、数学定义、特征维度、掩码和验收标准。
- [问题二建模](E-q/modeling/q_2.md)：局部模态缺失鲁棒预测的设计草稿，当前没有正式 CLI 实现。
- [问题三建模](E-q/modeling/q_3.md)：掩码感知编码、动态融合、双任务预测、反事实解释和证据映射。
- [版本分析](versions/v3.md)：问题一版本定位、资料结论和迭代要求。

## CMU-MOSEI 资料与基线工程

`CMU-MOSEI/` 保存相关论文、研究进展总结和 `Multimodal-Sentiment-Analysis` GitHub 项目。

- [专题总览](CMU-MOSEI/README.md)：论文创新点、模型框架、E 题适用性和工程审查。
- [专题阅读卡片](research/notes/cmu-mosei-literature.md)：研究方法谱系和证据入口。
- `CMU-MOSEI/Multimodal-Sentiment-Analysis/`：包含 MulT 跨模态 Transformer、TFN 风格高阶融合和 CTC 式软对齐代码。

该工程可以作为问题二/三的下游基线参考，但不能直接解决问题一。它读取特定格式的预计算 pickle，没有处理附件 1 原始视频审计、局部缺失 mask、E 题双任务输出和可回溯解释；使用前必须重写数据适配器并核验标签、padding 和有效长度。

## 问题三：训练、预测与可解释性

问题三当前实现由以下模块组成：

| 模块 | 作用 |
| --- | --- |
| `src/q_3/data.py` | 读取附件二/附件四、校验字段和形状、训练集标准化、CSV 安全输出 |
| `src/q_3/model.py` | 三模态独立掩码 Transformer、跨模态交互、动态门控、分类/回归双任务头 |
| `src/q_3/metrics.py` | Accuracy、macro-F1、MAE、Pearson 指标 |
| `src/q_3/explain.py` | 模态级反事实遮挡、局部窗口遮挡、证据窗口排序 |
| `cli/q3_run.py` | 完整训练、验证/测试评估、解释文件和附件四专项推理 |
| `test/test_q3.py` | 数据标准化、mask、缺失模态、模型输出和解释逻辑测试 |

### 问题三默认训练和评估

在项目根目录执行。默认读取附件二 `aligned_50.pkl`，只用训练集拟合标准化参数；验证集用于模型选择，测试集仅在模型固定后评估：

```powershell
python cli/q3_run.py
```

每次运行在 `E-q/q_3_output/<YYYYMMDD_HHMMSS_microseconds>/` 新建目录，不覆盖历史运行。典型运行配置如下：

```powershell
python cli/q3_run.py `
  --epochs 20 `
  --batch-size 64 `
  --hidden-dim 64 `
  --heads 4 `
  --layers 1 `
  --learning-rate 2e-4 `
  --weight-decay 1e-4 `
  --seed 20260924 `
  --device cuda
```

CPU 运行时删除 `--device cuda`，或显式指定：

```powershell
python cli/q3_run.py --epochs 20 --device cpu
```

### 问题三冒烟测试

先用少量样本确认依赖、数据路径、模型前向和输出目录均正常：

```powershell
python cli/q3_run.py `
  --epochs 1 `
  --max-train-samples 64 `
  --max-valid-samples 32 `
  --max-test-samples 32 `
  --explain-max-samples 4 `
  --seed 20260924 `
  --device cpu
```

### 问题三附件四最终推理

附件四无标签，只能在模型已经由附件二训练、验证和固定后进行最终推理，不能参与训练、调参或性能统计：

```powershell
python cli/q3_run.py `
  --epochs 20 `
  --run-attachment4 `
  --explain-max-samples 32 `
  --seed 20260924 `
  --device cuda
```

该运行目录中的 `predictions_attachment4.csv` 和 `evidence_mapping_attachment4.csv` 只能解释为专项预测与证据映射，不能计算或声称 Accuracy、F1、MAE、Pearson 等真实性能。

### 使用已有权重对附件四纯推理

如果已经完成训练并得到 `best_model.pt`，不需要再次设置或执行训练 epoch。传入 `--checkpoint` 后，程序会跳过附件二训练、验证和测试，只加载已有权重及其训练阶段生成的 `train_standardizer.npz`，然后对附件四进行预测和反事实解释：

```powershell
python cli/q3_run.py `
  --checkpoint E-q/q_3_output/20260925_085922_070518300/best_model.pt `
  --run-attachment4 `
  --explain-batch-size 8 `
  --explain-window 5 `
  --explain-stride 5 `
  --top-k 3 `
  --seed 20260924 `
  --device cuda
```

默认从 `best_model.pt` 同目录读取 `train_standardizer.npz`。如果标准化文件不在同目录，可显式指定：

```powershell
python cli/q3_run.py `
  --checkpoint path/to/best_model.pt `
  --standardizer path/to/train_standardizer.npz `
  --run-attachment4 `
  --device cuda
```

纯推理模式的运行摘要会明确记录 `epochs_requested=0`、`epochs_completed=0`、`optimizer_steps=0`，且不会生成 `training_log.csv` 或 `model_metrics.csv`。附件四没有真实标签，因此只能输出 `predictions_attachment4.csv` 和 `evidence_mapping_attachment4.csv`，不能报告真实性能指标。

### 问题三参数说明

`--feature-version` 当前仅支持 `aligned`；`unaligned` 不能直接复用当前跨模态时间解释接口。`--explain-window` 和 `--explain-stride` 分别控制局部遮挡窗口长度和步长，默认均为 5；`--top-k` 控制每个模态最多保留的证据窗口数量，默认 3；`--explain-max-samples 0` 可关闭验证集解释输出。完整参数可查看：

```powershell
python cli/q3_run.py --help
```

### 问题三当前调优配置

基线模型在 20 轮训练中第 3 轮验证损失最低，之后训练损失继续下降而验证损失上升，存在过拟合；同时多数类 `2` 的预测比例偏高，验证集类别 `1` 召回率偏低。当前代码支持仅使用训练集类别频数计算加权交叉熵：

```powershell
python cli/q3_run.py `
  --epochs 8 `
  --batch-size 64 `
  --hidden-dim 64 `
  --heads 4 `
  --layers 1 `
  --learning-rate 2e-4 `
  --weight-decay 1e-4 `
  --class-weighted `
  --cls-weight 1.0 `
  --reg-weight 1.0 `
  --seed 20260924 `
  --device cuda
```

已完成验证集调优实验：加权配置的验证集 Macro-F1 为 `0.5919`，类别 `1` 召回率约 `0.5815`；原基线 Macro-F1 为 `0.5538`，类别 `1` 召回率约 `0.2391`。加权配置验证集 Accuracy 为 `0.5989`，低于基线 `0.6126`，因此它代表“类别均衡优先”的候选方案，不应宣称所有指标均提升。调参只依据验证集，测试集仅在配置固定后作一次报告。

该候选权重已保存于：

```text
E-q/q_3_output/20260925_092027_593015300/best_model.pt
```

并已使用该权重完成附件四纯推理：

```text
E-q/q_3_output/20260925_092205_502758600/
```

后续论文应同时报告原基线和加权候选，至少比较 Accuracy、Macro-F1、各类别召回率、MAE 和 Pearson，不能只保留对某一个指标最有利的配置。

### 问题三可解释性完成流程

在已有完整训练目录上运行以下命令，可对完整验证集比较遮挡基线和窗口，并对附件四视频生成 OpenCV 解码审计、关键帧和样本解释卡：

```powershell
python scripts/q3_complete_explainability.py `
  --run-dir E-q/q_3_output/20260925_100021_726334600 `
  --valid-max-samples 0 `
  --batch-size 32 `
  --device cuda
```

输出会写入新的 `E-q/q_3_output/<时间戳>/`，包括参数选择表、视频解码审计、异常记录、关键帧、解释卡、运行配置和来源哈希。脚本不训练模型、不使用附件四标签，也不修改源运行目录或原始视频。

`keyframes/` 和 `evidence_cards/` 中的图片均保留原始视频画面，不叠加文字；对应参数分别存储在 `keyframes/keyframes.json` 和 `evidence_cards/evidence_cards.json` 中，JSON 的键就是图片文件名。

问题三每次运行主要生成：

| 文件 | 说明 |
| --- | --- |
| `run_config.json` | 数据路径哈希、维度、超参数、随机种子、设备和数据边界 |
| `train_standardizer.npz` | 仅由训练集拟合的三模态均值和标准差 |
| `best_model.pt` | 验证损失最优模型参数 |
| `training_log.csv` | 每轮训练/验证损失 |
| `predictions_valid.csv`、`predictions_test.csv` | 分类、回归预测、真实标签和内部门控值 |
| `model_metrics.csv` | Accuracy、macro-F1、MAE、Pearson |
| `explanations_valid.csv` | 模态反事实影响、归一化贡献、主模态和忠实性诊断 |
| `evidence_mapping_valid.csv` | 局部证据窗口到相对时间、帧区间和文本证据的映射 |
| `predictions_attachment4.csv` | 附件四专项预测与解释信息，无真实标签 |
| `evidence_mapping_attachment4.csv` | 附件四证据映射 |
| `validation_audit.json`、`anomalies.csv` | 数据边界、字段、有限值和异常审计 |
| `output_checksums.json`、`run_summary.json` | 输出哈希和运行摘要 |

内部门控值仅是模型融合参数；论文中的模态贡献应使用反事实遮挡结果，不应把门控值直接当作因果贡献。

### 问题二当前状态

问题二建模文档已完成方案设计，但当前仓库没有 `cli/q2_run.py` 或可确认的训练脚本。因此不能使用不存在的命令执行问题二训练或预测。实现时应继续遵守附件二 train/valid/test 边界，并将每次结果写入 `E-q/q_2_output/<时间戳>/`。

## 测试与代码检查

运行全部当前单元测试：

```powershell
python -m unittest discover -s test -p "test_*.py" -v
```

只运行问题三测试（当前 `test/` 为目录而非 Python package）：

```powershell
python -m unittest discover -s test -p "test_q3.py" -v
```

检查问题一和问题三入口语法：

```powershell
python -m py_compile scripts/q1_extract_features.py cli/q3_run.py
```

测试重点包括：输入维度和字段、训练集标准化、padding mask、整模态缺失时的有限输出、标签范围、预测指标和反事实解释输出。正式实验前仍需人工检查数据切分、结果表和解释窗口是否与原始素材语义一致。

## 论文与 LaTeX 编译

问题三正文草稿为 `draft/q_3.md`，其 LaTeX 首版位于 `draft/q_3/`：

```powershell
$markdown = (Get-Content -Raw -Encoding utf8 draft/q_3.md).Replace('\[', '$$').Replace('\]', '$$')
$markdown | pandoc --from markdown+tex_math_dollars+raw_tex `
  --to latex --standalone --top-level-division=section `
  -V documentclass=ctexart `
  -V papersize=a4 -V fontsize=12pt -V geometry:margin=2.5cm `
  -V linestretch=1.5 -o draft/q_3/q_3.tex

xelatex -interaction=nonstopmode -halt-on-error `
  -output-directory=draft/q_3 draft/q_3/q_3.tex
xelatex -interaction=nonstopmode -halt-on-error `
  -output-directory=draft/q_3 draft/q_3/q_3.tex
```

编译结果为 `draft/q_3/q_3.pdf`；修改正文后应重新生成 TeX 并至少编译两次，以更新目录、交叉引用和长表格宽度。论文草稿中的实验数字必须来自对应输出目录，附件四只能写预测和解释，不能写无标签性能。

## 资料知识库

资料入口：

- `research/README.md`：资料库使用规则；
- `research/source-catalog.md`：来源清单和证据等级；
- `research/notes/`：阅读卡片；
- `research/library.db`：SQLite/FTS5 本地全文检索库。

重建知识库：

```powershell
python scripts/build_library.py --force
```

关键词检索：

```powershell
python scripts/search_library.py "CMU-MOSEI" --limit 10 --json
python scripts/search_library.py "缺失 模态" --limit 10 --json
python scripts/search_library.py "reliability" --limit 10 --json
```

知识库会索引 `references/`、`research/`、`prompts/` 和 `CMU-MOSEI/` 下的 PDF、Markdown 与 Python 源码；未完成下载文件不纳入索引。论文指标和外部项目结果只能作为待复现资料，不能直接写成 E 题实验结论。

## 推荐工作流程

1. 读取 `AGENTS.md`，确认数据边界和竞赛合规要求。
2. 读取 E 题题面、`versions/v3.md` 和对应建模文档。
3. 检查输入数据和依赖环境，不修改原始附件。
4. 先运行问题一数据审计和透明基线，确认主键、标签、维度、长度和时间映射。
5. 对问题二、问题三保持附件 2 的 train/valid/test 边界，先建立单模态和 masked late fusion baseline，再比较复杂模型。
6. 仅用训练集拟合标准化、特征选择和模型参数；仅用验证集选结构、超参数和阈值。
7. 对附件 3、附件 4 只做最终推理，不报告无标签专项集真实性能。
8. 保存配置、依赖版本、随机种子、日志、结果表、图表和异常清单。

## 验证命令

问题一脚本语法检查：

```powershell
python -m py_compile scripts/q1_extract_features.py
```

问题一输出核验：

```powershell
$latest = Get-ChildItem E-q/q_1_output -Directory | Sort-Object Name -Descending | Select-Object -First 1
python -c "import sys, numpy as np; z=np.load(sys.argv[1] + '/q1_aligned_features.npz'); print({k:v.shape for k,v in z.items()})" $latest.FullName
Get-Content (Join-Path $latest.FullName 'run_summary.json')
Get-Content (Join-Path $latest.FullName 'anomalies.csv')
```

当前项目暂无正式单元测试目录内容；每次增加模型代码后，应补充与风险相匹配的测试，至少覆盖数据字段、形状、mask、标签映射、切分边界和输出格式。

## 重要风险

- 文本时间戳当前为均匀推断，不是真实逐词对齐；论文中必须如实说明。
- 视频容器帧数与实际解码帧数可能不一致，应使用 `video_metadata.csv` 和 `anomalies.csv` 复核。
- 音频覆盖不足时必须依赖 `modality_mask`，不能把零特征当作有效语音。
- 统一 50 窗口会损失细粒度时间信息；更精确的对齐需要可靠时间戳或独立时间轴方案。
- 当前问题一特征是透明统计基线，不代表最终预测模型性能。
- CMU-MOSEI 论文中的指标、GitHub 项目中的预训练权重和外部数据结果都不能直接作为本项目结论。
- 任何未经过运行日志、验证集结果或题面核对的数字，都必须标记为待确认。

## 合规说明

本项目中的外部论文和开源代码仅用于概念理解、方法比较、代码调试和复现设计。团队需要自主决定建模假设、模型选择和最终结论；论文正文应逐项说明数据输入、预处理、模型、求解、评价指标、实验结果、消融、局限性和可复现材料索引。不得在提交材料中出现参赛单位、队员姓名或队伍编号等身份信息。
