#!/usr/bin/env python3
"""
MBB 通用报告引擎
所有四大工作流共享的 PDF 渲染核心
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

# 注册中文字体（STHeiti：中英文混排效果优秀，英文字符间距更自然）
pdfmetrics.registerFont(TTFont('CN', '/System/Library/Fonts/STHeiti Light.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('CN-Bold', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=0))
# 字体常量
FONT = 'CN'
FONT_BOLD = 'CN-Bold'

# MBB 配色
NAVY = HexColor('#0f2942')
CORAL = HexColor('#e63946')
ORANGE = HexColor('#f77f00')
YELLOW = HexColor('#fcbf49')
GREEN = HexColor('#2a9d8f')
BLUE = HexColor('#457b9d')
GRAY_DARK = HexColor('#2b2d42')
GRAY_LIGHT = HexColor('#8d99ae')
BG = HexColor('#edf2f4')
WHITE = HexColor('#ffffff')

# 页面设置
W = 210 * mm
M = 18 * mm
CW = W - 2 * M


class MBBReportEngine:
    """MBB 通用报告引擎 - 四大工作流共享"""

    def __init__(self, filename, title, subtitle, accent_color=CORAL, page_scale=2.5):
        self.filename = filename
        self.title = title
        self.subtitle = subtitle
        self.accent = accent_color
        self.H = 297 * mm * page_scale
        self.c = canvas.Canvas(filename, pagesize=(W, self.H))
        self.y = self.H - M

    def text(self, x, y, text, font, size, color):
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        self.c.drawString(x, y, text)

    def wrap_text(self, text, max_width, font, size):
        """支持中英文混排的自动换行：中文逐字符断行，英文按单词断行"""
        self.c.setFont(font, size)
        lines = []
        current = ''
        i = 0
        while i < len(text):
            ch = text[i]
            test = current + ch
            if self.c.stringWidth(test, font, size) <= max_width:
                current += ch
                i += 1
            else:
                if current:
                    # 尝试在英文单词边界回退（避免英文单词被截断）
                    if ch != ' ' and ord(ch) < 0x4e00:
                        # 当前字符是ASCII且非空格，尝试回退到上一个空格
                        space_idx = current.rfind(' ')
                        if space_idx > 0 and len(current) - space_idx < 30:
                            lines.append(current[:space_idx])
                            current = current[space_idx + 1:]
                            continue
                    lines.append(current)
                current = ''
        if current:
            lines.append(current)
        return lines if lines else ['']

    # ── 标题区 ──────────────────────────────────────
    def draw_header(self):
        self.c.setFillColor(NAVY)
        self.c.rect(0, self.y - 70, W, 70, fill=1, stroke=0)
        self.text(M, self.y - 45, self.title, FONT_BOLD, 32, WHITE)
        self.text(M, self.y - 62, self.subtitle, FONT, 10, BG)
        self.c.setStrokeColor(self.accent)
        self.c.setLineWidth(3)
        self.c.line(M, self.y - 75, M + 50, self.y - 75)
        self.y -= 95

    # ── 区块标题 ────────────────────────────────────
    def draw_section_title(self, title, color=None):
        color = color or self.accent
        self.y -= 15
        self.text(M, self.y, title, FONT_BOLD, 18, NAVY)
        self.c.setFillColor(color)
        self.c.rect(M - 5, self.y - 3, 4, 22, fill=1, stroke=0)
        self.y -= 40

    # ── 洞察卡片 ────────────────────────────────────
    def draw_insight_card(self, data):
        """
        data = {
            'category': str, 'priority': int (1-5),
            'color': Color, 'thesis': str,
            'detail': str, 'impact': str, 'action': str
        }
        """
        # 先用wrap_text计算实际行数，动态确定卡片高度
        detail_lines = self.wrap_text(data['detail'], CW - 40, FONT, 8.5)
        impact_lines = self.wrap_text(data['impact'], CW - 40, FONT, 8.5)
        action_lines = self.wrap_text(data['action'], CW - 40, FONT, 8.5)
        thesis_lines = self.wrap_text(data['thesis'], CW - 30, FONT_BOLD, 11)

        # 动态计算卡片高度：标题区(45) + thesis行 + 3段(label+内容+间距)
        card_h = 50 + len(thesis_lines) * 15
        card_h += 15 + len(detail_lines) * 12 + 8
        card_h += 15 + len(impact_lines) * 12 + 8
        card_h += 15 + len(action_lines) * 12 + 10

        # 卡片背景 + 左侧色条
        self.c.setFillColor(BG)
        self.c.roundRect(M, self.y - card_h, CW, card_h, 6, fill=1, stroke=0)
        self.c.setFillColor(data['color'])
        self.c.roundRect(M, self.y - card_h, 6, card_h, 3, fill=1, stroke=0)

        yc = self.y - 20
        self.text(M + 15, yc, data['category'], FONT_BOLD, 13, NAVY)
        stars = "\u2605" * data['priority']
        self.c.setFont(FONT, 11)
        self.c.setFillColor(data['color'])
        self.c.drawRightString(W - M - 10, yc, stars)
        yc -= 20

        for line in thesis_lines:
            self.text(M + 15, yc, line, FONT_BOLD, 11, GRAY_DARK)
            yc -= 15
        yc -= 5

        # 事实
        self.text(M + 15, yc, "\u4e8b\u5b9e\uff1a", FONT_BOLD, 8.5, GRAY_LIGHT)
        yc -= 2
        for line in detail_lines:
            yc -= 11
            self.text(M + 25, yc, line, FONT, 8.5, GRAY_DARK)
        yc -= 12

        # 影响
        self.text(M + 15, yc, "\u5f71\u54cd\uff1a", FONT_BOLD, 8.5, GRAY_LIGHT)
        yc -= 2
        for line in impact_lines:
            yc -= 11
            self.text(M + 25, yc, line, FONT, 8.5, GRAY_DARK)
        yc -= 12

        # 建议
        self.text(M + 15, yc, "\u5efa\u8bae\uff1a", FONT_BOLD, 8.5, data['color'])
        yc -= 2
        for line in action_lines:
            yc -= 11
            self.text(M + 25, yc, line, FONT, 8.5, data['color'])
        yc -= 5

        self.y -= card_h + 12

    # ── 简洁信息卡片（适合榜单/股价等） ──────────────
    def draw_info_card(self, title_text, items, color=NAVY):
        """
        items = [(label, value, change, change_color), ...]
        """
        card_h = 25 + len(items) * 22 + 10
        self.c.setFillColor(BG)
        self.c.roundRect(M, self.y - card_h, CW, card_h, 6, fill=1, stroke=0)
        self.c.setFillColor(color)
        self.c.roundRect(M, self.y - card_h, 6, card_h, 3, fill=1, stroke=0)

        yc = self.y - 20
        self.text(M + 15, yc, title_text, FONT_BOLD, 12, NAVY)
        yc -= 22

        for label, value, change, ch_color in items:
            self.text(M + 20, yc, label, FONT, 9, GRAY_DARK)
            self.text(M + CW * 0.45, yc, str(value), FONT, 9, NAVY)
            self.c.setFont(FONT, 9)
            self.c.setFillColor(ch_color)
            self.c.drawRightString(W - M - 10, yc, str(change))
            yc -= 22

        self.y -= card_h + 12

    # ── 时间线 ──────────────────────────────────────
    def draw_timeline(self, events):
        """
        events = [(time_str, title, source, detail, color), ...]
        """
        timeline_x = M + 25
        text_max_w = W - M - timeline_x - 25
        y_offset = 0
        for i, (time, event, source, detail, color) in enumerate(events):
            # 计算标题和详情的换行
            title_lines = self.wrap_text(event, text_max_w, FONT_BOLD, 10)
            detail_lines = self.wrap_text(detail, text_max_w, FONT, 8)
            # 每条事件所需高度
            item_h = 18 + len(title_lines) * 14 + len(detail_lines) * 11 + 14

            y_pos = self.y - y_offset
            self.c.setFillColor(color)
            self.c.circle(timeline_x, y_pos, 5, fill=1, stroke=0)

            self.text(timeline_x + 15, y_pos + 8, time, FONT, 8, color)

            ty = y_pos - 5
            for tl in title_lines:
                self.text(timeline_x + 15, ty, tl, FONT_BOLD, 10, GRAY_DARK)
                ty -= 14

            for dl in detail_lines:
                self.text(timeline_x + 15, ty, dl, FONT, 8, GRAY_LIGHT)
                ty -= 11

            self.text(timeline_x + 15, ty, f"\u6765\u6e90: {source}", FONT, 7, GRAY_LIGHT)

            # 画连线到下一个
            if i < len(events) - 1:
                self.c.setStrokeColor(BG)
                self.c.setLineWidth(2)
                self.c.line(timeline_x, y_pos - 5, timeline_x, y_pos - item_h + 5)

            y_offset += item_h

        self.y -= y_offset + 15

    # ── 行动清单 ────────────────────────────────────
    def draw_actions(self, actions):
        """
        actions = [(priority_label, text, owner, deadline, color), ...]
        """
        for priority, action, owner, deadline, color in actions:
            self.c.setFillColor(color)
            self.c.roundRect(M, self.y - 16, 25, 16, 3, fill=1, stroke=0)
            self.c.setFont(FONT_BOLD, 10)
            self.c.setFillColor(WHITE)
            self.c.drawCentredString(M + 12.5, self.y - 12, priority)
            self.text(M + 33, self.y - 11, action, FONT, 9.5, GRAY_DARK)
            meta = f"{owner}  |  {deadline}"
            self.c.setFont(FONT, 7.5)
            self.c.setFillColor(GRAY_LIGHT)
            self.c.drawRightString(W - M, self.y - 11, meta)
            self.y -= 26
        self.y -= 10

    # ── 页脚 ────────────────────────────────────────
    def draw_footer(self, footer_text=None):
        footer_text = footer_text or "\u6570\u636e: AI News MCP  |  \u6846\u67b6: MECE + \u91d1\u5b57\u5854\u539f\u7406  |  \u673a\u5bc6 - \u4ec5\u4f9b\u5185\u90e8"
        self.c.setStrokeColor(self.accent)
        self.c.setLineWidth(2)
        self.c.line(M, M + 12, W - M, M + 12)
        self.c.setFont(FONT, 7)
        self.c.setFillColor(GRAY_LIGHT)
        self.c.drawCentredString(W / 2, M + 4, footer_text)

    # ── 运营维度总览卡片（游戏竞品监控专用） ──────────
    def draw_ops_summary_card(self, summary_data, dimension_stats):
        """
        绘制运营监控周报的维度总览卡片
        summary_data = {
            'total_articles': int,
            'key_highlights': [str, ...],
            'overall_assessment': str
        }
        dimension_stats = [
            {'name': str, 'count': int, 'priority': str, 'color': Color},
            ...
        ]
        """
        # 计算卡片高度
        assessment_lines = self.wrap_text(summary_data['overall_assessment'], CW - 40, FONT, 9)
        highlights_line_count = 0
        for h in summary_data['key_highlights']:
            highlights_line_count += len(self.wrap_text(h, CW - 55, FONT, 8.5))

        card_h = 55 + len(assessment_lines) * 13 + 15
        card_h += highlights_line_count * 12 + len(summary_data['key_highlights']) * 4 + 20
        card_h += len(dimension_stats) * 24 + 25

        # 卡片背景
        self.c.setFillColor(BG)
        self.c.roundRect(M, self.y - card_h, CW, card_h, 6, fill=1, stroke=0)
        self.c.setFillColor(NAVY)
        self.c.roundRect(M, self.y - card_h, 6, card_h, 3, fill=1, stroke=0)

        yc = self.y - 22
        self.text(M + 15, yc, "本周总览", FONT_BOLD, 14, NAVY)
        total_str = f"公众号文章数: {summary_data['total_articles']}"
        self.c.setFont(FONT, 9)
        self.c.setFillColor(GRAY_LIGHT)
        self.c.drawRightString(W - M - 10, yc + 2, total_str)
        yc -= 22

        # 整体评估
        self.text(M + 15, yc, "整体评估", FONT_BOLD, 9, GRAY_LIGHT)
        yc -= 5
        for line in assessment_lines:
            yc -= 13
            self.text(M + 20, yc, line, FONT, 9, GRAY_DARK)
        yc -= 18

        # 本周要点
        self.text(M + 15, yc, "本周要点", FONT_BOLD, 9, GRAY_LIGHT)
        yc -= 5
        for h in summary_data['key_highlights']:
            h_lines = self.wrap_text(h, CW - 55, FONT, 8.5)
            for j, hl in enumerate(h_lines):
                yc -= 12
                prefix = "• " if j == 0 else "  "
                self.text(M + 20, yc, prefix + hl, FONT, 8.5, GRAY_DARK)
            yc -= 4
        yc -= 15

        # 维度统计条
        self.text(M + 15, yc, "监控维度分布", FONT_BOLD, 9, GRAY_LIGHT)
        yc -= 18
        for ds in dimension_stats:
            # 优先级标签
            priority_colors = {'high': CORAL, 'medium': ORANGE, 'low': GRAY_LIGHT}
            priority_labels = {'high': '高', 'medium': '中', 'low': '低'}
            p_color = priority_colors.get(ds['priority'], GRAY_LIGHT)
            p_label = priority_labels.get(ds['priority'], '—')
            self.c.setFillColor(p_color)
            self.c.roundRect(M + 15, yc - 3, 18, 14, 2, fill=1, stroke=0)
            self.text(M + 17, yc, p_label, FONT_BOLD, 8, WHITE)
            self.text(M + 40, yc, ds['name'], FONT, 9.5, GRAY_DARK)
            count_str = f"{ds['count']} 条动态"
            self.c.setFont(FONT, 9)
            self.c.setFillColor(ds['color'])
            self.c.drawRightString(W - M - 10, yc, count_str)
            yc -= 24

        self.y -= card_h + 15

    # ── 运营动态详情卡片（游戏竞品监控专用） ──────────
    def draw_dimension_card(self, dimension_name, priority_level, entries, accent_color, images_base_dir=None):
        """
        绘制单个维度的运营动态详情卡片
        dimension_name: str
        priority_level: 'high'/'medium'/'low'
        entries: [{
            'title': str, 'date': str, 'tier': str,
            'detail': str, 'source_title': str,
            'player_feedback': str|None,
            'images': [{'file': str, 'desc': str}, ...]
        }, ...]
        accent_color: Color
        images_base_dir: str - 图片文件所在的基础目录绝对路径
        """
        if not entries:
            return

        IMG_W = CW - 60        # 图片绘制宽度
        IMG_MAX_H = 150         # 图片最大高度

        def _get_image_size(img_path):
            """获取图片实际显示尺寸，等比缩放"""
            try:
                from reportlab.lib.utils import ImageReader
                ir = ImageReader(img_path)
                iw, ih = ir.getSize()
                ratio = min(IMG_W / iw, IMG_MAX_H / ih)
                return iw * ratio, ih * ratio
            except Exception:
                return 0, 0

        # 计算卡片高度
        card_h = 35
        for entry in entries:
            detail_lines = self.wrap_text(entry.get('detail', ''), CW - 55, FONT, 8.5)
            entry_h = 22 + len(detail_lines) * 12 + 8
            if entry.get('player_feedback'):
                fb_lines = self.wrap_text(entry['player_feedback'], CW - 70, FONT, 8)
                entry_h += len(fb_lines) * 11 + 14
            if entry.get('source_title'):
                entry_h += 14
            # 图片高度
            if images_base_dir and entry.get('images'):
                for img in entry['images']:
                    if isinstance(img, dict) and img.get('file'):
                        img_path = os.path.join(images_base_dir, img['file'])
                        if os.path.exists(img_path):
                            _, ih = _get_image_size(img_path)
                            entry_h += ih + 8 + (12 if img.get('desc') else 0)
            card_h += entry_h + 8

        # 卡片背景 + 左侧色条
        self.c.setFillColor(BG)
        self.c.roundRect(M, self.y - card_h, CW, card_h, 6, fill=1, stroke=0)
        self.c.setFillColor(accent_color)
        self.c.roundRect(M, self.y - card_h, 6, card_h, 3, fill=1, stroke=0)

        yc = self.y - 22
        self.text(M + 15, yc, dimension_name, FONT_BOLD, 13, NAVY)

        # 优先级标签
        priority_colors = {'high': CORAL, 'medium': ORANGE, 'low': GRAY_LIGHT}
        priority_labels = {'high': '高优先级', 'medium': '中优先级', 'low': '低优先级'}
        p_color = priority_colors.get(priority_level, GRAY_LIGHT)
        p_label = priority_labels.get(priority_level, '')
        label_w = self.c.stringWidth(p_label, FONT_BOLD, 8) + 10
        self.c.setFillColor(p_color)
        self.c.roundRect(W - M - label_w - 10, yc - 3, label_w, 16, 3, fill=1, stroke=0)
        self.text(W - M - label_w - 5, yc, p_label, FONT_BOLD, 8, WHITE)
        yc -= 30

        for entry in entries:
            # Tier 标签 + 标题
            tier = entry.get('tier', 'T1')
            tier_colors = {'T0': CORAL, 'T1': ORANGE, 'T2': GRAY_LIGHT}
            t_color = tier_colors.get(tier, GRAY_LIGHT)
            self.c.setFillColor(t_color)
            self.c.roundRect(M + 15, yc - 2, 22, 14, 2, fill=1, stroke=0)
            self.text(M + 18, yc + 1, tier, FONT_BOLD, 8, WHITE)

            title_text = entry.get('title', '')
            date_text = entry.get('date', '')
            self.text(M + 42, yc, title_text, FONT_BOLD, 10, GRAY_DARK)
            self.c.setFont(FONT, 8)
            self.c.setFillColor(GRAY_LIGHT)
            self.c.drawRightString(W - M - 10, yc, date_text)
            yc -= 18

            # 详情
            detail_lines = self.wrap_text(entry.get('detail', ''), CW - 55, FONT, 8.5)
            for dl in detail_lines:
                yc -= 12
                self.text(M + 20, yc, dl, FONT, 8.5, GRAY_DARK)

            # 来源
            if entry.get('source_title'):
                yc -= 14
                self.text(M + 20, yc, f"来源: {entry['source_title']}", FONT, 7.5, GRAY_LIGHT)

            # 玩家反馈
            if entry.get('player_feedback'):
                yc -= 14
                self.text(M + 20, yc, "玩家反馈:", FONT_BOLD, 8, accent_color)
                fb_lines = self.wrap_text(entry['player_feedback'], CW - 70, FONT, 8)
                for fl in fb_lines:
                    yc -= 11
                    self.text(M + 30, yc, fl, FONT, 8, accent_color)

            # 图片嵌入
            if images_base_dir and entry.get('images'):
                for img in entry['images']:
                    if isinstance(img, dict) and img.get('file'):
                        img_path = os.path.join(images_base_dir, img['file'])
                        if os.path.exists(img_path):
                            iw, ih = _get_image_size(img_path)
                            if iw > 0 and ih > 0:
                                yc -= 8
                                # 居中绘制图片
                                img_x = M + 20 + (IMG_W - iw) / 2
                                yc -= ih
                                self.c.drawImage(img_path, img_x, yc, width=iw, height=ih, preserveAspectRatio=True)
                                # 图片描述
                                desc = img.get('desc', '')
                                if desc:
                                    yc -= 12
                                    self.text(M + 20 + (IMG_W - self.c.stringWidth(desc, FONT, 7)) / 2, yc, desc, FONT, 7, GRAY_LIGHT)

            yc -= 16

        self.y -= card_h + 12

    def save(self):
        self.c.save()
        # 裁剪页面：用 pypdf 去除尾部空白
        actual_h = self.H - self.y + M + 30
        if actual_h < self.H:
            try:
                from pypdf import PdfReader, PdfWriter
                offset = self.H - actual_h
                reader = PdfReader(self.filename)
                writer = PdfWriter()
                page = reader.pages[0]
                # MediaBox 坐标系：[左, 下, 右, 上]，裁掉底部空白区域
                mb = page.mediabox
                page.mediabox.lower_left = (float(mb.left), float(mb.bottom) + offset)
                writer.add_page(page)
                with open(self.filename, 'wb') as f:
                    writer.write(f)
                print(f"\u2705 \u62a5\u544a\u5df2\u751f\u6210: {self.filename}\uff08\u5df2\u88c1\u526a\u7a7a\u767d\uff09")
                return
            except Exception as e:
                print(f"\u26a0\ufe0f \u88c1\u526a\u5931\u8d25: {e}\uff0c\u4fdd\u7559\u539f\u59cb\u6587\u4ef6")
        print(f"\u2705 \u62a5\u544a\u5df2\u751f\u6210: {self.filename}")
