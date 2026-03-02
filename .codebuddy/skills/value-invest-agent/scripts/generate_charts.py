#!/usr/bin/env python3
"""
通用图表生成器 — 根据公司分析数据自动生成8张投行级图表
用法：
    python3 generate_charts.py <数据JSON文件路径> [输出目录]
    
数据JSON格式见 chart_data_template.json
"""

import sys
import os
import json

# 将 workflows 目录加入 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'workflows'))
from chart_generator import *


def load_chart_data(json_path: str) -> dict:
    """加载图表数据JSON文件，自动处理null值"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 递归清理null值：数值列表中的null替换为0
    _clean_nulls(data)
    return data


def _clean_nulls(obj, path=""):
    """递归清理JSON中的null值，数值数组中的null替换为0，并打印警告"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            _clean_nulls(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if item is None:
                # 检查列表中是否有数值，如果有则替换为0
                if any(isinstance(x, (int, float)) for x in obj if x is not None):
                    obj[i] = 0
                    print(f"  ⚠️ 自动修复: {path}[{i}] null → 0")
            elif isinstance(item, (dict, list)):
                _clean_nulls(item, f"{path}[{i}]")


def generate_all_charts(data: dict, output_dir: str) -> list:
    """
    根据数据字典生成全部图表，返回生成的文件路径列表
    
    data 字典结构：
    {
        "company_name": "苹果",
        "ticker": "AAPL",
        "current_price": 264.58,
        "data_source": "Apple IR / SEC EDGAR",
        "data_date": "2026.02.20",
        
        "revenue_trend": { ... },
        "business_mix": { ... },
        "margin_trend": { ... },
        "valuation_comp": { ... },
        "risk_matrix": { ... },
        "dcf_sensitivity": { ... },
        "valuation_range": { ... },
        "eps_waterfall": { ... }
    }
    """
    os.makedirs(output_dir, exist_ok=True)
    
    company = data.get('company_name', '公司')
    ticker = data.get('ticker', '')
    price = data.get('current_price', 0)
    source_base = data.get('data_source', 'AI Investment Research')
    data_date = data.get('data_date', '')
    
    # v6多币种支持：从JSON中读取货币配置
    currency_symbol = data.get('currency_symbol', '$')
    amount_unit = data.get('amount_unit', '亿美元')
    amount_unit_short = data.get('amount_unit_short', '亿')
    
    generated = []
    
    # ─── 图表1：营收与净利润趋势 ───
    if 'revenue_trend' in data:
        d = data['revenue_trend']
        path = chart_revenue_profit_trend(
            years=d['years'],
            revenue=d['revenue'],
            net_income=d['net_income'],
            margin=d['margin'],
            title=f'{company}（{ticker}）营收与净利润趋势',
            output_path=f'{output_dir}/01_revenue_trend.png',
            source=d.get('source', source_base),
            revenue_label=d.get('revenue_label', f'营收（{amount_unit}）'),
            income_label=d.get('income_label', f'净利润（{amount_unit}）'),
            margin_label=d.get('margin_label', '净利率'),
            currency_symbol=currency_symbol,
            amount_unit=amount_unit,
        )
        generated.append(('01_revenue_trend.png', '营收与净利润趋势'))
        print(f'✅ 图表1: 营收利润趋势 → {path}')
    
    # ─── 图表2：业务结构环形图 ───
    if 'business_mix' in data:
        d = data['business_mix']
        path = chart_business_mix(
            labels=d['labels'],
            sizes=d['sizes'],
            title=d.get('title', f'{company}业务营收构成（{amount_unit}）'),
            output_path=f'{output_dir}/02_business_mix.png',
            source=d.get('source', source_base),
            highlight_idx=d.get('highlight_idx', 0),
            currency_symbol=currency_symbol,
            amount_unit=amount_unit_short,
        )
        generated.append(('02_business_mix.png', '业务营收构成'))
        print(f'✅ 图表2: 业务结构 → {path}')
    
    # ─── 图表3：盈利能力趋势 ───
    if 'margin_trend' in data:
        d = data['margin_trend']
        path = chart_metric_trend(
            years=d['years'],
            metrics=d['metrics'],
            title=f'{company}（{ticker}）盈利能力趋势',
            output_path=f'{output_dir}/03_margin_trend.png',
            source=d.get('source', source_base),
            y_format=d.get('y_format', 'percent'),
            y_label=d.get('y_label', '百分比'),
        )
        generated.append(('03_margin_trend.png', '盈利能力趋势'))
        print(f'✅ 图表3: 盈利能力趋势 → {path}')
    
    # ─── 图表4：竞品估值对比 ───
    if 'valuation_comp' in data:
        d = data['valuation_comp']
        path = chart_valuation_comparison(
            companies=d['companies'],
            metrics=d['metrics'],
            title=d.get('title', f'{company} vs 竞对 关键估值指标对比'),
            output_path=f'{output_dir}/04_valuation_comp.png',
            source=d.get('source', f'StockAnalysis.com, {data_date}'),
            highlight_company=d.get('highlight_company', company),
        )
        generated.append(('04_valuation_comp.png', '竞品估值对比'))
        print(f'✅ 图表4: 竞品估值对比 → {path}')
    
    # ─── 图表5：风险矩阵 ───
    if 'risk_matrix' in data:
        d = data['risk_matrix']
        path = chart_risk_matrix(
            risks=d['risks'],
            title=f'{company}（{ticker}）风险评估矩阵',
            output_path=f'{output_dir}/05_risk_matrix.png',
            source=d.get('source', 'AI Investment Research'),
        )
        generated.append(('05_risk_matrix.png', '风险评估矩阵'))
        print(f'✅ 图表5: 风险矩阵 → {path}')
    
    # ─── 图表6：DCF敏感性热力图 ───
    if 'dcf_sensitivity' in data:
        d = data['dcf_sensitivity']
        path = chart_sensitivity_heatmap(
            row_labels=d['row_labels'],
            col_labels=d['col_labels'],
            values=d['values'],
            title=f'{company}（{ticker}）DCF敏感性分析（每股价值 {currency_symbol}）',
            output_path=f'{output_dir}/06_dcf_sensitivity.png',
            source=d.get('source', 'AI Investment Research'),
            row_title=d.get('row_title', 'WACC'),
            col_title=d.get('col_title', '永续增长率'),
            current_price=d.get('current_price', price),
            currency_symbol=currency_symbol,
        )
        generated.append(('06_dcf_sensitivity.png', 'DCF敏感性热力图'))
        print(f'✅ 图表6: DCF敏感性热力图 → {path}')
    
    # ─── 图表7：估值区间对比图（Football Field） ───
    if 'valuation_range' in data:
        d = data['valuation_range']
        path = chart_valuation_range(
            methods=d['methods'],
            low=d['low'],
            mid=d['mid'],
            high=d['high'],
            current_price=d.get('current_price', price),
            title=f'{company}（{ticker}）估值交叉验证（Football Field）',
            output_path=f'{output_dir}/07_valuation_range.png',
            source=d.get('source', 'AI Investment Research'),
            currency_symbol=currency_symbol,
        )
        generated.append(('07_valuation_range.png', '估值交叉验证'))
        print(f'✅ 图表7: 估值区间对比 → {path}')
    
    # ─── 图表8：EPS冲击瀑布图 ───
    if 'eps_waterfall' in data:
        d = data['eps_waterfall']
        path = chart_eps_waterfall(
            base_eps=d['base_eps'],
            impacts=[(item[0], item[1]) for item in d['impacts']],
            title=f'{company}（{ticker}）风险情景EPS冲击分析',
            output_path=f'{output_dir}/08_eps_waterfall.png',
            source=d.get('source', 'AI Investment Research'),
            currency_symbol=currency_symbol,
        )
        generated.append(('08_eps_waterfall.png', 'EPS冲击瀑布图'))
        print(f'✅ 图表8: EPS冲击瀑布图 → {path}')
    
    print(f'\n🎉 共生成 {len(generated)} 张图表')
    print(f'📁 输出目录: {output_dir}')
    
    return generated


def main():
    if len(sys.argv) < 2:
        print("用法: python3 generate_charts.py <数据JSON文件> [输出目录]")
        print("示例: python3 generate_charts.py chart_data_apple.json charts/")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    if len(sys.argv) >= 3:
        output_dir = sys.argv[2]
    else:
        output_dir = os.path.join(os.path.dirname(json_path), 'charts')
    
    data = load_chart_data(json_path)
    generate_all_charts(data, output_dir)


if __name__ == '__main__':
    main()
