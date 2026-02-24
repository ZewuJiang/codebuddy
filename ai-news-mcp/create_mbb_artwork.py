#!/usr/bin/env python3
"""
使用 Canvas Design 原理创建 MBB 风格战略报告艺术品
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from datetime import datetime
import os

# 注册中文字体
try:
    # 尝试使用系统中文字体
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    CN_FONT = 'STSong-Light'
    CN_FONT_BOLD = 'STSong-Light'
except:
    try:
        # macOS 系统字体
        pdfmetrics.registerFont(TTFont('PingFang', '/System/Library/Fonts/PingFang.ttc'))
        CN_FONT = 'PingFang'
        CN_FONT_BOLD = 'PingFang'
    except:
        # 回退到英文
        CN_FONT = 'Helvetica'
        CN_FONT_BOLD = 'Helvetica-Bold'

# MBB 配色方案 - Strategic Clarity
NAVY_BLUE = HexColor('#0f2942')      # 更深的海军蓝 - 权威
ACCENT_CORAL = HexColor('#e63946')   # 活力珊瑚红 - 强调
NEUTRAL_DARK = HexColor('#2b2d42')   # 深中性色 - 文本
NEUTRAL_LIGHT = HexColor('#8d99ae')  # 浅中性色 - 次要
BG_LIGHT = HexColor('#edf2f4')       # 背景浅色
WHITE = HexColor('#ffffff')

# 页面尺寸
PAGE_WIDTH = 210*mm
PAGE_HEIGHT = 297*mm * 2  # 长图 2 页

# 设计系统
MARGIN = 20*mm
CONTENT_WIDTH = PAGE_WIDTH - 2*MARGIN

class MBBArtwork:
    """MBB 战略报告艺术品生成器"""
    
    def __init__(self, filename):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
        self.y = PAGE_HEIGHT - MARGIN
        
    def draw_header_artwork(self):
        """艺术化标题设计"""
        # 背景色块 - 海军蓝
        self.c.setFillColor(NAVY_BLUE)
        self.c.rect(0, self.y - 80, PAGE_WIDTH, 80, fill=1, stroke=0)
        
        # 主标题 - 白色，极简
        self.c.setFillColor(WHITE)
        self.c.setFont(CN_FONT_BOLD, 36)
        self.c.drawString(MARGIN, self.y - 50, "AI 战略资讯")
        
        # 副标题
        self.c.setFont(CN_FONT, 12)
        self.c.setFillColor(BG_LIGHT)
        date_str = datetime.now().strftime("%Y.%m.%d")
        self.c.drawString(MARGIN, self.y - 70, f"游戏行业前沿动态  |  {date_str}")
        
        # 装饰性线条 - 珊瑚红
        self.c.setStrokeColor(ACCENT_CORAL)
        self.c.setLineWidth(3)
        self.c.line(MARGIN, self.y - 85, MARGIN + 60, self.y - 85)
        
        self.y -= 110
        
    def draw_executive_summary_artwork(self):
        """艺术化执行摘要"""
        # 区块标题
        self.c.setFont(CN_FONT_BOLD, 20)
        self.c.setFillColor(NAVY_BLUE)
        self.c.drawString(MARGIN, self.y, "核心洞察")
        
        # 装饰性色块
        self.c.setFillColor(ACCENT_CORAL)
        self.c.rect(MARGIN - 5, self.y - 5, 4, 25, fill=1, stroke=0)
        
        self.y -= 35
        
        # 5 大关键发现 - 卡片式设计
        findings = [
            {
                "title": "组织变革",
                "desc": "Microsoft Xbox 完成 AI 化",
                "detail": "CoreAI 负责人接任，标志性转折",
                "priority": 5,
                "color": ACCENT_CORAL
            },
            {
                "title": "伦理风险",
                "desc": "AI 内容审核缺失",
                "detail": "TikTok 拒删种族歧视广告",
                "priority": 4,
                "color": HexColor('#f77f00')
            },
            {
                "title": "市场调整",
                "desc": "工作室关闭潮持续",
                "detail": "本周 3+ 家工作室倒闭",
                "priority": 4,
                "color": HexColor('#fcbf49')
            },
            {
                "title": "技术应用",
                "desc": "AI 应用立场分化",
                "detail": "Unity 激进 vs Godot 保守",
                "priority": 3,
                "color": NEUTRAL_LIGHT
            },
            {
                "title": "政策法规",
                "desc": "合规成本上升",
                "detail": "Roblox 被诉 + 关税不确定",
                "priority": 3,
                "color": NEUTRAL_LIGHT
            },
        ]
        
        card_height = 70
        card_spacing = 10
        
        for i, finding in enumerate(findings):
            # 卡片背景
            self.c.setFillColor(BG_LIGHT)
            self.c.roundRect(
                MARGIN, 
                self.y - card_height, 
                CONTENT_WIDTH, 
                card_height, 
                8, 
                fill=1, 
                stroke=0
            )
            
            # 左侧彩色边框
            self.c.setFillColor(finding['color'])
            self.c.roundRect(
                MARGIN, 
                self.y - card_height, 
                8, 
                card_height, 
                4, 
                fill=1, 
                stroke=0
            )
            
            # 类别标题
            self.c.setFont(CN_FONT_BOLD, 14)
            self.c.setFillColor(NAVY_BLUE)
            self.c.drawString(MARGIN + 20, self.y - 25, finding['title'])
            
            # 描述
            self.c.setFont(CN_FONT, 11)
            self.c.setFillColor(NEUTRAL_DARK)
            self.c.drawString(MARGIN + 20, self.y - 42, finding['desc'])
            
            # 细节
            self.c.setFont(CN_FONT, 9)
            self.c.setFillColor(NEUTRAL_LIGHT)
            self.c.drawString(MARGIN + 20, self.y - 58, finding['detail'])
            
            # 优先级星标
            stars = "★" * finding['priority']
            self.c.setFont("Helvetica", 12)
            self.c.setFillColor(finding['color'])
            self.c.drawRightString(PAGE_WIDTH - MARGIN - 10, self.y - 35, stars)
            
            self.y -= card_height + card_spacing
        
        self.y -= 20
        
    def draw_timeline_artwork(self):
        """艺术化时间线"""
        # 区块标题
        self.c.setFont(CN_FONT_BOLD, 20)
        self.c.setFillColor(NAVY_BLUE)
        self.c.drawString(MARGIN, self.y, "关键时刻")
        
        # 装饰
        self.c.setFillColor(ACCENT_CORAL)
        self.c.rect(MARGIN - 5, self.y - 5, 4, 25, fill=1, stroke=0)
        
        self.y -= 40
        
        events = [
            ("02.21 04:32", "Phil Spencer 退休", "Microsoft", ACCENT_CORAL),
            ("02.21 04:28", "TikTok AI 广告争议", "Finji", HexColor('#f77f00')),
            ("02.21 03:08", "关税案 Supreme Court", "行业", NEUTRAL_LIGHT),
            ("02.21 01:12", "Roblox 被洛杉矶起诉", "Roblox", NEUTRAL_LIGHT),
            ("02.20 23:22", "Midsummer 工作室关闭", "行业", NEUTRAL_LIGHT),
        ]
        
        timeline_x = MARGIN + 30
        
        for i, (time, event, source, color) in enumerate(events):
            y_pos = self.y - i * 45
            
            # 时间节点圆圈
            self.c.setFillColor(color)
            self.c.circle(timeline_x, y_pos, 6, fill=1, stroke=0)
            
            # 连接线
            if i < len(events) - 1:
                self.c.setStrokeColor(BG_LIGHT)
                self.c.setLineWidth(2)
                self.c.line(timeline_x, y_pos - 6, timeline_x, y_pos - 39)
            
            # 时间标签
            self.c.setFont(CN_FONT_BOLD, 9)
            self.c.setFillColor(color)
            self.c.drawString(timeline_x + 15, y_pos + 10, time)
            
            # 事件描述
            self.c.setFont(CN_FONT, 11)
            self.c.setFillColor(NEUTRAL_DARK)
            self.c.drawString(timeline_x + 15, y_pos - 5, event)
            
            # 来源
            self.c.setFont(CN_FONT, 8)
            self.c.setFillColor(NEUTRAL_LIGHT)
            self.c.drawString(timeline_x + 15, y_pos - 18, f"来源: {source}")
        
        self.y -= len(events) * 45 + 20
        
    def draw_action_grid_artwork(self):
        """艺术化行动网格"""
        # 区块标题
        self.c.setFont(CN_FONT_BOLD, 20)
        self.c.setFillColor(NAVY_BLUE)
        self.c.drawString(MARGIN, self.y, "立即行动")
        
        # 装饰
        self.c.setFillColor(ACCENT_CORAL)
        self.c.rect(MARGIN - 5, self.y - 5, 4, 25, fill=1, stroke=0)
        
        self.y -= 40
        
        actions = [
            ("P0", "召开紧急战略会议", "管理层", "本周", ACCENT_CORAL),
            ("P0", "审查 AI 内容审核流程", "技术+法务", "本周", ACCENT_CORAL),
            ("P1", "制定 AI 伦理指南", "法务+HR", "本月", HexColor('#f77f00')),
            ("P1", "评估竞对 AI 能力", "战略部", "本月", HexColor('#f77f00')),
            ("P2", "试点 AI 工具", "技术部", "本季度", NEUTRAL_LIGHT),
        ]
        
        for priority, action, owner, deadline, color in actions:
            # 优先级标签
            self.c.setFillColor(color)
            self.c.roundRect(MARGIN, self.y - 18, 28, 18, 4, fill=1, stroke=0)
            
            self.c.setFont("Helvetica-Bold", 11)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(MARGIN + 14, self.y - 14, priority)
            
            # 行动描述
            self.c.setFont(CN_FONT, 11)
            self.c.setFillColor(NEUTRAL_DARK)
            self.c.drawString(MARGIN + 38, self.y - 14, action)
            
            # 元信息
            self.c.setFont(CN_FONT, 8)
            self.c.setFillColor(NEUTRAL_LIGHT)
            meta = f"{owner}  |  {deadline}"
            self.c.drawRightString(PAGE_WIDTH - MARGIN, self.y - 14, meta)
            
            self.y -= 30
        
        self.y -= 10
        
    def draw_footer_artwork(self):
        """艺术化页脚"""
        # 底部装饰线
        self.c.setStrokeColor(ACCENT_CORAL)
        self.c.setLineWidth(2)
        self.c.line(MARGIN, MARGIN + 15, PAGE_WIDTH - MARGIN, MARGIN + 15)
        
        # 页脚文字
        self.c.setFont(CN_FONT, 8)
        self.c.setFillColor(NEUTRAL_LIGHT)
        footer = "数据来源: AI News MCP  |  分析框架: MECE + 金字塔原理  |  机密 - 仅供内部"
        self.c.drawCentredString(PAGE_WIDTH/2, MARGIN + 5, footer)
        
    def generate(self):
        """生成艺术品"""
        print("🎨 开始创作 MBB 战略艺术品...")
        
        self.draw_header_artwork()
        print("  ✓ 标题艺术化完成")
        
        self.draw_executive_summary_artwork()
        print("  ✓ 执行摘要卡片完成")
        
        self.draw_timeline_artwork()
        print("  ✓ 时间线艺术化完成")
        
        self.draw_action_grid_artwork()
        print("  ✓ 行动网格完成")
        
        self.draw_footer_artwork()
        print("  ✓ 页脚装饰完成")
        
        self.c.save()
        print(f"✅ 艺术品已生成: {self.filename}")

if __name__ == "__main__":
    artwork = MBBArtwork("AI战略资讯-艺术品版-20260221.pdf")
    artwork.generate()
    
    print("\n" + "="*60)
    print("🎉 MBB 战略艺术品创作完成！")
    print("="*60)
    print("\n✨ 艺术品特点:")
    print("  • 完美中文渲染")
    print("  • 卡片式设计")
    print("  • 色彩丰富有层次")
    print("  • 视觉冲击力强")
    print("  • 博物馆级品质")
