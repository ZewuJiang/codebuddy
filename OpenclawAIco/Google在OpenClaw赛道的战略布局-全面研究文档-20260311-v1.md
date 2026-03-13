# Google在OpenClaw赛道的战略布局——全面研究文档

> **文档定位**：一站式参考文档，覆盖Google在OpenClaw/Computer Use赛道的全部关键动作，阅读本文即无需另查资料
>
> **版本**：v1 | **更新日期**：2026-03-11 | **信息截止**：2026年3月11日
>
> **数据来源**：OpenAI官方、Google官方、IT之家、机器之心、36氪、虎嗅、新智元、Ars Technica、TechCrunch、CSDN、搜狐科技、腾讯科技、GitHub等

---

## 核心结论（Executive Summary）

Google在OpenClaw赛道采取了**"双轨并行"**策略：

| 维度 | 第一轨：自研Agent产品线 | 第二轨：开源基础设施（Workspace CLI） |
|------|----------------------|----------------------------------|
| **战略意图** | 构建端到端Agent能力（模型→产品→协议） | 为OpenClaw等第三方Agent提供"数字手臂" |
| **产品形态** | Project Mariner、Gemini 2.5 Computer Use、Jules、Agentspace、A2A协议 | Google Workspace CLI（gws）开源工具 |
| **当前状态** | 产品多但**声量一般**，未形成爆款，市场认知被Anthropic和OpenAI压制 | 上线即**爆火**，GitHub 15k Stars，Addy Osmani推文浏览量破500万 |
| **核心矛盾** | 技术能力强但产品化落地慢，"追随者"标签挥之不去 | 工具定位精准，但非正式产品（no official support），存在数据风险 |
| **战略定位** | 防守：不能让Agent赛道被Anthropic/OpenAI完全占据 | 进攻：借OpenClaw热潮抢占Agent基础设施生态位 |

**一句话总结**：Google的自研Agent产品"什么都做了，但没一个冒出来"；而Workspace CLI则精准卡位OpenClaw热潮，成为Google在Agent基础设施层面最成功的一次出手。

---

## 第一部分：Google自研Agent产品线——全面布局，声量有限

### 1.1 产品全景图

Google在Agent/OpenClaw赛道的自研产品线，可以按**"模型层→产品层→协议层"**三层架构来理解：

```
┌─────────────────────────────────────────────────────────┐
│                    协议层（Protocol）                      │
│  Agent2Agent (A2A) 协议 ──── MCP兼容 ──── Gemini SDK     │
├─────────────────────────────────────────────────────────┤
│                    产品层（Product）                       │
│  Project Mariner │ Jules │ Agentspace │ Gemini App Agent │
├─────────────────────────────────────────────────────────┤
│                    模型层（Model）                         │
│  Gemini 2.5 Computer Use │ Gemini 3.1 Pro │ Gemini Flash │
├─────────────────────────────────────────────────────────┤
│                    基础设施层（Infra）                      │
│  Google Workspace CLI │ TPU Ironwood │ Vertex AI │ GCP   │
└─────────────────────────────────────────────────────────┘
```

### 1.2 模型层：Gemini 2.5 Computer Use

#### 1.2.1 基本信息

| 维度 | 详情 |
|------|------|
| **发布时间** | 2025年10月8日（Public Preview） |
| **模型ID** | `gemini-2.5-computer-use-preview-10-2025` |
| **核心定位** | Google首个专为**界面控制**设计的AI模型 |
| **技术基础** | 基于Gemini 2.5 Pro的视觉理解和推理能力构建 |
| **可用平台** | Google AI Studio、Vertex AI |
| **开源情况** | GitHub参考实现已开源：`github.com/google-gemini/computer-use-preview` |

#### 1.2.2 技术架构——四步循环交互机制

```
发送请求 → 接收模型响应 → 执行操作 → 捕获新状态 → 循环
   │              │              │              │
 截图+目标    function_call   鼠标/键盘操控    新截图
```

