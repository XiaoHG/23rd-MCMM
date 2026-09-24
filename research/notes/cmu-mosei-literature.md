# CMU-MOSEI 资料阅读卡片

本卡片是 `CMU-MOSEI/` 目录资料的知识库入口。详细分析见 [`CMU-MOSEI/README.md`](../../CMU-MOSEI/README.md)。

## 资料范围

- 24 个 PDF：CMU-MOSEI 数据集、TFN、MFN、MAG、多任务学习、COLD、不确定性/可靠性融合、对比学习、超图、专家模型、可解释融合和综述。
- `Multimodal-Sentiment-Analysis/`：PyTorch MulT/TFN/CTC 工程。
- `未确认 470226.crdownload`：未完成下载，不纳入结论。

## 方法谱系

| 阶段 | 代表资料 | 核心问题 | 对 E 题启示 |
| --- | --- | --- | --- |
| 2017--2018 | TFN、MFN、CMU-MOSEI/DFG | 高阶交互、动态记忆、异步模态 | 问题一保留时间映射，问题二比较高阶融合 |
| 2019--2020 | 多任务、MAG | 上下文联合任务、预训练语言模型适配 | 极性/强度联合学习，文本主导融合候选 |
| 2023--2024 | 综述、COLD | 方法分类、模态不确定性 | 建立术语和可靠性基线 |
| 2025--2026 | HAEMSA、HCRL、HCLF、RAF-Net、E-MoE、KAN-MCP | 专家、对比、可靠性、解释 | 设计局部缺失鲁棒性和解释忠实性消融 |

## 重要证据

- `P18-1208.pdf`：CMU-MOSEI 数据集论文和 Dynamic Fusion Graph；是问题一时间组织与问题三动态关系解释的主要依据。
- `D17-1115.pdf`：Tensor Fusion Network；是高阶交互基线来源。
- `2020.acl-main.214.pdf`：MAG-BERT/XLNet；是预训练语言模型融合候选。
- `COLD_Fusion_...pdf`、`Reliability-Aware_Adaptive_...pdf`、`3774905.3795845.pdf`、`electronics-15-03624.pdf`：问题二可靠性/不确定性候选。
- `2606.26473v1.pdf`：可靠性分数置换诊断；是问题三解释忠实性验证的重要依据。

## 使用限制

论文指标是原文报告，不能直接作为 E 题结果；外部数据集不能进入 E 题训练、调参、阈值选择和统计；CMU-MOSEI 工程需要适配 E-q 的 pickle 字段、有效长度、模态 mask 和双任务输出。

