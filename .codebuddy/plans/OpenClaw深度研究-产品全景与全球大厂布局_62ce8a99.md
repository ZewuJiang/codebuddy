---
name: OpenClaw深度研究-产品全景与全球大厂布局
overview: 基于已有的3份Framework设计稿（v1全景报告、Framework设计、融合版Framework）和4份子研究素材（是什么与发展历程、爆发式增长ABC研究、海外厂商全量扫描、中国厂商全量扫描），加上已缓存的搜索数据（6个batch JSON），综合调优Framework后产出一份50-65页级别的MBB级深度研究报告，主题"OpenClaw深度研究：产品全景与全球大厂布局"。产出MD+PDF，先存放在workflows/目录。
todos:
  - id: search-latest-data
    content: 使用 [skill:deep-research] 搜索 OpenClaw 2026年3月最新数据（GitHub stars/forks最新值、OpenRouter 3月排名、各厂商3月初最新Agent产品动态），并使用 [skill:wechat-article-search] 补充国内厂商3月初最新公众号文章
    status: completed
  - id: write-part1
    content: 撰写 Part 1 全景认知（M1行业概览含TAM三情景测算 + M2产品深度拆解含竞品横评），使用 [skill:industry-research] 确保分析框架达标，整合「是什么与发展历程」和「爆发式增长驱动ABC」两份子研究素材及JSON数据缓存，使用 [subagent:code-explorer] 定位素材中的关键数据
    status: completed
    dependencies:
      - search-latest-data
  - id: write-part2-overseas
    content: 撰写 Part 2 的 M3 海外大厂深度扫描（OpenAI/Meta/Anthropic/Microsoft/Google/Notion/Perplexity 逐家分析 + 对比矩阵 + 五大路线推演），整合「海外重点厂商布局动作全量扫描」子研究素材及batch_3a数据
    status: completed
    dependencies:
      - search-latest-data
  - id: write-part2-domestic
    content: 撰写 Part 2 的 M4 国内大厂深度扫描（云厂商卖铲战 + 模型厂商Token争夺 + 创业生态 + 国内Mapping梯队判定），整合「中国厂商布局全量扫描v7」子研究素材及batch_3b数据
    status: completed
    dependencies:
      - search-latest-data
  - id: write-part2-outlook
    content: 撰写 M5 竞争格局推演与行动启示（Bull/Base/Bear三情景 + 行业影响矩阵 + Token经济 + SWOT风险矩阵 + 趋势预判 + 行动建议），整合batch_3c竞争格局数据
    status: completed
    dependencies:
      - write-part2-overseas
      - write-part2-domestic
  - id: assemble-and-pdf
    content: 汇编全报告：撰写关键总结（三列布局Ø前置）并完全镜像到末尾总结，逐段终审质检（数据来源/三层论证/首尾镜像/命名规范），输出 MD 文件到 workflows/ 并使用 [skill:pdf] 和 md_to_pdf.py 生成 PDF，验证PDF质量（1页/2-5MB/无乱码）
    status: completed
    dependencies:
      - write-part1
      - write-part2-overseas
      - write-part2-domestic
      - write-part2-outlook
---

## 用户需求

综合已有的3个版本Framework（v1初版报告、Framework设计稿v2、融合版Framework v1.0）和4份深度子研究素材，调优报告框架，产出一份高质量的 MBB 级深度研究分析报告。

## 产品概述

主题为「OpenClaw 深度研究：产品全景与全球大厂布局」的深度研究报告，定位光子策略分析前沿研究级别，面向决策者阅读。

## 核心功能

1. **框架调优**：基于融合版 Framework v1.0 的 Part1+Part2 双轨结构，结合已有子研究素材的实际深度和覆盖面，精简冗余模块、补齐缺失板块，形成最终执行版框架
2. **关键总结（首尾镜像）**：三列布局，Ø前置核心论点，首尾一字不差完全镜像
3. **Part 1 OpenClaw 全景认知**：行业概览与趋势洞察（含市场规模三情景TAM测算）、OpenClaw产品深度拆解（6大功能模块逐一分析）、竞品生态横评（多维度对比矩阵+梯队判定）
4. **Part 2 全球大厂战略博弈**：海外大厂深度扫描（OpenAI/Meta/Anthropic/Microsoft/Google/Notion/Perplexity 逐家分析，含战略意图+产品路线+风险评估）、国内大厂深度扫描（云厂商卖铲战+模型厂商Token争夺+创业生态）、竞争格局与战略推演（Bull/Base/Bear三情景+行业影响矩阵）、影响判断与行动启示
5. **全量数据实时搜索**：所有关键数据、事件描述、政策状态必须来源于当期实时搜索结果，严禁使用AI训练数据作为直接来源
6. **输出为 MD + PDF**：暂存 workflows/ 目录，待用户确认后归档 OrbitOS

