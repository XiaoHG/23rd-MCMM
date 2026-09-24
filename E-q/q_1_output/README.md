# 问题一输出目录说明

本目录保存问题一“多模态情感特征提取与时序对齐”的历次运行结果。每次运行必须写入独立的时间戳子目录，例如：

```text
E-q/q_1_output/20260923_173914_388605600/
```

运行命令：

```powershell
python scripts/q1_extract_features.py --steps 50 --seed 20260923
```

## 一、题目要求与输出文件对应关系

### 1. 原始样本覆盖完整性

题目要求样本编号、模态文件和输出特征一一对应。当前使用以下稳定主键：

```text
sample_id = video_id + "_" + clip_id
```

对应文件如下：

| 要求 | 输出文件 | 说明 |
| --- | --- | --- |
| 样本编号和标签 | `labels.csv` | 保存附件 1 的 `video_id`、`clip_id`、`sample_id`、文本和标签 |
| 原始视频对应关系 | `input_file_manifest.csv` | 保存原始 MP4 路径、文件是否存在、文件大小和 SHA-256 |
| 特征行对应关系 | `sample_manifest.csv` | `feature_row_index` 指定样本在 NPZ 数组中的行号 |
| 三模态特征 | `q1_aligned_features.npz` | 保存 `text`、`audio`、`vision` 和掩码 |
| 样本处理状态 | `sample_manifest.csv` | 保存时长、有效窗口数、特征维度和异常状态 |

例如，若某条样本的 `feature_row_index=0`，则它对应：

```text
q1_aligned_features.npz["text"][0]
q1_aligned_features.npz["audio"][0]
q1_aligned_features.npz["vision"][0]
q1_aligned_features.npz["modality_mask"][0]
q1_aligned_features.npz["valid_lengths"][0]
```

当前完整运行结果为 100 条样本、100 个唯一 `sample_id`，没有因异常而静默删除样本。

### 2. 时序组织和原始素材对应

每条视频按有效时长划分为 50 个公共时间窗口：

\[
I_{i,k}=\left[\frac{kD_i}{50},\frac{(k+1)D_i}{50}\right),
\quad k=0,\ldots,49.
\]

`time_mapping.csv` 每个样本固定有 50 行，记录：

- `window_index`：公共时间窗口序号；
- `start_sec`、`end_sec`：窗口起止时间；
- `audio_sample_start`、`audio_sample_end`：对应音频采样位置；
- `frame_start`、`frame_end`、`frame_count`：对应视觉帧范围；
- `text_valid`、`audio_valid`、`vision_valid`：三种模态的有效状态；
- `text_time_source`、`audio_time_source`、`vision_time_source`：时间来源说明。

当前共有：

```text
100 个样本 × 50 个时间窗口 = 5000 条时间映射记录
```

文本没有使用真实逐词时间戳，因为附件 1 未提供该信息。当前文本时间通过视频时长对词元均匀分配，并在 `text_token_mapping.csv` 中标记为：

```text
inferred_uniform_text_timing
```

该规则可复现，但不能表述为真实的词级语音对齐。

### 3. 有效长度和填充规则

`q1_aligned_features.npz` 中的 `valid_lengths` 形状为 `(100, 3)`，三列依次表示：

```text
文本有效窗口数、音频有效窗口数、视觉有效窗口数
```

`modality_mask` 形状为 `(100, 50, 3)`，最后一维依次表示：

```text
[text_valid, audio_valid, vision_valid]
```

无效窗口的处理规则为：

```text
特征向量填充为 0
对应 modality_mask 设置为 0
```

后续模型必须使用 `modality_mask` 判断有效性，不能仅依据特征值是否为零来判断缺失。`valid_lengths` 是有效窗口数量，不代表有效窗口一定连续。

## 二、三模态特征定义

### 文本

- 从 `label-100.xlsx` 的 `text` 字段读取转写文本；
- 使用可复现的词元切分；
- 使用 SHA-256 稳定词元哈希生成 64 维表示；
- 增加 8 个词法统计量；
- 最终维度为 72；
- 输出数组：`text`，形状为 `(100, 50, 72)`。

### 音频

