# 华为杯数学建模资料库

本目录保存面向“华为杯”中国研究生数学建模竞赛的外部资料索引、研究笔记和可复用方法。资料以链接和摘要为主，不默认把整套论文、网盘压缩包或大型数据集复制进本仓库。

## 文件说明

- `source-catalog.md`：来源清单，区分官方来源、公开代码/论文、经验文章和待核验内容。
- `problem-trends.md`：2023--2025 年公开赛题矩阵、题型趋势与建模启示。
- `prompt-playbook.md`：Codex 项目中的提示词工作流、模板和反幻觉约束。
- `library.db`：由 `scripts/build_library.py` 生成的本地 SQLite/FTS5 检索库，索引论文文本、Markdown 笔记、专题工程源码和来源元数据。
- `../CMU-MOSEI/README.md`：CMU-MOSEI 专题资料总览，包含论文研究进展、模型框架、E 题适用性和 `Multimodal-Sentiment-Analysis` 工程审查；对应阅读卡片位于 `notes/cmu-mosei-literature.md`。

## 资料使用规则

1. 官方竞赛平台、题面、格式规范和 AI 工具使用规定优先于任何博客或开源仓库。
2. 开源仓库用于理解建模路线和复现实验，不把其中的结果直接当作本队结论，也不复制论文原文。
3. 论文或题面需要全文分析时，优先按 `source-catalog.md` 中的链接按需下载到本地临时目录，并记录来源、许可、文件哈希和用途。
4. 比赛期间必须先核对当届竞赛关于联网、生成式 AI、外部资料和成果署名的规定；不得让外部模型代替参赛者完成被禁止的工作。
5. 任何由资料推断出的结论都要标注为“资料归纳”，并在实际题目中重新验证。

## 推荐的本地资料层级

```text
research/
├── sources/       # 按需下载的公开资料；大文件默认不提交
├── notes/         # 针对某篇论文或某道题的阅读卡片
├── source-catalog.md
├── problem-trends.md
└── prompt-playbook.md
```

当前 `references/` 中已经存在一批此前下载的 2023--2025 优秀论文样本，详见该目录的 `README.md`。除这批既有缓存外，仍不建议继续批量下载版权不明的 PDF、网盘资料和竞赛数据。

## 检索数据库

首次建立或资料更新后运行：

```powershell
python scripts/build_library.py --force
```

关键词检索示例：

```powershell
python scripts/search_library.py "迁移学习" --year 2025 --problem E
python scripts/search_library.py "风电 疲劳 优化" --year 2024
python scripts/search_library.py "WLAN 吞吐" --limit 20 --json
```

数据库只作为候选资料定位器；正式引用前仍需打开原始论文、题面或官方文件核对上下文、页码和来源。

CMU-MOSEI 专题资料的使用顺序：先读 `CMU-MOSEI/README.md`，再用 `research/library.db` 按论文标题、模型名或“alignment/reliability/missing modality/explainability”等关键词定位原文，最后回到对应 PDF 和源码核对。资料中的实验指标只能作为待复现参考。