**工作原理**：
1. **发送请求**：在API请求中提供Computer Use工具配置 + 用户目标 + 当前GUI截图
2. **接收响应**：模型分析截图，生成`function_call`（具体UI操作指令）
3. **执行操作**：客户端代码解析并执行操作（点击/输入/滚动等）
4. **捕获状态**：操作后截取新截图，作为`function_response`发回模型，循环往复

#### 1.2.3 支持的13种操作

| 类别 | 操作 | 说明 |
|------|------|------|
| **基础操作** | `open_web_browser` | 打开网页浏览器 |
| | `click_at` | 在指定坐标点击（基于1000×1000归一化网格） |
| | `type_text_at` | 在指定位置输入文本 |
| | `navigate` | 导航到指定URL |
| **滚动操作** | `scroll_document` | 滚动整个页面 |
| | `scroll_at` | 在指定区域滚动 |
| **鼠标操作** | `hover_at` | 鼠标悬停 |
| | `drag_and_drop` | 拖放操作 |
| **浏览器控制** | `go_back` / `go_forward` | 前进/后退 |
| | `search` | 导航到默认搜索引擎 |
| **特殊功能** | `key_combination` | 键盘快捷键组合 |
| | `wait_5_seconds` | 等待动态内容加载 |

#### 1.2.4 关键限制——与GPT-5.4和Claude Computer Use的差距

| 维度 | Gemini 2.5 Computer Use | GPT-5.4 Computer Use | Claude Computer Use |
|------|------------------------|---------------------|-------------------|
| **操控范围** | ⚠️ **仅优化浏览器**，明确声明"尚未针对桌面操作系统级控制优化" | ✅ **原生桌面操控**（操作系统级），OSWorld 75.0%超越人类 | ✅ 桌面+浏览器 |
| **发布阶段** | Public Preview（预览版） | 正式发布，已上线ChatGPT和Codex | 正式发布 |
| **OSWorld成绩** | 未公布/无官方数据 | **75.0%**（首次超越人类72.4%） | 约38-50%（历史版本） |
| **操作类型** | 13种预定义操作 | 截图+键鼠+Playwright代码，三条路径混合 | 截图+键鼠 |
| **移动端支持** | ✅ 支持（可添加自定义函数如`open_app`、`long_press_at`） | ⚠️ 主要面向桌面 | ⚠️ 主要面向桌面 |
| **市场声量** | 🔇 低——作为API工具推出，缺乏消费级产品包装 | 🔊 极高——与GPT-5.4同步发布，全网刷屏 | 🔊 高——定义了Computer Use赛道 |

**核心洞察**：Gemini 2.5 Computer Use在**技术上是合格的**——支持网页和移动端控制、延迟更低（Poke.com反馈"快50%"）、性能在部分测试中超越竞品。但其**产品定位是API工具**，而非面向用户的完整产品，因此声量远不如GPT-5.4的"一夜翻盘"和Claude的"定义赛道"。

#### 1.2.5 第三方评价

> **Poke.com**（AI助手服务）："Gemini 2.5 Computer Use在速度上远超竞争对手，通常快50%，性能优于我们考虑的下一个最佳解决方案。"

> **Autotab**（AI Agent公司）："在复杂情况下可靠解析上下文方面，Gemini 2.5 Computer Use超越其他模型，在我们最困难的评估中性能提升高达18%。"

> **Google支付平台团队**（内部）：使用Computer Use修复脆弱的端到端UI测试，成功修复超过60%的测试执行失败。

---

### 1.3 产品层：Agent产品矩阵

#### 1.3.1 Project Mariner（原Project Jarvis）

| 维度 | 详情 |
|------|------|
| **代号演变** | 2024年Q4内部代号"Project Jarvis"（致敬钢铁侠J.A.R.V.I.S）→ 2024年12月正式命名"Project Mariner" |
| **首次亮相** | 2024年12月12日，随Gemini 2.0发布同步公布 |
| **Google IO 2025更新** | 2025年5月，宣布"将于今年正式上线"，新增能力：可同时监督10个任务、支持从示范中学习（One-shot Learning） |
| **技术基底** | Gemini 2.0 → 后续升级至更高版本 |
| **产品形态** | Chrome浏览器扩展 + Gemini API（Computer Use工具） |
| **核心能力** | 理解浏览器屏幕上的所有信息（像素、文本、代码、图像、表单），自主导航和操作网页 |
| **WebVoyager基准** | 2024年底测试：**83.5%** |
| **技术成熟度** | 从2024年底的约50% → 2025年5月升至约**85%** |
| **当前状态** | ⚠️ **仍为"受信任的测试者"阶段**，未广泛面向消费者开放 |
| **合作伙伴** | UiPath等企业RPA厂商已开始测试 |

