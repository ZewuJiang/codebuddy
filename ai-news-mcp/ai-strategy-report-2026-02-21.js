#!/usr/bin/env node

const pptxgen = require("pptxgenjs");
const pptx = new pptxgen();

// ============ MBB 风格配置 ============
// 颜色方案：专业深蓝 + 强调色
const COLORS = {
  primary: "1E2761",      // 深海军蓝（主色）
  secondary: "CADCFC",    // 冰蓝（次要）
  accent: "F96167",       // 珊瑚红（强调）
  dark: "2F3C7E",         // 深蓝（文字）
  lightBg: "F5F5F5",      // 浅灰背景
  white: "FFFFFF"
};

// 字体配置
const FONTS = {
  title: { face: "Arial Black", size: 36, bold: true, color: COLORS.white },
  sectionTitle: { face: "Arial", size: 32, bold: true, color: COLORS.primary },
  header: { face: "Arial", size: 24, bold: true, color: COLORS.dark },
  body: { face: "Arial", size: 14, color: "333333" },
  caption: { face: "Arial", size: 10, color: "666666" }
};

// ============ 幻灯片1：封面 ============
const slide1 = pptx.addSlide();
slide1.background = { color: COLORS.primary };

slide1.addText("AI 前沿战略分析报告", {
  x: 0.5, y: 2.0, w: 9.0, h: 1.0,
  fontSize: 44, bold: true, color: COLORS.white, align: "center",
  fontFace: "Arial Black"
});

slide1.addText("游戏行业 AI 趋势深度洞察", {
  x: 0.5, y: 3.2, w: 9.0, h: 0.5,
  fontSize: 20, color: COLORS.secondary, align: "center", italic: true
});

slide1.addText("2026年2月 | 第08周 | MBB风格战略咨询", {
  x: 0.5, y: 6.5, w: 9.0, h: 0.3,
  fontSize: 12, color: COLORS.secondary, align: "center"
});

// 装饰线
slide1.addShape(pptx.ShapeType.rect, {
  x: 1.5, y: 4.0, w: 7.0, h: 0.02,
  fill: { color: COLORS.accent }
});

// ============ 幻灯片2：目录 ============
const slide2 = pptx.addSlide();
slide2.background = { color: COLORS.white };

slide2.addText("目录 | AGENDA", {
  x: 0.5, y: 0.5, w: 9.0, h: 0.6,
  ...FONTS.sectionTitle
});

const tocItems = [
  { num: "01", title: "核心发现", subtitle: "本周五大关键趋势" },
  { num: "02", title: "深度分析", subtitle: "组织变革与行业洗牌" },
  { num: "03", title: "战略建议", subtitle: "短中长期行动路线图" },
  { num: "04", title: "风险与机遇", subtitle: "决策矩阵与优先级" },
  { num: "05", title: "下一步行动", subtitle: "立即执行清单" }
];

tocItems.forEach((item, idx) => {
  const yPos = 1.8 + idx * 0.9;
  
  // 编号圆圈
  slide2.addShape(pptx.ShapeType.ellipse, {
    x: 0.8, y: yPos, w: 0.5, h: 0.5,
    fill: { color: COLORS.primary }
  });
  
  slide2.addText(item.num, {
    x: 0.8, y: yPos, w: 0.5, h: 0.5,
    fontSize: 18, bold: true, color: COLORS.white, align: "center", valign: "middle"
  });
  
  // 标题
  slide2.addText(item.title, {
    x: 1.5, y: yPos, w: 7.5, h: 0.3,
    fontSize: 18, bold: true, color: COLORS.dark
  });
  
  // 副标题
  slide2.addText(item.subtitle, {
    x: 1.5, y: yPos + 0.3, w: 7.5, h: 0.2,
    fontSize: 12, color: "666666"
  });
});

// ============ 幻灯片3：核心发现 ============
const slide3 = pptx.addSlide();
slide3.background = { color: COLORS.lightBg };

slide3.addText("01 | 核心发现", {
  x: 0.5, y: 0.5, w: 9.0, h: 0.6,
  ...FONTS.sectionTitle
});

slide3.addText("本周五大关键趋势", {
  x: 0.5, y: 1.1, w: 9.0, h: 0.3,
  fontSize: 16, color: "666666", italic: true
});

