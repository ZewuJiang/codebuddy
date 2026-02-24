# 🤖 AI 前沿资讯实时监控 MCP Server

专为游戏公司战略分析师设计的 AI 资讯自动化监控系统。

## 📋 功能特性

### 🔍 数据源覆盖

- **顶级 AI 研究机构**: OpenAI、Anthropic、DeepMind、Google AI
- **AI 资讯平台**: MIT Tech Review、VentureBeat、The Verge
- **游戏行业 AI**: GameDeveloper、Gamasutra
- **学术论文**: arXiv (cs.AI, cs.LG, cs.CV, cs.CL, cs.GR)

### 🛠️ 核心工具

1. **fetch_ai_news** - 获取最新 AI 资讯
   - 支持时间范围：今日/本周/本月
   - 支持分类筛选：研究机构/新闻/游戏
   - 自动按时间排序

2. **fetch_arxiv_papers** - 获取 arXiv 最新论文
   - 支持多个 AI/ML 相关分类
   - 自动提取标题、作者、摘要

3. **generate_daily_report** - 生成每日简报
   - MBB 咨询风格
   - 包含关键洞察和战略建议

4. **generate_weekly_report** - 生成每周深度报告
   - 完整战略分析框架
   - 包含趋势预测和风险分析

## 🚀 安装部署

### 1. 安装依赖

```bash
cd ai-news-mcp
npm install
```

### 2. 构建项目

```bash
npm run build
```

### 3. 配置 MCP 客户端

在 CodeBuddy 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "ai-news": {
      "command": "node",
      "args": ["/Users/zewujiang/Desktop/AICo/codebuddy/ai-news-mcp/dist/index.js"],
      "env": {}
    }
  }
}
```

## 📖 使用示例

### 示例 1: 获取今日 AI 资讯

```typescript
// 调用 MCP 工具
fetch_ai_news({
  timeRange: "daily",
  category: "all",
  limit: 20
})
```

### 示例 2: 获取游戏 AI 论文

```typescript
fetch_arxiv_papers({
  category: "cs.GR",  // 图形学相关
  maxResults: 10
})
```

### 示例 3: 生成每日报告

```typescript
generate_daily_report({
  includeCategories: ["research", "news", "gaming"]
})
```

## 🔄 自动化工作流

### 每日工作流（建议早上 9:00）

1. 调用 `generate_daily_report` 获取每日简报
2. 使用 `content-research-writer` skill 进行深度分析
3. 使用 `presentation-design` skill 制作 PPT

### 每周工作流（建议周一上午）

1. 调用 `generate_weekly_report` 获取周报
2. 使用 `apify-trend-analysis` skill 进行趋势分析
3. 使用 `strategy-advisor` skill 生成战略建议
4. 使用 `pptx` skill 生成高管汇报 PPT

## 🎯 与现有 Skills 配合

```
AI News MCP (数据采集)
    ↓
apify-trend-analysis (趋势分析)
    ↓
content-research-writer (深度研究)
    ↓
market-research-reports (报告生成)
    ↓
presentation-design (可视化)
```

## 📝 MBB 风格报告模板

报告包含以下标准章节：

1. **Executive Summary** - 核心发现
2. **Industry Trends** - 行业动态
3. **Strategic Recommendations** - 战略建议
4. **Risks & Opportunities** - 风险与机遇

## 🔧 定制化配置

### 添加自定义 RSS 源

编辑 `src/index.ts` 中的 `AI_NEWS_SOURCES` 数组：

```typescript
const AI_NEWS_SOURCES = [
  { 
    name: '自定义源名称', 
    url: 'https://example.com/rss.xml', 
    category: 'custom' 
  },
  // ... 更多源
];
```

### 调整论文分类

修改 `ARXIV_CATEGORIES` 数组添加更多分类。

## 📊 数据更新频率

- **RSS 源**: 实时抓取（调用时）
- **arXiv 论文**: 每日更新
- **建议调用频率**: 
  - 每日报告：每天1次
  - 每周报告：每周1次

## 🛡️ 注意事项

1. 部分 RSS 源可能需要代理访问
2. arXiv API 有请求频率限制（建议不超过每3秒1次）
3. 建议设置定时任务自动生成报告

## 📧 支持

如有问题，请查阅 [MCP 官方文档](https://modelcontextprotocol.io/)

---

**版本**: 1.0.0  
**更新日期**: 2026-02-21