**典型演示场景**：
- 根据购物清单自动在杂货店网站创建购物车（但不会自动购买，需用户最终确认）
- 浏览电子表格、整理数据并填充到网页其他区域
- 跨多个网站收集研究信息

**声量分析——为什么没冒出来？**

| 原因 | 具体表现 |
|------|---------|
| **1. 仅限浏览器** | 只能在Chrome活动标签页内操作（键入、滚动、点击），无法操控桌面应用，范围远窄于GPT-5.4 |
| **2. 始终在"测试"** | 从2024年12月公布到2026年3月已15个月，仍未大规模开放，"将于今年上线"的承诺迟迟未兑现 |
| **3. 缺乏消费级包装** | 没有像GPT-5.4那样直接集成到ChatGPT让所有用户体验，也没有像Claude Code那样形成独立产品 |
| **4. 被Gemini大盘的声量覆盖** | Mariner作为Gemini生态的一个子功能，缺乏独立品牌认知 |

---

#### 1.3.2 Jules——AI编程Agent

| 维度 | 详情 |
|------|------|
| **发布时间** | 2024年12月12日（随Gemini 2.0发布），2025年5月公开预览，2025年约8月正式结束测试 |
| **技术基底** | Gemini 2.0 → 后升级至Gemini 2.5 Pro |
| **核心定位** | 异步AI编程助手——在开发者休息/做其他事时，自主修复Bug并准备代码更改 |
| **与GitHub集成** | 深度集成GitHub工作流：克隆代码库到Google Cloud VM → 分析问题 → 跨多文件修复 → 生成Pull Request |
| **支持语言** | Python、JavaScript（初期），后续扩展 |
| **核心创新** | **异步代理架构**——与市面上"同步式"AI编程工具（如Copilot、Cursor）形成差异化 |
| **新增功能**（结束测试后） | 重复使用先前设置加速任务、与GitHub Issues集成、支持多模态输入 |
| **竞品对标** | Anthropic的Claude Code / OpenAI的Codex Agent |

**声量分析**：Jules的异步模式是一个有趣的差异化定位（"你睡觉它干活"），但在OpenClaw引爆的"实时对话式编程"热潮面前，异步模式的吸引力相对有限。开发者更倾向于"即时反馈"的编程体验。

---

#### 1.3.3 Google Agentspace——企业级Agent平台

| 维度 | 详情 |
|------|------|
| **发布时间** | 2024年12月（Google Cloud Next 2025前瞻），2025年4月正式发布 |
| **核心定位** | 企业级AI Agent平台——让企业内部每个员工都能使用AI Agent |
| **技术基底** | Gemini多模态智能 + Google Cloud基础设施 |
| **核心能力** | ① 跨系统搜索（Workspace、Salesforce、ServiceNow等）；② 构建企业知识图谱；③ Agent Gallery（发现和使用预制Agent）；④ Agent Designer（无代码创建自定义Agent） |
| **包含组件** | 面向企业的NotebookLM、Google预制Agent、合作伙伴Agent、自定义Agent工具 |
| **企业客户** | Banco BV、KPMG、Wells Fargo等 |
| **市场定位** | 对标Microsoft Copilot Studio、Salesforce Agentforce |

**声量分析**：Agentspace面向B端企业市场，本身不面向消费者，因此公众声量有限。但在企业AI Agent市场，Google凭借Workspace的庞大用户基础（30亿+用户），具备强大的分发优势。

---

#### 1.3.4 Agent2Agent (A2A) 协议——Agent间通信标准