- 从 MP4 中提取音频；
- FFmpeg 转换为单声道、16000 Hz PCM；
- 每个公共时间窗口提取 12 个频带能量和 8 个时域/频域统计量；
- 最终维度为 20；
- 输出数组：`audio`，形状为 `(100, 50, 20)`。

### 视觉

- 使用 OpenCV 实际解码视频帧；
- 将帧缩放到 `64 x 36`；
- 提取 RGB、灰度、边缘、运动和空间差异统计量；
- 最终维度为 20；
- 输出数组：`vision`，形状为 `(100, 50, 20)`。

当前特征是透明基线，不等同于 BERT、COVAERP、Facet 或其他预训练情感特征。

## 三、复现和审计文件

| 文件 | 用途 |
| --- | --- |
| `run_config.json` | 工具、参数、随机种子、维度、时间规则和数据边界 |
| `run_summary.json` | 样本数、输出形状、异常数量和输出契约 |
| `validation_audit.json` | 自动检查样本覆盖、ID 对应、窗口数量、掩码、零填充和有限值 |
| `output_checksums.json` | 生成文件的 SHA-256 摘要 |
| `anomalies.csv` | 视频解码、帧数不一致和音频覆盖等异常记录 |
| `video_metadata.csv` | FPS、分辨率、容器帧数、实际解码帧数和音频状态 |
| `typical_sample.json` | 典型样本的文本、标签、时间和词元信息 |
| `typical_sample_timeline.png` | 典型样本三模态有效时间窗口可视化 |

最新完整运行目录中的自动审计结果为：

```text
processed_samples = 100
text shape = (100, 50, 72)
audio shape = (100, 50, 20)
vision shape = (100, 50, 20)
modality_mask shape = (100, 50, 3)
validation_audit.passed = true
```

## 四、异常和方法限制

当前有 90 条样本的 MP4 容器帧数与实际解码帧数不一致，另有音频窗口覆盖不足记录。这些问题均写入 `anomalies.csv`，没有被静默删除。视觉时间窗以实际成功解码帧重新分配，音频不足窗口保留有效掩码。

需要在论文中明确说明：

1. 文本时间是均匀推断代理，不是真实逐词时间戳；
2. 文本、音频和视觉特征是可审计基线，不应写成最优情感特征；
3. 当前视觉特征没有显式人脸表情或动作语义识别；
4. 当前音频特征是频谱和时域统计，不等同于专用语音情感模型；
5. 原始视频和标签只读，附件 1 的 100 条样本均保留。

完整建模说明见 [`E-q/modeling/q_1.md`](../modeling/q_1.md)，特征生成代码见 [`scripts/q1_extract_features.py`](../../scripts/q1_extract_features.py)。

## 五、当前问题一建模与技术细节

### 5.1 模型定位

当前问题一采用“基于公共相对时间轴的三模态特征提取与掩码对齐模型”。它的任务是把附件 1 的原始视频和转写文本转换为后续问题可读取、可定位、可复现的时序特征，不直接完成情感分类或情感强度回归。

模型的核心输出可以写为：

\[
H_i^{(T)}\in\mathbb{R}^{50\times72},\quad
H_i^{(A)}\in\mathbb{R}^{50\times20},\quad
H_i^{(V)}\in\mathbb{R}^{50\times20},
\]

以及三模态有效掩码：

\[
Q_i\in\{0,1\}^{50\times3}.
\]

100 条样本堆叠后得到：

```text
text:          (100, 50, 72)
audio:         (100, 50, 20)
vision:        (100, 50, 20)
modality_mask: (100, 50, 3)
valid_lengths: (100, 3)
```

这里的 50 是每条样本的公共时间位置数，不是原始视频都被切成相同秒数；每条样本先使用自己的有效时长，再进行相对时间归一化。

### 5.2 数学建模对象

第 (i) 个样本的三类原始序列分别表示为：

\[
X_i^{(m)}=\{x_{i,r}^{(m)},\tau_{i,r}^{(m)}\},
\qquad m\in\{T,A,V\},
\]

其中 (T)、(A)、(V) 分别表示文本、音频和视觉，(r) 是模态内部的位置，\(\tau_{i,r}^{(m)}\) 是该位置在样本时间轴上的时间区间。模态特征提取统一写成：

\[
z_{i,r}^{(m)}=f_m(x_{i,r}^{(m)};\theta_m),
\]

