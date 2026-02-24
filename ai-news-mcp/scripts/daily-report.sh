#!/bin/bash

# AI 资讯每日自动化脚本
# 用法: ./daily-report.sh

echo "🤖 开始生成 AI 前沿资讯每日报告..."
echo "📅 日期: $(date '+%Y-%m-%d')"
echo ""

# 设置输出目录
OUTPUT_DIR="$HOME/AI-Reports/daily"
mkdir -p "$OUTPUT_DIR"

# 设置报告文件名
REPORT_FILE="$OUTPUT_DIR/AI-Daily-$(date '+%Y%m%d').md"

# 调用 MCP 生成报告（这里需要通过 CodeBuddy 或其他 MCP 客户端调用）
cat > "$REPORT_FILE" << 'EOF'
# 🤖 AI 前沿资讯 - 每日简报

**日期**: $(date '+%Y年%m月%d日')

---

> 💡 **提示**: 请在 CodeBuddy 中运行以下命令来生成完整报告：
> 
> ```
> 使用 ai-news MCP 的 generate_daily_report 工具生成今日 AI 资讯报告
> ```

## 📋 快速操作指南

### 1️⃣ 生成每日报告

在 CodeBuddy 中执行：
```
调用 ai-news.generate_daily_report，包含研究机构、新闻和游戏三个分类的资讯
```

### 2️⃣ 获取最新论文

```
调用 ai-news.fetch_arxiv_papers，获取今日最新的 10 篇 AI/ML 论文
```

### 3️⃣ 深度分析

结合 Skills 进行分析：
```
1. 使用 apify-trend-analysis 分析趋势
2. 使用 content-research-writer 撰写深度报告
3. 使用 presentation-design 制作 PPT
```

---

## 🎯 今日重点关注

- [ ] 顶级研究机构新动态
- [ ] 游戏 AI 应用进展
- [ ] 生成式 AI 突破
- [ ] 多模态模型更新

EOF

echo "✅ 报告模板已创建: $REPORT_FILE"
echo ""
echo "📌 下一步操作："
echo "   1. 在 CodeBuddy 中打开此文件"
echo "   2. 使用 AI News MCP 工具填充实际内容"
echo "   3. 结合 Skills 进行深度分析"
echo ""
echo "💡 提示: 建议使用 cron 设置每天早上 9:00 自动运行此脚本"
echo "   示例: 0 9 * * * /path/to/daily-report.sh"
