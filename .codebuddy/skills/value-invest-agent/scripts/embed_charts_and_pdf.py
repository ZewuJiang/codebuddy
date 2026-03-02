#!/usr/bin/env python3
"""
价值投资分析工作流引擎 — 图表嵌入与PDF生成
将图表引用自动嵌入MD报告的对应章节位置，并生成PDF

用法：
    # 仅嵌入图表（推荐：先嵌入再单独生成PDF）
    python3 embed_charts_and_pdf.py embed <报告MD文件> [charts目录]
    
    # 仅生成PDF
    python3 embed_charts_and_pdf.py pdf <报告MD文件> [输出PDF路径]
    
    # 嵌入图表 + 生成PDF（一步到位）
    python3 embed_charts_and_pdf.py all <报告MD文件> [charts目录]

v2升级要点（2026-02-25）：
    - 简化正则匹配：使用章节标题精确匹配，不再依赖段落内容关键词
    - 分离 embed 和 pdf 子命令，避免一步执行卡住
    - null值自动过滤
    - 增加超时保护和详细错误输出
"""

import sys
import os
import re
import glob

# ─── 图表嵌入位置配置 ─────────────────────────────────
# 策略：以"下一个章节标题"为锚点，在它之前插入图表
# 这样不依赖段落内文措辞，只依赖章节编号结构（1.1, 1.2, ... 3.1, 3.2...）
CHART_INSERT_RULES = {
    '01_revenue_trend': {
        'description': '营收与净利润趋势',
        'insert_before_section': r'^#{2,3}\s+1\.5\s',
        'fallback_after_pattern': r'(?:营收|净利率|净利润).*(?:趋势|CAGR|复合增长|同比)',
        'alt_text': '{company}营收与净利润趋势',
    },
    '02_business_mix': {
        'description': '业务营收构成',
        'insert_before_section': r'^#{2,3}\s+3\.2\s',
        'fallback_after_pattern': r'(?:业务|主营|营收构成).*(?:阶段|成长|成熟)',
        'alt_text': '{company}业务构成',
    },
    '03_margin_trend': {
        'description': '盈利能力趋势',
        'insert_before_section': r'^#{2,3}\s+1\.6\s',
        'fallback_after_pattern': r'(?:盈利|FCF|现金流|ROE|ROIC).*(?:质量|优异|特征)',
        'alt_text': '{company}盈利能力趋势',
    },
    '04_valuation_comp': {
        'description': '竞品估值对比',
        'insert_before_section': r'^#{2,3}\s+3\.3\s',
        'fallback_after_pattern': r'(?:竞.*?对比|护城河|战略洞察|So What)',
        'alt_text': '估值指标竞品对比（PE / PS / 净利率）',
    },
    '05_risk_matrix': {
        'description': '风险评估矩阵',
        'insert_before_section': r'^#{2,3}\s+3\.6\s',
        'fallback_after_pattern': r'(?:风险矩阵|风险等级|低概率)',
        'alt_text': '{company}风险评估矩阵',
    },
    '06_dcf_sensitivity': {
        'description': 'DCF敏感性热力图',
        'insert_before_section': r'^#{3,4}\s+方法四',
        'fallback_after_pattern': r'(?:DCF.*?中枢|敏感性矩阵|WACC.*?永续)',
        'alt_text': 'DCF敏感性分析热力图（WACC × 永续增长率）',
    },
    '07_valuation_range': {
        'description': '估值区间Football Field图',
        'insert_before_section': r'^#{2,3}\s+不同情景目标价',
        'fallback_after_pattern': r'(?:综合估值中枢|五法加权|Football Field|调整后综合)',
        'alt_text': '五种估值方法交叉验证 — Football Field图',
    },
    '08_eps_waterfall': {
        'description': 'EPS冲击瀑布图',
        'insert_before_section': r'^#{2,3}\s+3\.6\s',
        'fallback_after_pattern': r'(?:EPS冲击|瀑布|合计冲击|压力测试)',
        'alt_text': '风险因素对EPS的冲击瀑布图',
    },
}


def find_insert_position(md_text: str, rule: dict, chart_file: str) -> int:
    """
    在MD文本中找到图表应该插入的位置（返回插入点的字符偏移量）
    策略优先级：
      1. 如果图表已存在 → 返回 -1
      2. 在"下一章节标题"之前插入（最可靠）
      3. fallback: 用段落内容关键词匹配
    """
    # 检查图表是否已嵌入
    if chart_file in md_text:
        return -1

    # 策略1：在下一个章节标题之前插入
    section_pattern = rule.get('insert_before_section', '')
    if section_pattern:
        match = re.search(section_pattern, md_text, re.MULTILINE)
        if match:
            # 在该标题行之前插入（回退到前一个空行）
            pos = match.start()
            # 向前找到最近的非空行末尾
            prev_newline = md_text.rfind('\n\n', 0, pos)
            if prev_newline > 0:
                return prev_newline
            return pos

    # 策略2：fallback — 用段落内容关键词
    fallback = rule.get('fallback_after_pattern', '')
    if fallback:
        matches = list(re.finditer(fallback, md_text))
        if matches:
            match = matches[-1]
            pos = match.end()
            next_newlines = md_text.find('\n\n', pos)
            if next_newlines > 0:
                return next_newlines
            return pos

    return -2  # 未找到匹配位置