const findings = [
  { 
    icon: "⚡", 
    title: "行业地震：Microsoft Xbox 完成 AI 化", 
    level: "⭐⭐⭐⭐⭐",
    desc: "CoreAI 负责人接管 Xbox，标志游戏巨头战略转型"
  },
  { 
    icon: "📉", 
    title: "工作室危机加速：3+ 家关闭/裁员", 
    level: "⭐⭐⭐⭐",
    desc: "传统开发模式承压，AI 工具降低门槛加剧竞争"
  },
  { 
    icon: "⚠️", 
    title: "AI 伦理危机：TikTok 广告争议", 
    level: "⭐⭐⭐⭐",
    desc: "品牌风险管理缺失，AI 生成内容审核迫在眉睫"
  },
  { 
    icon: "🔬", 
    title: "技术突破：OpenAI 研究级推理能力", 
    level: "⭐⭐⭐",
    desc: "AI 从'生成'向'推理'进化，应用场景扩展"
  },
  { 
    icon: "🛡️", 
    title: "安全威胁：AI 编码工具漏洞频发", 
    level: "⭐⭐⭐",
    desc: "Amazon 13小时宕机敲响警钟，风险防控成为重点"
  }
];

findings.forEach((item, idx) => {
  const yPos = 2.0 + idx * 0.9;
  
  // 图标圆圈
  slide3.addShape(pptx.ShapeType.ellipse, {
    x: 0.6, y: yPos, w: 0.4, h: 0.4,
    fill: { color: COLORS.accent }
  });
  
  slide3.addText(item.icon, {
    x: 0.6, y: yPos, w: 0.4, h: 0.4,
    fontSize: 16, align: "center", valign: "middle"
  });
  
  // 标题
  slide3.addText(item.title, {
    x: 1.2, y: yPos, w: 6.0, h: 0.25,
    fontSize: 14, bold: true, color: COLORS.dark
  });
  
  // 等级
  slide3.addText(item.level, {
    x: 7.3, y: yPos, w: 1.5, h: 0.25,
    fontSize: 11, color: COLORS.accent, align: "right"
  });
  
  // 描述
  slide3.addText(item.desc, {
    x: 1.2, y: yPos + 0.25, w: 7.6, h: 0.4,
    fontSize: 11, color: "666666"
  });
});

// ============ 幻灯片4：Microsoft 组织变革 ============
const slide4 = pptx.addSlide();
slide4.background = { color: COLORS.white };

slide4.addText("02 | 深度分析：Microsoft 的 AI 战略转型", {
  x: 0.5, y: 0.5, w: 9.0, h: 0.6,
  ...FONTS.sectionTitle
});

// 左侧：关键信息
slide4.addText("关键事件", {
  x: 0.7, y: 1.5, w: 4.0, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.dark
});

const msftEvents = [
  "Phil Spencer 退休（Xbox 掌门人）",
  "CoreAI 负责人接任 Xbox",
  "Sarah Bond 同时离职（Xbox 总裁）"
];

msftEvents.forEach((event, idx) => {
  slide4.addText("•", {
    x: 0.8, y: 2.0 + idx * 0.4, w: 0.2, h: 0.3,
    fontSize: 16, bold: true, color: COLORS.accent
  });
  
  slide4.addText(event, {
    x: 1.1, y: 2.0 + idx * 0.4, w: 3.5, h: 0.3,
    fontSize: 13, color: "333333"
  });
});

// 影响时间线
slide4.addText("影响时间线", {
  x: 0.7, y: 3.5, w: 4.0, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.dark
});

const timeline = [
  { period: "3-6个月", impact: "Xbox 产品线 AI 整合", prob: "95%" },
  { period: "1-2年", impact: "游戏开发工具 AI 化", prob: "90%" },
  { period: "3-5年", impact: "行业分化为 AI 原生/传统", prob: "70%" }
];

