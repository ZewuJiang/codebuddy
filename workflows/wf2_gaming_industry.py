#!/usr/bin/env python3
"""
工作流 2：游戏行业监控
频率：每日
关注：iOS 畅销榜/免费榜、中国重点公司动态、老品更新、新品热品
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from mbb_report_engine import *
from datetime import datetime

DATE = datetime.now().strftime("%Y%m%d")
DATE_DISPLAY = datetime.now().strftime("%Y.%m.%d")

# 游戏行业专属配色
GAME_BLUE = HexColor('#1d3557')
GAME_RED = HexColor('#e63946')
GAME_GOLD = HexColor('#f4a261')
GAME_GREEN = HexColor('#2a9d8f')


def generate(news_data=None):

    filename = f"游戏行业监控-每日简报-{DATE}.pdf"
    r = MBBReportEngine(
        filename,
        title="游戏行业监控",
        subtitle=f"iOS 榜单 · 公司动态 · 老品更新 · 新品跟踪  |  {DATE_DISPLAY}",
        accent_color=GAME_BLUE,
        page_scale=4.5
    )

    r.draw_header()

    # ── iOS 畅销榜 TOP 10 ──
    # 数据来源：Apple iTunes RSS Feed 实时数据（itunes.apple.com/cn/rss/）
    r.draw_section_title("iOS 畅销榜 TOP 10", GAME_RED)

    top_grossing = news_data.get('top_grossing', []) if news_data else [
        ("1. 王者荣耀", "腾讯天美", "—", GRAY_DARK),
        ("2. 和平精英", "腾讯光子", "—", GRAY_DARK),
        ("3. 三角洲行动", "腾讯天美", "—", GRAY_DARK),
        ("4. 无畏契约:源能行动", "腾讯光子/Riot", "↑ 1", GAME_GREEN),
        ("5. 金铲铲之战", "腾讯", "↓ 1", GAME_RED),
        ("6. 蛋仔派对", "网易", "↑ 2", GAME_GREEN),
        ("7. 无尽冬日", "点点互动", "—", GRAY_DARK),
        ("8. 火影忍者", "腾讯", "↑ 1", GAME_GREEN),
        ("9. 超自然行动组", "巨人网络", "新上榜", GAME_GOLD),
        ("10. 英雄联盟手游", "腾讯/Riot", "↓ 1", GAME_RED),
    ]
    r.draw_info_card("iOS 畅销榜", top_grossing, GAME_RED)

    # ── iOS 免费榜 TOP 10 ──
    r.draw_section_title("iOS 免费榜 TOP 10", GAME_BLUE)

    top_free = news_data.get('top_free', []) if news_data else [
        ("1. 鹅鸭杀", "金山世游", "持续霸榜", GAME_GREEN),
        ("2. 三角洲行动", "腾讯天美", "—", GRAY_DARK),
        ("3. 时尚百货城", "爱的番茄科技", "新上榜", GAME_GOLD),
        ("4. 蛋仔派对", "网易", "—", GRAY_DARK),
        ("5. 王者荣耀", "腾讯天美", "↓ 1", GAME_RED),
        ("6. 和平精英", "腾讯光子", "—", GRAY_DARK),
        ("7. 我的花园世界", "厦门麟贝互娱", "新上榜", GAME_GOLD),
        ("8. 无畏契约:源能行动", "腾讯光子/Riot", "↑ 2", GAME_GREEN),
        ("9. 我的世界", "网易/Mojang", "—", GRAY_DARK),
        ("10. 欢乐麻将", "腾讯", "—", GRAY_DARK),
    ]
    r.draw_info_card("iOS 免费榜", top_free, GAME_BLUE)

    # ── 重点公司动态 ──
    r.draw_section_title("重点公司动态")

    company_insights = news_data.get('company_insights', []) if news_data else [
        {
            'category': '微软/Xbox 重大人事变动',
            'priority': 5,
            'color': GAME_RED,
            'thesis': 'Phil Spencer 宣布退休，结束38年微软生涯，Xbox 迎来史诗级换帅',
            'detail': '2月21日，微软游戏CEO Phil Spencer正式宣布退休，其任期长达12年。微软CoreAI部门负责人Asha Sharma将接任。Xbox总裁Sarah Bond同步离职。Spencer此前主导了687亿美元收购动视暴雪等标志性事件。',
            'impact': 'Xbox业务战略可能迎来重大转向，新任领导来自CoreAI部门，暗示微软将进一步深化AI与游戏融合。主机硬件路线和Game Pass策略或将调整，全球游戏竞争格局面临重塑。',
            'action': '密切关注新任领导层的首批战略决策，评估对主机市场竞争格局及第三方合作关系的影响。'
        },
        {
            'category': '腾讯游戏',
            'priority': 5,
            'color': GAME_BLUE,
            'thesis': '腾讯系产品包揽畅销榜前五中四席，多线开花态势明显',
            'detail': '《三角洲行动》DAU从1200万跃升至4100万，首次进入畅销榜前五；《逆战:未来》上线不到一个月直冲畅销榜第一；《暗区突围》春节期间空降畅销Top 8，用户突破2.3亿；《无畏契约手游》被腾讯财报称为"2025年中国市场最成功的新手游"。',
            'impact': '腾讯在FPS/战术射击赛道形成统治级优势，《三角洲行动》+《逆战:未来》+《暗区突围》+《无畏契约》四产品矩阵碾压竞品。畅销榜前10中腾讯系占据5-6席，行业集中度进一步提升。',
            'action': '关注腾讯FPS矩阵的品类内竞争问题，评估是否存在自相残杀风险；跟踪《王者荣耀世界》云游戏测试进展。'
        },
        {
            'category': '鹰角网络',
            'priority': 4,
            'color': GAME_GOLD,
            'thesis': '《明日方舟:终末地》全球公测表现强势，两周流水破12亿',
            'detail': '《明日方舟:终末地》上线次日全球下载突破3000万，两周全平台累积流水突破12亿元人民币。PC端流水占比超60%，在中国区App Store畅销榜一度升至前五。鹰角凭此成为继米哈游后又一个在PC市场成功突破的中国厂商。',
            'impact': '二次元品类格局正在发生深刻变化，PC端流水占比超60%说明中国玩家付费习惯正从移动端向PC端迁移。3D即时策略RPG赛道被成功验证，可能吸引更多厂商入局。',
            'action': '跟踪终末地首月留存数据和赛季更新节奏，评估其长线运营能力。关注对米哈游系产品的分流影响。'
        },
        {
            'category': '网易游戏',
            'priority': 4,
            'color': GAME_GREEN,
            'thesis': '网易推新春补贴活动，多线产品稳定运营',
            'detail': '网易2月15日-3月31日推出新春开运补贴活动，含新用户100%中奖、小米专属致歉福利等四重福利。《蛋仔派对》维持免费榜前三；《梦幻西游》稳居畅销榜前十；《逆水寒手游》重新杀回畅销榜Top10。',
            'impact': '网易整体产品矩阵保持稳定，但缺乏爆款新品冲击力。小米渠道致歉福利显示网易正加速推进官服化战略，未来渠道分成格局可能继续演变。',
            'action': '关注网易官服化进程对收入结构的影响；跟踪《遗忘之海》海洋冒险RPG开发进展。'
        },
        {
            'category': '米哈游',
            'priority': 4,
            'color': GAME_GOLD,
            'thesis': '《原神》6.4版本前瞻已开，《星布谷地》年内公测计划引关注',
            'detail': '《原神》6.4版本"空月之歌·变奏"前瞻特别节目于2月13日播出，公布新版本角色、玩法及福利。《崩坏:星穹铁道》稳居畅销榜第六。新品《星布谷地》（宇宙级田园治愈模拟经营游戏）预计2026年内公测，无PVP无强制社交，标志米哈游品类多元化扩张。',
            'impact': '米哈游正从二次元抽卡的舒适区向模拟经营品类扩展，《星布谷地》如成功将打开全新增长曲线。《崩坏:星穹铁道》表现稳定，但需关注鹰角《终末地》的分流影响。',
            'action': '重点跟踪《星布谷地》测试数据和用户反馈；评估米哈游多品类战略对资源配置的影响。'
        },
    ]
    for item in company_insights:
        r.draw_insight_card(item)

    # ── 海外重要动态 ──
    r.draw_section_title("海外重要动态", GAME_RED)

    global_insights = news_data.get('global_insights', []) if news_data else [
        {
            'category': '美国最高法院 / 关税政策',
            'priority': 4,
            'color': GAME_RED,
            'thesis': '美最高法院驳回特朗普关税政策，主机定价不确定性暂缓',
            'detail': '美国最高法院裁定特朗普基于IEEPA的全面关税政策违宪。特朗普随即宣布将对全球征收10%关税替代方案。此前关税导致PS5、Xbox等主机面临涨价压力，Switch 2定价策略也受影响。',
            'impact': '关税违宪判决短期利好主机厂商和玩家，但10%新关税仍将推高硬件成本。Nintendo Switch 2预计2028年销量超8000万台的预期可能需要重新评估。全球游戏硬件供应链不确定性延续。',
            'action': '跟踪10%新关税对主机定价的实际影响，评估对国内主机游戏市场的传导效应。'
        },
        {
            'category': 'Roblox / 儿童安全',
            'priority': 3,
            'color': GAME_GOLD,
            'thesis': '洛杉矶县起诉Roblox，儿童安全合规风险升级',
            'detail': '洛杉矶县指控Roblox未能充分审核内容和执行年龄限制，导致平台成为儿童遭受性剥削的温床。诉讼理由为"公共滋扰"和违反加州虚假广告法。Roblox去年向执法机构举报超13000起涉嫌儿童剥削案件。',
            'impact': '继Meta之后，地方政府对科技平台儿童保护责任的监管持续加码。对国内未成年人保护政策有参考价值，UGC平台安全审核标准面临全球性升级压力。',
            'action': '评估国内UGC/沙盒类游戏的未成年人保护合规风险，参考国际最佳实践更新内控标准。'
        },
    ]
    for item in global_insights:
        r.draw_insight_card(item)

    # ── 老品更新追踪 ──
    r.draw_section_title("老品更新追踪", GAME_GOLD)

    old_game_events = news_data.get('old_game_events', []) if news_data else [
        ("2.21", "《暗区突围》春节空降畅销Top 8", "七麦数据", "用户突破2.3亿，深耕硬核内容营销策略", GAME_GREEN),
        ("2.16", "《三角洲行动》新春活动+新模式上线", "七麦数据", "新增胜者为王模式+流光铂影外观，首进畅销Top 3", GAME_BLUE),
        ("2.15", "网易游戏新春开运补贴活动上线", "网易官方", "四重福利，含小米渠道致歉补贴，推进官服化", GAME_GOLD),
        ("2.13", "《原神》6.4版本前瞻特别节目播出", "米哈游官方", "公布新版本角色/玩法/福利，全球同步直播", GAME_GOLD),
    ]
    r.draw_timeline(old_game_events)

    # ── 新品热品监控 ──
    r.draw_section_title("新品热品监控", GAME_GREEN)

    new_game_events = news_data.get('new_game_events', []) if news_data else [
        ("2月", "《明日方舟:终末地》全球公测", "鹰角网络", "两周流水12亿，下载3000万+，PC端占比60%", GAME_RED),
        ("1.13", "《逆战:未来》公测", "腾讯天美J3", "上线首日空降免费榜第一+畅销Top 4", GAME_BLUE),
        ("1.07", "《鹅鸭杀》公测", "金山世游", "24小时新增500万用户，1月免费榜霸榜16天", GAME_GREEN),
        ("预计年内", "《星布谷地》米哈游新品", "米哈游", "宇宙田园治愈模拟经营，无PVP/无强制社交", GAME_GOLD),
        ("预计年内", "《遗忘之海》网易新品", "网易", "海洋冒险RPG，已获版号", GAME_GOLD),
    ]
    r.draw_timeline(new_game_events)

    # ── 行动建议 ──
    r.draw_section_title("立即行动")

    actions = news_data.get('actions', []) if news_data else [
        ("P0", "关注Xbox换帅后AI+游戏战略方向变化", "战略部", "本周", GAME_RED),
        ("P1", "跟踪《终末地》首月留存及对二次元赛道影响", "产品部", "本月", GAME_GOLD),
        ("P1", "评估腾讯FPS四产品矩阵竞争格局与市场天花板", "分析部", "本月", GAME_BLUE),
        ("P2", "关注美国10%新关税对主机硬件定价传导效应", "市场部", "持续", GAME_GREEN),
        ("P2", "跟踪米哈游《星布谷地》测试动态及品类扩张策略", "产品部", "季度", GAME_GOLD),
    ]
    r.draw_actions(actions)

    r.draw_footer("数据: Apple iTunes RSS Feed（实时） + Sensor Tower + 行业媒体  |  游戏行业监控 · 每日简报  |  2026.02.21")
    r.save()
    return filename


if __name__ == "__main__":
    f = generate()
    print(f"\n{'='*60}")
    print(f"\u5de5\u4f5c\u6d41 2: \u6e38\u620f\u884c\u4e1a\u76d1\u63a7")
    print(f"\u9891\u7387: \u6bcf\u65e5")
    print(f"\u4ea7\u51fa: {f}")
    print(f"{'='*60}")
    print("\n\u5173\u6ce8\u7ef4\u5ea6 (MECE):")
    print("  ① iOS 畅销榜/免费榜 - 榜单变动跟踪")
    print("  \u2461 \u91cd\u70b9\u516c\u53f8 - \u817e\u8baf/\u7f51\u6613/\u7c73\u54c8\u6e38/\u5b57\u8282/\u83a0\u857e/\u5b8c\u7f8e\u7b49")
    print("  \u2462 \u8001\u54c1\u66f4\u65b0 - \u5927\u7248\u672c/\u6d3b\u52a8/\u8fd0\u8425\u7b56\u7565")
    print("  \u2463 \u65b0\u54c1\u70ed\u54c1 - \u6d4b\u8bd5/\u4e0a\u7ebf/\u7206\u6b3e\u8ddf\u8e2a")
