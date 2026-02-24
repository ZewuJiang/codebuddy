#!/usr/bin/env python3
"""
工作流 5：游戏竞品运营监控
频率：每周（周一早8点）
关注：玩法内容、活跃活动、商业化、内容营销、电竞赛事、其他重大事件
数据来源：微信公众号 + TapTap官方论坛 + 游戏官网
"""
import sys
import os
import json
import glob

# 确保工作目录为脚本所在目录（输出文件路径可控）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from mbb_report_engine import *
from datetime import datetime

DATE = datetime.now().strftime("%Y%m%d")
DATE_DISPLAY = datetime.now().strftime("%Y.%m.%d")

# 游戏运营监控专属配色
OPS_NAVY = HexColor('#1a1a2e')
OPS_RED = HexColor('#e63946')
OPS_ORANGE = HexColor('#f77f00')
OPS_GOLD = HexColor('#f4a261')
OPS_GREEN = HexColor('#2a9d8f')
OPS_BLUE = HexColor('#457b9d')
OPS_PURPLE = HexColor('#6c5ce7')

# 维度配色映射
DIMENSION_COLORS = {
    'gameplay_content': OPS_RED,
    'active_events': OPS_BLUE,
    'monetization': OPS_GOLD,
    'content_marketing': OPS_GREEN,
    'esports': OPS_PURPLE,
    'other_major': GRAY_LIGHT,
}

# 维度显示顺序（按优先级）
DIMENSION_ORDER = [
    'gameplay_content',
    'active_events',
    'monetization',
    'content_marketing',
    'esports',
    'other_major',
]

DATA_DIR = os.path.join(SCRIPT_DIR, 'game_ops_data')
REGISTRY_PATH = os.path.join(DATA_DIR, 'game_registry.json')


def load_registry():
    """加载游戏注册表"""
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f).get('games', {})
    return {}


