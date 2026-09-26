---
title: "math-modeling-skill"
date: "2026-06-01"
sitename: "SkillsLLM"
source_url: "https://skillsllm.com/skill/math-modeling-skill"
source_url_canonical: "https://skillsllm.com/skill/math-modeling-skill"
search_query: "数学建模 codex"
search_title: "math-modeling-skill - AI Agents on GitHub"
search_snippet: "June 1, 2026 - math-modeling-skill is an open-source ai agents skill for AI coding assistants such as Claude Code, Codex CLI, and ChatGPT, built by XiaoMaColtAI. 数学建模技能 - 面向 CUMCM、MCM/ICM 等数学建模竞赛的三阶段…"
---

by XiaoMaColtAI
数学建模技能 - 面向 CUMCM、MCM/ICM 等数学建模竞赛的三阶段工作流：建模分析、Python/MATLAB 编程与 DOCX 论文生成。包含丰富的算法资源库(优化/预测/评价/图论/机器学习等)、角色指导文档、论文模板和实用工具脚本
# Add to your Claude Code skills
git clone https://github.com/XiaoMaColtAI/math-modeling-skill
Guides for using ai agents skills like math-modeling-skill.
Last scanned: 6/1/2026
{
  "issues": [],
  "status": "PASSED",
  "scannedAt": "2026-06-01T09:27:20.482Z",
  "npmAuditRan": true,
  "pipAuditRan": true
}
See how math-modeling-skill compares with popular alternatives.
math-modeling-skill is an open-source ai agents skill for AI coding assistants such as Claude Code, Codex CLI, and ChatGPT, built by XiaoMaColtAI. 数学建模技能 - 面向 CUMCM、MCM/ICM 等数学建模竞赛的三阶段工作流：建模分析、Python/MATLAB 编程与 DOCX 论文生成。包含丰富的算法资源库(优化/预测/评价/图论/机器学习等)、角色指导文档、论文模板和实用工具脚本. It has 1,696 GitHub stars.
Yes. math-modeling-skill passed SkillsLLM's automated security scan — a dependency vulnerability audit plus prompt-injection heuristics — with no high-severity issues. You can read the full report in the Security Report section on this page.
Clone the repository with "git clone https://github.com/XiaoMaColtAI/math-modeling-skill" and add it to your Claude Code skills directory (see the Installation section above). math-modeling-skill ships a SKILL.md manifest, so compatible agents can discover and load it automatically.
math-modeling-skill is primarily written in Python. It is open-source under XiaoMaColtAI on GitHub, so you can review or fork the full source.
Yes. SkillsLLM lists many other AI Agents skills you can browse and compare side by side. Open the AI Agents category from the badge at the top of this page, or use the Related Skills and comparison links further down to weigh math-modeling-skill against similar tools.
No comments yet. Be the first to share your thoughts!
⚠️ Third-Party Software Notice
This skill is third-party open-source software developed and hosted independently on GitHub. SkillsLLM is an informational directory and does not control or maintain the underlying repository.
Any security checks, ratings, or warnings displayed by SkillsLLM are automated and limited in scope. They do not constitute a security certification or guarantee that the software is safe, error-free, or free from malicious code, vulnerabilities, compromised dependencies, or prompt-injection risks.
Review the source code, permissions, dependencies, and configuration before installing or running any third-party skill. Use is at your own risk. To the maximum extent permitted by applicable law, SkillsLLM is not liable for losses arising from third-party software.
本 Skill 用三个独立角色完成数学建模。生成的论文仅供用户参考，不作为可直接提交的作品。论文结构与格式必须以目标竞赛当届官方规则和官方模板为准，不能用往届经验替代官方要求。
使用前：请先阅读根目录 使用指南.md，明确本 Skill 的交付物使用边界，并把它复制到工作区（PROJECT_ROOT）：
PowerShell（Windows）：
Copy-Item "<SKILL_ROOT>\使用指南.md" "<PROJECT_ROOT>\使用指南.md"
bash（macOS/Linux）：
cp "<SKILL_ROOT>/使用指南.md" "<PROJECT_ROOT>/使用指南.md"
<SKILL_ROOT> 是本 Skill 的安装目录（含 SKILL.md 的目录），<PROJECT_ROOT> 是你的题目/项目目录。
用户明确点名本 Skill 或任务命中本 Skill 时，严格执行以下协议；不要把它降级为建议：
SKILL_ROOT、PROJECT_ROOT、当前阶段、目标竞赛与届次、计划读取的角色和工具入口。未确认的官方规则明确标为待核验。SKILL.md；使用 PDF、Excel、论文搜索、DOCX 或 LaTeX 时，再实际读取对应工具的 references/Subagent调度.md 在关键节点立即派发独立质检；禁止等全流程结束后才首次派发，作者自检不能替代独立验收。除固定质检外，不主动派发其他 Subagent；仅在用户明确启用具体协作任务时按所选范围执行。references/交付与截止时间协议.md，核验当届官方截止时间与提交约束，尽早走通完整导出链路并维护可立即提交的 Checkpoint V1；后续优化不得破坏该版本。M1/P1/P2/W1/W2 质检 Subagent；调研、原型和并行实验等可选协作默认关闭，不询问、不暂停流程。M1 建模终检、P1 最小可运行结果、P2 编程终检、W1 证据大纲和 W2 论文终检。FAIL 必须按证据返回对应角色修正并复验；被审产物发生实质变化时，相关 PASS 立即失效。BLOCKED 或受限交付并明确报告“独立验收未完成”，不得把主 Agent 自检描述为独立通过或声称完整完成。
详细的默认开关、可选协作任务、派发输入、固定回执和并行边界见 references/Subagent调度.md。
| 用户意图 | 加载入口 | 是否要求前一阶段已完成 | 
|---|---|---|
| 完整建模、完成整题 | references/roles/建模手/SKILL.md →references/roles/编程手/SKILL.md →references/roles/论文手/SKILL.md | 按顺序执行 | 
| 只做题目分析、选模型 | references/roles/建模手/SKILL.md | 否 | 
| 只写代码、跑结果、出图 | references/roles/编程手/SKILL.md | 需要题目和可执行的模型说明；缺失时先补齐必要分析 | 
| 只写或修改论文 | references/roles/论文手/SKILL.md | 需要题目、模型、真实运行结果和图表；缺失时回退到对应阶段 | 
不要在单阶段任务中强制执行完整流程。
只交付：
题目分析报告.md术语表格.md
交付：
.py）或 MATLAB（.m）代码；可同时交付两种语言。.csv、题目要求的 .xlsx。raw_q1_*、process_q1_*、result_q1_* 等格式，不设上限。相同内容的 SVG、PNG 和灰度预览按 1 张逻辑图计数。flow_overall_model.*、flow_qN_model.*，与三类候选图分开计数，不替代结果图。results/复现清单.json，含随机种子、输入文件 SHA-256、运行时和依赖版本、关键参数、唯一复现命令。
默认交付 Word 论文；用户显式要求时才生成 LaTeX 论文。
完整论文.docx；由 LaTeX 转换时同时保留哈希绑定的 .conversion.json。完整论文-LaTeX/ 源码项目、由其实际编译得到的 完整论文.pdf 和哈希绑定的 .build.json。
用户明确要求 LaTeX 时，同时生成两种格式且正文内容、数据、图表和结论保持一致。内部检查记录不作为额外交付物。
无论目标竞赛为何，论文默认至少包含 8 幅正式图；当届官方规则或用户明确要求与此冲突时，以其要求为准并记录依据。
先读当前阶段的 SKILL.md，再按其中“何时加载”表读取所需参考，禁止一次性加载全部资料。
| 当前任务 | 额外读取 | 
|---|---|
| 选模型或查算法 | references/算法索引.md ，再读取一个或少数几个相关assets/*.md | 
| 搜索论文 | tools/paper_search/SKILL.md | 
| 读取题目 PDF | tools/pdf/SKILL.md | 
| 处理 Excel | tools/xlsx/SKILL.md | 
| 画图 | tools/figure/SKILL.md | 
| 生成 Word 论文 | tools/docx/SKILL.md | 
| 生成 LaTeX 论文 | tools/latex/SKILL.md | 
| LaTeX 论文转 Word | tools/docx/SKILL.md | 
| 派发 Subagent 或阶段质检 | references/Subagent调度.md | 
| 真实竞赛、截止时间或最终提交 | references/交付与截止时间协议.md | 
完整导航见 references/README.md。
面向数学建模竞赛与建模项目的三阶段工作流
关注我
本 Skill 将数学建模任务拆分为 建模分析 → 代码实现 → 论文撰写 三个阶段。既可以按顺序完成整道题，也可以只执行其中一个阶段。
当前版本：1.3.0
生成的论文仅供参考。论文结构与格式必须以目标竞赛当届官方规则和官方模板为准。
| 阶段 | 角色 | 核心任务 | 独立门禁 | 固定交付物 | 
|---|---|---|---|---|
| ① | 建模手 | 理解题目、设计模型、定义算法和验证方案 | M1 建模终检 | 题目分析报告.md 、术语表格.md | 
| ② | 编程手 | 编写并运行 Python/MATLAB，生成结果与图 | P1 最小可运行结果、P2 编程终检 | 代码、结果表格、三类各至少 3 张且覆盖全部子问题的候选图、至少 1 幅总体建模流程图、 results/复现清单.json | 
| ③ | 论文手 | 基于真实结果构建论证并生成 Word 论文 | W1 证据大纲、W2 论文终检 | 至少 8 幅且覆盖全部子问题的正式图；默认交付 完整论文.docx ；用户显式要求时同时交付 LaTeX 源码项目、PDF 与哈希清单 | 
质检 Subagent 是阶段内只读验收者，不是第四个固定角色。默认只启用固定质检；其他协作仅在用户明确选择后运行。P1 在全量计算和正式出图前执行，W1 在长篇正文和双格式排版前执行；禁止等全流程结束后才首次质检。完整协议见 Subagent 调度与阶段门禁。
本 Skill 可用于支持本地 Skills 或 Agent 工作流的工具，例如 Claude Code、Codex、Cursor、Trae 和 Qoder。具体加载方式以对应工具的当前文档为准。
本仓库同时提供 DeepSeek Harness（dsh）的 Agent 预设：dsh-plugin/math-modeling-agent/，把三阶段工作流、五门禁质检、任务看板与完成判定封装为 mm_* 工具，供 dsh 桌面端使用。
安装：把整个 dsh-plugin/math-modeling-agent/ 目录复制到本机 dsh 预设根目录（<dsh-home>\.agent-presets\，Windows 默认 C:\Users\<用户名>\AppData\Roaming\dsh-desktop\dsh-home\.agent-presets），目录名即预设 id（如 math-modeling）。也可直接复制 dsh-plugin/README.md 中附带的安装提示词给 dsh Agent 自动完成安装。
使用：新建 dsh 会话 → 选择预设「数学建模 Workbench」，即可使用 mm_project_init / mm_phase_enter / mm_todo / mm_gate / mm_check_deliverables / mm_complete / mm_state 等工具，并通过 skill 工具加载内置 math-modeling 知识库。
插件为自包含设计：知识库随预设持久化，不依赖外部仓库路径，可整体复制到任意机器使用。
git clone https://github.com/XiaoMaColtAI/math-modeling-skill.git
克隆后，将仓库放入所用 Agent 的 Skills 目录或按其方式加载本目录。
npx skills add https://github.com/xiaomacoltai/math-modeling-skill --skill math-modeling
也可以下载仓库 ZIP，解压后放入对应 Skills 目录。
完整流程：
使用数学建模 Skill 完成这道题，默认生成 Word 论文。
使用数学建模 Skill 完成这道题，同时生成 Word 和 LaTeX 论文。
使用官方 LaTeX 模板完成这道题，只交付完整 LaTeX 源码项目和编译 PDF。
使用数学建模 Skill 完成这道题，额外启用附件盘点、文献调研和算法原型 Subagent。
使用数学建模 Skill 完成这道题，除固定质检外不使用其他 Subagent。
单阶段执行：
只做建模分析，输出题目分析报告和术语表格。
只实现现有模型，使用 MATLAB 运行并生成全部结果和图。
根据现有代码结果生成完整论文.docx。
根据现有代码结果和官方模板生成 LaTeX 论文并实际编译（需显式要求）。
主入口见 SKILL.md。
典型产物结构：
PROJECT_ROOT/
├── data/                         # 题目附件，只读
├── 题目分析报告.md
├── 术语表格.md
├── 问题1_求解.py 或 问题1_求解.m
├── results/
│   ├── 问题1_结果.csv
│   └── 复现清单.json
├── figures/
│   ├── raw_q1_*.svg / raw_q1_*.png
│   ├── process_q1_*.svg / process_q1_*.png
│   ├── result_q1_*.svg / result_q1_*.png
│   ├── raw_q2_* / process_q2_* / result_q2_*  # 其余问题依次覆盖
│   ├── flow_overall_model.svg / .png     # 总体建模流程图（必须）
│   ├── flow_qN_model.svg / .png          # 子问题流程图（按需）
│   └── _qa/                       # 自动生成的灰度质检预览
├── 完整论文.docx                 # 默认交付的 Word 论文
├── 完整论文.conversion.json      # LaTeX→DOCX 输入/输出/模板哈希与警告记录（LaTeX 可选时）
├── 完整论文-LaTeX/               # LaTeX 源码项目（用户显式要求时）
│   ├── main.tex
│   ├── latex-project.json         # 模板来源、主入口及代码/图表资源绑定
│   ├── references.bib
│   └── 官方模板附带的 cls/sty/bst 等资源
├── 完整论文.pdf                  # 由 LaTeX 源码实际编译（用户显式要求时）
└── 完整论文.build.json           # 源码/PDF 哈希、工具版本、命令与门禁结果（用户显式要求时）
| 工具 | 用途 | 
|---|---|
| 科研可视化 | 数据剖析、选图决策、Nature/SCI 出版级绘制、建模流程图、自检闭环、多格式导出 | 
| 双引擎论文搜索 | OpenAlex + AnySearch 搜索、融合和交叉核验 | 
| DOCX 工具 | 官方模板、递归 LaTeX→DOCX、警告发布门禁、OMML 公式、三线表、修订、批注和校验 | 
| LaTeX 工具 | 环境诊断、官方模板溯源、真实编译、哈希绑定、引用与 PDF 质量校验 | 
| Excel 工具 | XLSX 模板处理、公式重算和错误检查 | 
| PDF 工具 | 读取题目 PDF，提取文本、表格和图片 | 
python tools/paper_search/scripts/hybrid_scholar.py \
  --query "robust optimization vehicle routing" \
  --limit 10 \
  --json
--email 提供礼貌池邮箱。ANYSEARCH_API_KEY。
Python 只检查实际需要的功能：
python references/roles/编程手/scripts/check_env.py \
  --features data visualization optimization
MATLAB 使用：
addpath("references/roles/编程手/scripts");
report = check_matlab_env(["data", "visualization", "optimization"]);
算法资料覆盖七类问题：
| 类别 | 代表方向 | 
|---|---|
| 优化 | 线性、整数、非线性、多目标和启发式优化 | 
| 预测 | 灰色预测、时间序列、回归和机器学习预测 | 
| 评价 | AHP、TOPSIS、熵权、灰色关联和 DEA | 
| 图论 | 最短路、网络流、生成树和匹配 | 
| 统计 | 检验、聚类、降维和多元统计 | 
| 综合 | 蒙特卡洛、排队、博弈、马尔科夫和微分方程 | 
| 机器学习 | 随机森林、集成学习和异常检测 | 
先读取 算法索引，再按问题类型加载对应资料。每道子问题最多使用两个独立模型体系；物理题中同一机理的基础近似与高精度展开按一个模型族计数。
默认只生成 Word 论文；用户显式要求时同时生成 LaTeX/PDF 论文。当届官方提交要求仍决定实际可提交的版本。
完整流程与门禁见 tools/docx/SKILL.md、tools/latex/SKILL.md。
以下图表展示本项目可视化规范生成的候选图效果。
工作流可用于 CUMCM、MCM/ICM、APMCM、MathorCup、认证杯、数维杯等数学建模竞赛和一般建模项目。不同竞赛的页面、摘要、编号、页数和提交格式必须按当届官方要求配置。
math-modeling-skill/
├── VERSION
├── SKILL.md
├── README.md
├── CHANGELOG.md
├── assets/                         # 算法资料
├── imgs/                           # README 示例图
├── references/
│   ├── README.md                   # 渐进式导航
│   ├── 算法索引.md
│   └── roles/
│       ├── 建模手/
│       ├── 编程手/
│       └── 论文手/
├── tools/                          # DOCX、LaTeX、PDF、XLSX、论文搜索
├── dsh-plugin/                     # DeepSeek Harness 插件预设（独立分发）
│   └── math-modeling-agent/        # Agent 预设：mm_* 工具 + 内置知识库
└── tests/                          # 回归测试
python -m unittest discover -s tests -v
python tools/docx/scripts/self_check.py
python -m compileall -q tools references/roles/编程手/scripts
回归测试覆盖双引擎搜索、公式转换、DOCX、LaTeX 模板与校验、Excel 重算、论文结构、动态依赖、复现清单和科学绘图工具。
1.3.0 完善算法资料与建模方法论，新增评阅人抓分方法论、求解稳健性、机器学习算法扩充，并补充交付与截止时间保护协议与 DeepSeek Harness 插件支持。详细内容见 CHANGELOG.md。
采用语义化版本 MAJOR.MINOR.PATCH：
MAJOR：固定交付物、目录契约、命令参数或数据结构发生不兼容变化。MINOR：增加向后兼容的新能力。PATCH：向后兼容的错误修复、文档校正或测试补充。
完整记录见 CHANGELOG.md。
该图每日读取 GitHub 官方累计 Star 数自动更新；画布为 16:9，纵轴每 50 Star 一格，并在当前数值上方保留一个完整刻度。