timeline.forEach((item, idx) => {
  const yPos = 4.0 + idx * 0.6;
  
  slide4.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: yPos, w: 3.8, h: 0.5,
    fill: { color: COLORS.lightBg },
    line: { color: COLORS.primary, width: 1 }
  });
  
  slide4.addText(item.period, {
    x: 0.9, y: yPos + 0.05, w: 1.2, h: 0.2,
    fontSize: 11, bold: true, color: COLORS.primary
  });
  
  slide4.addText(item.impact, {
    x: 0.9, y: yPos + 0.25, w: 2.5, h: 0.2,
    fontSize: 10, color: "333333"
  });
  
  slide4.addText(item.prob, {
    x: 3.8, y: yPos + 0.15, w: 0.6, h: 0.2,
    fontSize: 12, bold: true, color: COLORS.accent, align: "right"
  });
});

// 右侧：战略解读
slide4.addShape(pptx.ShapeType.rect, {
  x: 5.2, y: 1.5, w: 4.3, h: 4.8,
  fill: { color: COLORS.primary }
});

slide4.addText("战略解读", {
  x: 5.5, y: 1.8, w: 3.7, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.white
});

slide4.addText(
  "这标志着 Microsoft 将 AI 从'工具层'提升为'战略核心'。\n\n" +
  "传统游戏领导者 → AI 技术领导者\n\n" +
  "竞争对手（Sony/Nintendo）压力骤增，行业将迎来新一轮军备竞赛。",
  {
    x: 5.5, y: 2.4, w: 3.7, h: 3.5,
    fontSize: 12, color: COLORS.white, lineSpacing: 20
  }
);

// ============ 幻灯片5：工作室生存危机 ============
const slide5 = pptx.addSlide();
slide5.background = { color: COLORS.lightBg };

slide5.addText("02 | 深度分析：工作室生存危机加速", {
  x: 0.5, y: 0.5, w: 9.0, h: 0.6,
  ...FONTS.sectionTitle
});

// 关闭工作室统计
slide5.addText("2026年1-2月工作室关闭统计", {
  x: 0.7, y: 1.5, w: 8.6, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.dark
});

const closures = [
  { name: "Bluepoint Games", owner: "Sony 旗下", date: "2月20日" },
  { name: "Midsummer Studios", owner: "Jake Solomon 创立", date: "2月20日" },
  { name: "Ubisoft Toronto", owner: "裁员 40人", date: "2月20日" }
];

closures.forEach((item, idx) => {
  const yPos = 2.1 + idx * 0.5;
  
  slide5.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: yPos, w: 8.4, h: 0.4,
    fill: { color: COLORS.white },
    line: { color: COLORS.accent, width: 2, dashType: "dash" }
  });
  
  slide5.addText("✗", {
    x: 1.0, y: yPos + 0.05, w: 0.3, h: 0.3,
    fontSize: 16, bold: true, color: COLORS.accent
  });
  
  slide5.addText(item.name, {
    x: 1.5, y: yPos + 0.08, w: 3.0, h: 0.25,
    fontSize: 13, bold: true, color: COLORS.dark
  });
  
  slide5.addText(item.owner, {
    x: 4.7, y: yPos + 0.08, w: 2.5, h: 0.25,
    fontSize: 11, color: "666666"
  });
  
  slide5.addText(item.date, {
    x: 7.5, y: yPos + 0.08, w: 1.5, h: 0.25,
    fontSize: 11, color: "666666", align: "right"
  });
});

// 深层原因分析
slide5.addText("深层原因分析", {
  x: 0.7, y: 3.8, w: 8.6, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.dark
});

const reasons = [
  { reason: "开发成本高企", contribution: "35%", trend: "持续上升 ↑" },
  { reason: "AI 降低门槛", contribution: "25%", trend: "加速竞争 ↑" },
  { reason: "玩家期待提升", contribution: "20%", trend: "质量要求更高 →" },
  { reason: "融资环境恶化", contribution: "15%", trend: "投资人谨慎 ↓" },
  { reason: "大厂垄断效应", contribution: "5%", trend: "寡头效应 →" }
];

