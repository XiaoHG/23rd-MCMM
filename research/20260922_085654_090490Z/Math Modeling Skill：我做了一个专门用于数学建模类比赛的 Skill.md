---
title: "Math Modeling Skill：我做了一个专门用于数学建模类比赛的 Skill"
author: "XiaoMaColtAI"
date: "2026-03-15"
sitename: "掘金"
source_url: "https://juejin.cn/post/7616936839875395618"
source_url_canonical: "https://juejin.cn/post/7616936839875395618"
search_query: "数学建模 codex"
search_title: "Math Modeling Skill：我做了一个专门用于数学建模类比赛的 Skill"
search_snippet: "Math Modeling Skill：数学建模 Skill 完整指南 摘要：我做了一个专门用于数学建模的 Skill，适用于 Claude Code、OpenClaw 等所有支持 Skills 的 Agent 平台。通过建模分析→代码实现→论文撰写的三阶段协作工作流，集成 60+ 算法资源库和 4 个专业文档处理工具，支持数学建模竞赛全流程自动化，帮助数学建模 ..."
---

Math Modeling Skill：数学建模 Skill 完整指南
摘要：我做了一个专门用于数学建模的 Skill，适用于 Claude Code、OpenClaw 等所有支持 Skills 的 Agent 平台。通过建模分析→代码实现→论文撰写的三阶段协作工作流，集成 60+ 算法资源库和 4 个专业文档处理工具，支持数学建模竞赛全流程自动化，帮助数学建模竞赛（CUMCM、MCM/ICM）选手和研究人员高效完成从问题分析到论文产出的全流程。
一、问题背景：为什么需要 Agent Skill？
在数学建模竞赛中，参赛队伍通常面临三大挑战：
- 模型选择困难：面对实际问题，不知道选择哪种数学模型
- 代码实现耗时：大量的编程和可视化工作占用宝贵时间
- 论文撰写压力大：需要在有限时间内产出 15000+ 字的规范论文
传统的解决方案依赖于团队成员的个人能力，而 Agent Skill 的出现为解决这些问题提供了新思路。
开源地址 ：
- GitHub：github.com/XiaoMaColtA…
- Gitee：gitee.com/xiaomacolta…
二、什么是 Agent Skill？
核心概念
Agent Skill 是一种结构化的技能定义格式，用于扩展 AI Agent 的能力边界。
这种技能格式通过标准化的配置文件和模块化设计，使 Agent 能够：
- 理解特定领域的专业需求
- 调用外部工具和 API
- 遵循结构化的工作流程
- 产出符合领域规范的成果
本数学建模 Skill 可运行在任何支持 Skills 的 Agent 平台上，包括 Claude Code、OpenClaw 等。
三、技能概述
数学建模 Agent Skill 为数学建模类竞赛和项目提供结构化的三阶段工作流程：
flowchart TB
    subgraph Modeling[建模分析 建模手]
        A[阅读题目] --> B[问题分析] --> C[选择算法模型] --> D[算法设计] --> E[术语规范]
        E --> F[分析报告]
        E --> G[术语表格]
    end
    Modeling -.->|分析报告 + 术语表 | Coding
    subgraph Coding[代码实现 编程手]
        H[理解需求] --> I[代码设计] --> J[编写代码] --> K[运行求解] --> L[结果验证]
        L --> M[数据可视化]
        M --> N[结果输出]
        M --> O[README 文档]
    end
    Coding -.->|代码 + 结果 + 图表 | Writing
    subgraph Writing[论文撰写 论文手]
        P[收集资料] --> Q[论文规划] --> R[撰写论文] --> S[完整论文]
    end
    style Modeling fill:#e1f5ff,stroke:#0288d1
    style Coding fill:#fff4e1,stroke:#f57c00
    style Writing fill:#ffe1f5,stroke:#c2185b