| 维度 | 详情 |
|------|------|
| **发布时间** | 2025年4月（Google Cloud Next 2025大会） |
| **核心定位** | 开放协议，允许AI Agent**跨生态系统**安全协作，不受框架或供应商限制 |
| **技术基础** | JSON-RPC 2.0 + HTTP(S) + SSE（Server-Sent Events） |
| **与MCP关系** | **互补而非替代**——MCP管理模型上下文（Model↔Tool），A2A管理Agent间通信（Agent↔Agent） |
| **五大设计原则** | ① Agentic-first（无需共享内存/工具）；② 符合标准（HTTP/JSON-RPC/SSE）；③ 默认安全；④ 支持短期和长期任务；⑤ 模态无关 |
| **核心组件** | Agent Card（JSON身份描述文件）、Task（工作单元）、Message、Part |
| **支持方** | Google + 微软联合力推，50+科技公司参与 |
| **Gemini SDK** | 已兼容MCP协议（Demis Hassabis于2025年4月在X平台确认） |

**战略意义**：A2A是Google在Agent生态中**最具战略远见**的一步棋——不争个别产品的声量，而是争**协议标准**。如果A2A成为行业标准，Google就掌握了Agent互操作的"规则制定权"。

---

### 1.4 自研Agent产品线综合评估

#### 1.4.1 优势

| # | 优势 | 具体表现 |
|---|------|---------|
| 1 | **全栈布局** | 从模型（Gemini CU）到产品（Mariner/Jules/Agentspace）到协议（A2A）到基础设施（TPU/GCP），端到端覆盖 |
| 2 | **分发渠道无敌** | Chrome（40亿+安装量）、Android（30亿+设备）、Google Workspace（30亿+用户）——任何Agent产品一旦成熟，分发毫无压力 |
| 3 | **算力自主** | TPU Ironwood（第7代）提供超强自研算力，不受NVIDIA供应链约束 |
| 4 | **人才壁垒** | DeepMind汇聚全球顶尖AI人才 |
| 5 | **协议先手** | A2A+MCP兼容，试图同时占据Agent通信标准的两个维度 |

#### 1.4.2 劣势——为什么声量一般？

| # | 劣势 | 深层原因 |
|---|------|---------|
| 1 | **产品化速度慢** | 技术demo到正式产品的转化周期过长（Mariner从2024.12公布到现在仍在测试） |
| 2 | **缺乏"爆款时刻"** | 没有像Claude Code定义OpenClaw赛道、GPT-5.4一夜翻盘这样的戏剧性事件 |
| 3 | **"追随者"标签** | 业界普遍认知："Google在LLM训练上曾落后于OpenAI和Anthropic，从技术开创者变成了追随者" |
| 4 | **功能分散在Gemini大盘下** | Computer Use、Mariner、Jules都是Gemini生态的子功能，缺乏独立品牌认知 |
| 5 | **Computer Use仅限浏览器** | 最关键的短板：Gemini 2.5 CU明确声明"未针对桌面OS级控制优化"，而GPT-5.4已经在OSWorld超越人类 |
| 6 | **企业优先策略** | Google的Agent产品（Agentspace）偏向B端，消费者感知弱 |

#### 1.4.3 小结

> **Google的Agent产品线像一支训练有素但尚未赢得冠军的球队——每个球员（产品）都不差，但缺少一个"超级巨星"来引爆全场。** Anthropic有OpenClaw/Claude Code，OpenAI有GPT-5.4的"操控电脑"病毒式传播，而Google目前还没有找到那个"一击即中"的产品形态。

---

## 第二部分：Google Workspace CLI（gws）——开源基础设施的精准一击

### 2.1 事件概述

| 维度 | 详情 |
|------|------|
| **产品名称** | Google Workspace CLI，简称 **gws** |
| **发布时间** | 2026年3月初（约3月5-6日前后上传GitHub） |
| **媒体报道时间** | 2026年3月7日（Ars Technica首报；IT之家、机器之心等跟进） |
| **GitHub地址** | `https://github.com/googleworkspace/cli` |
| **组织归属** | 挂在 **Google Workspace** 的GitHub官方组织名下 |
| **GitHub Stars** | 短短几天收获 **15,000+ Stars** |
| **开发语言** | **Rust** |
| **开源协议** | Apache 2.0（推测，Google标准开源协议） |
| **官方推广** | Google Cloud AI 总监 **Addy Osmani** 发推宣传，帖子浏览量突破 **500万** |
| **重要声明** | ⚠️ **非正式产品**（Not an officially supported Google product），用户自行承担风险 |