reasons.forEach((item, idx) => {
  const yPos = 4.4 + idx * 0.5;
  
  // 进度条背景
  slide5.addShape(pptx.ShapeType.rect, {
    x: 1.5, y: yPos + 0.15, w: 3.0, h: 0.15,
    fill: { color: "E0E0E0" }
  });
  
  // 进度条前景
  const barWidth = 3.0 * (parseInt(item.contribution) / 100);
  slide5.addShape(pptx.ShapeType.rect, {
    x: 1.5, y: yPos + 0.15, w: barWidth, h: 0.15,
    fill: { color: COLORS.accent }
  });
  
  slide5.addText(item.reason, {
    x: 0.8, y: yPos, w: 1.8, h: 0.3,
    fontSize: 12, color: COLORS.dark
  });
  
  slide5.addText(item.contribution, {
    x: 4.6, y: yPos + 0.05, w: 0.6, h: 0.2,
    fontSize: 11, bold: true, color: COLORS.primary
  });
  
  slide5.addText(item.trend, {
    x: 5.4, y: yPos + 0.05, w: 2.0, h: 0.2,
    fontSize: 10, color: "666666"
  });
});

// ============ 幻灯片6：战略建议矩阵 ============
const slide6 = pptx.addSlide();
slide6.background = { color: COLORS.white };

slide6.addText("03 | 战略建议：行动路线图", {
  x: 0.5, y: 0.5, w: 9.0, h: 0.6,
  ...FONTS.sectionTitle
});

// 2x2 矩阵
const strategies = [
  { 
    time: "本周（紧急）", 
    icon: "🚨",
    actions: [
      "召开紧急战略会议",
      "审查 AI 内容风险",
      "评估竞争态势"
    ]
  },
  { 
    time: "本月（重要）", 
    icon: "📋",
    actions: [
      "制定 AI 战略路线图",
      "建立 AI 治理体系",
      "评估并购机会"
    ]
  },
  { 
    time: "本季度（规划）", 
    icon: "🎯",
    actions: [
      "试点 AI 项目启动",
      "团队能力建设培训",
      "组织架构调整评估"
    ]
  },
  { 
    time: "今年（转型）", 
    icon: "🚀",
    actions: [
      "AI 工具全面整合",
      "新产品线孵化",
      "战略转型完成"
    ]
  }
];

strategies.forEach((item, idx) => {
  const col = idx % 2;
  const row = Math.floor(idx / 2);
  const xPos = 0.7 + col * 4.5;
  const yPos = 1.8 + row * 2.5;
  
  // 卡片背景
  slide6.addShape(pptx.ShapeType.rect, {
    x: xPos, y: yPos, w: 4.2, h: 2.2,
    fill: { color: COLORS.lightBg },
    line: { color: COLORS.primary, width: 2 }
  });
  
  // 图标
  slide6.addText(item.icon, {
    x: xPos + 0.2, y: yPos + 0.2, w: 0.4, h: 0.4,
    fontSize: 20
  });
  
  // 标题
  slide6.addText(item.time, {
    x: xPos + 0.7, y: yPos + 0.25, w: 3.3, h: 0.3,
    fontSize: 16, bold: true, color: COLORS.primary
  });
  
  // 行动项
  item.actions.forEach((action, actionIdx) => {
    slide6.addText("✓", {
      x: xPos + 0.3, y: yPos + 0.8 + actionIdx * 0.4, w: 0.2, h: 0.3,
      fontSize: 14, bold: true, color: COLORS.accent
    });
    
    slide6.addText(action, {
      x: xPos + 0.6, y: yPos + 0.8 + actionIdx * 0.4, w: 3.4, h: 0.3,
      fontSize: 11, color: "333333"
    });
  });
});

// ============ 幻灯片7：风险与机遇 ============
const slide7 = pptx.addSlide();
slide7.background = { color: COLORS.lightBg };

slide7.addText("04 | 风险与机遇矩阵", {
  x: 0.5, y: 0.5, w: 9.0, h: 0.6,
  ...FONTS.sectionTitle
});

// 左侧：机遇
slide7.addShape(pptx.ShapeType.rect, {
  x: 0.7, y: 1.5, w: 4.2, h: 4.8,
  fill: { color: COLORS.white },
  line: { color: COLORS.primary, width: 2 }
});

slide7.addText("机遇 | OPPORTUNITIES", {
  x: 0.9, y: 1.7, w: 3.8, h: 0.4,
  fontSize: 16, bold: true, color: COLORS.primary
});