其中 \(f_m\) 是对应模态的确定性特征提取规则，\(\theta_m\) 是固定的切分、采样和统计参数。当前版本不使用外部情感数据拟合这些参数。

样本主键定义为：

```text
sample_id = video_id + "_" + clip_id
```

它负责跨文件关联；`feature_row_index` 负责指出该样本在 NPZ 数组第一维中的位置。二者共同避免把目录遍历顺序误当作样本对应关系。

### 5.3 公共时间窗对齐

令样本 (i) 的有效视频时长为 (D_i)，令公共窗口数为 (L=50)，则第 (k) 个窗口定义为：

\[
I_{i,k}=\left[\frac{kD_i}{L},\frac{(k+1)D_i}{L}\right),
\qquad k=0,1,\ldots,L-1.
\]

使用半开区间的原因是相邻窗口只共享边界而不重复计数。对模态 (m)，窗口特征由落入该时间区间的原始特征聚合得到：

\[
h_{i,k}^{(m)}=
\operatorname{Agg}\left(
\left\{z_{i,r}^{(m)}:
\tau_{i,r}^{(m)}\cap I_{i,k}\neq\varnothing
\right\}\right).
\]

当前的 `Agg` 规则为：

```text
文本：窗口内词元特征取均值
音频：窗口内波形直接计算频谱和时域统计量
视觉：窗口内实际解码帧的图像统计特征取均值
```

该方案将不同采样率的模态放入同一个相对时间坐标，但没有声称文本获得了真实词级时间戳。文本时间来源单独标记为 `inferred_uniform_text_timing`。

### 5.4 文本特征技术细节

文本由 `label-100.xlsx` 的 `text` 字段提供。当前采用正则规则切分英文单词、带撇号单词、数字和标点，不依赖外部词表。

对词元 (w) 使用两个 SHA-256 哈希位置生成 64 维稳定哈希表示：

\[
(j_s,\eta_s)=g(w,s),\qquad s\in\{0,1\},
\]

并在对应位置累加：

\[
e(w)_{j_s}\mathrel{+}=\frac{\eta_s}{\sqrt{2}}.
\]

同时加入 8 个词法统计量：

```text
是否字母、是否数字、是否标点、归一化词长、元音比例、
首字母是否大写、是否含问号/感叹号、词元相对位置
```

因此单个词元特征维度为：

\[
d_T=64+8=72.
\]

附件 1 没有真实逐词时间戳。若一条文本有 (n_i) 个词元，则第 (r) 个词元采用均匀推断区间：

\[
\hat{\tau}_{i,r}^{(T)}=
\left[\frac{rD_i}{n_i},\frac{(r+1)D_i}{n_i}\right).
\]

词元所属窗口由其区间中心确定；同一窗口有多个词元时取均值。所有词元的索引、推断区间、窗口编号和时间来源写入 `text_token_mapping.csv`。

### 5.5 音频特征技术细节

音频由 FFmpeg 从 MP4 中解码为单声道、16000 Hz 的 PCM 波形。对第 (k) 个时间窗，其采样区间为：

\[
N_{i,k}=\left[
\lfloor t_{i,k}^{\mathrm{start}}f_s\rfloor,
\lfloor t_{i,k}^{\mathrm{end}}f_s\rfloor
\right),
\qquad f_s=16000.
\]

窗口波形先去均值，再计算功率谱：

\[
P_{i,k}(f)=|\operatorname{FFT}(a_{i,k})|^2.
\]

音频特征由两部分组成：

1. 将 0--8000 Hz 等分为 12 个频带，计算每个频带平均能量并使用 \(\log(1+x)\) 压缩；
2. 计算 RMS、过零率、谱质心、谱带宽、85% 谱滚降、归一化谱熵、波形峰值和标准差。

最终维度为：

\[
d_A=12+8=20.
\]

窗口有效采样点少于 32 时，该窗口写入零向量并设置 `audio_valid=0`；否则设置为 1。采样起止位置和实际采样点数写入 `time_mapping.csv`。

### 5.6 视觉特征技术细节

视觉使用 OpenCV 实际逐帧解码，先将每帧缩放至 `64 x 36`，再转换为 RGB 和灰度图。每帧提取 20 维统计特征：