核心特性：
- 🔄 三阶段协作：建模分析、代码实现、论文撰写，各司其职
- 📚 算法资源库：涵盖优化、预测、评价、图论、统计、综合、机器学习 7 大类 60+ 算法
- 🛠️ 文档处理集成：集成 pdf、xlsx、docx、paper_search 四个专业子技能
- 🎯 三角色模式：建模手（大脑）、编程手（双手）、论文手（喉舌）
四、核心架构
1. 三阶段工作流
第一阶段：建模分析（建模手）
输入：题目文档（PDF）、附件数据（Excel）
处理流程：
- 使用 pdf skill 读取题目，理解问题背景
- 使用 xlsx skill 分析附件数据
- 使用 paper_search skill 搜索相关文献
- 确定数学模型和算法
- 创建术语表格保持一致性
产出：
- 题目分析报告.md - 问题分析、模型选择、公式推导
- 术语表格.md - 中英文术语对照表
sequenceDiagram
    participant User as 用户
    participant Agent as Agent Skill
    participant PDF as pdf skill
    participant XLSX as xlsx skill
    participant Search as paper_search skill
    User->>Agent: 提交题目文档
    Agent->>PDF: 读取题目
    PDF-->>Agent: 题目文本
    Agent->>XLSX: 分析附件数据
    XLSX-->>Agent: 数据结构
    Agent->>Search: 搜索相关文献
    Search-->>Agent: 参考文献
    Agent->>User: 输出分析报告
第二阶段：代码实现（编程手）
输入：题目原文、建模分析报告、术语表格
处理流程：
- 确认编程语言（Python/MATLAB）
- 按题目分模块编写代码
- 使用 xlsx skill 处理表格数据
- 绘制 SCI/Nature 风格图表
- 创建 README 文档
产出：
- 问题 X_求解.py - 解题代码
- 结果表格.csv/xlsx - 计算结果
- 可视化图表.png - 高质量图表
- README.md - 项目说明
flowchart TB
    subgraph Coding[代码实现 编程手]
        H[理解需求] --> I[代码设计]
        I --> J[编写代码]
        J --> K[运行求解]
        K --> L[结果验证]
        L --> M[数据可视化]
        M --> N[结果输出]
        N --> O[README 文档]
        style H fill:#ffffff,stroke:#333,stroke-width:1px
        style I fill:#ffffff,stroke:#333,stroke-width:1px
        style J fill:#ffffff,stroke:#333,stroke-width:1px
        style K fill:#ffffff,stroke:#333,stroke-width:1px
        style L fill:#ffffff,stroke:#333,stroke-width:1px
        style M fill:#ffffff,stroke:#333,stroke-width:1px
        style N fill:#ffffff,stroke:#333,stroke-width:1px
        style O fill:#ffffff,stroke:#333,stroke-width:1px
    end
    style Coding fill:#fff4e1,stroke:#f57c00,stroke-width:2px
第三阶段：论文撰写（论文手）
输入：题目原文、建模分析文档、代码实现结果
处理流程：
- 检查/选择论文模板
- 使用 docx skill 生成.docx 格式论文
- 撰写完整章节（摘要、问题重述、模型建立、求解、评价、推广）
- 确保图表引用正确、格式规范
产出：
- 论文.docx - 完整数学建模论文（≥15000 字）
flowchart TB
    subgraph Writing[论文撰写 论文手]
        P[收集资料] --> Q[论文规划]
        Q --> R[撰写论文]
        R --> S[完整论文]
        style P fill:#ffffff,stroke:#333,stroke-width:1px
        style Q fill:#ffffff,stroke:#333,stroke-width:1px
        style R fill:#ffffff,stroke:#333,stroke-width:1px
        style S fill:#ffffff,stroke:#333,stroke-width:1px
    end
    style Writing fill:#ffe1f5,stroke:#c2185b,stroke-width:2px
