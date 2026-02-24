---
name: todo-app-development
overview: 创建一个功能完善的 Todo 待办应用（纯网页版），包含添加/删除/编辑、完成状态、分类标签、优先级、截止日期等功能，采用简约现代风格，支持本地存储，最后部署到腾讯 Lighthouse 服务器。
design:
  architecture:
    framework: html
  styleKeywords:
    - 简约现代
    - 卡片式设计
    - 渐变色点缀
    - 扁平化图标
    - 流畅动画
  fontSystem:
    fontFamily: PingFang SC, Segoe UI, Roboto
    heading:
      size: 28px
      weight: 600
    subheading:
      size: 16px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#4A90E2"
      - "#5BA3F5"
      - "#357ABD"
    background:
      - "#F5F7FA"
      - "#FFFFFF"
      - "#E8EDF3"
    text:
      - "#2C3E50"
      - "#7F8C8D"
      - "#BDC3C7"
    functional:
      - "#E74C3C"
      - "#F39C12"
      - "#27AE60"
      - "#95A5A6"
todos:
  - id: create-todo-app
    content: 创建 todo-app 目录并实现完整的 Todo 应用（index.html）,包含任务增删改查、分类管理、优先级设置、截止日期、localStorage 持久化和简约现代 UI
    status: completed
  - id: create-readme
    content: 编写 README.md 说明文档,描述功能特性、使用方法和部署指南
    status: completed
    dependencies:
      - create-todo-app
  - id: local-preview
    content: 在浏览器中预览 Todo 应用,验证所有功能正常运行
    status: completed
    dependencies:
      - create-todo-app
  - id: deploy-lighthouse
    content: 使用 [integration:lighthouse] 将 Todo 应用部署到腾讯云 Lighthouse 服务器,配置静态网页服务并提供公网访问地址
    status: completed
    dependencies:
      - local-preview
---

## 产品概述

一个功能完善的个人待办事项管理应用,帮助用户高效组织和追踪日常任务。

## 核心功能

- **任务管理**：创建、编辑、删除待办事项,支持标记完成/未完成状态
- **分类系统**：通过标签对任务进行分类管理,快速筛选查看
- **优先级标识**：设置任务优先级（高/中/低）,通过颜色视觉区分
- **截止日期**：为任务设置到期时间,过期任务自动高亮提醒
- **数据持久化**：使用 localStorage 本地存储,刷新页面数据不丢失
- **搜索过滤**：支持按分类、优先级、完成状态筛选任务

## 技术栈选择

- **前端架构**：纯 HTML5 + CSS3 + 原生 JavaScript（ES6+）
- **存储方案**：localStorage API
- **部署平台**：腾讯云 Lighthouse 轻量应用服务器

## 实现方案

### 架构设计

采用单文件 HTML 架构,所有代码（HTML结构、CSS样式、JavaScript逻辑）封装在一个 `index.html` 文件中,参考现有 lottery-app 的成功实践。这种方案具有以下优势：

- 部署简单,无需构建工具
- 本地预览方便,直接用浏览器打开即可
- 适合轻量级应用,维护成本低

### 核心模块设计

#### 1. 数据模型

```
Task 对象结构:
{
  id: string (UUID),
  title: string,
  completed: boolean,
  priority: 'high' | 'medium' | 'low',
  category: string,
  dueDate: string (ISO 8601 格式),
  createdAt: string,
  updatedAt: string
}
```

#### 2. 功能模块

- **TaskManager**：任务CRUD操作、状态管理
- **StorageManager**：localStorage 读写封装
- **UIController**：DOM操作、事件绑定、视图渲染
- **FilterManager**：任务筛选、搜索逻辑

### 实现细节

#### 性能优化

- 使用事件委托处理列表项点击,避免为每个任务绑定独立事件监听器
- localStorage 操作采用批量更新,减少 I/O 频率
- 任务列表渲染使用 DocumentFragment,减少 DOM 重排
- 对于大量任务（>100条）,实现虚拟滚动或分页加载

#### 用户体验

- 添加任务时自动聚焦输入框,支持 Enter 快捷键提交
- 编辑模式下 ESC 取消、Enter 保存
- 删除操作添加确认提示,防止误操作
- 任务完成时添加划线动画和淡出效果
- 截止日期临近（24小时内）显示警告样式

#### 数据可靠性

- localStorage 写入前进行容量检测,超限时提示用户清理
- 数据序列化使用 try-catch 包裹,解析失败时不影响应用启动
- 提供数据导出/导入功能（JSON格式）,方便备份

#### 向后兼容