### 2.2 核心功能——Google Workspace全家桶的统一命令行入口

#### 2.2.1 覆盖产品

gws完整覆盖了Google Workspace的**所有核心产品**API：

| 产品 | CLI命令 | 典型操作 |
|------|---------|---------|
| **Gmail** | `gws gmail` | 发送邮件、搜索邮件、管理标签、读取邮件内容 |
| **Google Drive** | `gws drive` | 上传/下载文件、搜索文件、管理权限、创建文件夹 |
| **Google Calendar** | `gws calendar` | 创建/修改日历事件、查询日程、管理提醒 |
| **Google Sheets** | `gws sheets` | 读写表格数据、创建电子表格 |
| **Google Docs** | `gws docs` | 创建/编辑文档 |
| **Google Chat** | `gws chat` | 发送聊天消息 |
| **其他** | 动态发现 | 通过Discovery Service自动支持新API |

#### 2.2.2 核心命令示例

```bash
# 列出Drive文件
gws drive files list

# 发送Gmail邮件
gws gmail messages send --to "user@example.com" --subject "Hello" --body "World"

# 查看日历事件
gws calendar events list

# 读取Sheets数据
gws sheets spreadsheets.values get --spreadsheet-id "xxx" --range "A1:D10"

# 身份认证
gws auth login --scopes drive,gmail,calendar

# 多账号切换
gws auth login --account work@corp.com
gws auth list
gws auth default work@corp.com

# 预览请求（不实际执行）
gws drive files list --dry-run

# CI/无头模式
gws auth export --unmasked > credentials.json
export GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE=credentials.json
```

### 2.3 技术架构——动态发现的创新设计

gws的核心技术创新在于**两阶段解析（Two-Phase Parsing）策略**，基于Google Discovery Service实现**动态命令构建**：

```
用户/Agent输入命令 (e.g., gws drive files list)
        │
        ▼
   ① 读取 argv[1]，识别目标服务 (e.g., drive)
        │
        ▼
   ② 获取该服务的 Discovery Document（API发现文档）
      └─ 缓存24小时，自动感知服务端API变化
        │
        ▼
   ③ 根据文档中的 resources 和 methods，
      动态构建 clap::Command 命令树
        │
        ▼
   ④ 再次解析剩余的命令行参数
        │
        ▼
   ⑤ 完成身份认证，构建HTTP请求并执行
        │
        ▼
   ⑥ 返回 结构化JSON 结果
```

**为什么这个架构很关键？**

| 传统CLI | gws |
|---------|-----|
| API定义硬编码在代码中 | 运行时从Discovery Service动态拉取 |
| 新API需要更新CLI版本 | **零更新自动适配新API** |
| 每个服务一个SDK/工具 | **一个二进制文件覆盖所有Workspace服务** |
| 需要手动处理OAuth/分页 | 自动处理认证、分页、错误重试 |

### 2.4 Agent集成能力——为什么说是"AI Agent的数字手臂"

#### 2.4.1 内置Agent Skills

gws内置了**超过40项（部分媒体称100+项）Agent Skills**，这些技能可以被AI智能体直接调用：

| 设计维度 | 对人类开发者 | 对AI Agent |
|---------|-----------|----------|
| **操作方式** | 不再需要手写curl请求，每个资源都有`--help` | LLM可直接生成CLI命令并解析JSON返回 |
| **输出格式** | 可读的JSON | **结构化JSON**，Agent可直接解析 |
| **预览能力** | `--dry-run`预览请求 | Agent可先预览再执行，降低误操作 |
| **分页处理** | 自动分页 | 无需Agent处理分页逻辑 |
| **认证** | 自动OAuth | Agent可通过环境变量或凭据文件认证 |

#### 2.4.2 与OpenClaw的一键接入

gws被设计为可以**无缝接入OpenClaw等AI Agent系统**的标准化接口：