## 技术栈

- 报告撰写格式：Markdown（长文）
- PDF 转换：`workflows/md_to_pdf.py`（单页长图，STHeiti/PingFang SC 字体，280mm 页宽，MBB 咨询风格）
- 数据获取：web_search / web_fetch 实时搜索
- 已有数据缓存：`workflows/openclaw_research_data/*.json`（6份搜索数据）
- 已有子研究素材：`OpenclawAIco/` 目录下4份深度研究文档

## 实现方案

### 整体策略

采用「框架调优 → 分模块搜索补料+撰写 → 总汇编+质检 → PDF输出」的四阶段流水线。基于融合版 Framework v1.0 的双轨结构（Part1 全景认知 + Part2 大厂博弈），结合已有4份子研究的实际覆盖深度进行框架微调，然后逐模块补充最新数据并撰写正文。

### 关键技术决策

1. **框架微调而非重写**：融合版 Framework v1.0 经过3轮迭代已趋成熟，仅需微调——将 M2E 竞品横评精简并入 M2 尾部，M5 和 M6 合并为「格局推演与行动启示」，控制总篇幅在 50-60 页（200-250 段正文）

2. **素材复用优先级**：

- 一手优先：4份子研究文档（含官方证据链）直接作为正文底稿
- 二手补充：6份 JSON 数据缓存作为数据引用源
- 三手搜索：仅对时效性数据（3月初最新动态、GitHub 最新星标、OpenRouter 最新排名）做增量搜索

3. **写作风格锁定**：

- Ø 前置核心结论 + abcd 分支论据 + 123 子论点的三层论证法
- 首尾关键总结完全镜像
- 每页底部标注信息来源
- 表格优先、判断性语言、3-5行段落

4. **报告总篇幅控制**：目标 50-60 页 MD 长文，阅读时间 25-35 分钟；关键总结 2 页 + Part1 约 18-22 页 + Part2 约 28-34 页 + 总结 2 页

## 实现注意事项

1. **数据时效性红线**：所有关键数字（GitHub stars、OpenRouter 排名、收购金额、产品发布日期等）必须来自当期实时搜索或已有子研究中标注的一手来源，不得使用训练数据直接填充；撰写时自查三问——来自当期搜索？时间戳最新？追问能指向具体来源？

2. **素材整合策略**：

- OpenClaw 产品定义/架构/历程 → 主用「是什么与发展历程」文档
- 增长数据/用例/技术拆解 → 主用「爆发式增长驱动 A/B/C」文档
- 海外大厂 → 主用「海外重点厂商布局动作全量扫描」文档
- 国内厂商 → 主用「中国厂商布局全量扫描 v7」文档
- 市场规模/竞品/竞争格局 → 主用 JSON 数据缓存 + 增量搜索

3. **PDF 输出标准**：使用 `workflows/md_to_pdf.py` 生成单页长图 PDF，验证 `file xxx.pdf` 显示 1 page、文件 2-5MB、Mac 预览无乱码

## 架构设计

### 报告最终结构（调优后）

