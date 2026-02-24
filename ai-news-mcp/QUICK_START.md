# 🚀 AI News MCP - 快速开始指南

## ⚠️ 重要提示

**在使用 MCP 工具之前，您需要先重启 CodeBuddy！**

MCP 配置已添加到 `~/.codebuddy/mcp.json`，但需要重启才能生效。

---

## 📋 重启后如何使用

### **方式 1: 直接对话（最简单）** ⭐

重启 CodeBuddy 后，直接输入以下任一命令：

```
# 示例 1: 获取今日 AI 资讯
请使用 ai-news 获取今日 AI 资讯

# 示例 2: 获取游戏 AI 资讯
请使用 ai-news 获取今日游戏行业 AI 资讯

# 示例 3: 获取最新论文
请使用 ai-news 获取最新的 AI/ML 论文

# 示例 4: 生成每日报告
请使用 ai-news 生成今日 AI 资讯简报

# 示例 5: 生成每周报告
请使用 ai-news 生成本周 AI 战略分析报告
```

AI 会自动调用相应的 MCP 工具并返回结果。

---

### **方式 2: 查看可用工具**

重启后，您可以查询 MCP 提供的工具：

```
列出 ai-news MCP 的所有可用工具
```

应该会看到 4 个工具：
1. ✅ `fetch_ai_news` - 获取最新 AI 资讯
2. ✅ `fetch_arxiv_papers` - 获取 arXiv 论文
3. ✅ `generate_daily_report` - 生成每日简报
4. ✅ `generate_weekly_report` - 生成每周报告

---

## 🎯 实际使用示例

### **示例 1: 每日早晨快速浏览**

```
你好，请帮我获取今日 AI 前沿资讯，重点关注：
1. 顶级研究机构（OpenAI、Anthropic、DeepMind）的新动态
2. 游戏行业的 AI 应用进展
3. 生成式 AI 的最新突破

请给我一个简洁的 Markdown 格式摘要。
```

**预期输出**: 10-20 条今日最新资讯，按来源分类

---

### **示例 2: 准备每周汇报**

```
请帮我生成本周 AI 战略分析报告，包含以下内容：
1. 本周重要 AI 资讯汇总
2. 游戏行业 AI 应用趋势分析
3. 竞品动态（如有）
4. 给高管的战略建议

请使用 MBB 咨询风格，生成完整报告框架。
```

**预期输出**: MBB 风格的周报框架（包含 Executive Summary、Industry Trends、Strategic Recommendations 等章节）

---

### **示例 3: 深度研究某个主题**

```
我想研究"多模态 AI 在游戏中的应用"，请帮我：
1. 获取相关的最新学术论文（arXiv）
2. 收集行业资讯和应用案例
3. 分析技术趋势
4. 生成一份深度研究报告

请从 ai-news MCP 开始收集数据。
```

**预期输出**: 
- 10+ 篇相关论文
- 最新行业资讯
- 深度分析报告（可结合 Skills）

---

### **示例 4: 组合使用 MCP + Skills**

```
请执行以下完整工作流：

第1步：使用 ai-news MCP 获取本周 AI 资讯
第2步：使用 apify-trend-analysis skill 分析趋势
第3步：使用 content-research-writer skill 撰写深度报告
第4步：使用 presentation-design skill 制作 PPT 大纲
第5步：使用 pptx skill 生成最终 PPT

主题：本周 AI 游戏应用战略分析
```

**预期输出**: 从数据采集到 PPT 的完整输出

---

## 🔧 高级用法

### **自定义参数**

```
请使用 ai-news 的 fetch_ai_news 工具，参数如下：
- timeRange: weekly（本周）
- category: gaming（游戏分类）
- limit: 30（最多 30 条）
```

### **只获取论文**

```
请使用 ai-news 的 fetch_arxiv_papers 工具，获取：
- 分类：cs.GR（图形学，适合游戏 AI）
- 数量：15 篇
```

---

## 📊 可用的参数选项

### `fetch_ai_news` 工具参数

