---
name: skill-global-search
description: 从 github、skills.sh 搜索和安装 Agent Skills（80,000+ 技能库）。当用户提到"skill"并有查找/搜索/安装意图时触发，如"有没有...skill"、"找个skill"、"搜索SQL相关的skill"。不用于普通网页搜索。
---

# Skill 全局搜索

从 skills.sh（80,000+ 技能目录）和 GitHub 搜索并安装 Agent Skills。

## 工作流程

### 第一步：检查环境

先运行此命令：

```bash
node --version
```

- **成功**（显示版本如 `v20.x.x`）→ 进入 **第二步A**
- **失败**（command not found）→ 进入 **第二步B**

---

### 第二步A：双源并行搜索（CLI + GitHub 同等重要）

> ⛔ **核心约束（违反任一条即为失败）**：
> 1. **CLI 和 GitHub 必须都有结果才能输出**（除非某源确实无结果）
> 2. **GitHub 结果必须单独处理和展示**，不能被 CLI 结果"淹没"
> 3. **必须对 GitHub 搜索结果执行 web_fetch** — 无论 CLI 是否有结果

#### 执行顺序：

**2A-1: 关键词扩展**（在脑中完成，不需输出）
- 用户关键词 → 英文翻译 + 同义词 + 相关工具名
- 例：自动化剪辑 → video editing, video clipper, ffmpeg, remotion

**2A-2: 第一批并行搜索**（同一批次 tool call，共 4 个）
```
execute_command: npx skills find "{英文关键词}"
web_search: site:github.com SKILL.md {关键词} {工具名}
web_search: github awesome-claude-skills {关键词}
web_search: github claude skill {工具名} agent
```

**2A-3: 第二批 GitHub 补充搜索**（如果第一批 GitHub 结果不理想，必须再搜）
```
web_search: github {工具名}-skill claude code
web_search: site:github.com claude agent {同义词/相关工具}
```

> ⚠️ **GitHub 搜索至少 3 次**，因为：
> - 第 1 次（精确搜）：`site:github.com SKILL.md {关键词}` — 找独立 skill 仓库
> - 第 2 次（合集搜）：`awesome-claude-skills {关键词}` — 找合集
> - 第 3 次（工具搜）：`{工具名}-skill` 或 `claude skill {工具名}` — 找特定工具封装

**2A-4: GitHub 结果深挖**（⚠️ 必选，这是之前遗漏的关键步骤）
- **无论 CLI 是否有结果**，都必须对 GitHub 搜索中找到的仓库执行 `web_fetch`
- 优先深挖：
  1. `awesome-claude-skills` 或类似合集 → 提取具体 skill
  2. 包含 `SKILL.md` 的独立仓库 → 获取描述
  3. 知名工具的 skill 封装（如 ffmpeg-skill, remotion-skill）

**2A-5: 结果合并与去重**
- CLI 结果 → 直接列出
- GitHub 结果 → 必须单独列出，即使与 CLI 有重复也要标注来源

**⛔ 结果处理规则：**

| 搜索结果类型 | 处理方式 |
|------------|---------|
| CLI 返回的 skill | ✅ 加入 "来自 skills.sh" 分区 |
| GitHub 独立 skill 仓库 | ✅ 加入 "来自 GitHub" 分区（必须有这个分区！） |
| awesome-xxx 合集 | ⚠️ 用 `web_fetch` 深挖后，将具体 skill 加入 GitHub 分区 |
| 博客/教程文章 | ❌ 忽略 |
| 普通工具仓库（无 SKILL.md） | ❌ 忽略 |

#### 输出前自检（必须全部打勾才能输出）：
- [ ] CLI 搜索已完成？
- [ ] **GitHub web_search 至少执行了 3 次？**（精确搜 + 合集搜 + 工具搜）
- [ ] **对 GitHub 结果执行了 web_fetch？**（这是关键！）
- [ ] 输出中包含 "来自 GitHub" 分区？（即使为空也要说明 "GitHub 未找到相关 skill"）
- [ ] 如果搜到 awesome 合集，已深挖提取具体 skill？

**输出模板：**
```
找到 N 个关于 "{关键词}" 的 skill：

## 📦 来自 skills.sh (CLI)
| # | Skill | 安装命令 |
|---|-------|---------|
| 1 | nextlevelbuilder/ui-ux-pro-max-skill | `npx skills add nextlevelbuilder/ui-ux-pro-max-skill` |
| 2 | vercel-labs/agent-skills | `npx skills add vercel-labs/agent-skills` |

## 🔍 来自 GitHub
| # | Skill | ⭐ Stars | 描述 | URL |
|---|-------|---------|-----|-----|
| 3 | some-user/sql-helper | ⭐ 234 | 自然语言转 SQL | https://github.com/... |

需要安装哪个？（输入序号）
```

然后进入 **第三步**。

---

### 第二步B：降级方案（无 Node.js）

**首先告知用户：**

```
未安装 Node.js。请选择：

1. **安装 Node.js**（推荐，完整功能）
   - macOS: `brew install node`
   - Ubuntu: `sudo apt install nodejs npm`
   - Windows: https://nodejs.org

2. **继续使用网页搜索**（功能受限但可用）

选择哪个？
```