```
关键总结（2页）— 三列布局，Ø前置，首尾完全镜像

Part 1：OpenClaw 全景认知（18-22页）
  M1 行业概览及趋势洞察（5-7页）
    1.1 AI Agent 行业定义与三大底层驱动力
    1.2 市场规模 TAM 三情景测算（B端+C端，悲观/基准/乐观+CAGR）
    1.3 产品趋势 Timeline（2023-2026 全景时间轴）
    1.4 技术趋势四大支柱（多模型路由/MCP-A2A/持久记忆/安全沙箱）
  M2 OpenClaw 产品深度拆解 + 竞品横评（10-14页）
    2.1 项目概况与创始人
    2.2 核心功能模块拆解（Gateway/执行器/记忆/多端/Skills/安全）
    2.3 Skills 生态拆解
    2.4 版本迭代与路线图
    2.5 核心优缺点
    2.6 竞品生态全景 + 多维度对比矩阵 + 梯队判定

Part 2：全球大厂战略博弈（28-34页，核心）
  M3 海外大厂深度扫描（14-18页）
    3.1 大厂动作 Timeline 全景图
    3.2 OpenAI：收编创始人的全盘棋（3页）
    3.3 Meta：20亿收购后的 Manus 进化（3页）
    3.4 Anthropic：48小时疯狂迭代的紧迫感（2页）
    3.5 Microsoft：Copilot Agent化的生态壁垒（2页）
    3.6 Google：模型+平台赋能（1-2页）
    3.7 SaaS平台 Agent化浪潮：Notion/Perplexity（1-2页）
    3.8 海外巨头对比矩阵 + 五大路线推演
  M4 国内大厂深度扫描（8-10页）
    4.1 国内 AI Agent 全景 Timeline
    4.2 云厂商卖铲战深度分析（腾讯云/阿里云/百度智能云/华为云/火山引擎/天翼云）
    4.3 模型厂商 Token 争夺战（Kimi/MiniMax/智谱/DeepSeek/百炼/混元）
    4.4 创业生态爆发
    4.5 国内格局 Mapping + 梯队判定
  M5 竞争格局推演与行动启示（6-8页）
    5.1 三大路线 Bull/Base/Bear 情景推演
    5.2 行业影响矩阵（渗透速度 x 影响深度）
    5.3 Token 经济全景 + 商业模式演变
    5.4 风险与机会雷达（SWOT + 风险矩阵）
    5.5 三段式趋势预判（短/中/长期）
    5.6 行动建议（3-5条）

总结（2页）— 关键总结完全镜像 + 厂商能力 Mapping 全景图
```

## 目录结构

```
workflows/
  OpenClaw深度研究-产品全景与全球大厂布局-20260306-HHMM-v1.md  # [NEW] 最终报告 MD 文件，50-60页深度研究报告正文
  OpenClaw深度研究-产品全景与全球大厂布局-20260306-HHMM-v1.pdf  # [NEW] 最终报告 PDF 文件，由 md_to_pdf.py 生成的单页长图PDF

已有素材文件（只读引用，不修改）:
  OpenclawAIco/OpenClaw-是什么与发展历程-MBB梳理-202603051539-v1.md
  OpenclawAIco/OpenClaw-爆发式增长驱动与A-B-C综合研究-202603051608-v2.md
  OpenclawAIco/OpenClaw-海外重点厂商布局动作全量扫描-202603052151-v1.md
  OpenclawAIco/OpenClaw-中国厂商布局全量扫描-202603052030-v7.md
  workflows/openclaw_research_data/batch_2a_market_tam.json
  workflows/openclaw_research_data/batch_2b_product_deep_dive.json
  workflows/openclaw_research_data/batch_2c_competitor_landscape.json
  workflows/openclaw_research_data/batch_3a_overseas_giants.json
  workflows/openclaw_research_data/batch_3b_domestic_giants.json
  workflows/openclaw_research_data/batch_3c_competition_scenarios.json
  workflows/md_to_pdf.py  # PDF转换脚本
```

## Agent Extensions

### Skill

- **deep-research**
- 用途：对报告中时效性最强的数据（GitHub最新星标、OpenRouter 2026年3月最新排名、各厂商3月初最新动态、市场规模最新预测）进行多源实时搜索、交叉验证和引用追踪
- 预期结果：获取经过多源验证的最新数据点，每个关键数字附带可追溯来源链接

- **wechat-article-search**
- 用途：补充搜索国内厂商最新动态的微信公众号文章（特别是3月初各云厂商/模型厂商的最新OpenClaw相关公告和活动）
- 预期结果：获取各国内厂商官方公众号的最新文章链接和核心要点，用于补充M4国内大厂章节的时效性内容

- **industry-research**
- 用途：为 M1 行业概览章节提供AI Agent行业趋势分析方法论框架、市场规模测算的最佳实践、产业链分析方法
- 预期结果：输出结构化的行业分析框架，确保M1章节的分析方法论达到MBB咨询标准

- **pdf**
- 用途：将最终完成的 MD 报告转换为符合 MBB 咨询风格的 PDF 文件
- 预期结果：生成单页长图 PDF，中文字体正确，排版美观，文件大小 2-5MB

### SubAgent

- **code-explorer**
- 用途：在撰写报告过程中快速定位和读取已有素材文件中的具体数据段落、证据链接和关键数字
- 预期结果：高效从4份子研究文档和6份JSON数据缓存中提取所需内容，避免遗漏关键素材