2. 三角色协作模式
| 角色 | 定位 | 核心能力 | 对应阶段 | 
|---|---|---|---|
| 🧠 建模手 | 团队的大脑 | 数学建模、算法设计 | 建模分析 | 
| 💻 编程手 | 团队的双手 | 代码实现、数据可视化 | 代码实现 | 
| 📝 论文手 | 团队的发言人 | 学术写作、成果整理 | 论文撰写 | 
这种分工模式确保了专业的人做专业的事，每个阶段都有明确的输入输出规范。
五、算法资源库
本 Skill 内置 7 大类 60+ 算法的详细说明文档，位于 assets/ 目录：
算法分类速查
| 类别 | 数量 | 代表算法 | 适用场景 | 
|---|---|---|---|
| ⚙️ 优化算法 | 15 | 线性规划、遗传算法、PSO、模拟退火、鲸鱼优化 | 资源分配、路径规划、参数优化 | 
| 📈 预测算法 | 11 | 灰色预测、ARIMA、神经网络、LSTM、XGBoost | 时间序列预测、趋势分析 | 
| ⭐ 评价算法 | 11 | AHP、TOPSIS、熵权法、DEA | 方案评估、绩效评价 | 
| 🕸️ 图论网络 | 6 | 最短路径、最大流、最小生成树 | 网络优化、路径问题 | 
| 📊 统计分析 | 9 | K-Means、层次聚类、PCA、因子分析 | 数据降维、聚类分析 | 
| 🎲 综合算法 | 6 | 蒙特卡洛、排队论、博弈论、微分方程 | 复杂系统建模 | 
| 🤖 机器学习 | 3 | 随机森林、AdaBoost、孤立森林 | 分类、回归、异常检测 | 
算法文档结构
每个算法的说明文档包含：
# 算法名称
## 数学原理
- 核心公式
- 推导过程
## 适用范围
- 问题类型
- 数据要求
## 可视化图表
- 算法流程图
- 效果对比图
## 关键文献
- 经典论文引用
- 最新研究进展
## 代码实现
- Python 示例
- MATLAB 示例
六、集成的子 Skill
本 Skill 集成了四个专业的文档处理子 Skill，位于 tools/ 目录：
1. 📑 pdf skill - PDF 文档处理
功能：
- 读取 PDF 格式的题目文档
- 提取文本和表格数据
- 支持 PDF 合并、拆分
使用示例：
from pdf import PDFHandler
handler = PDFHandler()
text = handler.extract_text("problem.pdf")
tables = handler.extract_tables("data.pdf")
2. 📊 xlsx skill - Excel 表格处理
功能：
- 读取和编辑.xlsx 文件
- 处理题目附带的数据表格
- 输出计算结果到 Excel
- 使用 Excel 公式而非硬编码值
核心规范：
# ❌ 错误：硬编码计算结果
total = df['Sales'].sum()
sheet['B10'] = total  # 硬编码 5000
# ✅ 正确：使用 Excel 公式
sheet['B10'] = '=SUM(B2:B9)'  # 保留公式
3. 📘 docx skill - Word 文档处理
功能：
- 创建、读取、编辑.docx 文件
- 生成格式规范的数学建模论文
- 支持表格、图片、公式等复杂格式
使用示例：
from docx import Document
doc = Document()
doc.add_heading('摘要', level=1)
doc.add_paragraph('本文研究了...')
doc.add_picture('figure1.png')
doc.save('论文.docx')
4. 🔎 paper_search skill - 论文搜索
功能：
- 通过 OpenAlex API 搜索学术论文
- 自动生成标准引用格式
- 支持摘要重建和多字段搜索
配置要求：
from paper_search import OpenAlexScholar
# 需要配置邮箱以提高 API 访问限制
scholar = OpenAlexScholar(email="your-email@example.com")
papers = scholar.search_papers("grey prediction model")
七、快速开始
安装步骤
方法一：npx 一键安装（推荐）
npx skills add https://github.com/XiaoMaColtAI/math-modeling-skill.git
方法二：Git 克隆
git clone https://github.com/XiaoMaColtAI/math-modeling-skill.git \
  ~/.claude/skills/math-modeling-skill
方法三：手动安装
- 
下载 ZIP 文件或克隆到本地
- 
复制到 Agent 的 skills 目录： 
  - macOS/Linux: ~/.claude/skills/
  - Windows: %USERPROFILE%.claude\skills
  - OpenClaw: ./skills/ 或配置文件中指定路径