**如果用户选择选项 2**，使用 web_search 工具执行以下查询：

1. 搜索：`skills.sh {英文关键词} skill`
2. 搜索：`github claude code skill {英文关键词} {相关工具名}`

**从搜索结果中提取 GitHub URL 并展示：**

```
通过网页搜索找到以下 skill：

| # | Skill | GitHub URL |
|---|-------|------------|
| 1 | ui-ux-pro-max-skill | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |

需要我安装 #1 吗？
```

然后进入 **第三步B** 手动安装。

---

### 第三步：安装

> ⚠️ **默认安装到当前项目的 `.codebuddy/skills/` 目录**，不使用 symlink。
> 安装前必须向用户确认安装位置。

**3.1 确认安装位置（必须询问用户）：**
```
即将安装 {skill-name} 到：
  → {project_path}/.codebuddy/skills/{skill-name}/

确认安装？(y/n)
```

**3.2 执行安装（使用 git clone + copy，确保文件直接在项目中）：**

```bash
# 克隆到临时目录
git clone --depth 1 https://github.com/{owner}/{repo}.git /tmp/{repo}

# 在项目中创建 skill 目录
mkdir -p .codebuddy/skills/{skill-name}

# 复制 skill 文件（非 symlink）
# 检查 SKILL.md 在根目录还是子目录
if [ -f /tmp/{repo}/SKILL.md ]; then
  cp /tmp/{repo}/SKILL.md .codebuddy/skills/{skill-name}/
elif [ -f /tmp/{repo}/skills/{skill-name}/SKILL.md ]; then
  cp -r /tmp/{repo}/skills/{skill-name}/* .codebuddy/skills/{skill-name}/
elif [ -f /tmp/{repo}/.claude/skills/{skill-name}/SKILL.md ]; then
  cp -r /tmp/{repo}/.claude/skills/{skill-name}/* .codebuddy/skills/{skill-name}/
fi

# 复制附加文件（如存在）
cp -r /tmp/{repo}/scripts .codebuddy/skills/{skill-name}/ 2>/dev/null
cp -r /tmp/{repo}/data .codebuddy/skills/{skill-name}/ 2>/dev/null
cp -r /tmp/{repo}/references .codebuddy/skills/{skill-name}/ 2>/dev/null

# 清理临时文件
rm -rf /tmp/{repo}
```

**3.3 验证安装：**
```bash
ls -la .codebuddy/skills/{skill-name}/
cat .codebuddy/skills/{skill-name}/SKILL.md | head -10
```

**3.4 向用户确认：**
```
✓ 已安装 {skill-name}！

位置: .codebuddy/skills/{skill-name}/
文件: SKILL.md (+ 其他文件如有)

现在可以通过提及该 skill 的能力来使用它。
```

---

### 第三步B：备选方案（npx skills add）

> ⚠️ 注意：`npx skills add` 可能创建 symlink，不推荐作为默认方式。
> 仅当第三步失败时使用，且需要后续将 symlink 转为实际文件。

```bash
npx skills add {owner/repo} -y

# 如果创建了 symlink，转换为实际文件
if [ -L .codebuddy/skills/{skill-name} ]; then
  target=$(readlink .codebuddy/skills/{skill-name})
  rm .codebuddy/skills/{skill-name}
  cp -r "$target" .codebuddy/skills/{skill-name}
fi
```

**注意：** 如果 SKILL.md 在子目录中（如 `skills/skill-name/SKILL.md`），需相应调整复制路径。

---

## 快速参考

### 热门 Skills

| Skill | 用途 | 安装命令 |
|-------|-----|---------|
| vercel-labs/agent-skills | React, PR 审查 | `npx skills add vercel-labs/agent-skills` |
| anthropics/skills | PDF, PPTX, XLSX, DOCX 处理 | `npx skills add anthropics/skills` |
| nextlevelbuilder/ui-ux-pro-max-skill | UI/UX 设计 | `npx skills add nextlevelbuilder/ui-ux-pro-max-skill` |
| lackeyjb/playwright-skill | Playwright 浏览器自动化测试 | `npx skills add lackeyjb/playwright-skill` |

### 常用命令

| 命令 | 功能 |
|-----|-----|
| `npx skills find {关键词}` | 搜索 skills |
| `npx skills add {repo}` | 安装到项目 |
| `npx skills add {repo} -g` | 全局安装 |
| `npx skills add {repo} -l` | 列出仓库中的 skills |
| `npx skills check` | 检查更新 |
| `npx skills update` | 更新全部 |

### 常见问题排查

| 问题 | 解决方案 |
|-----|---------|
| npx 未找到 | 安装 Node.js 或使用手动方法 |
| 无搜索结果 | 尝试英文关键词、更宽泛的词、相关工具名 |
| 安装失败 | 检查网络；尝试手动 git clone |
| Skill 不工作 | 重启 IDE；检查路径 |

---

## 相关资源

- 浏览所有 skills: https://skills.sh
- 创建自己的 skill: 使用 **skill-writer** skill