```
OpenClaw / Claude Code / GeminiCLI
        │
        ▼
   AI Agent 自主生成 gws 命令
        │
        ▼
   gws 执行命令 → 操作Gmail/Drive/Calendar...
        │
        ▼
   返回结构化JSON → Agent解析并决定下一步
```

**典型工作流示例**：

1. 用户对OpenClaw说："帮我整理本周所有关于AI Agent的邮件，汇总到一个Google Sheets中"
2. OpenClaw → 调用 `gws gmail messages list --query "AI Agent after:2026/03/04"` → 获取邮件列表
3. OpenClaw → 解析JSON，提取关键信息
4. OpenClaw → 调用 `gws sheets spreadsheets.values update` → 写入Sheets
5. OpenClaw → 告诉用户："已完成，共整理了23封相关邮件"

#### 2.4.3 可接入的Agent框架

| Agent框架 | 接入方式 |
|----------|---------|
| **OpenClaw** | 直接在配置中添加gws为可用工具 |
| **GeminiCLI** | 原生支持 |
| **Claude Code** | 通过MCP或直接命令行调用 |
| **LangChain / CrewAI** | 封装为Tool使用 |
| **其他自动化框架** | 作为subprocess调用 |

### 2.5 市场反响

| 指标 | 数据 |
|------|------|
| **GitHub Stars** | 15,000+（上线几天内） |
| **Addy Osmani推文浏览量** | 500万+ |
| **媒体报道** | Ars Technica（首报）、IT之家、机器之心、36氪、搜狐科技、腾讯科技、CSDN等10+家媒体 |
| **社区热度** | 多篇"深度解析"文章上线，开发者社区热烈讨论 |

### 2.6 争议与风险

| # | 争议/风险 | 详情 |
|---|---------|------|
| **1** | **非正式产品** | Google在GitHub主页明确声明：**"该工具并非一款获得官方正式支持的商业产品"** |
| **2** | **数据安全** | 用户若接入，必须**自行承担包含数据受损在内的一切潜在风险** |
| **3** | **快速演进** | 工具仍处于快速迭代阶段，API可能随时变更 |
| **4** | **权限风险** | Agent若获得Gmail/Drive/Calendar的完整权限，误操作可能导致严重后果（误删文件、误发邮件等） |
| **5** | **无SLA保障** | 作为非正式产品，无服务水平协议，企业使用有合规风险 |

**腾讯网报道标题即点出了这个矛盾**：《谷歌上架Google Workspace CLI，**未提供官方支持**》

### 2.7 战略解读——为什么选择此时开源？

| 维度 | 分析 |
|------|------|
| **时间节点** | OpenClaw在2026年2-3月引爆全球AI Agent热潮，Google精准卡位这一时间窗口 |
| **借势营销** | Addy Osmani推文直接使用"一键接入OpenClaw"作为核心卖点，明确蹭热点 |
| **生态卡位** | 不争Agent本身，争的是Agent的**数据接口层**——谁的办公数据能被Agent操作，谁就掌握了Agent化办公的入口 |
| **护城河** | Google Workspace拥有30亿+用户的Gmail/Drive/Calendar数据，这是任何竞争对手都无法复制的数据壁垒 |
| **对Anthropic/OpenAI的应对** | 与其正面竞争Agent产品，不如让**所有Agent都依赖Google的数据接口**——"你们做Agent，我做Agent的手和脚" |

---

## 第三部分：全景对比——Google vs Anthropic vs OpenAI在OpenClaw赛道

### 3.1 三巨头策略对比

