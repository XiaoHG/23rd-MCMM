---
title: "GitHub - xzwwwwww/Enhanced-mathmodel-Codex-skills: 增强版的数学建模skills，专门用于codex智能体使用，全流程自动生成一篇数学建模论文"
author: "Xzwwwwww"
date: "2026-05-06"
sitename: "GitHub"
source_url: "https://github.com/xzwwwwww/enhanced-mathmodel-codex-skills"
source_url_canonical: "https://github.com/xzwwwwww/enhanced-mathmodel-codex-skills"
search_query: "数学建模 codex"
search_title: "GitHub - xzwwwwww/Enhanced-mathmodel-Codex-skills: 增强版的数学建模skills，专门用于codex智能体使用，全流程自动生成一篇数学建模论文"
search_snippet: "增强版数学建模 Codex skills 套件，用于把数学建模赛题从“题面与附件”推进到“模型路线、实验模板、论文草稿、Word 文档和最终 QA 报告”。"
---

增强版数学建模 Codex skills 套件，用于把数学建模赛题从“题面与附件”推进到“模型路线、实验模板、论文草稿、Word 文档和最终 QA 报告”。
本仓库基于 Codex 全局 skills 机制组织，只使用全局路径 ~/.codex/skills。
这套 skills 主要覆盖数学建模论文生产的完整流程：
- 读取赛题文件，拆解问题一/二/三。
- 判断任务类型，例如预测、评价、优化、聚类、仿真、图论等。
- 生成模型推荐路线，包括基线模型、改进模型、评价指标、验证方式和风险点。
- 根据模型路线生成可运行实验模板。
- 清洗附件数据并生成探索性图表。
- 生成论文微单元任务清单。
- 批量生成论文微单元并合并为 final_paper.md 。
- 生成 final_paper.docx 。
- 执行最终 QA，检查占位符、章节缺失、图表断链、基线/验证缺失、Word 是否存在等问题。
| Skill | 作用 | 
|---|---|
| paper-workflow-orchestrator | 一键总流程入口，负责串联所有步骤。 | 
| problem-doc-model-selector | 解析赛题 PDF/DOCX/TXT，生成问题映射和外部数据需求。 | 
| modeling-paper-rubric-and-model-selector | 模型方法库、结构化模型推荐、实验模板生成。 | 
| data-cleaning-and-visualization | 清洗附件/外部数据并生成 EDA 图表。 | 
| quality-assurance-auditor | 生成任务清单，并做最终论文质量审计。 | 
| paper-micro-unit-generator | 按任务清单生成微单元并合并论文。 | 
| authoritative-data-harvester | 根据 data_requirements.json 获取或提示补充外部数据。 | 
| context-memory-keeper | 记录阶段状态、文献/数据来源和上下文记忆。 | 
将本仓库的 skills/ 下所有目录复制到全局 Codex skills 目录：
cp -R skills/* ~/.codex/skills/
然后重启 Codex，使新 skills 生效。
安装后目录应类似：
~/.codex/skills/
├── authoritative-data-harvester/
├── context-memory-keeper/
├── data-cleaning-and-visualization/
├── modeling-paper-rubric-and-model-selector/
├── paper-micro-unit-generator/
├── paper-workflow-orchestrator/
├── problem-doc-model-selector/
└── quality-assurance-auditor/
每个数学建模项目建议使用独立目录。进入项目目录后运行总流程。
your-mathmodel-project/
├── problem_files/        # 放赛题 PDF/DOCX/TXT 和附件数据
├── crawled_data/         # 可选，放外部补充数据
└── paper_output/         # 自动生成，存放所有输出
初始化项目目录：
python ~/.codex/skills/paper-workflow-orchestrator/scripts/run_mathmodel.py --init-only
然后把赛题和附件放入：
problem_files/
支持常见文件：
- .txt
- .md
- .csv
- .xlsx
- .xls
- .docx
- .pdf
PDF/DOCX 解析依赖本机是否安装了对应 Python 包；如果缺少依赖，脚本会降级提示。
在项目根目录运行：
python ~/.codex/skills/paper-workflow-orchestrator/scripts/run_mathmodel.py
总流程会依次执行：
赛题解析
-> 外部数据需求检查
-> 模型推荐
-> 实验模板生成
-> 数据清洗与可视化
-> QA 任务清单
-> 微单元生成
-> 合并 Markdown
-> 生成 Word
-> 最终 QA 审计
如果 problem_files/ 为空，流程会阻塞并提示你先放入赛题和附件。
运行后主要产物在 paper_output/：
paper_output/
├── step1/
│   ├── problem_analysis.md      # 赛题解析报告
│   └── question_map.json        # 子问题、任务类型、约束、指标映射
├── plan/
│   ├── model_recommendations.md # 模型推荐报告
│   └── model_recommendations.json
├── experiments/
│   ├── experiment_templates.md
│   ├── experiment_templates_manifest.json
│   └── *.py                     # 可运行实验模板
├── data_cleaned/                # 清洗后的数据
├── figures/                     # 自动生成的图表
├── tasks.json                   # 微单元任务清单
├── micro_units/                 # 微单元文本
├── generate_log.json            # 生成日志
├── final_paper.md               # 合并后的论文草稿
├── final_paper.docx             # Word 版本
├── ref_check.md                 # 图表/公式引用检查
├── qa_report.md                 # 最终 QA 报告
└── qa_report.json
适合想直接从赛题跑到论文草稿：
python ~/.codex/skills/paper-workflow-orchestrator/scripts/run_mathmodel.py
适合调试、补跑或单独使用某个能力。
只初始化目录：
python ~/.codex/skills/paper-workflow-orchestrator/scripts/run_mathmodel.py --init-only
只做最终 QA：
python ~/.codex/skills/paper-workflow-orchestrator/scripts/run_mathmodel.py --audit-only
只解析赛题：
python ~/.codex/skills/problem-doc-model-selector/scripts/parse_problem.py --project . --write-data-requirements
只生成模型推荐：
python ~/.codex/skills/modeling-paper-rubric-and-model-selector/scripts/recommend_models.py \
  --file problem_files/problem.txt
只生成实验模板：
python ~/.codex/skills/modeling-paper-rubric-and-model-selector/scripts/generate_experiment_templates.py --project .
只做数据清洗与可视化：
python ~/.codex/skills/data-cleaning-and-visualization/scripts/run_pipeline.py
只生成任务清单：
python ~/.codex/skills/quality-assurance-auditor/scripts/pipeline.py
只生成微单元：
python ~/.codex/skills/paper-micro-unit-generator/scripts/generate_all_offline.py
只合并论文：
python ~/.codex/skills/paper-micro-unit-generator/scripts/merge.py
模型推荐完成后，会根据推荐类型生成实验模板到：
paper_output/experiments/
当前模板包括：
- forecasting_regression.py ：预测/回归基线。
- evaluation_ranking.py ：熵权 TOPSIS 综合评价。
- optimization_scheduling.py ：资源分配/0-1 优化基线。
- clustering_profile.py ：K-means 聚类画像。
- sensitivity_analysis.py ：参数扰动敏感性分析。
- monte_carlo_simulation.py ：Monte Carlo 不确定性仿真。
这些模板是可运行起点，不是最终答案。你需要根据赛题字段、目标函数和约束进一步修改。
核心流程尽量做了降级处理，但以下包会增强能力：
pip install pandas numpy matplotlib seaborn python-docx requests
可选 PDF 解析：
pip install pymupdf pdfplumber
如果缺少 pandas 或 seaborn，数据清洗/可视化会跳过，但总流程仍会继续生成论文骨架和 QA 报告。
本套件已经去掉 .trae/skills 和项目内 .codex/skills 兼容逻辑。
技能代码只从：
~/.codex/skills
读取。
项目目录只用于：
- 读取 problem_files/
- 读取 crawled_data/
- 写入 paper_output/
- 写入可选的 data_requirements.json
把赛题 PDF/DOCX/TXT 和附件数据放入：
problem_files/
再运行一键流程。
通常是缺少依赖：
pip install pandas numpy matplotlib seaborn
可能原因：
- 附件数据不是 CSV/Excel/TXT。
- 缺少 pandas 、matplotlib 或seaborn 。
- 数据中没有足够的数值列。
当前 final_paper.docx 由 python-docx 直接生成，公式会以 LaTeX 源码形式保留。需要正式排版时，可在 Word 中用 MathType 或公式工具进一步处理。
QA 只检查结构性问题，例如缺章节、占位符、断链、基线/验证描述等。正式参赛前仍需要人工补充真实实验结果、图表解释、参考文献和排版。
- 新建项目目录。
- 运行 --init-only 。
- 放入赛题和附件。
- 运行一键总流程。
- 查看 paper_output/step1/problem_analysis.md 和paper_output/plan/model_recommendations.md 。
- 修改 paper_output/experiments/ 中的实验模板，跑出真实结果。
- 重新运行合并和 QA。
- 人工润色 final_paper.docx 。
.
├── README.md
├── .gitignore
└── skills/
    ├── authoritative-data-harvester/
    ├── context-memory-keeper/
    ├── data-cleaning-and-visualization/
    ├── modeling-paper-rubric-and-model-selector/
    ├── paper-micro-unit-generator/
    ├── paper-workflow-orchestrator/
    ├── problem-doc-model-selector/
    └── quality-assurance-auditor/
不要把 GitHub token、私有数据、未公开赛题答案或个人隐私数据提交到仓库。problem_files/、paper_output/、crawled_data/ 已在 .gitignore 中忽略。