```text
RGB 全图均值                 3 维
RGB 全图标准差               3 维
灰度均值和标准差             2 维
Canny 边缘密度               1 维
与上一帧的灰度平均绝对差     1 维
中心区域 RGB 均值            3 维
上下区域 RGB 均值差          3 维
左右区域 RGB 均值差          3 维
窗口帧数/容器声明帧数        1 维
```

因此：

\[
d_V=3+3+2+1+1+3+3+3+1=20.
\]

每个实际解码帧依据其顺序分配到 50 个窗口，同一窗口内的帧特征取均值。容器声明帧数只用于记录和异常比较；当它与实际解码帧数不一致时，时间组织使用实际解码帧，避免引用错误元数据。

### 5.7 掩码、有效长度和填充

三模态有效掩码定义为：

\[
q_{i,k}^{(m)}=
\mathbf{1}\left(
\exists r,\ 
\tau_{i,r}^{(m)}\cap I_{i,k}\neq\varnothing
\right).
\]

代码中：

```text
modality_mask[i, k, 0] = text_valid
modality_mask[i, k, 1] = audio_valid
modality_mask[i, k, 2] = vision_valid
```

对每个模态，`valid_lengths` 定义为：

\[
\ell_i^{(m)}=\sum_{k=0}^{49}q_{i,k}^{(m)}.
\]

它是有效窗口数量，不保证有效窗口连续。无效窗口的特征向量为零，但零值必须与掩码一起解释：

```text
特征值 = 0 且 mask = 0：没有有效观测或被填充
特征值接近 0 且 mask = 1：可能是真实信号特征
```

因此，问题二和问题三中的池化、注意力和融合过程必须显式使用 `modality_mask`，不能仅用特征值是否为零判断缺失。

### 5.8 当前建模的算法流程

```text
1. 读取 label-100.xlsx 和原始 MP4 目录
2. 构造 sample_id，检查标签主键唯一性
3. 按 video_id/clip_id 定位 MP4，记录大小和 SHA-256
4. 读取视频元数据并实际解码视频帧
5. 用 FFmpeg 解码单声道 16 kHz 音频
6. 对文本生成词元特征和均匀推断时间区间
7. 按样本有效时长划分 50 个半开公共时间窗
8. 计算各窗口的文本、音频和视觉特征
9. 生成三模态有效掩码和 valid_lengths
10. 输出特征数组、标签清单、时间映射和异常记录
11. 自动检查样本覆盖、ID 顺序、窗口数、掩码、零填充和有限值
```

### 5.9 计算与复现参数

当前正式运行固定：

```text
脚本：scripts/q1_extract_features.py
随机种子：20260923
公共时间窗：50
文本维度：72
音频维度：20
视觉维度：20
音频采样率：16000 Hz
视频缩放尺寸：64 x 36
音频最小有效窗口采样数：32
```

问题一当前特征提取主要是逐样本视频解码和音频 FFT，计算量随视频总帧数、音频采样点数和文本词元数近似线性增长；单个音频窗口的频谱计算受 FFT 长度限制。脚本不依赖训练集拟合标准化参数，因此当前问题一不会产生由训练/验证切分造成的标准化泄漏。运行配置、源文件摘要和输出摘要分别保存在 `run_config.json`、`input_file_manifest.csv` 和 `run_summary.json`。

### 5.10 模型的适用边界

当前模型的主要价值是建立一个透明的、可审计的输入基线：它保证样本覆盖、公共时间组织、模态有效性和原始位置映射。它不是情感预测器，也没有证明某一模态对情感标签的因果贡献。

当前最重要的技术限制有三点：

1. 文本时间是均匀推断，不是真实词级强制对齐；
2. 文本哈希特征、音频统计特征和视觉统计特征不具备预训练模型的高级语义表达能力；
3. 90 条样本存在容器帧数与实际解码帧数差异，1 条样本存在音频窗口覆盖不足，这些现象已被记录并通过掩码处理，但仍应在论文中作为数据质量限制说明。

后续替换为 BERT、语音情感模型、视觉表情模型或可学习跨模态对齐模块时，必须保留本板块规定的 `sample_id`、`feature_row_index`、时间映射、`modality_mask`、`valid_lengths` 和异常记录接口。
