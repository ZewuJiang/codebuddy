#!/usr/bin/env python3
"""将Markdown报告转换为PDF（修复macOS预览中文乱码问题）"""
import markdown
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
import os
import sys
import subprocess


def find_chinese_font():
    """查找macOS系统中可用的中文字体文件路径"""
    candidates = [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    # 通过fontconfig查找PingFang
    try:
        result = subprocess.run(
            ["fc-list", "PingFang SC", "file"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            path = result.stdout.strip().split(":")[0]
            if os.path.exists(path):
                return path
    except Exception:
        pass

    return None


def convert_md_to_pdf(md_path, pdf_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    html_body = markdown.markdown(
        md_content, extensions=['tables', 'fenced_code', 'toc']
    )

    font_path = find_chinese_font()
    if font_path:
        font_url = "file://" + font_path.replace(" ", "%20")
        font_face_css = f"""
@font-face {{
    font-family: 'ChineseFont';
    src: url('{font_url}');
    font-weight: normal;
    font-style: normal;
}}
@font-face {{
    font-family: 'ChineseFont';
    src: url('{font_url}');
    font-weight: bold;
    font-style: normal;
}}
"""
        font_family = "'ChineseFont', 'Hiragino Sans GB', 'PingFang SC', 'STHeiti', sans-serif"
        print(f"Using font: {font_path}")
    else:
        font_face_css = ""
        font_family = "'PingFang SC', 'Hiragino Sans GB', 'STHeiti', sans-serif"
        print("WARNING: No CJK font file found, PDF may have garbled text")

    font_config = FontConfiguration()

    html_full = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{font_face_css}
@page {{
    size: A4;
    margin: 2cm 1.5cm;
    @bottom-center {{ content: counter(page); font-size: 10px; color: #666; }}
}}
body {{
    font-family: {font_family};
    font-size: 11px;
    line-height: 1.6;
    color: #333;
}}
h1, h2, h3, h4, h5, h6, p, td, th, li, blockquote, span, div {{
    font-family: {font_family};
}}
h1 {{ font-size: 22px; color: #1a1a2e; border-bottom: 3px solid #1a1a2e; padding-bottom: 8px; margin-top: 20px; }}
h2 {{ font-size: 17px; color: #16213e; border-bottom: 2px solid #0f3460; padding-bottom: 5px; margin-top: 18px; }}
h3 {{ font-size: 14px; color: #0f3460; margin-top: 14px; }}
h4 {{ font-size: 12px; color: #533483; margin-top: 10px; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 10px; }}
th {{ background-color: #1a1a2e; color: white; padding: 6px 8px; text-align: left; font-weight: 600; }}
td {{ padding: 5px 8px; border-bottom: 1px solid #ddd; }}
tr:nth-child(even) {{ background-color: #f8f9fa; }}
strong {{ color: #e94560; }}
blockquote {{ border-left: 4px solid #0f3460; padding: 8px 12px; margin: 10px 0; background: #f0f4ff; font-size: 10.5px; }}
code {{ background: #f4f4f4; padding: 1px 4px; border-radius: 3px; font-size: 10px; }}
pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; font-size: 9px; }}
hr {{ border: none; border-top: 1px solid #ccc; margin: 15px 0; }}
ul, ol {{ padding-left: 20px; }}
li {{ margin-bottom: 3px; }}
</style>
</head>
<body>
{html_body}
</body>
</html>'''

    HTML(string=html_full).write_pdf(pdf_path, font_config=font_config)
    size = os.path.getsize(pdf_path)
    print(f"PDF generated: {pdf_path} ({size:,} bytes)")

if __name__ == "__main__":
    md_file = sys.argv[1] if len(sys.argv) > 1 else "AI二级分析-苹果-20260223-2200-v1.md"
    pdf_file = md_file.replace('.md', '.pdf')
    convert_md_to_pdf(md_file, pdf_file)
