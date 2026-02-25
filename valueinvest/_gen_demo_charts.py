#!/usr/bin/env python3
"""用苹果报告真实数据生成示范图表"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'workflows'))
from chart_generator import *

output_dir = os.path.join(os.path.dirname(__file__), 'charts')
os.makedirs(output_dir, exist_ok=True)

# 图表1: 营收与净利润趋势
chart_revenue_profit_trend(
    years=['FY2021', 'FY2022', 'FY2023', 'FY2024', 'FY2025', 'TTM'],
    revenue=[3658, 3943, 3833, 3910, 4162, 4356],
    net_income=[947, 998, 970, 937, 1120, 1178],
    margin=[25.88, 25.31, 25.31, 23.97, 26.92, 27.04],
    title='苹果（AAPL）营收与净利润趋势',
    output_path=f'{output_dir}/01_revenue_trend.png',
    source='Apple IR / SEC EDGAR'
)
print('✅ 图表1: 营收利润趋势')

# 图表2: 业务结构环形图
chart_business_mix(
    labels=['iPhone', '服务', 'Mac', 'iPad', '可穿戴/配件'],
    sizes=[2290, 1040, 375, 290, 330],
    title='苹果FY2025业务营收构成（亿美元）',
    output_path=f'{output_dir}/02_business_mix.png',
    source='Apple Q1 FY2026 Earnings',
    highlight_idx=0
)
print('✅ 图表2: 业务结构')

# 图表3: 盈利能力趋势
chart_metric_trend(
    years=['FY2021', 'FY2022', 'FY2023', 'FY2024', 'FY2025', 'TTM'],
    metrics={
        '毛利率': [41.78, 43.31, 44.13, 46.21, 46.91, 47.33],
        '净利率': [25.88, 25.31, 25.31, 23.97, 26.92, 27.04],
    },
    title='苹果（AAPL）盈利能力趋势',
    output_path=f'{output_dir}/03_margin_trend.png',
    source='Apple IR / SEC EDGAR',
    y_format='percent', y_label='百分比'
)
print('✅ 图表3: 盈利能力趋势')

# 图表4: 竞品估值对比
chart_valuation_comparison(
    companies=['Apple', 'Microsoft', 'Google', 'Samsung'],
    metrics={
        'PE(TTM)': [33.5, 35.0, 24.0, 12.0],
        'PEG': [3.3, 2.2, 1.7, 2.4],
        'ROIC(%)': [58.2, 32.0, 28.0, 8.5],
    },
    title='苹果 vs 竞对 关键估值指标对比',
    output_path=f'{output_dir}/04_valuation_comp.png',
    source='StockAnalysis.com, 2026.02.20',
    highlight_company='Apple'
)
print('✅ 图表4: 竞品估值对比')

# 图表5: 风险矩阵
chart_risk_matrix(
    risks=[
        {'name': '关税贸易摩擦', 'probability': 0.7, 'impact': 0.9, 'level': '高'},
        {'name': '反垄断监管', 'probability': 0.8, 'impact': 0.75, 'level': '高'},
        {'name': 'AI战略落后', 'probability': 0.5, 'impact': 0.7, 'level': '中高'},
        {'name': '中国市场/地缘', 'probability': 0.5, 'impact': 0.75, 'level': '中高'},
        {'name': '估值泡沫', 'probability': 0.5, 'impact': 0.7, 'level': '中高'},
        {'name': '供应链集中', 'probability': 0.2, 'impact': 0.9, 'level': '中'},
        {'name': 'iPhone依赖', 'probability': 0.35, 'impact': 0.7, 'level': '中'},
        {'name': '服务增长放缓', 'probability': 0.3, 'impact': 0.6, 'level': '中'},
        {'name': '创新疲乏', 'probability': 0.3, 'impact': 0.45, 'level': '中低'},
        {'name': '宏观下行', 'probability': 0.3, 'impact': 0.45, 'level': '中低'},
    ],
    title='苹果（AAPL）风险评估矩阵',
    output_path=f'{output_dir}/05_risk_matrix.png',
    source='AI Investment Research'
)
print('✅ 图表5: 风险矩阵')

# 图表6: DCF敏感性热力图
chart_sensitivity_heatmap(
    row_labels=['8.0%', '8.5%', '9.0%', '9.5%', '10.0%'],
    col_labels=['2.0%', '2.5%', '3.0%', '3.5%', '4.0%'],
    values=[
        [225, 240, 260, 285, 320],
        [215, 228, 243, 262, 290],
        [195, 202, 210, 225, 245],
        [182, 188, 195, 208, 225],
        [170, 175, 182, 192, 205],
    ],
    title='苹果（AAPL）DCF敏感性分析（每股价值 USD）',
    output_path=f'{output_dir}/06_dcf_sensitivity.png',
    source='AI Investment Research',
    current_price=264.58
)
print('✅ 图表6: DCF敏感性热力图')

# 图表7: 估值区间对比图（Football Field）
chart_valuation_range(
    methods=['PE估值法', 'EV/EBITDA', 'DCF估值法', 'FCF Yield', '分析师一致'],
    low=[252, 224, 195, 165, 164],
    mid=[284, 244, 210, 186, 299],
    high=[320, 265, 260, 207, 325],
    current_price=264.58,
    title='苹果（AAPL）估值交叉验证（Football Field）',
    output_path=f'{output_dir}/07_valuation_range.png',
    source='AI Investment Research'
)
print('✅ 图表7: 估值区间对比')

# 图表8: EPS冲击瀑布图
chart_eps_waterfall(
    base_eps=8.60,
    impacts=[
        ('关税全面落地', -1.20),
        ('反垄断裁决', -0.44),
        ('AI战略失败', -0.50),
        ('中国区下滑', -0.28),
        ('服务增长放缓', -0.33),
    ],
    title='苹果（AAPL）风险情景EPS冲击分析',
    output_path=f'{output_dir}/08_eps_waterfall.png',
    source='AI Investment Research'
)
print('✅ 图表8: EPS冲击瀑布图')

print('\n🎉 全部8张图表生成完成！')
print(f'📁 输出目录: {output_dir}')