| 参数 | 选项 | 说明 |
|------|------|------|
| `timeRange` | `daily`, `weekly`, `monthly` | 时间范围 |
| `category` | `all`, `research`, `news`, `gaming` | 资讯分类 |
| `limit` | 数字（默认 20） | 返回条数 |

### `fetch_arxiv_papers` 工具参数

| 参数 | 选项 | 说明 |
|------|------|------|
| `category` | `cs.AI`, `cs.LG`, `cs.CV`, `cs.CL`, `cs.GR`, `all` | 论文分类 |
| `maxResults` | 数字（默认 10） | 返回论文数 |

### `generate_daily_report` 工具参数

| 参数 | 选项 | 说明 |
|------|------|------|
| `includeCategories` | `["research", "news", "gaming", "papers"]` | 包含的分类 |

### `generate_weekly_report` 工具参数

| 参数 | 选项 | 说明 |
|------|------|------|
| `focusAreas` | `["gaming", "generative-ai", "multimodal"]` | 重点关注领域 |

---

## ⚡ 快速命令速查表

```bash
# 基础查询
"获取今日 AI 资讯"
"获取本周 AI 资讯"
"获取游戏 AI 资讯"
"获取最新 AI 论文"

# 报告生成
"生成今日 AI 简报"
"生成本周 AI 战略报告"

# 组合查询
"获取今日游戏 AI 资讯并分析趋势"
"获取本周资讯并生成 MBB 风格报告"
"获取多模态 AI 论文并撰写研究报告"

# 高级用法
"使用 ai-news 获取本周游戏分类的 30 条资讯"
"使用 ai-news 获取计算机视觉（cs.CV）的 20 篇最新论文"
```

---

## 🐛 故障排查

### 问题 1: "找不到 ai-news MCP"

**原因**: 未重启 CodeBuddy

**解决**: 
1. 完全退出 CodeBuddy
2. 重新启动
3. 等待 MCP 加载完成（通常 5-10 秒）

---

### 问题 2: "MCP 工具调用失败"

**检查清单**:
```bash
# 1. 检查 MCP 文件是否存在
ls /Users/zewujiang/Desktop/AICo/codebuddy/ai-news-mcp/dist/index.js

# 2. 检查 Node.js 是否安装
node --version

# 3. 检查 MCP 配置
cat ~/.codebuddy/mcp.json

# 4. 手动测试 MCP（可选）
node /Users/zewujiang/Desktop/AICo/codebuddy/ai-news-mcp/dist/index.js
```

---

### 问题 3: "获取资讯失败"

**可能原因**:
- 网络连接问题
- RSS 源暂时不可访问
- arXiv API 限流

**解决**: 
- 检查网络连接
- 稍后重试
- 尝试只获取部分分类的资讯

---

## 💡 最佳实践

### 1. **每日使用习惯**

```
早上 9:00
  ↓
"请使用 ai-news 获取今日 AI 资讯，重点关注游戏和生成式 AI"
  ↓
5 分钟快速浏览
  ↓
标记需要深度研究的主题
```

### 2. **每周深度分析**

```
周一上午
  ↓
"请生成本周 AI 战略分析报告"
  ↓
使用 Skills 进行深度分析
  ↓
制作 PPT 给高管
```

### 3. **专题研究**

```
确定研究主题
  ↓
"获取相关论文和资讯"
  ↓
使用 content-research-writer 撰写报告
  ↓
使用 market-research-reports 生成咨询级报告
```

---

## 🎯 下一步

1. ✅ **立即重启 CodeBuddy**
2. ✅ **测试第一个命令**: `"请使用 ai-news 获取今日 AI 资讯"`
3. ✅ **阅读完整文档**: [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)
4. ✅ **设置自动化**: 配置定时任务或 GitHub Actions

---

## 📞 帮助

- 📖 完整文档: [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)
- 🔧 技术文档: [README.md](./README.md)
- ✅ 安装总结: [INSTALLATION_SUCCESS.md](./INSTALLATION_SUCCESS.md)

---

**祝您使用愉快！🎉**

记得多喝水！💧