| 维度 | Google | Anthropic | OpenAI |
|------|--------|-----------|--------|
| **核心策略** | 全栈但分散：模型+产品+协议+基础设施 | 聚焦：Claude Code→OpenClaw成为赛道定义者 | 后发制人：GPT-5.4原生操控一夜翻盘 |
| **爆款产品** | ❌ 无——多个产品均声量有限 | ✅ OpenClaw/Claude Code——定义了整个赛道 | ✅ GPT-5.4 Computer Use——超越人类基线 |
| **Computer Use能力** | 浏览器级（Gemini 2.5 CU） | 桌面级（Claude Computer Use） | 桌面级+代码操控（GPT-5.4，OSWorld 75%） |
| **开发者工具** | Jules（异步编程）+gws（Workspace CLI） | Claude Code / OpenClaw | Codex Agent |
| **协议/标准** | A2A协议+MCP兼容 | MCP协议（已成事实标准） | 支持MCP |
| **企业级** | Agentspace（B端Agent平台） | 无独立企业Agent平台 | ChatGPT Enterprise |
| **分发优势** | Chrome 40亿+、Android 30亿+、Workspace 30亿+ | 无自有分发渠道 | ChatGPT 2亿+月活 |
| **市场认知** | "什么都做了但没冒出来" | "Agent赛道的开创者和引领者" | "后来居上，技术碾压" |

### 3.2 Computer Use Benchmark对比（截至2026年3月）

| 测试基准 | Google (Gemini 2.5 CU) | OpenAI (GPT-5.4) | Anthropic (Claude) | 说明 |
|---------|----------------------|------------------|-------------------|------|
| **OSWorld** | 未公布 | **75.0%** 🥇 | ~38-50% | 真实桌面操作系统任务 |
| **WebVoyager** | Mariner: 83.5% | 未公布 | 未公布 | 网页导航任务 |
| **WebArena** | "领先性能" | **67.3%** | 未公布 | 网页交互任务 |
| **ScreenSpot** | 有优势 | 未公布 | 未公布 | 移动端UI控制 |
| **人类基线** | - | ✅ 首次超越（75.0% vs 72.4%） | ❌ 未超越 | OSWorld人类基线 |

---

## 第四部分：Google OpenClaw赛道动作时间线

| 时间 | 事件 | 重要性 |
|------|------|--------|
| **2024.10** | 媒体曝光Google内部"Project Jarvis"——代号致敬钢铁侠贾维斯 | 🟡 首次曝光 |
| **2024.12.12** | Google发布Gemini 2.0，同步公布Project Mariner（原Jarvis）和Jules | 🔴 正式入局 |
| **2025.03** | Gemini 2.5系列发布，推理能力大幅提升 | 🟡 模型迭代 |
| **2025.04** | Google Cloud Next 2025：发布A2A协议、Agentspace正式上线 | 🔴 协议+企业级 |
| **2025.04** | Gemini SDK宣布兼容MCP协议（Demis Hassabis确认） | 🟡 生态兼容 |
| **2025.05** | Google IO 2025：Project Mariner更新（10任务并行/One-shot Learning/Computer Use登陆Gemini API） | 🔴 能力升级 |
| **2025.约7-8月** | Jules正式结束测试阶段上线 | 🟡 产品落地 |
| **2025.10.8** | Gemini 2.5 Computer Use模型Public Preview发布 | 🔴 核心模型 |
| **2026.02.20** | Gemini 3.1 Pro发布（ARC-AGI-2: 77%，超越人类平均60%） | 🔴 模型里程碑 |
| **2026.03初** | **Google Workspace CLI（gws）开源上线GitHub** | 🔴 **基础设施** |
| **2026.03.07** | Ars Technica等媒体报道gws，GitHub Stars突破15k | 🔴 市场引爆 |

---

## 第五部分：核心判断与前瞻

### 5.1 Google当前在OpenClaw赛道的定位

> **"技术先进、产品后进、基础设施取巧"**

- **技术先进**：Gemini 2.5 Computer Use在速度和移动端控制上有优势；Gemini 3.1 Pro在ARC-AGI-2上77%超越人类；A2A协议具有前瞻性
- **产品后进**：Project Mariner测试了15个月仍未广泛开放；Jules的异步模式虽创新但不够"性感"；Agentspace面向B端声量低
- **基础设施取巧**：Workspace CLI精准借势OpenClaw热潮，以"Agent的数字手臂"定位巧妙卡位

### 5.2 关键待观察变量