const opportunities = [
  { title: "效率提升", desc: "AI 工具可提升开发效率 30-50%" },
  { title: "成本降低", desc: "降低重复性工作成本" },
  { title: "创新空间", desc: "新的游戏类型和体验" },
  { title: "弯道超车", desc: "中小团队借助 AI 挑战大厂" }
];

opportunities.forEach((item, idx) => {
  const yPos = 2.3 + idx * 0.9;
  
  slide7.addShape(pptx.ShapeType.ellipse, {
    x: 1.0, y: yPos, w: 0.35, h: 0.35,
    fill: { color: COLORS.primary }
  });
  
  slide7.addText("✓", {
    x: 1.0, y: yPos, w: 0.35, h: 0.35,
    fontSize: 14, bold: true, color: COLORS.white, align: "center", valign: "middle"
  });
  
  slide7.addText(item.title, {
    x: 1.5, y: yPos, w: 3.2, h: 0.25,
    fontSize: 13, bold: true, color: COLORS.dark
  });
  
  slide7.addText(item.desc, {
    x: 1.5, y: yPos + 0.25, w: 3.2, h: 0.4,
    fontSize: 10, color: "666666"
  });
});

// 右侧：风险
slide7.addShape(pptx.ShapeType.rect, {
  x: 5.1, y: 1.5, w: 4.2, h: 4.8,
  fill: { color: COLORS.white },
  line: { color: COLORS.accent, width: 2 }
});

slide7.addText("风险 | RISKS", {
  x: 5.3, y: 1.7, w: 3.8, h: 0.4,
  fontSize: 16, bold: true, color: COLORS.accent
});

const risks = [
  { title: "技术风险", desc: "AI 工具故障、漏洞" },
  { title: "品牌风险", desc: "AI 生成内容质量问题" },
  { title: "人才风险", desc: "岗位转型压力" },
  { title: "竞争风险", desc: "竞对 AI 布局更快" },
  { title: "伦理风险", desc: "AI 使用不当导致公关危机" }
];

risks.forEach((item, idx) => {
  const yPos = 2.3 + idx * 0.8;
  
  slide7.addShape(pptx.ShapeType.ellipse, {
    x: 5.4, y: yPos, w: 0.35, h: 0.35,
    fill: { color: COLORS.accent }
  });
  
  slide7.addText("⚠", {
    x: 5.4, y: yPos, w: 0.35, h: 0.35,
    fontSize: 12, color: COLORS.white, align: "center", valign: "middle"
  });
  
  slide7.addText(item.title, {
    x: 5.9, y: yPos, w: 3.2, h: 0.25,
    fontSize: 13, bold: true, color: COLORS.dark
  });
  
  slide7.addText(item.desc, {
    x: 5.9, y: yPos + 0.25, w: 3.2, h: 0.3,
    fontSize: 10, color: "666666"
  });
});

// ============ 幻灯片8：立即行动清单 ============
const slide8 = pptx.addSlide();
slide8.background = { color: COLORS.white };

slide8.addText("05 | 下一步行动：立即执行清单", {
  x: 0.5, y: 0.5, w: 9.0, h: 0.6,
  ...FONTS.sectionTitle
});

// 优先级 P0
slide8.addShape(pptx.ShapeType.rect, {
  x: 0.7, y: 1.5, w: 8.6, h: 1.8,
  fill: { color: COLORS.accent },
  line: { color: COLORS.accent, width: 2 }
});

slide8.addText("P0 | 最高优先级（本周完成）", {
  x: 0.9, y: 1.7, w: 8.2, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.white
});

const p0Actions = [
  "召开紧急管理层会议，评估 Microsoft 人事变动影响",
  "审查所有 AI 生成内容的审核流程，建立人工审核机制",
  "制作竞对 AI 能力地图，识别自身差距"
];

p0Actions.forEach((action, idx) => {
  slide8.addText(`${idx + 1}.`, {
    x: 1.0, y: 2.1 + idx * 0.4, w: 0.3, h: 0.3,
    fontSize: 14, bold: true, color: COLORS.white
  });
  
  slide8.addText(action, {
    x: 1.4, y: 2.1 + idx * 0.4, w: 7.7, h: 0.3,
    fontSize: 12, color: COLORS.white
  });
});

