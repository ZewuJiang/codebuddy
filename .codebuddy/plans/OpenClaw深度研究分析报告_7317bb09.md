---
name: OpenClaw深度研究分析报告
overview: 全面梳理2026年现象级开源AI Agent项目OpenClaw的发展历程、技术架构、国内外大厂布局情况，以MBB咨询风格产出深度研究分析报告（MD+PDF）。
todos:
  - id: wechat-research
    content: 使用 [skill:wechat-article-search] 搜索 OpenClaw 相关微信公众号文章，重点覆盖大厂布局、技术解析、产业分析
    status: completed
  - id: deep-research
    content: 使用 [skill:deep-research] 对 OpenClaw 进行全网深度研究，补充海外大厂动态、GitHub 数据、竞争格局等关键信息
    status: completed
  - id: write-report
    content: 整合全部研究素材，撰写 MBB 风格 MD 研究报告（执行摘要+全景概述+大厂布局+竞争格局+趋势研判+风险提示），输出至 OrbitOS 热点分析目录
    status: completed
    dependencies:
      - wechat-research
      - deep-research
  - id: generate-pdf
    content: 使用 [skill:pdf] 调用 workflows/md_to_pdf.py 将 MD 报告转换为单页长图 PDF，验证中文无乱码且排版正确
    status: completed
    dependencies:
      - write-report
---

## 用户需求

老板要求全面梳理 OpenClaw 的信息，重点关注国内外大厂的布局情况，产出一份详尽且有效的研究分析报告，以 MBB 咨询风格格式呈现。

## 产品概述

产出一份关于 OpenClaw（开源AI Agent运行时框架）的深度研究报告，覆盖项目全景、技术架构、市场热度、国内外大厂布局（核心重点）、竞争格局、产业影响及趋势研判。信息源以微信公众号文章为重点，辅以全网权威媒体。报告以 MBB 咨询风格（McKinsey/BCG/Bain）排版，输出 MD+PDF 双格式（单页长图）。

## 核心内容板块

1. **执行摘要**：一页纸浓缩核心发现与关键判断
2. **OpenClaw 全景概述**：起源（Peter Steinberger）、发展里程碑（Clawdbot→Moltbot→OpenClaw）、核心技术架构（本地优先、Skills插件、多平台接入）、关键数据（24.8万星标登顶GitHub）
3. **国内外大厂布局全景分析**（核心重点章节）：

- 海外巨头：OpenAI（挖走创始人）、Meta（20亿美元收购Manus）、Anthropic（Claude Cowork）
- 国内云厂商"卖铲"战：百度智能云、阿里云、腾讯云一键部署服务对比
- 国内模型厂商"绑龙虾"：Kimi Claw、MaxClaw、智谱API套餐、网易有道龙虾应用、阿里CoPaw
- 创业生态：王慧文"英雄帖"等

4. **竞争格局与路线之争**：OpenClaw（开源本地优先）vs Manus（云端托管）vs Claude Cowork 的路线对比
5. **产业影响与趋势研判**：AI Agent 元年、从对话到执行的范式跃迁、对企业数字化的影响
6. **风险提示与关键不确定性**

## 技术方案

### 技术栈

- **信息采集**：使用 `[skill:wechat-article-search]` 搜索微信公众号文章 + `[skill:deep-research]` 进行全网深度研究
- **报告撰写**：Markdown 格式，MBB 咨询风格（深蓝+红色强调色系）
- **PDF 转换**：使用项目现有 `workflows/md_to_pdf.py`（v13.0，WeasyPrint 两轮渲染法，单页长图，STHeiti 字体，280mm 宽幅）

### 实现方案

1. **信息采集阶段**：通过 `wechat-article-search` 技能重点搜索微信公众号平台文章（用户明确要求 mp.weixin.qq.com），同时使用 `deep-research` 技能进行多源综合研究，确保信息全面、准确、时效性强
2. **报告撰写阶段**：按 MBB 咨询报告结构组织内容，使用表格、引用块、层级标题等 Markdown 元素，适配现有 `md_to_pdf.py` 的 CSS 样式体系（H1→H2→H3→H4层级、深蓝深色表头+斑马纹表格、红色强调色引用块）
3. **PDF 生成阶段**：调用 `workflows/md_to_pdf.py` 脚本转换，输出单页长图 PDF

### 实施要点

- **数据时效性**：所有数据、事件、引用必须来自实时搜索结果，严禁使用训练数据作为报告内容直接来源
- **信息源标注**：关键数据点标注来源（公众号名称/媒体名称），提升报告可信度
- **MD 格式适配**：严格按照 `md_to_pdf.py` 的 CSS 层级体系撰写（H1 报告标题、H2 章节、H3 子章节、H4 细分模块），确保 PDF 排版美观
- **表格设计**：大厂布局对比、竞争格局分析等核心内容使用结构化表格呈现，利用现有深色表头+斑马纹样式

### 目录结构

```
/Users/zewujiang/Desktop/OrbitOS/30_专题研究/热点分析/
├── OpenClaw深度研究-国内外大厂布局全景分析-20260304-v1.md   # [NEW] MBB风格研究报告MD源文件，包含执行摘要、全景概述、大厂布局分析（海外+国内云厂商+模型厂商+创业生态）、竞争格局、趋势研判、风险提示共6大章节，大量结构化表格
└── OpenClaw深度研究-国内外大厂布局全景分析-20260304-v1.pdf # [NEW] 由md_to_pdf.py生成的单页长图PDF，280mm宽幅，STHeiti中文字体，MBB咨询排版风格
```

## Agent Extensions

### Skill

- **wechat-article-search**
- 用途：搜索微信公众号平台文章，获取关于 OpenClaw 的深度分析、大厂布局、产业评论等中文权威内容
- 预期结果：获取 15-20 篇高质量微信公众号文章，覆盖 OpenClaw 技术解析、大厂动态、产业趋势等维度，作为报告核心信息源

- **deep-research**
- 用途：对 OpenClaw 进行企业级深度研究，多源综合搜索，覆盖 GitHub 数据、海外媒体报道、大厂官方公告、行业分析等
- 预期结果：产出经过交叉验证的全面研究素材，包含国内外大厂布局详情、竞争格局数据、关键时间线等，确保报告数据准确可靠

- **pdf**
- 用途：使用项目现有 `workflows/md_to_pdf.py` 脚本将 MD 报告转换为 MBB 风格单页长图 PDF
- 预期结果：生成 280mm 宽幅、STHeiti 中文字体、深蓝+红色强调色系的专业 PDF 文件，Mac Preview 无乱码