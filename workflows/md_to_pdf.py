#!/usr/bin/env python3
"""
Markdown → PDF 转换器 (v13.0)
将投资Agent的MD报告转为宽幅、精美排版的PDF（单页长图形式，无分页）
使用 markdown + weasyprint + pdfplumber，支持中文、表格、emoji

🔴 核心约束（v13.0铁律，违反会导致Mac Preview中文乱码）:
1. font-family必须STHeiti优先，严禁PingFang SC排首位
   - PingFang SC子集嵌入后Mac Preview CID映射与系统字体冲突→中文乱码
2. 使用两轮渲染法v2（probe测高度→精确高度重渲染），严禁pypdf裁剪mediabox
   - pypdf裁剪会破坏字体CMap映射→乱码
3. CSS中每个选择器只允许定义一次（如h3），禁止重复定义
4. 生成后必须验证：字体嵌入为STHeiti（非PingFang SC）+中文可提取+Mac Preview无乱码
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

/* ══════════════════════════════════════════════
   GS Investment Research Style · v13.0
   设计原则：
   1. 字体层级清晰：H1(32)→H2(22)→H3(17)→H4(15)→body(14)→table(13)
   2. 颜色体系统一：深蓝#0a1628主调+红#c8102e强调+蓝灰#3d5a80辅助
   3. 间距节奏协调：标题前留白>标题后留白，段间距适中
   4. 同级元素严格一致：同级标题/正文/表格字体大小完全相同
   ══════════════════════════════════════════════ */

/* ─── 全局基础 ─── */
body {{
    font-family: "STHeiti", "Hiragino Sans GB", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 14px;
    line-height: 1.8;
    color: #1a1a2e;
    background: #ffffff;
    max-width: 100%;
    -webkit-font-smoothing: antialiased;
}}

/* ─── 标题层级体系（严格递进，绝不重复定义） ─── */
h1 {{
    font-size: 32px;
    font-weight: 800;
    color: #0a1628;
    border-bottom: 3px solid #c8102e;
    padding-bottom: 12px;
    margin-top: 0;
    margin-bottom: 20px;
    letter-spacing: 0.5px;
}}

h2 {{
    font-size: 22px;
    font-weight: 700;
    color: #0a1628;
    margin-top: 32px;
    margin-bottom: 14px;
    padding-bottom: 8px;
    padding-left: 12px;
    border-bottom: 2px solid #e8ecf0;
    border-left: 4px solid #c8102e;
    letter-spacing: 0.3px;
}}

h3 {{
    font-size: 17px;
    font-weight: 700;
    color: #1d3557;
    margin-top: 24px;
    margin-bottom: 10px;
    padding-left: 10px;
    padding-bottom: 5px;
    border-left: 3px solid #3d5a80;
    border-bottom: 1px solid #edf2f4;
}}

h4 {{
    font-size: 15px;
    font-weight: 600;
    color: #3d5a80;
    margin-top: 18px;
    margin-bottom: 8px;
    padding-left: 8px;
    border-left: 2px solid #a8c5da;
}}

/* ─── 段落 & 正文 ─── */
p {{
    margin: 10px 0;
    line-height: 1.85;
    font-size: 14px;
    color: #1a1a2e;
}}

p strong {{
    color: #0a1628;
    font-size: 14px;
}}

strong {{
    font-weight: 700;
}}

/* ─── 引用块（Analyst Note风格） ─── */
blockquote {{
    background: linear-gradient(135deg, #f7f9fc 0%, #edf1f7 100%);
    border-left: 4px solid #c8102e;
    border-radius: 0 6px 6px 0;
    padding: 16px 20px;
    margin: 16px 0;
    color: #2b2d42;
    font-size: 13.5px;
    line-height: 1.9;
}}

blockquote strong {{
    color: #c8102e;
    font-size: 14px;
}}

blockquote p {{
    font-size: 13.5px;
    margin: 6px 0;
    line-height: 1.9;
}}

/* ─── 引用块内列表 ─── */
blockquote ul, blockquote ol {{
    margin: 8px 0;
    padding-left: 22px;
}}

blockquote li {{
    margin-bottom: 4px;
    line-height: 1.85;
    font-size: 13.5px;
}}

blockquote ul li strong {{
    color: #1d3557;
    font-size: 13.5px;
}}

/* ─── 引用块内表格 ─── */
blockquote table {{
    margin: 10px 0;
    font-size: 12.5px;
}}

blockquote table th {{
    padding: 8px 10px;
    font-size: 12px;
}}

blockquote table td {{
    padding: 7px 10px;
    font-size: 12.5px;
}}

blockquote table td:first-child {{
    white-space: nowrap;
}}

/* ─── One-Liner核心摘要（红底白字横幅） ─── */
h2 + blockquote:first-of-type {{
    background: linear-gradient(135deg, #c8102e 0%, #a00d24 100%);
    color: #ffffff;
    border-left: none;
    border-radius: 8px;
    padding: 14px 24px;
    font-size: 17px;
    font-weight: 700;
    text-align: center;
    letter-spacing: 0.5px;
    line-height: 1.6;
}}

h2 + blockquote:first-of-type strong {{
    color: #ffffff;
    font-size: 18px;
}}

/* ─── 表格（投行数据表风格） ─── */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 13px;
    border-radius: 6px;
    overflow: hidden;
    table-layout: auto;
    word-wrap: break-word;
    border: 1px solid #d1d9e0;
}}

thead {{
    background: linear-gradient(180deg, #0a1628 0%, #142238 100%);
    color: #ffffff;
}}

th {{
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 12.5px;
    letter-spacing: 0.3px;
    white-space: nowrap;
    border-right: 1px solid rgba(255,255,255,0.08);
}}

td {{
    padding: 9px 12px;
    border-bottom: 1px solid #e8ecf0;
    color: #2b2d42;
    font-size: 13px;
    line-height: 1.65;
}}

tbody tr:nth-child(even) {{
    background: #f5f7fa;
}}

tbody tr:nth-child(odd) {{
    background: #ffffff;
}}

/* ─── 表格首列加粗（行标题） ─── */
td:first-child {{
    font-weight: 600;
    color: #1d3557;
}}

/* ─── 涨跌加粗项高亮 ─── */
td strong {{
    color: #c8102e;
    font-weight: 700;
}}

/* ─── P1/P2操作表首行加粗 ─── */
h3:nth-of-type(n) + table tbody tr:first-child {{
    font-weight: 600;
}}

/* ─── 代码 ─── */
code {{
    background: #edf2f4;
    color: #c8102e;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: "SF Mono", "Menlo", "Monaco", "PingFang SC", "Noto Sans CJK SC", monospace;
    font-size: 12.5px;
}}

pre {{
    background: #f0f2f5;
    border-radius: 6px;
    padding: 14px 16px;
    margin: 14px 0;
    overflow-x: auto;
    font-family: "SF Mono", "Menlo", "PingFang SC", "Noto Sans CJK SC", monospace;
    font-size: 12.5px;
    line-height: 1.65;
    color: #2b2d42;
    border: 1px solid #d1d9e0;
}}

pre code {{
    background: none;
    color: #2b2d42;
    padding: 0;
    font-family: inherit;
}}

/* ─── 列表 ─── */
ul, ol {{
    padding-left: 24px;
    margin: 10px 0;
}}

li {{
    margin-bottom: 5px;
    line-height: 1.8;
    font-size: 14px;
}}

/* ─── 水平线（章节分隔） ─── */
hr {{
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #c8102e 0%, #3d5a80 40%, #d1d9e0 100%);
    margin: 30px 0;
}}

/* ─── 免责声明 ─── */
p em:last-child {{
    font-size: 12px;
    color: #8d99ae;
}}

/* ─── 图表图片样式 ─── */
img {{
    max-width: 72%;
    height: auto;
    display: block;
    margin: 12px auto;
    border-radius: 4px;
    box-shadow: 0 1px 4px rgba(10, 22, 40, 0.10);
    border: 1px solid #e8ecf0;
}}

/* ─── 涨跌颜色 ─── */
td:nth-child(n) {{
    white-space: normal;
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
    
    # 两轮渲染法（v2）：先probe测量内容高度，再用精确高度重新渲染
    # 关键：不使用pypdf裁剪，避免破坏字体CMap映射导致乱码
    
    import pdfplumber
    
    base_dir = os.path.dirname(os.path.abspath(md_path))
    
    # ── 第1轮：Probe渲染（超大页面，仅用于测量内容高度） ──
    probe_css = build_css(MAX_PAGE_HEIGHT_MM)
    probe_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><style>{probe_css}</style></head>
<body>{html_body}</body></html>"""
    
    probe_path = output_path + ".probe.pdf"
    HTML(string=probe_html, base_url=base_dir).write_pdf(probe_path)
    
    # 用 pdfplumber 精确测量内容底边
    with pdfplumber.open(probe_path) as plumb:
        p = plumb.pages[0]
        page_height_pt = float(p.height)
        
        max_content_bottom = 0
        if p.chars:
            max_content_bottom = max(c['bottom'] for c in p.chars)
        if p.rects:
            content_rects = [r for r in p.rects if r['height'] < page_height_pt * 0.5]
            if content_rects:
                max_content_bottom = max(max_content_bottom, max(r['bottom'] for r in content_rects))
        if p.lines:
            max_content_bottom = max(max_content_bottom, max(l['bottom'] for l in p.lines))
        if p.images:
            max_content_bottom = max(max_content_bottom, max(img['bottom'] for img in p.images))
    
    # 清理probe文件
    os.remove(probe_path)
    
    # 计算精确页面高度（内容高度 + 底部边距 + 安全余量）
    if max_content_bottom > 0:
        margin_bottom_pt = MARGIN_BOTTOM_MM * 72 / 25.4
        exact_height_pt = max_content_bottom + margin_bottom_pt + 20  # 20pt安全余量
        exact_height_mm = int(exact_height_pt * 25.4 / 72) + 1
        print(f"   📐 内容高度: {int(max_content_bottom * 25.4 / 72)}mm → 页面高度: {exact_height_mm}mm")
    else:
        exact_height_mm = MAX_PAGE_HEIGHT_MM
        print(f"   ⚠️ 无法测量内容高度，使用最大值: {exact_height_mm}mm")
    
    # ── 第2轮：精确渲染（用实际内容高度，WeasyPrint原生输出，无裁剪） ──
    final_css = build_css(exact_height_mm)
    final_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><style>{final_css}</style></head>
<body>{html_body}</body></html>"""
    
    HTML(string=final_html, base_url=base_dir).write_pdf(output_path)
    
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