def embed_charts(md_path: str, charts_dir: str = None, company_name: str = '') -> str:
    """
    将charts目录下的图表引用嵌入到MD报告中
    返回修改后的MD文本
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    if charts_dir is None:
        charts_dir = os.path.join(os.path.dirname(md_path), 'charts')

    # 确定charts相对于MD文件的路径
    md_dir = os.path.dirname(os.path.abspath(md_path))
    charts_abs = os.path.abspath(charts_dir)
    charts_rel = os.path.relpath(charts_abs, md_dir)

    # 扫描charts目录
    chart_files = sorted(glob.glob(os.path.join(charts_abs, '*.png')))

    if not chart_files:
        print(f"⚠️ 未在 {charts_dir} 找到图表文件")
        return md_text

    # 自动检测公司名
    if not company_name:
        basename = os.path.basename(md_path)
        match = re.search(r'股票深度分析-(.+?)-\d{8}', basename)
        if match:
            company_name = match.group(1)
        else:
            company_name = '公司'

    inserted = 0
    skipped = 0
    failed = 0

    for chart_path in chart_files:
        chart_filename = os.path.basename(chart_path)
        prefix = chart_filename.replace('.png', '')

        if prefix not in CHART_INSERT_RULES:
            print(f"  ⏭️ 未知图表: {chart_filename}，跳过")
            continue

        rule = CHART_INSERT_RULES[prefix]
        rel_path = f'{charts_rel}/{chart_filename}'

        try:
            pos = find_insert_position(md_text, rule, chart_filename)
        except Exception as e:
            print(f"  ❌ {rule['description']} — 匹配出错: {e}")
            failed += 1
            continue

        if pos == -1:
            print(f"  ✓ {rule['description']} — 已存在，跳过")
            skipped += 1
            continue

        if pos == -2:
            print(f"  ⚠️ {rule['description']} — 未找到插入位置，跳过")
            failed += 1
            continue

        alt_text = rule['alt_text'].format(company=company_name)
        insert_text = f'\n\n![{alt_text}]({rel_path})\n'

        md_text = md_text[:pos] + insert_text + md_text[pos:]
        inserted += 1
        print(f"  ✅ {rule['description']} → 已嵌入（位置: {pos}）")

    print(f"\n📊 嵌入结果：{inserted} 张新增，{skipped} 张已存在，{failed} 张失败")

    # 回写MD文件
    if inserted > 0:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_text)
        print(f"💾 已更新: {md_path}")

    return md_text


def generate_pdf(md_path: str, pdf_path: str = None):
    """调用 md_to_pdf.py 生成PDF"""
    workflows_dir = os.path.join(os.path.dirname(__file__), '..', 'workflows')
    md_to_pdf_script = os.path.join(workflows_dir, 'md_to_pdf.py')

    if not os.path.exists(md_to_pdf_script):
        print(f"❌ 未找到 md_to_pdf.py: {md_to_pdf_script}")
        return None

    # 动态导入
    sys.path.insert(0, workflows_dir)
    from md_to_pdf import md_to_pdf

    if pdf_path is None:
        pdf_path = os.path.splitext(md_path)[0] + '.pdf'

    print(f"🔄 开始生成PDF: {pdf_path}")
    result = md_to_pdf(md_path, pdf_path)
    return result


def main():
    if len(sys.argv) < 3:
        print("用法:")
        print("  python3 embed_charts_and_pdf.py embed <报告MD文件> [charts目录]  — 仅嵌入图表")
        print("  python3 embed_charts_and_pdf.py pdf <报告MD文件> [输出PDF路径]   — 仅生成PDF")
        print("  python3 embed_charts_and_pdf.py all <报告MD文件> [charts目录]     — 嵌入+PDF")
        print()
        print("示例:")
        print("  python3 embed_charts_and_pdf.py embed 股票深度分析-苹果-20260225-1948-v2.md charts/")
        print("  python3 embed_charts_and_pdf.py pdf 股票深度分析-苹果-20260225-1948-v2.md")
        print("  python3 embed_charts_and_pdf.py all 股票深度分析-苹果-20260225-1948-v2.md charts/")
        sys.exit(1)

    command = sys.argv[1].lower()
    md_path = sys.argv[2]

    if command == 'embed':
        charts_dir = sys.argv[3] if len(sys.argv) >= 4 else None
        print(f"📄 报告文件: {md_path}")
        print(f"📁 图表目录: {charts_dir or '自动检测'}")
        print()
        print("═══ 嵌入图表引用 ═══")
        embed_charts(md_path, charts_dir)
        print("\n✅ 图表嵌入完成！")

    elif command == 'pdf':
        pdf_path = sys.argv[3] if len(sys.argv) >= 4 else None
        print(f"📄 报告文件: {md_path}")
        print()
        print("═══ 生成PDF ═══")
        generate_pdf(md_path, pdf_path)
        print("\n✅ PDF生成完成！")

    elif command == 'all':
        charts_dir = sys.argv[3] if len(sys.argv) >= 4 else None
        print(f"📄 报告文件: {md_path}")
        print(f"📁 图表目录: {charts_dir or '自动检测'}")
        print()
        print("═══ Step 1: 嵌入图表引用 ═══")
        embed_charts(md_path, charts_dir)
        print("\n═══ Step 2: 生成PDF ═══")
        generate_pdf(md_path)
        print("\n🎉 工作流完成！")

    else:
        print(f"❌ 未知命令: {command}")
        print("可用命令: embed, pdf, all")
        sys.exit(1)


if __name__ == '__main__':
    main()
