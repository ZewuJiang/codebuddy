---
name: berkshire-abel-letter-analysis
overview: 生成一份专业的伯克希尔·哈撒韦阿贝尔首份股东信解读与持仓建议文档（MD+PDF），去除AI味道，风格像投行研报，可直接发群里给大老板。
todos:
  - id: write-md
    content: 撰写伯克希尔-阿贝尔股东信解读MD文档，投行研报风格，包含核心结论、三大信号、财务数据表、持仓建议更新，去除AI味道
    status: completed
  - id: generate-pdf
    content: 使用 [skill:pdf] 通过 md_to_pdf.py 将MD转换为单页长图PDF并验证中文无乱码
    status: completed
    dependencies:
      - write-md
---

## 用户需求

大老板周末（2026年3月1日）在群里转发了伯克希尔哈撒韦新任CEO格雷格·阿贝尔的首份致股东信（2月28日发布）。此前投资计划中BRK-B被列为"稳健标的"并标注"接任巴菲特后需再观察"。用户需要生成一份专业解读文档直接丢群里作为回复。

## 产品概述

一份精炼的投行研报风格文档，对阿贝尔首份致股东信进行专业解读，同时更新对伯克希尔持仓的判断建议，直接供大老板和群内成员阅读。

## 核心特征

- MD文档 + PDF文档，放在 workflows/ 目录下
- 投行/顶尖策略师研报风格，零AI味道，语气用"我们"
- 篇幅2-3页，短句、数据驱动、直接下判断
- 呼应此前"需再观察"的立场，给出阶段性结论更新
- 包含阿贝尔股东信三大超预期信号、关键财务数据、持仓建议更新
- 文件名：伯克希尔-阿贝尔股东信解读-20260301-1903-v1.md / .pdf

## 技术栈

- Markdown 撰写文档
- 现有 `workflows/md_to_pdf.py`（v13.0）脚本转换PDF
- WeasyPrint + pdfplumber 两轮渲染法生成单页长图PDF
- 中文字体：STHeiti 优先
- 页面宽度：280mm，MBB咨询/GS Investment Research 排版风格

## 实现方案

1. 在 `workflows/` 下创建 MD 文件，采用与现有晨报/深度分析一致的 Markdown 格式体系（h1标题 → h2章节 → h3小节 → 表格 → blockquote引用块）
2. 内容采用投行 Equity Research Note 风格：开篇元数据表 → 核心结论（Rating Change / Executive Summary）→ 阿贝尔股东信三大信号 → 关键财务数据表 → 持仓建议更新 → 风险提示与下一验证节点
3. 使用现有 `md_to_pdf.py` 脚本转换为PDF（单页长图，深色表头+斑马纹表格，红色强调色）
4. 语气把控：全程"我们"视角，禁用"综上所述""值得注意的是""总而言之"等AI套话，用短句、数据、直接判断

## 实现细节

### MD文档结构设计（对齐现有GS Investment Research风格）

文档结构规划：

- **元数据表**：报告类型、日期、版本、数据源
- **§1 核心结论**：Rating Update横幅 + 三句话总结 + "此前判断 → 更新判断"对比表
- **§2 阿贝尔首份股东信：三个超预期信号**：运营型CEO锐度 / 投资哲学延续 / 3733亿现金战略
- **§3 2025年报关键数据**：财务数据表（营业利润、净利润、现金储备、浮存金等）+ 投资组合数据
- **§4 持仓建议更新**：具体加仓区间、仓位建议、验证节点
- **§5 风险与关注**：两大风险 + 5月2日股东大会验证窗口
- **免责声明**

### 去AI味道要点

- 不用"首先""其次""最后"结构
- 不用"综上所述""值得注意的是""需要指出的是"
- 多用破折号、短句、数据直接说话
- 判断用"我们认为""数据显示""逻辑清晰"
- 适当使用投行术语：succession risk premium、war chest、conglomerate discount、sweet spot

### PDF转换命令

```
cd /Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows
python3 md_to_pdf.py "伯克希尔-阿贝尔股东信解读-20260301-1903-v1.md" "伯克希尔-阿贝尔股东信解读-20260301-1903-v1.pdf"
```

## 目录结构

```
workflows/
├── 伯克希尔-阿贝尔股东信解读-20260301-1903-v1.md   # [NEW] 阿贝尔首份致股东信专业解读，投行研报风格，包含核心结论、三大信号、财务数据、持仓建议更新。对齐现有GS Investment Research CSS样式体系（h1/h2/h3层级、深色表头表格、红色blockquote横幅）
├── 伯克希尔-阿贝尔股东信解读-20260301-1903-v1.pdf   # [NEW] 由md_to_pdf.py生成的单页长图PDF，280mm宽幅，STHeiti字体，MBB咨询风格排版
└── md_to_pdf.py                                       # [EXISTING] 现有MD转PDF脚本，直接复用
```

## Agent Extensions

### Skill

- **pdf**
- 用途：在MD文件生成后，使用md_to_pdf.py脚本将MD转换为PDF文档
- 预期结果：生成符合MBB咨询风格的单页长图PDF，中文无乱码，280mm宽幅