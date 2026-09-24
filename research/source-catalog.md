# 来源清单

更新时间：2026-09-22。链接可访问性和页面内容会变化；重要事实在正式使用前应回到官方页面复核。

## 1. 官方与规则来源

| 来源 | 用途 | 可信度 | 备注 |
| --- | --- | --- | --- |
| [中国研究生创新实践系列大赛平台：数学建模竞赛](https://cpipc.acge.org.cn/cw/hp/4) | 报名、赛程、当届通知、竞赛规则和往届回顾 | A | 竞赛事实的首选来源；页面显示 2026 年第二十三届相关通知，不能用第三方资料替代当届通知 |
| [OpenAI Codex](https://openai.com/codex/) | Codex 产品定位和官方入口 | A | 项目级行为仍以当前 Codex 文档和本项目 `AGENTS.md` 为准 |
| [Codex AGENTS.md 指南](https://developers.openai.com/codex/guides/agents-md) | 项目指令文件的官方参考 | A | 当前环境访问该页受到 403，已记录链接但未把无法验证的细节当作事实 |
| [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering) | 提示词的结构化、约束、示例和评估思路 | A | 适用于提示词设计原则，不等同于竞赛规则 |

## 2. 历年题面、通知和论文索引

| 来源 | 覆盖范围 | 用途 | 可信度 |
| --- | --- | --- | --- |
| [zhanwen/MathModel](https://github.com/zhanwen/MathModel) | 公开整理了研究生赛题面、2023 年优秀论文索引、2023--2025 模板/通知/获奖信息 | 题面定位、论文样本、格式文件 | B+ |
| [zhanwen/MathModel：2023 研究生赛题](https://github.com/zhanwen/MathModel) | 仓库中 `国赛试题/2023年研究生数学建模竞赛试题` 目录下的 A--F 题面及附件 | 题型和数据结构分析 | B+ |
| [zhanwen/MathModel：2024 研究生赛题](https://github.com/zhanwen/MathModel) | 仓库中 `国赛试题/2024年研究生数学建模竞赛试题` 目录下的 A--F 题面及附件 | 题型和数据结构分析 | B+ |
| [zhanwen/MathModel：2023 优秀论文目录](https://github.com/zhanwen/MathModel) | 仓库中 `国赛论文/2023年优秀论文` 分题目录下的公开 PDF 样本 | 写作结构和方法对比 | B |
| [everythingisok0125-lang/Huawei01](https://github.com/everythingisok0125-lang/Huawei01) | 2025 A--F 题名、来源索引和公开资料说明 | 2025 题面交叉核验 | B |
| [LUORANCHENG/HUAWEI_Math_Modeling_Knowledge](https://github.com/LUORANCHENG/HUAWEI_Math_Modeling_Knowledge) | 2025 备赛计划、题型回顾、提示词范例和学习材料入口 | 经验归纳和工作流启发 | C |

## 3. 可复现代码和解法样本

| 来源 | 可借鉴内容 | 风险 |
| --- | --- | --- |
| [zhenhua-chen1/Postgraduate-Mathematical-Contest-in-Modelling2](https://github.com/zhenhua-chen1/Postgraduate-Mathematical-Contest-in-Modelling2) | 历年数据分析类代码，仓库说明称曾获一等奖 | 代码质量、数据泄漏和结果需逐行复核，不能直接采用 |
| [Jayc-Z/2022HuaweiCup](https://github.com/Jayc-Z/2022HuaweiCup) | 2022 E 题草原放牧策略的完整思路与技术路线 | 论文结果属于他队方案，适合学习拆题和复现，不适合直接移植结论 |
| [wxzher/2025-HuaweiCup-E](https://github.com/wxzher/2025-HuaweiCup-E) | 2025 E 题高速列车轴承的特征工程、CNN、迁移学习和 Grad-CAM 结构 | 深度学习结果依赖数据和训练设置，需检查随机种子、划分方式和计算资源 |
| [Nanqipro/25HuaweiCup_MCM](https://github.com/Nanqipro/25HuaweiCup_MCM) | 2025 C 题围岩裂隙识别、参数拟合、三维重构和钻孔优化案例 | 三等奖作品的公开实现，适合做工程流程参考而非“标准答案” |
| [latexstudio/GMCMthesis](https://github.com/latexstudio/GMCMthesis) | 全国研究生数学建模论文 LaTeX 模板和格式说明 | 模板版本需与当届官方格式规范核对 |

## 4. 资料质量判断

- **A：官方或原始发布方**。用于规则、赛程、格式、当届通知。
- **B：有明确仓库、题面或文件来源的公开资料**。用于题面定位、代码复现和结构对比。
- **C：个人博客、视频、经验帖或二次整理**。只用于发现关键词和候选方法，不作为唯一证据。

## 5. 暂不批量下载的原因

近三年优秀论文的公开集合规模较大，且部分通过网盘分发、版权和文件稳定性不明确。当前仓库已有一批本地缓存，详见 `references/README.md`；后续仍只下载与某一道题直接相关的少量论文，并在 `research/notes/` 建立阅读记录：来源 URL、下载日期、文件哈希、题目、方法、可复现性和可疑点。

## 6. CMU-MOSEI 专题资料

| 路径 | 内容 | 使用方式 | 证据状态 |
| --- | --- | --- | --- |
| `CMU-MOSEI/README.md` | CMU-MOSEI 论文、研究进展、模型框架、E 题映射和 GitHub 工程审查 | 先读总览，再按论文文件核对原文 | 资料归纳，指标须复现 |
| `research/notes/cmu-mosei-literature.md` | 可检索的专题阅读卡片和方法谱系 | 用于关键词检索和定位原始 PDF | 资料归纳 |
| `CMU-MOSEI/Multimodal-Sentiment-Analysis/` | PyTorch MulT、TFN 风格高阶融合、CTC 软对齐工程 | 仅作代码结构和基线参考，需适配 E-q | 源码已读，未完成 E 题复现 |
| `CMU-MOSEI/*.pdf` | 24 个本地论文/预印本文件 | 以本地文件为核对对象，正式引用前记录版本与哈希 | 原始文件，来源链接待逐份补齐 |

该专题资料由 `scripts/build_library.py` 纳入 `research/library.db`，索引 PDF、Markdown 和专题工程源码；未完成的 `.crdownload` 文件不纳入索引。
