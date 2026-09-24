# 问题一输出说明

本目录由 `scripts/q1_extract_features.py` 自动生成，运行编号为 `20260923_173914_388605600`。上级目录 `E-q/q_1_output/` 保存历次运行结果，本次运行不会覆盖历史结果。

## 运行

```powershell
python scripts/q1_extract_features.py
```

## CSV 兼容说明

CSV 使用 UTF-8 BOM，并对以 `=、+、-、@` 开头的文本字段添加 Excel 安全前缀 `'`，防止 `video_id`、`sample_id` 等内容被 Excel 当作公式而显示为 `#NAME?`。Excel 打开时会显示原始文本；使用 Python `csv` 读取时，如需还原机器主键，应去除字段开头的单个 `'`。

## 核心文件

- `q1_aligned_features.npz`：`text/audio/vision` 三模态特征、`modality_mask`、`valid_lengths` 和 `sample_ids`。
- `labels.csv`：从附件 1 标签表读取的原始标签副本。
- `sample_manifest.csv`：100 条样本的处理状态、时长、维度和异常标记。
- `video_metadata.csv`：视频帧率、分辨率、帧数、时长及音频解码信息。
- `time_mapping.csv`：公共时间窗到音频采样点、视频帧和三模态有效状态的映射。
- `text_token_mapping.csv`：词元到均匀推断时间区间的映射。
- `anomalies.csv`：异常样本和处理状态。
- `typical_sample.json`、`typical_sample_timeline.png`：典型样本核验材料。
- `run_config.json`、`run_summary.json`：参数、特征定义、数据边界和运行摘要。

## 特征与时间说明

文本特征为固定 SHA-256 词元哈希向量加 8 个词法统计量；音频特征由 FFmpeg 解码为单声道 16 kHz 后提取 12 个频带能量和 8 个信号统计量；视觉特征由 OpenCV 提取颜色、灰度、边缘、运动和空间差异统计量。三种特征均按视频时长划分为 50 个公共时间窗。附件 1 未提供逐词时间戳，因此文本时间区间标记为 `inferred_uniform_text_timing`，只能视为可复现的时间代理。

本输出是问题一的透明基线特征，不等同于 BERT、COVAERP 或 Facet 特征。后续替换特征提取器时，应保持 `sample_id`、时间映射、有效掩码和输出文件契约。


## Audit contract

- `sample_manifest.csv` contains one row per source label and the stable `feature_row_index` used by all NPZ arrays.
- `input_file_manifest.csv` maps every sample to its source MP4 and records existence, size, and SHA-256.
- `validation_audit.json` checks sample coverage, one-to-one IDs, time-window counts, finite features, binary masks, and zero padding.
- `output_checksums.json` records SHA-256 digests for generated artifacts.
- Invalid windows are zero padded and must be identified through `modality_mask=0`; `valid_lengths` counts valid windows and does not claim contiguity.
