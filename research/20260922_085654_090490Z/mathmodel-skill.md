---
title: "mathmodel-skill"
date: "2026-06-11"
sitename: "SkillsLLM"
source_url: "https://skillsllm.com/skill/mathmodel-skill"
source_url_canonical: "https://skillsllm.com/skill/mathmodel-skill"
search_query: "数学建模 codex"
search_title: "mathmodel-skill - AI Agents on GitHub"
search_snippet: "mathmodel-skill is an open-source ai agents skill for AI coding assistants such as Claude Code, Codex CLI, and ChatGPT, built by handsomeZR-netizen. 三竞赛 (CUMCM/MCM/电工杯) 数学建模 skill — harness-agnostic,…"
---

三竞赛 (CUMCM/MCM/电工杯) 数学建模 skill — harness-agnostic, 同时支持 Claude Code 与 Codex CLI, 全程问答式 (Friendly Mode), 10 阶段 + 4 反馈层 + per-Qi 加权聚合 + 题型 dim 加权 + empirical 实测分位锚定
# Add to your Claude Code skills
git clone https://github.com/handsomeZR-netizen/mathmodel-skill
Guides for using ai agents skills like mathmodel-skill.
Last scanned: 6/11/2026
{
  "issues": [],
  "status": "PASSED",
  "scannedAt": "2026-06-11T08:49:59.334Z",
  "npmAuditRan": true,
  "pipAuditRan": true,
  "promptInjectionRan": true
}
See how mathmodel-skill compares with popular alternatives.
mathmodel-skill is an open-source ai agents skill for AI coding assistants such as Claude Code, Codex CLI, and ChatGPT, built by handsomeZR-netizen. 三竞赛 (CUMCM/MCM/电工杯) 数学建模 skill — harness-agnostic, 同时支持 Claude Code 与 Codex CLI, 全程问答式 (Friendly Mode), 10 阶段 + 4 反馈层 + per-Qi 加权聚合 + 题型 dim 加权 + empirical 实测分位锚定. It has 285 GitHub stars.
Yes. mathmodel-skill passed SkillsLLM's automated security scan — a dependency vulnerability audit plus prompt-injection heuristics — with no high-severity issues. You can read the full report in the Security Report section on this page.
Clone the repository with "git clone https://github.com/handsomeZR-netizen/mathmodel-skill" and add it to your Claude Code skills directory (see the Installation section above). mathmodel-skill ships a SKILL.md manifest, so compatible agents can discover and load it automatically.
mathmodel-skill is primarily written in Python. It is open-source under handsomeZR-netizen on GitHub, so you can review or fork the full source.
Yes. SkillsLLM lists many other AI Agents skills you can browse and compare side by side. Open the AI Agents category from the badge at the top of this page, or use the Related Skills and comparison links further down to weigh mathmodel-skill against similar tools.
No comments yet. Be the first to share your thoughts!
⚠️ Third-Party Software Notice
This skill is third-party open-source software developed and hosted independently on GitHub. SkillsLLM is an informational directory and does not control or maintain the underlying repository.
Any security checks, ratings, or warnings displayed by SkillsLLM are automated and limited in scope. They do not constitute a security certification or guarantee that the software is safe, error-free, or free from malicious code, vulnerabilities, compromised dependencies, or prompt-injection risks.
Review the source code, permissions, dependencies, and configuration before installing or running any third-party skill. Use is at your own risk. To the maximum extent permitted by applicable law, SkillsLLM is not liable for losses arising from third-party software.
10 阶段把 72–96 小时的竞赛协作变成可恢复、可检查的流程。用户回答关键问题，agent 维护状态与脚本。每阶段产出经过 rubric 自评、定向精修与跨阶段一致性回检；Stage 8–9 先遵守当届官方规则，再做多视角终审。CUMCM 包含 91 份来源文档，其中 59 份进入文本统计；MCM/电工杯经验统计明确为 n=0，不提供合成分位。
v6.1 更新: 加入竞赛规则基线与 AI 使用披露链路；三竞赛统一使用 marker 模板并对提交元数据 fail closed；修复状态路径错位、评分 verdict 持久化、题型权重合并和 YAML frontmatter 等问题；新增 preflight doctor 与自动化验证。
Codex 优先按 skill 目录发现本文件:
$HOME/.agents/skills/mathmodel-skill/<repo>/.agents/skills/mathmodel-skill/agents/openai.yaml.codex-plugin/plugin.json + skills/mathmodel-skill/SKILL.md shimAGENTS.md 仍可作为 repo / workspace 级 instructions, 但不是唯一入口
当 skill 已安装后, 用户可直接说"开始建模"或显式说"使用 $mathmodel-skill 开始建模"。
本 skill v6.1 以 Codex Skills 为一等入口, 同时保持 harness-agnostic 设计:
| harness | 入口文件 | 用户交互工具 | 状态文件 | 
|---|---|---|---|
| Claude Code | SKILL.md (本文件) | AskUserQuestion 工具 | <cwd>/state/decision_log.json | 
| Codex CLI / Codex app | skill 目录中的 SKILL.md + 可选AGENTS.md | markdown 编号列表 | 同上 (互通) | 
跨 harness 互通: day 1 用 Codex 跑 stage 0-2, day 2 切回 Claude Code 接着 stage 3+, 状态完全保留。详见 references/harness_compat.md。
核心原则: 用户只需回答编号问题, 不应被要求手敲 bash / python / json。
优先使用当前 harness 可用的原生选择 UI；没有时回退到 markdown 编号列表。两者语义等价，见 references/harness_compat.md §1。
| 类型 | 位置 | 例 | 
|---|---|---|
| skill 内通用 | skill 根目录的相对路径 | references/stage_05_subproblem_loop.md ,templates/shared/decision_log.json | 
| 竞赛特化 | competitions/<comp>/... 按 decision_log.competition dispatch | competitions/cumcm/winning_patterns.md ,competitions/mcm/abstract_template.md | 
| LaTeX 模板 | templates/latex/<comp>/main.tex | templates/latex/cumcm/main.tex ,templates/latex/mcm/main.tex | 
| 用户产物 | 用户工作目录的相对路径 | <cwd>/state/ ,<cwd>/results/ ,<cwd>/figures/ ,<cwd>/paper_workspace/ | 
| state 持久化 | <cwd>/state/decision_log.json | 各 stage 必读必写 | 
| 环境变量 | MATHMODEL_STATE_DIR (兼容CUMCM_STATE_DIR ) /MATHMODEL_COMPETITION 可覆盖 | scripts 用此变量 | 
约定: <skill>/ = skill 安装目录, <cwd>/ = 用户 cwd, <comp>/ = 当前竞赛 (cumcm | mcm | diangong)。
1. 一段话介绍 (≤50 字): "启动数学建模工作流, 10 阶段 + 三竞赛, 全程问答式."
2. 收集下列 5 个启动字段；用户已经提供或 state 已记录的字段不再询问，只把尚缺字段合并成一轮问答 (Claude Code: AskUserQuestion; Codex: 编号列表):
   - 竞赛 (cumcm 国赛 / mcm 美赛 / diangong 电工杯, 默认 cumcm)
   - 题号 (依竞赛: cumcm A-E / mcm A-F / diangong A-B; "未公布"亦可)
   - 队员数 + 各人擅长 (建模/编程/写作)
   - 截止时间 (ISO 字符串或 "距现在 X 小时")
   - 题目 PDF 路径 ("未公布"亦可)