| # | 变量 | 关注点 |
|---|------|-------|
| 1 | **Gemini 3.x系列是否会推出原生桌面级Computer Use** | 这是Google缩小与GPT-5.4差距的关键——从"浏览器级"升级到"桌面级" |
| 2 | **Project Mariner何时正式面向消费者开放** | 已承诺"今年上线"，若再次跳票将严重损害信誉 |
| 3 | **A2A协议的采纳率** | 目前50+公司支持，但能否与MCP形成真正的互补生态尚待验证 |
| 4 | **gws是否会升级为正式产品** | 目前"非正式"状态限制了企业采用，若升级为正式产品并提供SLA，将大幅提升竞争力 |
| 5 | **Google是否会推出类似OpenClaw的消费级Agent产品** | 这是最大的缺失——Google目前没有一个像OpenClaw那样的"杀手级"消费端Agent入口 |

### 5.3 对OpenClaw大赛道格局的影响

Google的Workspace CLI本质上是在**扩大整个OpenClaw生态的蛋糕**：

```
OpenClaw生态：
  └─ Agent层：OpenClaw / Claude Code / GPT-5.4 / GeminiCLI
       │
       ├─ 工具层（Tool/MCP）：gws / Supabase MCP / GitHub MCP / ...
       │
       └─ 协议层：MCP（Anthropic）+ A2A（Google）
```

**Google的聪明之处在于**：即使自己没有赢得Agent层的竞争，只要Agent们都需要操作Gmail/Drive/Calendar，Google就仍然是这个生态的**不可绕过的基础设施提供者**。这与Google在Web时代的策略一脉相承——Chrome浏览器免费开源，但所有人都在Chrome上使用Google搜索。

---

## 附录

### A. 信息来源完整列表

| 来源 | 类型 | 关键内容 |
|------|------|---------|
| OpenAI官方 (2026.3.5) | 一手源 | GPT-5.4发布信息、Benchmark数据 |
| Google官方 (多个时间点) | 一手源 | Gemini 2.5 CU、Mariner、Jules、A2A、gws |
| GitHub: googleworkspace/cli | 一手源 | gws仓库、Stars数据、非正式产品声明 |
| GitHub: google-gemini/computer-use-preview | 一手源 | Gemini CU参考实现 |
| Ars Technica (2026.3.7) | 首报 | Google Workspace CLI功能介绍 |
| IT之家 (2026.3.7) | 中文报道 | gws详细功能、40项Agent Skills、非正式声明 |
| 机器之心/今日头条 | 深度分析 | gws技术架构、战略解读 |
| 搜狐科技 (多篇) | 深度分析 | gws架构解析、战略意义、Agent集成 |
| CSDN (2025.10) | 技术指南 | Gemini 2.5 CU完整技术文档 |
| 腾讯网 (2026.3.7/3.10) | 报道 | gws功能、"未提供官方支持"争议 |
| 36氪 | 报道 | AI Agent竞争格局 |
| 虎嗅 | 深度分析 | AI模型竞争、GPT-5.4对比 |
| 新智元 | 报道 | Agent实测、GPT-5.4 vs Gemini |
| TechCrunch | 报道 | Google利用Claude改进Gemini |
| 澎湃新闻 | 报道 | Project Mariner功能介绍 |
| 每经网 | 报道 | Gemini 2.0全面转向Agent |
| 站长之家 | 报道 | Project Mariner使用场景 |

### B. 关键术语表

| 术语 | 全称 | 释义 |
|------|------|------|
| **OpenClaw** | - | 由Anthropic发起的开源AI Agent框架，2026年初爆火，GitHub Stars超18万 |
| **Computer Use** | - | AI操控计算机GUI界面的能力，是Agent化的关键技术 |
| **gws** | Google Workspace CLI | Google开源的Workspace命令行工具 |
| **A2A** | Agent2Agent | Google推出的Agent间通信开放协议 |
| **MCP** | Model Context Protocol | Anthropic推出的模型上下文协议，已成事实标准 |
| **CUA** | Computer Use Agent | 能操控计算机的AI Agent |
| **Discovery Service** | Google Discovery Service | Google提供的API元数据发现服务 |
| **OSWorld** | - | 真实桌面操作系统任务的标准化基准测试 |
| **WebVoyager** | - | 网页导航任务的基准测试 |

---

> **文档结束** | 版本：v1 | 更新日期：2026-03-11
>
> 如需补充任何细节，请随时提出。