def load_game_data(game_name=None, week=None, year=None):
    """加载指定游戏指定周次的 JSON 数据，并合并注册表中的基础信息"""
    data = None
    if game_name and week is not None and year is not None:
        filepath = os.path.join(DATA_DIR, game_name, f"week_{int(week):02d}_{int(year)}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
    # 自动查找最新数据文件
    if data is None and game_name:
        game_dir = os.path.join(DATA_DIR, game_name)
        if os.path.isdir(game_dir):
            files = sorted(glob.glob(os.path.join(game_dir, 'week_*.json')), reverse=True)
            if files:
                with open(files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)

    # 合并注册表默认值到 meta（注册表为 fallback，周报数据优先）
    if data:
        registry = load_registry()
        reg_info = registry.get(game_name, {})
        meta = data.get('meta', {})
        for key in ('wechat_account', 'developer', 'publisher', 'game_type'):
            if not meta.get(key) and reg_info.get(key):
                meta[key] = reg_info[key]
        # 补充 data_sources（如果数据文件中未定义，则从注册表构建）
        if not meta.get('data_sources') and reg_info.get('sources'):
            sources = []
            if reg_info.get('wechat_account'):
                sources.append(f"微信公众号「{reg_info['wechat_account']}」")
            if reg_info['sources'].get('taptap'):
                sources.append(f"TapTap官方论坛 {reg_info['sources']['taptap']}")
            if reg_info['sources'].get('official_site'):
                sources.append(f"官网 {reg_info['sources']['official_site']}")
            if sources:
                meta['data_sources'] = sources
    return data


def get_all_games():
    """获取所有已有数据的游戏列表"""
    games = []
    if os.path.isdir(DATA_DIR):
        for item in os.listdir(DATA_DIR):
            game_dir = os.path.join(DATA_DIR, item)
            if os.path.isdir(game_dir) and glob.glob(os.path.join(game_dir, 'week_*.json')):
                games.append(item)
    return sorted(games)


def _sources_short(meta):
    """从 meta 中提取来源简称（取中文部分或域名）"""
    if not meta.get('data_sources'):
        return meta.get('wechat_account', '')
    parts = []
    for s in meta['data_sources'][:3]:
        # 优先取 URL 前的中文描述，否则取完整字符串
        if ' http' in s:
            parts.append(s[:s.index(' http')].strip())
        else:
            parts.append(s)
    return ' / '.join(parts)


def generate_pdf(data):
    """生成 PDF 格式周报"""
    meta = data['meta']
    summary = data['summary']
    dimensions = data['dimensions']

    game_name = meta.get('game_name', '未知游戏')
    week_num = meta.get('week_number', 0)
    date_range = f"{meta['date_range'][0]} ~ {meta['date_range'][1]}"

    filename = f"游戏竞品运营监控-{game_name}-第{week_num:02d}周-{DATE}.pdf"

    # 计算需要的页面高度（考虑图片）
    images_base_dir = os.path.join(DATA_DIR, game_name, 'images')
    total_entries = 0
    total_images = 0
    for d in DIMENSION_ORDER:
        if d in dimensions:
            entries = dimensions[d].get('entries', [])
            total_entries += len(entries)
            for entry in entries:
                for img in entry.get('images', []):
                    if isinstance(img, dict) and img.get('file'):
                        if os.path.exists(os.path.join(images_base_dir, img['file'])):
                            total_images += 1
    page_scale = max(4.0, 2.5 + total_entries * 0.6 + total_images * 0.8)

    sources_str = _sources_short(meta)

    r = MBBReportEngine(
        filename,
        title=f"{game_name} · 运营监控周报",
        subtitle=f"第{week_num}周 ({date_range})  |  数据源: {sources_str}  |  {DATE_DISPLAY}",
        accent_color=OPS_NAVY,
        page_scale=page_scale
    )

    r.draw_header()

    # ── 本周总览 ──
    r.draw_section_title("本周总览", OPS_NAVY)

    dimension_stats = []
    for dim_key in DIMENSION_ORDER:
        if dim_key in dimensions:
            dim = dimensions[dim_key]
            dimension_stats.append({
                'name': dim['display_name'],
                'count': len(dim.get('entries', [])),
                'priority': dim.get('priority_level', 'low'),
                'color': DIMENSION_COLORS.get(dim_key, GRAY_LIGHT),
            })

    r.draw_ops_summary_card(summary, dimension_stats)

    # ── 各维度详情 ──
    for dim_key in DIMENSION_ORDER:
        if dim_key not in dimensions:
            continue
        dim = dimensions[dim_key]
        entries = dim.get('entries', [])
        if not entries:
            continue

        color = DIMENSION_COLORS.get(dim_key, GRAY_LIGHT)
        r.draw_section_title(dim['display_name'], color)
        r.draw_dimension_card(
            dim['display_name'],
            dim.get('priority_level', 'low'),
            entries,
            color,
            images_base_dir=images_base_dir
        )

    # ── 行动建议 ──
    r.draw_section_title("关注建议", OPS_NAVY)
    actions = generate_actions_from_data(data)
    r.draw_actions(actions)

    r.draw_footer(
        f"数据源: {sources_str}  |  "
        f"游戏竞品运营监控 · 第{week_num}周  |  {DATE_DISPLAY}"
    )
    r.save()
    return filename


def generate_actions_from_data(data):
    """根据监控数据自动生成关注建议"""
    actions = []
    dimensions = data['dimensions']

    # 高优先级维度中的 T0 级别条目
    for dim_key in ['gameplay_content', 'active_events', 'monetization']:
        if dim_key not in dimensions:
            continue
        for entry in dimensions[dim_key].get('entries', []):
            if entry.get('tier') == 'T0':
                actions.append((
                    "P0",
                    f"重点关注: {entry['title']}",
                    "竞品分析",
                    entry.get('date', '本周'),
                    OPS_RED
                ))

    # 有玩家反馈的条目
    for dim_key in DIMENSION_ORDER:
        if dim_key not in dimensions:
            continue
        for entry in dimensions[dim_key].get('entries', []):
            if entry.get('player_feedback') and entry.get('tier') in ('T0', 'T1'):
                actions.append((
                    "P1",
                    f"跟踪玩家反馈: {entry['title']}",
                    "用户研究",
                    "持续",
                    OPS_ORANGE
                ))
                break  # 每个维度只取一条

    # 商业化动态
    if 'monetization' in dimensions and dimensions['monetization'].get('entries'):
        actions.append((
            "P1",
            "持续监控商业化策略变化及玩家付费意愿",
            "商业分析",
            "本月",
            OPS_GOLD
        ))

    # 限制最多6条
    return actions[:6]


def generate_markdown(data):
    """生成 Markdown 格式周报"""
    meta = data['meta']
    summary = data['summary']
    dimensions = data['dimensions']

    game_name = meta.get('game_name', '未知游戏')
    week_num = meta.get('week_number', 0)
    wechat = meta.get('wechat_account', '-')
    date_range = f"{meta['date_range'][0]} ~ {meta['date_range'][1]}"

    lines = []
    lines.append(f"# {game_name} · 运营监控周报")
    lines.append(f"")
    lines.append(f"> 第{week_num}周 ({date_range}) | 公众号: {wechat}")
    lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"")

    # 游戏基本信息
    lines.append(f"## 游戏信息")
    lines.append(f"")
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| 游戏名称 | {game_name} |")
    lines.append(f"| 研发商 | {meta.get('developer', '-')} |")
    lines.append(f"| 运营商 | {meta.get('publisher', '-')} |")
    lines.append(f"| 游戏类型 | {meta.get('game_type', '-')} |")
    lines.append(f"| 监控公众号 | {wechat} |")
    lines.append(f"| 监控周期 | {date_range} |")
    if meta.get('data_sources'):
        for i, src in enumerate(meta['data_sources'], 1):
            lines.append(f"| 数据来源{i} | {src} |")
    if meta.get('note'):
        lines.append(f"| 备注 | {meta['note']} |")
    lines.append(f"")

    # 本周总览
    lines.append(f"## 本周总览")
    lines.append(f"")
    lines.append(f"**公众号文章数**: {summary['total_articles']}")
    lines.append(f"")
    lines.append(f"**整体评估**: {summary['overall_assessment']}")
    lines.append(f"")
    lines.append(f"**本周要点**:")
    lines.append(f"")
    for h in summary['key_highlights']:
        lines.append(f"- {h}")
    lines.append(f"")

    # 维度统计
    lines.append(f"### 监控维度统计")
    lines.append(f"")
    lines.append(f"| 维度 | 优先级 | 动态数 |")
    lines.append(f"|------|--------|--------|")
    priority_map = {'high': '🔴 高', 'medium': '🟡 中', 'low': '⚪ 低'}
    for dim_key in DIMENSION_ORDER:
        if dim_key in dimensions:
            dim = dimensions[dim_key]
            p = priority_map.get(dim.get('priority_level', 'low'), '⚪ 低')
            count = len(dim.get('entries', []))
            lines.append(f"| {dim['display_name']} | {p} | {count} |")
    lines.append(f"")

    # 各维度详情
    for dim_key in DIMENSION_ORDER:
        if dim_key not in dimensions:
            continue
        dim = dimensions[dim_key]
        entries = dim.get('entries', [])
        if not entries:
            continue

        p = priority_map.get(dim.get('priority_level', 'low'), '⚪ 低')
        lines.append(f"## {dim['display_name']}（{p}）")
        lines.append(f"")
        lines.append(f"> {dim.get('description', '')}")
        lines.append(f"")

        for i, entry in enumerate(entries, 1):
            tier = entry.get('tier', 'T1')
            lines.append(f"### {i}. [{tier}] {entry['title']}")
            lines.append(f"")
            lines.append(f"- **日期**: {entry.get('date', '-')}")
            lines.append(f"- **详情**: {entry.get('detail', '-')}")
            if entry.get('source_url'):
                source_title = entry.get('source_title', '链接')
                lines.append(f"- **来源**: [{source_title}]({entry['source_url']})")
            if entry.get('player_feedback'):
                lines.append(f"- **玩家反馈**: {entry['player_feedback']}")
            if entry.get('images'):
                for img in entry['images']:
                    if isinstance(img, dict) and img.get('file'):
                        img_rel = f"game_ops_data/{game_name}/images/{img['file']}"
                        lines.append(f"")
                        lines.append(f"![{img.get('desc', '')}]({img_rel})")
                    elif isinstance(img, str):
                        lines.append(f"- **关键截图**: {img}")
            lines.append(f"")

    # 关注建议
    lines.append(f"## 关注建议")
    lines.append(f"")
    actions = generate_actions_from_data(data)
    for priority, action, owner, deadline, _ in actions:
        lines.append(f"- **[{priority}]** {action} — {owner} | {deadline}")
    lines.append(f"")

    # 页脚
    lines.append(f"---")
    lines.append(f"")
    if meta.get('data_sources'):
        sources_md = ' | '.join(meta['data_sources'])
        lines.append(f"*数据来源: {sources_md}*")
    else:
        lines.append(f"*数据来源: {wechat} 微信公众号*")
    lines.append(f"")
    lines.append(f"*游戏竞品运营监控 · 第{week_num}周 | {datetime.now().strftime('%Y.%m.%d')}*")

    md_filename = f"游戏竞品运营监控-{game_name}-第{week_num:02d}周-{DATE}.md"
    md_content = '\n'.join(lines)

    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"✅ Markdown 报告已生成: {md_filename}")
    return md_filename


