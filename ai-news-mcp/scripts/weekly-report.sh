#!/bin/bash

# AI 资讯每周自动化脚本
# 用法: ./weekly-report.sh

echo "📊 开始生成 AI 战略分析每周报告..."
echo "📅 周期: $(date '+%Y年第%U周')"
echo ""

# 设置输出目录
OUTPUT_DIR="$HOME/AI-Reports/weekly"
mkdir -p "$OUTPUT_DIR"

# 设置报告文件名
REPORT_FILE="$OUTPUT_DIR/AI-Weekly-W$(date '+%U')-$(date '+%Y').md"

cat > "$REPORT_FILE" << 'EOF'
# 📈 AI 战略分析 - 每周深度报告

**周期**: $(date '+%Y年第%U周')
**日期**: $(date '+%Y-%m-%d')

---

> 💡 **提示**: 请在 CodeBuddy 中运行以下命令来生成完整报告

## 📋 报告生成流程

### 阶段 1: 数据收集（MCP）

```
调用 ai-news.generate_weekly_report，关注领域：gaming, generative-ai, multimodal
```

### 阶段 2: 趋势分析（Skill）

```
使用 apify-trend-analysis skill 分析本周 AI 行业趋势
```

### 阶段 3: 竞品分析（Skill）

```
使用 competitive-analysis skill 分析游戏行业竞争态势
```

### 阶段 4: 战略建议（Skill）

```
使用 strategy-advisor skill 生成战略决策建议
```

### 阶段 5: 报告生成（Skill）

```
使用 market-research-reports skill 生成 MBB 风格完整报告
```

### 阶段 6: PPT 制作（Skill）

```
使用 presentation-design skill 制作高管汇报 PPT
```

---

## 📊 本周关键指标

- AI 重大新闻: [待统计]
- 新发论文: [待统计]
- 游戏 AI 应用: [待统计]
- 行业融资: [待统计]

## 🎯 重点关注领域

1. **游戏 AI 应用**
   - [ ] NPC 智能化
   - [ ] 程序化内容生成
   - [ ] 玩家行为预测

2. **生成式 AI**
   - [ ] 新模型发布
   - [ ] 游戏应用案例
   - [ ] 技术突破

3. **多模态 AI**
   - [ ] 视觉+语言模型
   - [ ] 游戏场景理解
   - [ ] 交互式 AI

## 💼 给高管的建议

### 立即行动（0-3个月）
- [待 AI 分析填充]

### 中期规划（3-12个月）
- [待 AI 分析填充]

### 长期布局（1-3年）
- [待 AI 分析填充]

EOF

echo "✅ 周报模板已创建: $REPORT_FILE"
echo ""
echo "📌 下一步操作："
echo "   1. 在 CodeBuddy 中打开此文件"
echo "   2. 按照流程逐步生成各部分内容"
echo "   3. 使用 Skills 进行深度分析"
echo "   4. 制作 PPT 给高管汇报"
echo ""
echo "💡 提示: 建议每周一早上 9:00 运行此脚本"
echo "   示例: 0 9 * * 1 /path/to/weekly-report.sh"