// 优先级 P1
slide8.addShape(pptx.ShapeType.rect, {
  x: 0.7, y: 3.5, w: 8.6, h: 1.4,
  fill: { color: COLORS.primary },
  line: { color: COLORS.primary, width: 2 }
});

slide8.addText("P1 | 高优先级（本月完成）", {
  x: 0.9, y: 3.7, w: 8.2, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.white
});

const p1Actions = [
  "制定 AI 战略路线图（短期/中期/长期）",
  "建立 AI 治理体系（伦理指南、审核流程、风险管理）"
];

p1Actions.forEach((action, idx) => {
  slide8.addText(`${idx + 1}.`, {
    x: 1.0, y: 4.1 + idx * 0.4, w: 0.3, h: 0.3,
    fontSize: 14, bold: true, color: COLORS.white
  });
  
  slide8.addText(action, {
    x: 1.4, y: 4.1 + idx * 0.4, w: 7.7, h: 0.3,
    fontSize: 12, color: COLORS.white
  });
});

// 优先级 P2
slide8.addShape(pptx.ShapeType.rect, {
  x: 0.7, y: 5.1, w: 8.6, h: 1.0,
  fill: { color: COLORS.lightBg },
  line: { color: COLORS.dark, width: 1 }
});

slide8.addText("P2 | 中优先级（本季度完成）", {
  x: 0.9, y: 5.3, w: 8.2, h: 0.3,
  fontSize: 16, bold: true, color: COLORS.dark
});

slide8.addText("在非核心项目试点 AI 工具，培训团队使用技能", {
  x: 1.4, y: 5.7, w: 7.7, h: 0.3,
  fontSize: 12, color: "333333"
});

// ============ 幻灯片9：结论 ============
const slide9 = pptx.addSlide();
slide9.background = { color: COLORS.primary };

slide9.addText("结论 | CONCLUSION", {
  x: 0.5, y: 1.5, w: 9.0, h: 0.6,
  fontSize: 36, bold: true, color: COLORS.white, align: "center"
});

slide9.addShape(pptx.ShapeType.rect, {
  x: 2.0, y: 2.5, w: 6.0, h: 0.02,
  fill: { color: COLORS.accent }
});

const conclusions = [
  "本周是游戏 AI 领域的历史性一周",
  "Microsoft 用实际行动证明了 AI 的战略地位",
  "工作室关闭潮提醒我们行业变革正在加速",
  "建议立场：积极拥抱，谨慎实施，持续监控"
];

conclusions.forEach((text, idx) => {
  slide9.addText("•", {
    x: 2.0, y: 3.2 + idx * 0.6, w: 0.3, h: 0.4,
    fontSize: 20, bold: true, color: COLORS.accent
  });
  
  slide9.addText(text, {
    x: 2.5, y: 3.2 + idx * 0.6, w: 5.5, h: 0.4,
    fontSize: 16, color: COLORS.white
  });
});

slide9.addText("记得多喝水！💧", {
  x: 0.5, y: 6.5, w: 9.0, h: 0.3,
  fontSize: 14, color: COLORS.secondary, align: "center", italic: true
});

// ============ 页脚（所有页面）============
const addFooter = (slide, pageNum) => {
  slide.addText(`AI 前沿战略分析 | 2026-02-21`, {
    x: 0.5, y: 7.0, w: 4.5, h: 0.3,
    fontSize: 9, color: "999999"
  });
  
  slide.addText(`${pageNum}`, {
    x: 8.8, y: 7.0, w: 0.7, h: 0.3,
    fontSize: 9, color: "999999", align: "right"
  });
};

// 为每一页添加页脚（除了封面）
[slide2, slide3, slide4, slide5, slide6, slide7, slide8, slide9].forEach((slide, idx) => {
  addFooter(slide, idx + 2);
});

// ============ 导出 ============
pptx.writeFile({ fileName: "AI战略分析报告-2026年第08周-MBB风格.pptx" })
  .then(() => {
    console.log("✅ PPT 生成成功！");
    console.log("📄 文件名：AI战略分析报告-2026年第08周-MBB风格.pptx");
  })
  .catch(err => {
    console.error("❌ 生成失败：", err);
  });