def generate(news_data=None):
    """
    统一入口：生成游戏竞品运营监控周报
    与 run_all.py 调度器兼容的标准函数签名
    """
    results = []
    games = get_all_games()

    if not games:
        print("⚠️ 未找到任何游戏监控数据，使用内置示例数据")
        games = ['超自然行动组']

    for game_name in games:
        data = load_game_data(game_name)
        if not data:
            print(f"⚠️ {game_name}: 未找到数据文件，跳过")
            continue

        print(f"\n📊 正在生成: {game_name} 周报...")
        try:
            pdf_file = generate_pdf(data)
            md_file = generate_markdown(data)
            results.append((game_name, pdf_file, md_file))
        except Exception as e:
            print(f"❌ {game_name} 报告生成失败: {e}")
            import traceback
            traceback.print_exc()

    if results:
        print(f"\n{'='*60}")
        print(f"  游戏竞品运营监控 - 周报生成完成")
        print(f"{'='*60}")
        for game, pdf, md in results:
            print(f"  📄 {game}:")
            print(f"     PDF: {pdf}")
            print(f"     MD:  {md}")
        return results[0][1]  # 返回第一个 PDF 文件名
    else:
        print("❌ 无报告生成")
        return None


if __name__ == "__main__":
    f = generate()
    print(f"\n{'='*60}")
    print(f"工作流 5: 游戏竞品运营监控")
    print(f"频率: 每周")
    print(f"产出: {f}")
    print(f"{'='*60}")
    print("\n监控维度 (按优先级):")
    print("  🔴 高 ① 玩法内容 - 版本更新/新玩法/新角色")
    print("  🔴 高 ② 活跃活动 - 节庆/留存/邀请活动")
    print("  🔴 高 ③ 商业化 - 付费内容/皮肤/充值")
    print("  🟡 中 ④ 内容营销 - 创作者/KOL/热门内容")
    print("  🟡 中 ⑤ 电竞赛事 - 重大赛事节点")
    print("  ⚪ 低 ⑥ 其他重大事件 - 线下活动/品牌联动")