- macOS/Linux: 
验证安装
重启 Agent 或重新加载 skills 后，使用以下命令测试：
/math-modeling 帮我分析这道数学建模题
如果安装成功，Skill 将被激活并开始执行任务。
八、使用示例
场景一：完整解题流程
# 调用 Skill
/math-modeling 帮我做这道数学建模题
# Agent 自动执行：
# 1. 📋 建模分析：阅读题目，选择模型
# 2. 💻 代码实现：编写代码，求解结果
# 3. 📝 论文撰写：撰写完整论文
场景二：分阶段执行
# 仅进行建模分析
/math-modeling 进行建模分析
# 仅进行代码实现
/math-modeling 进行代码实现
# 仅进行论文撰写
/math-modeling 进行论文撰写
场景三：特定任务
# 分析题目用什么模型
"这道数模题应该用什么模型？"
# 编写求解代码
"帮我用 Python 求解这个问题"
# 完善论文
"帮我优化一下摘要部分"
九、目录结构
math-modeling-skill/
├── SKILL.md                    # 技能主定义文件
├── README.md                   # 使用说明
├── assets/                     # 算法资源库
│   ├── README.md              # 算法快速索引
│   ├── 01-优化算法说明.md
│   ├── 02-预测类算法说明.md
│   ├── 03-评价类算法说明.md
│   ├── 04-图论与网络分析算法说明.md
│   ├── 05-统计分析与数据处理算法说明.md
│   ├── 06-综合类算法说明.md
│   └── 07-机器学习算法说明.md
├── references/                 # 参考文档
│   ├── roles/                 # 角色说明
│   │   ├── 建模手说明.md
│   │   ├── 编程手说明.md
│   │   └── 论文手说明.md
│   ├── Outstanding Thesis/    # 优秀论文库
│   │   ├── CUMCM/             # 国赛获奖论文
│   │   └── 2017MCM ICM/       # 美赛 O 奖论文
│   └── 论文模板.docx          # 标准模板
└── tools/                      # 子 Skill
    ├── docx/                  # Word 处理
    ├── pdf/                   # PDF 处理
    ├── xlsx/                  # Excel 处理
    └── paper_search/          # 论文搜索
十、典型使用场景
1. 数学建模竞赛备赛
- 快速原型：使用 Skill 快速建立基线模型
- 算法参考：查阅算法资源库获取实现思路
- 论文规范：学习优秀论文的结构和表述
2. 科研项目管理
- 问题分解：将复杂问题拆解为可建模的子问题
- 自动化分析：批量处理实验数据
- 成果整理：自动生成规范的技术报告
3. 教学与培训
- 案例演示：展示完整建模流程
- 代码教学：提供可运行的示例代码
- 论文指导：学习规范的学术写作
十一、配置说明
Paper Search 邮箱配置
paper_search skill 使用 OpenAlex API 搜索论文，需配置邮箱：
# 命令行方式
python tools/paper_search/scripts/openalex_scholar.py \
  --query "linear programming" \
  --email "your-email@example.com"
# 代码方式
scholar = OpenAlexScholar(email="your-email@example.com")
API 信息：
- 地址：api.openalex.org
- 文档：docs.openalex.org/
- 费用：完全免费
十二、进阶技巧
1. 算法组合创新
本 Skill 鼓励算法组合创新：
灰色预测 + 神经网络 = 组合预测模型
图论算法 + 优化算法 = 网络优化方案
聚类分析 + 评价算法 = 多维度评估体系
2. 论文 AI 味去除
针对 AI 生成论文容易被检测的问题，论文手说明文档中包含了去 AI 味写作指南：
七大类 AI 痕迹识别与去除：
| AI 痕迹类型 | 识别特征 | 去除方法 | 
|---|---|---|
| 内容模式 | "标志着/重要的是/关键作用" | 用具体数据替代 | 
| 模糊归因 | "专家认为/独立报道" | 明确引用来源 | 
| 公式结构 | "不仅...而且..." | 多样化句式 | 
| 宣传语气 | "突破性的/令人振奋" | 客观陈述结果 | 
| 过度格式 | 大量破折号、粗体 | 适度使用 | 
| 空泛结论 | "具有重要意义" | 说明具体贡献 | 
| 缺乏细节 | 无数据支撑 | 补充量化指标 | 
自查清单（论文撰写时必须遵守）：
- 是否使用了 AI 高频词汇？
- 是否过度使用破折号、粗体？
- 是否有"不仅...而且..."结构？
- 是否有模糊的"专家认为"？
- 每句话是否都有具体数据支撑？
- 是否承认了模型的局限性？