3. 自动初始化 (agent 自动完成, 不要让用户编辑 json):
   - 不存在 `<cwd>/state/decision_log.json` → 创建目录并复制 `<skill>/templates/shared/decision_log.json` 到该路径
   - 写入 decision_log.competition = <选定竞赛>
   - 已存在 → 读 current_stage 字段决定恢复点
4. 加载 `competitions/<comp>/current_rules.md`（若存在），打开其中官方链接核对当届规则并写入 compliance；再按需加载 winning patterns
5. 进入 Stage 0 (`references/stage_00_kickoff.md`), 不重复问已知字段；若题面未公布，完成环境与协作准备后保持 `qi_count=null` 并等待题面，不进入 Stage 1
已有 state 触发 (用户中途回到 skill):
1. 读 `<cwd>/state/decision_log.json` 的 competition 与 current_stage
2. 加载对应 stage_NN.md (按需结合 competitions/<comp>/* 内容)
3. 不重复读 winning_patterns
时长 / 语言 / 模板 / 数据状态 由 competition 决定; token 预算 / 反馈深度由 mode 决定。两者正交组合。
| Competition | 时长 | 语言 | LaTeX | 规则基线 | 经验数据状态 | 
|---|---|---|---|---|---|
| cumcm | 72h | 中文 | xelatex / 原创 ctexart | CUMCM 2026 | 91 来源文档 / 59 可提取样本 | 
| mcm | 96h | English | pdflatex / article | COMAP 2027 | n=0 ，无论文分位 | 
| diangong | 72h | 中文 | xelatex / ctex | 官网 2026-03-21 页面 | n=0 ，无论文分位 | 
| Mode | 上下文策略 | 反馈层 | 用途 | 
|---|---|---|---|
| fast | 只保留当前阻断项与最小证据 | L1 单次 | 选题试跑 / sanity check | 
| standard | 按阶段加载并保留决策摘要 | L1+L2 | 默认主流程 | 
| championship | 在终审阶段扩展证据与独立视角 | L1+L2+L3+L4 + red-team | 提交前最后冲刺 | 
模式自动推荐 (按距 deadline 剩余):
60h: standard (最后 6h 升 championship)
| # | 阶段 | reference | 时长 | 反馈 | 竞赛差异点 | 
|---|---|---|---|---|---|
| 0 | 团队启动 + 资料预扫 | stage_00_kickoff.md | 1h | L1 | 时长 / 语言 / 编译器 / 题号体系 | 
| 1 | 选题 (多题对比 → 1) | stage_01_problem_selection.md | 2-4h | L1 | 题号体系 (A-E/A-F/A-B) + task_type 写入 | 
| 2 | 问题深度解析与分解 | stage_02_analysis.md | 2-3h | L1 | 通用 | 
| 3 | 模型选型 (证据驱动的候选比较) | stage_03_model_selection.md | 2-4h | L1 + 反事实 | 通用 | 
| 4 | Foundation (假设+符号+术语) | stage_04_foundation.md | 1h | L1 | 通用 | 
| 5 | 递归子问题循环 Q1..Qn + per-Qi 加权聚合 | stage_05_subproblem_loop.md | 按题目分配 | L1 + 子检查点 | 从题面提取实际子问数；per-Qi 加权 | 
| 6 | 全局灵敏度 / 稳健性 | stage_06_robustness.md | 2-3h | L1 + L2 | 工程参数 (diangong) vs 数学参数 (cumcm/mcm) | 
| 7 | 模型评价 + 推广 | stage_07_evaluation.md | 1-2h | L1 | 通用 | 
| 8 | 论文写作 + 合规装配 | stage_08_writing.md | 12-30h | L1 + L2 | 当届规则、AI 披露、摘要类型与 LaTeX 模板 | 
| 9 | 提交合规 + Panel | stage_09_review.md | 2-6h | L1 + L3 panel | 页数/匿名/披露 + anti-patterns + personas | 
只在进入阶段 N 时加载 references/stage_NN_*.md。切勿一次性全读。
各阶段额外加载 (按需 + 按 competition 切换):
<cwd>/state/decision_log.json 必读references/rubrics.md 对应章节 (L1 评分用)competitions/<comp>/topic_specs.json (题号 → task_type 映射)references/model_catalog.md (跨竞赛通用)scripts/score_artifact.py --mode aggregate_qi 聚合competitions/<comp>/current_rules.md 存在时读取，并核对其中官方链接competitions/<comp>/{winning_patterns, phrase_bank, abstract_template, paper_skeleton}.mdcompetitions/<comp>/empirical.json 只作评分前参考；CUMCM 为 59 份可提取样本的观察分位，MCM/电工杯为 n=0 占位且不得推断数值门槛anti_patterns.md 与 rubric_overlay.json 的 panel personasreferences/feedback_layer*.mdreferences/harness_compat.md
verdict 优先级 (从高到低):
| verdict | 触发 | 行为 | 
|---|---|---|
| block | issues 含 ≥1 high-severity | 暂停 skill, 用户介入 | 
| pass_early | raw_min ≥ 9 AND weighted_mean ≥ 9 | iter-1 早退 | 
| pass | raw_min ≥ 7 AND weighted_mean ≥ 8 | 进下一阶段 | 
| pass_with_review (stage 5) | 任 Qi mark_for_review 但加权阈值满足 | 进 stage 6, L2 必读 review_qis | 
| refine | 其他 | section-patch 精修, iter+=1 (cap 3) | 
| refine_partial (stage 5) | 任 Qi.min < 7, 其他 Qi 已 pass | 仅 refine 该 Qi, 不动其他 | 
| carryover | iter == 3 仍 refine | 进下一阶段, 标记由 L2 处理 | 
weighted_mean = Σ(s_i × w_i) / Σ(w_i), 权重来自 config/dim_weights.json[<comp>][<task_type>] (clamp [0.7, 1.5]); task_type=default 全 1.0 等价老逻辑。
此定义在 feedback_layer1_critic.md / rubrics.md / scripts/score_artifact.py 三处必须完全一致。
每阶段:
current_stage += 1
decision_log.json v3.1 schema 关键字段 (与 templates/shared/decision_log.json 对齐):
competition, task_type, mode, current_stage, budget, events, complianceqi_count, qi_weights, qi_statusweighted_mean, review_qis, refine_qis (stage 5 加权聚合用)
L2 跨阶段回检 (stage 5/6/8 末尾) 读这个文件主动找冲突, 触发定向回滚: 不重做整阶段, 只针对冲突点。
scripts/extract_diff.py), 优先只传相关 sectionnull，不得估算成已用额度competitions/cumcm/: 91 份来源文档，59 份成功文本提取并进入观察分位；现有提取有局限，不能解释为官方阈值或获奖预测competitions/mcm/: 规则基线已按 COMAP 2027 核对；经验模式是维护者启发，empirical 为 competitions/diangong/: 官网参赛规则与论文规范已于 2026-07-22 核对；经验模式是维护者启发，empirical 为 当前 scripts/ingest_papers.py 是维护期归档工具，不能直接重建三个竞赛包的 empirical.json。新增语料前先补来源 provenance、提取 QA 与分组样本量。
核心工作流可离线运行；当届规则与问题要求必须从官方来源重新核对。下列资源可作人工补充:
personqianduixue/Math_Model, datawhalechina/intro-mathmodel, dxs.moe.gov.cn 优秀论文展廊comap.com, MCM Tutorial (Frank Giordano)
A structured Agent workflow for CUMCM, MCM/ICM, and Diangong Cup — designed to keep a 72–96 hour modeling project coherent from the first decision to the final submission.
数学建模比赛很少因为“缺少一个更聪明的回答”而失败。
更常见的情况是：模型已经换了，摘要还没有更新；第二问重新求解后，第三问仍在引用旧结果；某个关键假设只存在于聊天记录里；直到提交前，团队才发现匿名、页数或 AI 使用披露不符合要求。
mathmodel-skill 为这些问题而设计。
它不是一个试图一次生成整篇论文的 Prompt，也不是一个替团队做决定的黑盒 Agent。它是一套可执行的建模工作流：将选题、拆题、模型选择、求解、稳健性分析、论文装配和终审组织为 10 个阶段，并用一份共享决策日志保存整个项目的状态。
当比赛持续数十小时、队员交替协作，或者工作从 Codex 切换到 Claude Code 时，项目仍然能够沿着同一条主线继续，而不是重新依赖聊天上下文和个人记忆。
支持：
日常使用中，你不需要手工维护 JSON，也不需要记住每个脚本的参数。Agent 会在需要判断的节点向团队确认，并负责维护状态、调用工具和整理产物。
设计动机 · 工作方式 · 设计原则 · 竞赛支持 · 快速开始 · 可信边界
一场数学建模比赛，本质上不是一道独立问题，而是一组彼此依赖的决定。
选题会影响数据与时间分配；假设会限制模型边界；模型会决定求解方式与图表；结果发生变化后，摘要、评价、灵敏度分析和结论都需要同步调整。
如果这些依赖只存在于对话记录、临时文件或某位队员的记忆里，协作就会逐渐失去一致性。项目可能仍在向前推进，但不同部分已经不再描述同一个模型。
mathmodel-skill 将这些隐含关系显式化。
它帮助团队持续回答四个问题：
它不保证模型一定正确，也不预测奖项。它做的是更基础、也更重要的事情：让项目可以被恢复、检查、局部修改，并最终交付。
flowchart LR
    A["题目与团队约束"] --> B["10 阶段主流程"]
    C["竞赛特化包"] --> B
    D["decision_log.json"] <--> B
    B --> E["模型 · 结果 · 图表 · 论文"]
    E --> F["L1 / L2 / L3 / L4 反馈"]
    F -->|"定向修补"| B
整个系统由三部分组成。
主流程定义阶段顺序、进入条件、退出条件和回退路径。
每个阶段都有明确的输入与产物。Agent 不会把整场比赛压缩成一次长执行，而是在可检查的位置停下来，让团队知道已经完成了什么，以及为什么可以继续。
state/decision_log.json 是项目的连续记忆。
它记录：
对话用于交流，日志用于接力。即使上下文切换，项目状态仍然保留在工作区中。
语言模型适合分析、比较与生成，但并不适合承担所有机械检查。
因此，评分重算、模板装配、环境诊断、差分应用、AI 披露生成和部分合规检查由脚本完成。模型负责需要判断的工作，脚本负责可以确定的工作，团队保留最终决定权。
| 比赛中的常见情况 | mathmodel-skill 的处理方式 | 
|---|---|
| 对话越来越长，早期决定难以追溯 | 所有阶段共用 state/decision_log.json ，统一保存选择、依据、评分与回退记录 | 
| 总体表现尚可，但某个关键维度明显不足 | Verdict 同时检查最低分和加权均分；高严重度问题不能被平均数掩盖 | 
| 只有 Q2 需要返工，却牵连全部结果 | Stage 5 按 Qi 保存状态，支持 refine_partial ，只修改受影响的子问 | 
| 三类竞赛要求不同，维护成本不断增加 | 保留一条主流程，通过 competition pack、权重 overlay 和模板表达差异 | 
| Markdown 章节已经生成，但主 TeX 没有正确引用 | 模板使用显式 section marker；缺失、重复或未知 marker 会直接失败 | 
| 封面或摘要仍含占位符，却被误当作正式稿 | 正式渲染采用 fail-closed 检查；占位符只能用于显式 dry-run | 
| 临近提交才发现页数、匿名或 AI 披露问题 | Stage 0、8、9 会重新打开规则入口；未通过合规门不能进入 submission_ready | 
| Pandoc、TeX 或依赖问题直到最后才暴露 | doctor.py 集中检查结构、竞赛包、Python、Pandoc、TeX 与可选依赖 | 
mathmodel-skill 的设计目标不是加入尽可能多的组件，而是让每个组件只承担自己最擅长的工作。
更长的 Prompt 可以增加背景信息，却不能天然维护状态、依赖与回退路径。
这里仍然使用模型完成各阶段任务，但“项目现在在哪里”“上一阶段决定了什么”“什么条件下可以继续”由工作流显式维护。上下文可以变化，项目结构不需要随之消失。
RAG 很适合寻找竞赛规则、领域论文、真实数据和方法依据，但它并不负责决定下一阶段，也不会自动判断新结果是否推翻旧假设。
因此，仓库内材料采用版本可控、按阶段加载的竞赛包；外部检索负责提供证据，主流程负责组织行动。
多个 Agent 在选题比较、模型攻击和终稿评审中很有价值，但如果每一步都依赖多方协商，协调成本和符号漂移会迅速增加。
主流程始终围绕一份共享日志推进。并行视角只出现在适合独立判断的节点；终稿 Panel 可以并行执行，也可以在单 Agent 环境中顺序降级。
单 Agent 并不等于黑盒。
fast 和 standard 模式都可以由一个 Agent 完成，但每个阶段仍然留下明确产物，关键选择仍然需要确认，评分仍然由脚本重算，问题仍然可以按 section 或 Qi 局部修补。
团队可以随时查看进度、接管项目、切换模型，或回到某个具体决定，而不必从头重做。
Codex 与 Claude Code 可以在同一工作区中读取相同的 state schema。这里的共享来自项目目录，而不是云同步，因此切换工具时仍需保留完整工作区与产物。
选竞赛、选题、接受模型、决定回修等节点通过原生选择 UI 或编号列表完成。团队负责方向判断，Agent 负责状态写入、文件组织和脚本调用。
根目录 SKILL.md 只承担调度职责。阶段细则、rubric、竞赛规则和模板按需加载，避免无关内容占用上下文。
CUMCM、MCM/ICM 与电工杯不会被维护为三套互相漂移的工作流。它们的差异被限制在：
competitions/<comp>/
加权均分可以用于排序，但任何低于门槛的关键维度都需要单独处理。题型权重被限制在 [0.7, 1.5]，避免局部偏好过度放大。
Stage 5 保存每个 Qi 的分数、权重和状态。某个子问失败时，流程只返回真正受影响的位置，而不是默认推翻全部结果。
CUMCM 分位描述的是公开样本中的观察位置，不是官方评分线，也不能用于推导获奖概率。
MCM/ICM 与电工杯的经验层明确记录为 n=0，不会生成缺乏数据支持的“经验分位”。
current_rules.md 保存最近核对日期和官方入口。Stage 0、8、9 仍要求重新查看当届通知，因为仓库基线不能覆盖未来变化。
台账记录工具、版本、使用阶段、用途、采用内容和人工复核。
CUMCM 会根据是否使用 AI 生成相应的支撑材料 PDF 或正文声明；MCM 报告会直接接入主模板，避免截止前再依赖记忆补写。
YAML/JSON、竞赛包、反模式计数、评分边界、模板 marker、渲染 dry-run 和代码模板边界均有自动测试覆盖。
| Stage | 任务 | 关键产物 | 主要检查 | 
|---|---|---|---|
| 0 | 团队启动与资料预扫 | 竞赛、角色、时限、环境、规则基线 | 可执行性与合规入口 | 
| 1 | 多题比较与选题 | 选择理由、放弃项、题型判断 | 资源匹配与失败风险 | 
| 2 | 问题拆解 | 子问、变量、约束、依赖图 | 逻辑完整性 | 
| 3 | 模型选型 | 候选模型、证据、反事实与淘汰理由 | 模型与问题的匹配程度 | 
| 4 | Foundation | 假设、符号、术语表 | 一致性与可解释性 | 
| 5 | 递归求解 Q1…Qn | formulation、代码、结果、图表 | per-Qi 评分与定向回修 | 
| 6 | 稳健性分析 | 风险匹配的验证、稳健区间、失败边界 | 灵敏度与结论可靠性 | 
| 7 | 模型评价 | 优点、局限、改进、迁移条件 | 边界是否诚实、结论能否推广 | 
| 8 | 论文装配 | paper_workspace/*.md 、TeX/PDF、AI 台账 | 跨阶段一致性与格式合规 | 
| 9 | 提交前终审 | 最终 PDF、支持材料、Panel 记录 | 合规门、证据链与视觉检查 | 
三种模式使用同一条主流程，只调整反馈预算和评审深度。
| Mode | 反馈层 | 适用场景 | 
|---|---|---|
| fast | L1 单轮 | 选题试跑、快速 sanity check | 
| standard | L1 + L2 | 默认比赛流程 | 
| championship | L1 + L2 + L3 + L4 + red-team | 终稿前的深度评审 | 
评分工具输出的是流程状态，而不是奖项预测：
block · refine · refine_partial · pass_with_review · pass · pass_early · carryover
| 竞赛包 | 语言与模板 | 当前材料 | 可信度说明 | 
|---|---|---|---|
| CUMCM 国赛 | 中文；XeLaTeX / 原创 ctexart 电子论文模板 | 收集 91 份公开论文源样本，其中 59 份成功提取文本并进入统计；42 项维护者反模式检查 | 当前材料最完整；观察分位不是官方门槛，规则以当届通知为准 | 
| MCM/ICM 美赛 | English；pdfLaTeX / article | 16 项维护者检查；已记录 COMAP 2027 页数、字号与 AI 披露基线 | 经验层 n=0 ，不提供论文分位；提交前必须重新核对 COMAP 要求 | 
| 电工杯 | 中文；XeLaTeX / ctexart | 12 项工程导向检查；已记录官网页序、25 页正文、支撑材料与匿名基线 | 经验层 n=0 ；当前官网未提供专门 AI 格式，仍需检查当届通知 | 
截至 2026-07-22，仓库已核对：
这些链接构成仓库当前的规则基线，但不能替代参赛当年的官方文件。
git clone https://github.com/handsomeZR-netizen/mathmodel-skill.git \
  ~/.agents/skills/mathmodel-skill
python ~/.agents/skills/mathmodel-skill/scripts/doctor.py \
  --competition cumcm
mkdir -p my-modeling-project
cd my-modeling-project
codex
git clone https://github.com/handsomeZR-netizen/mathmodel-skill.git `
  "$HOME\.agents\skills\mathmodel-skill"
python "$HOME\.agents\skills\mathmodel-skill\scripts\doctor.py" `
  --competition cumcm
New-Item -ItemType Directory -Force my-modeling-project | Out-Null
Set-Location my-modeling-project
codex
进入 Codex 后输入：
使用 $mathmodel-skill，开始 CUMCM 建模。
首次启动时，Agent 会先确认竞赛、题目、队伍能力、截止时间和题面位置，然后创建共享状态并进入 Stage 0。工作区已经存在状态时，则从最近的检查点继续。
也可以安装到当前项目：
mkdir -p .agents/skills
git clone https://github.com/handsomeZR-netizen/mathmodel-skill.git \
  .agents/skills/mathmodel-skill
git clone https://github.com/handsomeZR-netizen/mathmodel-skill.git \
  ~/.claude/skills/mathmodel-skill
mkdir -p my-modeling-project
cd my-modeling-project
claude
进入 Claude Code 后输入：
开始建模
或：
使用 mathmodel-skill 开始 MCM 建模
核心工作流和 doctor.py --skip-tools 不依赖完整的科学计算栈。只有在需要运行仓库中的建模起步代码时，才需要安装额外依赖：
python -m pip install -r \
  ~/.agents/skills/mathmodel-skill/templates/shared/requirements.txt
正式进行论文转换与编译时，还需要安装 Pandoc 和 TeX Live 或 MiKTeX。
简化转换器仅用于 --no-compile 结构预检，不应作为正式论文的编译方式。
my-modeling-project/
├── state/
│   └── decision_log.json       # 决策、评分、回退、规则与 AI 使用台账
├── results/                    # 结构化结果与可复现实验输出
├── figures/                    # 最终图表
├── paper_workspace/            # 01_abstract.md … 10_appendix.md，以及按需披露片段
├── paper_output/               # TeX 中间文件与最终 PDF
└── support_materials/          # 代码、数据清单与竞赛要求的披露材料
Codex 与 Claude Code 可以在同一目录中接力。decision_log.json 负责保存流程状态，但不会自动同步工作区之外的文件。
| 工具 | 用途 | 典型调用 | 
|---|---|---|
