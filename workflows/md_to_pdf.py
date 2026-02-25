#!/usr/bin/env python3
"""
Markdown → PDF 转换器
将投资Agent的MD报告转为宽幅、精美排版的PDF（单页长图形式，无分页）
使用 markdown + weasyprint + pypdf，支持中文、表格、emoji
"""

import sys
import os
import re
import markdown
from weasyprint import HTML

# ─── 页面参数 ──────────────────────────────────────────
PAGE_WIDTH_MM = 280
MARGIN_TOP_MM = 16
MARGIN_BOTTOM_MM = 16
MARGIN_LR_MM = 20
# 超大页面高度，确保所有内容在一页内
MAX_PAGE_HEIGHT_MM = 30000

# ─── CSS 样式 ───────────────────────────────────────────
def build_css(height_mm: int) -> str:
    return f"""
@page {{
    size: {PAGE_WIDTH_MM}mm {height_mm}mm;
    margin: {MARGIN_TOP_MM}mm {MARGIN_LR_MM}mm {MARGIN_BOTTOM_MM}mm {MARGIN_LR_MM}mm;
}}

body {{
    font-family: "STHeiti", "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif;
    font-size: 13px;
    line-height: 1.75;
    color: #1a1a2e;
    background: #ffffff;
    max-width: 100%;
}}

/* ─── 标题 ─── */
h1 {{
    font-size: 28px;
    font-weight: 700;
    color: #0f2942;
    border-bottom: 3px solid #e63946;
    padding-bottom: 10px;
    margin-top: 0;
    margin-bottom: 16px;
}}

h2 {{
    font-size: 20px;
    font-weight: 700;
    color: #0f2942;
    margin-top: 28px;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #edf2f4;
    border-left: 4px solid #e63946;
    padding-left: 10px;
}}

h3 {{
    font-size: 16px;
    font-weight: 600;
    color: #2b2d42;
    margin-top: 20px;
    margin-bottom: 8px;
    padding-left: 8px;
    border-left: 3px solid #457b9d;
}}

/* ─── 元数据行 ─── */
p strong {{
    color: #0f2942;
}}

/* ─── 引用块（今日预测等） ─── */
blockquote {{
    background: linear-gradient(135deg, #f8f9fc 0%, #eef2f7 100%);
    border-left: 4px solid #e63946;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin: 14px 0;
    color: #2b2d42;
    font-size: 13px;
    line-height: 2.0;
}}

blockquote strong {{
    color: #e63946;
    font-size: 14px;
}}

/* ─── 表格 ─── */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 12px;
    border-radius: 6px;
    overflow: hidden;
    table-layout: auto;
    word-wrap: break-word;
}}

thead {{
    background: #0f2942;
    color: #ffffff;
}}

th {{
    padding: 10px 10px;
    text-align: left;
    font-weight: 600;
    font-size: 11.5px;
    letter-spacing: 0.3px;
    white-space: nowrap;
}}

td {{
    padding: 8px 10px;
    border-bottom: 1px solid #edf2f4;
    color: #2b2d42;
    font-size: 12px;
    line-height: 1.6;
}}

tbody tr:nth-child(even) {{
    background: #f8f9fc;
}}

tbody tr:hover {{
    background: #eef2f7;
}}

/* ─── 代码 ─── */
code {{
    background: #edf2f4;
    color: #e63946;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: "SF Mono", "Menlo", "Monaco", monospace;
    font-size: 12px;
}}

/* ─── 列表 ─── */
ul, ol {{
    padding-left: 22px;
    margin: 8px 0;
}}

li {{
    margin-bottom: 4px;
    line-height: 1.7;
}}

/* ─── 水平线 ─── */
hr {{
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #e63946 0%, #457b9d 50%, #edf2f4 100%);
    margin: 24px 0;
}}

/* ─── 段落 ─── */
p {{
    margin: 8px 0;
    line-height: 1.75;
}}

/* ─── 加粗 ─── */
strong {{
    font-weight: 700;
}}

/* ─── 免责声明 ─── */
p em:last-child {{
    font-size: 11px;
    color: #8d99ae;
}}

/* ─── 引用块内列表优化 ─── */
blockquote ul, blockquote ol {{
    margin: 6px 0;
    padding-left: 20px;
}}

blockquote li {{
    margin-bottom: 3px;
    line-height: 1.8;
    font-size: 12.5px;
}}

/* ─── 引用块内表格 ─── */
blockquote table {{
    margin: 8px 0;
    font-size: 12px;
}}

blockquote table th {{
    padding: 8px 10px;
    font-size: 11px;
}}

blockquote table td {{
    padding: 7px 10px;
    font-size: 12px;
}}

blockquote table td:first-child {{
    white-space: nowrap;
}}

/* ─── h4标题（分级子标题） ─── */
h4 {{
    font-size: 14px;
    font-weight: 600;
    color: #457b9d;
    margin-top: 14px;
    margin-bottom: 6px;
}}

/* ─── 涨跌颜色标记（v7.0新增） ─── */
td:nth-child(n) {{
    white-space: normal;
}}

/* ─── 涨跌加粗项高亮 ─── */
td strong {{
    color: #e63946;
    font-weight: 700;
}}

/* ─── h3子标题（A/B/C/D分级子表标题） ─── */
h3 {{
    font-size: 16px;
    font-weight: 700;
    color: #1d3557;
    margin-top: 20px;
    margin-bottom: 10px;
    padding-bottom: 4px;
    border-bottom: 1px solid #edf2f4;
}}

/* ─── One-Liner摘要（v7.0新增） ─── */
h2 + blockquote:first-of-type {{
    background: linear-gradient(135deg, #e63946 0%, #c1121f 100%);
    color: #ffffff;
    border-left: none;
    border-radius: 8px;
    padding: 12px 20px;
    font-size: 16px;
    font-weight: 700;
    text-align: center;
    letter-spacing: 0.5px;
}}

h2 + blockquote:first-of-type strong {{
    color: #ffffff;
    font-size: 17px;
}}

/* ─── P1/P2操作清单背景色区分（v7.0新增） ─── */
h3:nth-of-type(n) + table tbody tr:first-child {{
    font-weight: 600;
}}

/* ─── 分析师判断要点式列表优化 ─── */
blockquote ul li strong {{
    color: #1d3557;
    font-size: 12.5px;
}}

/* ─── 图表图片样式（投行报告风格，紧凑排版） ─── */
img {{
    max-width: 72%;
    height: auto;
    display: block;
    margin: 10px auto;
    border-radius: 4px;
    box-shadow: 0 1px 4px rgba(15, 41, 66, 0.10);
    border: 1px solid #edf2f4;
}}

/* ─── 可证伪条件表格状态标记 ─── */
td:last-child {{
    font-weight: 500;
}}
"""