- 保持 localStorage 数据结构稳定,新增字段使用默认值
- 应用启动时检查数据版本,必要时进行迁移

## 目录结构

项目采用扁平化结构,便于部署和维护:

```
todo-app/
├── index.html          # [NEW] 主应用文件。包含完整的 HTML 结构、CSS 样式和 JavaScript 逻辑。实现任务的增删改查、分类筛选、优先级设置、截止日期管理、localStorage 持久化等功能。采用简约现代设计风格,支持响应式布局,包含流畅的交互动画和视觉反馈。
└── README.md           # [NEW] 项目说明文档。描述应用功能、使用方法、技术栈、本地运行指南和 Lighthouse 部署步骤。
```

## 关键代码结构

### 任务数据模型

```javascript
class Task {
  constructor(title, category = '默认', priority = 'medium', dueDate = null) {
    this.id = this.generateId();
    this.title = title;
    this.completed = false;
    this.priority = priority; // 'high' | 'medium' | 'low'
    this.category = category;
    this.dueDate = dueDate;
    this.createdAt = new Date().toISOString();
    this.updatedAt = new Date().toISOString();
  }
  
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
}
```

### 存储管理器接口

```javascript
class StorageManager {
  static save(tasks) { /* 保存到 localStorage */ }
  static load() { /* 从 localStorage 读取 */ }
  static clear() { /* 清空数据 */ }
  static export() { /* 导出 JSON */ }
  static import(jsonData) { /* 导入 JSON */ }
}
```

### UI 控制器核心方法

```javascript
class UIController {
  static renderTasks(tasks, filter = {}) { /* 渲染任务列表 */ }
  static addTask(task) { /* 添加任务到 DOM */ }
  static updateTask(taskId, updates) { /* 更新任务显示 */ }
  static deleteTask(taskId) { /* 从 DOM 移除任务 */ }
  static showMessage(text, type) { /* 显示提示消息 */ }
}
```

## 设计风格

采用简约现代主义风格,以清爽的蓝白配色为主,营造高效专注的办公氛围。界面布局采用卡片式设计,层次分明,留白充足,视觉舒适。

## 页面布局（单页面应用）

### 1. 顶部导航区

- 应用标题"Todo List"居中显示,使用品牌色渐变
- 右侧显示任务统计信息（总数/已完成数）
- 背景使用微妙的渐变色,增加视觉层次

### 2. 任务输入区

- 大型输入框占据顶部,带有 placeholder 提示"添加新任务..."
- 输入框右侧为"添加"按钮,使用主色调
- 下方为快捷设置栏：分类下拉选择、优先级按钮组、日期选择器
- 卡片式容器,带有轻微阴影和圆角

### 3. 筛选工具栏

- 水平排列的标签页切换：全部/进行中/已完成
- 分类快速过滤按钮组,显示各分类任务数量
- 优先级过滤按钮：全部/高/中/低
- 搜索框（可选）,支持关键词搜索

### 4. 任务列表区

- 任务卡片垂直排列,每个任务占一行
- 任务卡片包含：
- 左侧：圆形复选框（完成/未完成切换）
- 中间：任务标题（可点击编辑）、分类标签、截止日期
- 右侧：优先级彩色标识、编辑按钮、删除按钮
- 优先级颜色编码：高-红色、中-橙色、低-绿色
- 已完成任务显示删除线和降低透明度
- 过期任务边框显示警告红色

### 5. 底部操作区

- 清除已完成任务按钮
- 数据导出/导入按钮
- 应用信息和版本号

## 交互设计

- 添加任务时输入框展开动画,聚焦时边框高亮
- 任务完成时播放勾选动画,卡片淡出效果
- 删除时显示确认对话框,带有滑出动画
- 编辑模式切换时输入框平滑过渡
- 筛选切换时列表淡入淡出
- 悬停效果：卡片轻微上浮,阴影加深

## 响应式设计

- 桌面端（>768px）：双列布局,左侧筛选工具,右侧任务列表
- 平板端（768px-1024px）：单列布局,筛选工具栏折叠
- 移动端（<768px）：紧凑布局,操作按钮图标化,输入区简化

## 集成服务

### Lighthouse

- **用途**：将 Todo 应用部署到腾讯云轻量应用服务器,提供公网访问能力
- **使用阶段**：应用开发完成后,执行部署操作
- **预期结果**：
- 查询用户可用的 Lighthouse 实例
- 将 todo-app 目录上传到服务器
- 配置静态网页服务（Nginx 或 Apache）
- 开放 HTTP 端口（80或自定义端口）
- 返回公网访问 URL,用户可通过域名访问 Todo 应用