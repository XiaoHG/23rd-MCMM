---
title: "GitHub - KAI-SHUNG/math-model-plot-skill: 数学建模 数模竞赛 面向 matplotlib/scipy/numpy/openpyxl 的作图 skill"
author: "KAI-SHUNG"
date: "2026-09-14"
sitename: "GitHub"
source_url: "https://github.com/KAI-SHUNG/math-model-plot-skill"
source_url_canonical: "https://github.com/KAI-SHUNG/math-model-plot-skill"
search_query: "数学建模 codex"
search_title: "GitHub - KAI-SHUNG/math-model-plot-skill: 数学建模 数模竞赛 面向 matplotlib/scipy/numpy/openpyxl 的作图 skill · GitHub"
search_snippet: "面向数学建模竞赛的专业绘图 Skill，适用于 Claude Code 和 Codex。"
---

面向数学建模竞赛的专业绘图 Skill，适用于 Claude Code 和 Codex。
它为 Python 数模出图提供统一约束，包括虚拟环境检查、数据来源追溯、中英文字体配置、LaTeX 公式、坐标轴与图例规范，以及 PDF/PNG 双格式输出。
- 开始绘图前检查 .venv 和 Python 绘图库依赖
- 追溯模型代码、Excel、CSV 等数据来源
- 中文优先使用宋体，英文优先使用 Times New Roman
- 在 WSL 中优先加载 Windows 字体目录
- 数学公式和符号使用 LaTeX 原始字符串
- 坐标轴标明单位，几何图保持正确比例
- 图例尽量避免遮挡主体数据
- 优先输出 PDF，同时输出不低于 300 dpi 的 PNG
- 文件名统一使用连字符，例如 q1-trajectory-result.png
- 图片默认保存到绘图源文件或脚本所在目录
math-model-plot-skill/
├── README.md
├── claude/
│   └── math-model-plot-skill/
│       └── SKILL.md
└── codex/
    └── math-model-plot-skill/
        └── SKILL.md
两个版本独立维护。Codex 版本保留了与旧版 viz-standard skill 配合使用的说明。
Skill 本身不安装 Python 包。执行绘图任务时，项目环境通常需要：
python -m pip install numpy scipy matplotlib openpyxl
建议在项目自己的 .venv 中安装依赖。实际任务不使用 Excel 时，可以不安装 openpyxl。
git clone https://github.com/KAI-SHUNG/math-model-plot-skill.git
mkdir -p ~/.claude/skills
cp -R math-model-plot-skill/claude/math-model-plot-skill ~/.claude/skills/
安装后的文件应位于：
~/.claude/skills/math-model-plot-skill/SKILL.md
仅在当前项目使用时，也可以复制到项目目录：
mkdir -p .claude/skills
cp -R math-model-plot-skill/claude/math-model-plot-skill .claude/skills/git clone https://github.com/KAI-SHUNG/math-model-plot-skill.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse -Force ".\math-model-plot-skill\claude\math-model-plot-skill" "$env:USERPROFILE\.claude\skills\math-model-plot-skill"
安装完成后，重启 Claude Code 或开启一个新会话，使其重新发现 Skill。
git clone https://github.com/KAI-SHUNG/math-model-plot-skill.git
mkdir -p ~/.codex/skills
cp -R math-model-plot-skill/codex/math-model-plot-skill ~/.codex/skills/
安装后的文件应位于：
~/.codex/skills/math-model-plot-skill/SKILL.md
也可以使用跨工具共享目录：
mkdir -p ~/.agents/skills
cp -R math-model-plot-skill/codex/math-model-plot-skill ~/.agents/skills/git clone https://github.com/KAI-SHUNG/math-model-plot-skill.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\math-model-plot-skill\codex\math-model-plot-skill" "$env:USERPROFILE\.codex\skills\math-model-plot-skill"
安装完成后，重启 Codex 或开启一个新任务，使其重新加载 Skill。
安装后直接用自然语言提出数模绘图任务，无须手动运行 SKILL.md。例如：
请使用 math-model-plot-skill，根据 q1.py 的模型结果绘制轨迹图，同时输出 PDF 和 300 dpi PNG。
读取 data.xlsx 的 Results 工作表，绘制参数敏感性热力图，标明数据来源、坐标单位和关键结论。
检查当前项目的虚拟环境和字体，然后把现有 matplotlib 图改成适合数学建模论文的中英文规范格式。
也可以不写出 Skill 名称。请求中包含“数模画图”“竞赛出图”“matplotlib”“可视化”“Excel 画图”等场景时，客户端可根据 Skill 描述自动调用它。
先更新本地仓库：
cd math-model-plot-skill
git pull
然后重新执行对应平台的复制命令，覆盖已安装版本即可。
- 优先输出 .pdf ，并同时输出.png
- PNG 建议使用 dpi >= 300
- 输出到绘图脚本或图源文件所在目录
- 文件名使用连字符 - ，不使用下划线_
- 图名示例：q1-trajectory-result.pdf 、q1-trajectory-result.png
- 坐标轴必须带单位或明确标记为无量纲
- 图中公式使用 r"$...$" 形式的 LaTeX 字符串
完整规则请查看对应工具目录内的 SKILL.md。
