# 23rd-MCMM

2026 年第二十三届中国研究生数学建模竞赛 E 题项目。当前题目为“复杂场景下多模态情感预测的数学建模与算法设计”，项目使用 Python 完成资料整理、数据审计、三模态特征提取、时序对齐、后续鲁棒预测和可解释性分析。

## 项目状态

当前已经完成：

- E 题原始题面和附件的工作副本整理；
- CMU-MOSEI 相关论文、模型和 GitHub 工程资料分析；
- 问题一透明基线特征提取和时间对齐脚本；
- 100 条原始视频的特征、掩码、时间映射、异常清单和典型样本输出；
- 本地论文与源码知识库索引。

当前尚未完成：

- 问题二的局部模态缺失鲁棒预测模型；
- 问题三的完整预测、解释卡和附件 4 专项推理；
- 问题二、问题三的正式实验表、消融结果和论文结论。

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
├── src/                               # 预留的可复用核心代码目录
├── cli/                               # 预留的命令行入口
├── test/                              # 预留的测试目录
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
python -m pip install numpy pandas openpyxl opencv-python matplotlib pymupdf
```

如果运行 CMU-MOSEI 下的 PyTorch 基线工程，还需要按照本机 CPU/CUDA 版本从 PyTorch 官方渠道安装匹配版本的 `torch`。不要盲目复制不匹配的 CUDA 安装命令；先执行：

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

如需使用 Transformer 预训练模型，再按实际模型和许可安装：

```powershell
python -m pip install transformers
```

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
- [问题二建模](E-q/modeling/q_2.md)：当前为空，待实现局部模态缺失鲁棒预测。
- [问题三建模](E-q/modeling/q_3.md)：当前为空，待实现可解释性情感预测。
- [版本分析](versions/v3.md)：问题一版本定位、资料结论和迭代要求。

## CMU-MOSEI 资料与基线工程

`CMU-MOSEI/` 保存相关论文、研究进展总结和 `Multimodal-Sentiment-Analysis` GitHub 项目。

- [专题总览](CMU-MOSEI/README.md)：论文创新点、模型框架、E 题适用性和工程审查。
- [专题阅读卡片](research/notes/cmu-mosei-literature.md)：研究方法谱系和证据入口。
- `CMU-MOSEI/Multimodal-Sentiment-Analysis/`：包含 MulT 跨模态 Transformer、TFN 风格高阶融合和 CTC 式软对齐代码。

该工程可以作为问题二/三的下游基线参考，但不能直接解决问题一。它读取特定格式的预计算 pickle，没有处理附件 1 原始视频审计、局部缺失 mask、E 题双任务输出和可回溯解释；使用前必须重写数据适配器并核验标签、padding 和有效长度。

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