def preprocess_md(md_text: str) -> str:
    """预处理MD文本，优化排版"""
    
    # 处理"今日预测"引用块：将 | 分隔符换成换行
    def fix_prediction_block(match):
        content = match.group(1)
        if content.count('|') >= 3:
            parts = content.split('|')
            lines = []
            for p in parts:
                p = p.strip()
                if p:
                    lines.append(f"> {p}")
            return '\n'.join(lines)
        return match.group(0)
    
    md_text = re.sub(
        r'> \*\*今日预测\*\*: (.+?)(?=\n\n|\n(?!>))',
        lambda m: fix_prediction_block(m),
        md_text,
        flags=re.DOTALL
    )
    
    return md_text



def md_to_pdf(md_path: str, output_path: str = None):
    """
    将Markdown文件转为精美PDF（单页长图，无分页）
    """
    if not os.path.exists(md_path):
        print(f"❌ 文件不存在: {md_path}")
        return None
    
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
    
    md_text = preprocess_md(md_text)
    
    html_body = markdown.markdown(
        md_text,
        extensions=['tables', 'fenced_code', 'nl2br'],
        output_format='html5'
    )
    
    if output_path is None:
        base = os.path.splitext(md_path)[0]
        output_path = f"{base}.pdf"
    
    print(f"📄 正在转换: {os.path.basename(md_path)}")
    print(f"   → 输出: {os.path.basename(output_path)}")
    
    # 两步渲染：先用超大页面生成，再用 pdfplumber 精确裁剪底部空白
    
    import pdfplumber
    from pypdf import PdfReader, PdfWriter
    
    # 第1步：用超大页面渲染，确保所有内容在一页内
    probe_css = build_css(MAX_PAGE_HEIGHT_MM)
    probe_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><style>{probe_css}</style></head>
<body>{html_body}</body></html>"""
    
    probe_path = output_path + ".probe.pdf"
    # 使用MD文件所在目录的绝对路径作为base_url，确保图片引用能正确解析
    base_dir = os.path.dirname(os.path.abspath(md_path))
    HTML(string=probe_html, base_url=base_dir).write_pdf(probe_path)
    
    # 第2步：用 pdfplumber 精确测量内容底边（top 坐标系，原点在左上角）
    with pdfplumber.open(probe_path) as plumb:
        p = plumb.pages[0]
        page_height_pt = float(p.height)
        page_width_pt = float(p.width)
        
        # 找所有字符中最大的 bottom 值（即最低文字的底边）
        max_content_bottom = 0
        if p.chars:
            max_content_bottom = max(c['bottom'] for c in p.chars)
        # 也检查表格线条（rects），但过滤掉超大背景矩形
        if p.rects:
            content_rects = [r for r in p.rects if r['height'] < page_height_pt * 0.5]
            if content_rects:
                max_rect_bottom = max(r['bottom'] for r in content_rects)
                max_content_bottom = max(max_content_bottom, max_rect_bottom)
        # 也检查线条（lines）
        if p.lines:
            max_line_bottom = max(l['bottom'] for l in p.lines)
            max_content_bottom = max(max_content_bottom, max_line_bottom)
        # 也检查嵌入图片（images）
        if p.images:
            max_img_bottom = max(img['bottom'] for img in p.images)
            max_content_bottom = max(max_content_bottom, max_img_bottom)
    
    if max_content_bottom > 0:
        # pdfplumber 的 bottom 是从顶部算起的距离
        # pypdf 的 mediabox 原点在左下角
        margin_bottom_pt = MARGIN_BOTTOM_MM * 72 / 25.4
        # 内容底部 + 边距 = 需要保留的总高度（从顶部算起）
        keep_height_pt = max_content_bottom + margin_bottom_pt
        # 转为 pypdf 坐标：new_bottom = 页面总高度 - 保留高度
        new_bottom = max(0, page_height_pt - keep_height_pt)
        print(f"   📐 页面原高: {int(page_height_pt * 25.4 / 72)}mm → 裁剪后: {int(keep_height_pt * 25.4 / 72)}mm (去除 {int(new_bottom * 25.4 / 72)}mm 空白)")
    else:
        new_bottom = 0
    
    # 第3步：裁剪并输出
    reader = PdfReader(probe_path)
    page = reader.pages[0]
    page.mediabox.lower_left = (0, new_bottom)
    page.mediabox.upper_right = (page_width_pt, page_height_pt)
    
    writer = PdfWriter()
    writer.add_page(page)
    writer.write(output_path)
    
    os.remove(probe_path)
    
    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ PDF已生成（单页长图）: {output_path} ({size_kb:.0f} KB)")
    
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        default_md = os.path.join(script_dir, f"投资Agent-每日分析-{date_str}.md")
        if os.path.exists(default_md):
            md_to_pdf(default_md)
        else:
            print(f"用法: python3 md_to_pdf.py <markdown文件路径> [输出pdf路径]")
            print(f"默认文件不存在: {default_md}")
    else:
        md_path = sys.argv[1]
        out_path = sys.argv[2] if len(sys.argv) > 2 else None
        md_to_pdf(md_path, out_path)
