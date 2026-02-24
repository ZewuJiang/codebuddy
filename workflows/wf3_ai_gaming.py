#!/usr/bin/env python3
"""
工作流 3：AI+游戏前沿赛道
频率：每周
关注：AI 提效、AI NPC、AI 原生游戏、AI+游戏创意组合
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from mbb_report_engine import *
from datetime import datetime

DATE = datetime.now().strftime("%Y%m%d")
DATE_DISPLAY = datetime.now().strftime("%Y.%m.%d")
WEEK_NUM = datetime.now().isocalendar()[1]

# AI+游戏专属配色
AIGAME_PURPLE = HexColor('#7b2cbf')
AIGAME_CYAN = HexColor('#00b4d8')
AIGAME_PINK = HexColor('#ff006e')


def generate(news_data=None):

    filename = f"AI+游戏前沿-周报第{WEEK_NUM:02d}周-{DATE}.pdf"
    r = MBBReportEngine(
        filename,
        title="AI+游戏前沿",
        subtitle=f"AI提效 · AI NPC · AI原生游戏 · 创意组合  |  第{WEEK_NUM:02d}周  {DATE_DISPLAY}",
        accent_color=AIGAME_PURPLE,
        page_scale=5.5
    )

    r.draw_header()

    # ── 本周核心洞察 ──
    r.draw_section_title("本周核心洞察")

    insights = news_data.get('insights', []) if news_data else [
        {
            'category': '行业生态巨变',
            'priority': 5,
            'color': AIGAME_PURPLE,
            'thesis': '微软Xbox换帅CoreAI总裁：38年老将Phil Spencer退休，AI战略全面接管游戏业务',
            'detail': '2026年2月20日，微软游戏CEO Phil Spencer正式宣布退休（1988年入职，38年职业生涯），Xbox总裁Sarah Bond同步辞职。接任者Asha Sharma此前担任微软CoreAI产品总裁，拥有Meta产品VP和Instacart COO经验。Sharma在全员信中明确三大优先级：伟大游戏、Xbox回归、游戏未来。她承诺"不追逐短期效率，不向生态系统充斥没有灵魂的AI垃圾（AI slop）"，强调游戏是人类创造的艺术。Matt Booty晋升为首席内容官。（来源：Game Developer 2026.02.20报道，Phil Spencer在Bluesky确认）',
            'impact': '微软将CoreAI最高负责人直接空降为游戏CEO，是科技巨头AI+游戏战略最强信号。这意味着Azure AI、Copilot等AI能力将深度整合进Xbox/Game Pass生态。"反AI slop"表态表明微软将走高质量AI赋能路线而非粗暴替代，对全行业AI游戏策略产生示范效应。',
            'action': '密切跟踪Asha Sharma上任后微软AI+游戏的具体落地动作；评估自身AI游戏战略是否存在"AI slop"风险。'
        },
        {
            'category': 'AI安全/版权',
            'priority': 5,
            'color': ORANGE,
            'thesis': 'TikTok拒绝下架AI生成种族歧视游戏广告：平台AI滥用风险全面暴露',
            'detail': '2026年2月21日Game Developer报道，独立游戏工作室Finji（代表作《Night in the Woods》《Tunic》）发现TikTok通过其"Smart Creative"AI功能自动生成了未经授权的广告。尽管Finji已关闭该AI功能，TikTok仍自动生成并发布了篡改游戏《Usual June》主角形象的广告——AI将黑人女性主角June的穿着从短裤运动鞋改为比基尼过膝靴，涉及种族歧视和性暗示。Finji经数周投诉，TikTok客服反复承认又否认，最终拒绝移除。Finji CEO Bekah Saltsman已停止在TikTok投放广告。（来源：Game Developer 2026.02.21，基于IGN审查的聊天记录截图）',
            'impact': '平台AI自动生成内容对游戏IP安全构成系统性风险。TikTok的Smart Creative功能在客户明确关闭后仍自动生成内容，暴露了平台AI工具的透明度和可控性严重不足。该事件将推动行业建立AI生成广告内容的标识审核机制。',
            'action': '立即排查TikTok等社交平台AI广告功能是否未经授权使用自有游戏素材；建立AI广告侵权监测和快速响应机制。'
        },
        {
            'category': 'AI提效工具',
            'priority': 4,
            'color': AIGAME_PINK,
            'thesis': 'Unity CEO预言AI提示词直接生成游戏 + Godot社区反AI slop：行业态度两极分化',
            'detail': '2026年2月20日Game Developer Patch Notes #41报道：Unity CEO最新表态称开发者将很快能通过AI提示词（prompt）直接生成可玩游戏，标志引擎层AI原生化加速。同日报道另一面：Godot引擎社区资深开发者公开痛批AI生成的代码和内容为"AI slop"（AI垃圾），认为大量低质量AI生成PR严重拉低开源社区代码质量。两则消息对比鲜明，映射了游戏行业对AI的深度撕裂。（来源：Game Developer 2026.02.20）',
            'impact': 'Unity CEO的表态是引擎层面拥抱AI的官方表态，但Godot社区的强烈反弹证明开发者群体对AI的接受度远非一致。引擎公司推AI和开源社区反AI slop将成为2026年游戏开发生态的核心矛盾线。',
            'action': '跟踪Unity AI原生工具更新节奏；在引入AI辅助开发时建立代码质量审查机制，避免AI slop问题。'
        },
        {
            'category': 'AI+硬件供应链',
            'priority': 4,
            'color': AIGAME_CYAN,
            'thesis': '美最高法院裁定关税违宪，但AI数据中心抢占芯片产能正在推高游戏主机成本',
            'detail': '2026年2月21日，美国最高法院以6:3裁定特朗普2025年IEEPA关税违宪。但Game Developer同日分析指出，游戏主机价格仍难回落——核心原因是AI数据中心的巨额支出导致RAM和硬盘全球性短缺。OpenAI于2025年12月与三星签约锁定全球40%的DRAM产能，消费级RAM价格飙涨171%。Valve Steam Deck OLED出现缺货，任天堂社长警告内存短缺"可能给盈利能力带来压力"。特朗普已根据1974年贸易法另行宣布新的10%关税。（来源：Game Developer 2026.02.21）',
            'impact': 'AI对游戏行业的影响已从软件层面扩展到硬件供应链。AI数据中心与游戏主机在芯片/内存上的直接竞争，正在结构性推高游戏硬件成本。这是一个被严重低估的AI+游戏交叉风险。',
            'action': '评估AI芯片短缺对自有硬件产品线和云游戏成本的影响；关注任天堂Switch 2和下一代主机的定价策略。'
        },
        {
            'category': '平台安全/AI治理',
            'priority': 4,
            'color': GREEN,
            'thesis': '洛杉矶县起诉Roblox危害儿童安全：AI UGC平台治理挑战加剧',
            'detail': '2026年2月19日，洛杉矶县在高等法院起诉Roblox，指控其存在"不公平和欺骗性的商业行为，危及并剥削儿童"。起诉书称Roblox是"不安全的在线环境，已成为掠夺者的温床"，平台架构允许成年人轻易锁定未成年人并进行诱骗。此前路易斯安那州（2025年）也曾起诉该公司，澳大利亚通讯部长本月也致信表达对平台UGC中色情和自杀材料的担忧。Roblox发表声明反驳并表示将积极应诉。（来源：Game Developer 2026.02.21报道）',
            'impact': '作为全球最大的AI+UGC游戏平台，Roblox面临多国/多地区的法律围剿。随着AI大幅降低UGC内容生成门槛，平台内容安全审核的压力将指数级上升，这对所有布局AI+UGC的游戏公司都是重大警示。',
            'action': '审视自有UGC平台的AI内容审核能力是否匹配AI降低创作门槛后的内容增量；关注Roblox案的司法进展对行业政策的影响。'
        },
    ]

    for item in insights:
        r.draw_insight_card(item)

    # ── 本周关键事件 ──
    r.draw_section_title("本周关键事件")

    events = news_data.get('events', []) if news_data else [
        ("2.21", "美最高法院6:3裁定特朗普关税违宪，但AI芯片短缺持续推高游戏主机成本", "Game Developer", "OpenAI锁定三星40%DRAM产能，消费级RAM涨171%，Steam Deck缺货", AIGAME_CYAN),
        ("2.21", "TikTok拒绝下架AI生成的种族歧视游戏广告", "Game Developer", "Finji Games遭AI Smart Creative功能自动生成侵权内容，平台拒绝处理", ORANGE),
        ("2.21", "洛杉矶县起诉Roblox：危及并剥削儿童（2.19起诉）", "Game Developer", "指控平台成为掠夺者温床，继路易斯安那州后第二起诉讼", GREEN),
        ("2.20", "Phil Spencer退休，CoreAI总裁Asha Sharma接任Xbox CEO", "Game Developer", "38年老将谢幕，AI背景新帅承诺不搞AI slop，Sarah Bond同步辞职", AIGAME_PURPLE),
        ("2.20", "Unity CEO预言开发者将能用AI提示词直接生成游戏", "Game Developer", "引擎层面AI原生化加速，行业开发范式面临颠覆", AIGAME_PINK),
        ("2.20", "Godot社区资深开发者公开抨击AI生成内容为slop", "Game Developer", "开源引擎社区对AI代码PR质量下降表达强烈不满", ORANGE),
        ("2.20", "Midsummer Studios宣布关闭", "Game Developer", "前Firaxis老将Jake Solomon创办的AI生活模拟游戏工作室倒闭", CORAL),
    ]
    r.draw_timeline(events)

    # ── 行动建议 ──
    r.draw_section_title("立即行动")

    actions = news_data.get('actions', []) if news_data else [
        ("P0", "排查TikTok等平台AI广告功能是否未经授权使用自有游戏素材和IP", "市场/法务部", "本周", CORAL),
        ("P0", "评估微软Xbox换帅对自身平台合作关系和AI游戏战略的影响", "战略部", "本周", AIGAME_PURPLE),
        ("P1", "审视自有UGC平台的AI内容审核能力，对标Roblox案的监管趋势", "安全/合规部", "本月", GREEN),
        ("P1", "跟踪Unity AI原生工具更新，引入AI辅助开发时建立代码质量审查机制", "技术部", "本月", AIGAME_PINK),
        ("P2", "评估AI芯片/内存短缺对游戏硬件成本和云游戏服务价格的中长期影响", "供应链/财务部", "本季度", AIGAME_CYAN),
    ]
    r.draw_actions(actions)

    r.draw_footer("数据: AI News MCP + Game Developer (实时验证)  |  AI+游戏前沿 · 第08周周报  |  2026.02.21")
    r.save()
    return filename


if __name__ == "__main__":
    f = generate()
    print(f"\n{'='*60}")
    print(f"\u5de5\u4f5c\u6d41 3: AI+\u6e38\u620f\u524d\u6cbf\u8d5b\u9053")
    print(f"\u9891\u7387: \u6bcf\u5468")
    print(f"\u4ea7\u51fa: {f}")
    print(f"{'='*60}")
    print("\n\u5173\u6ce8\u7ef4\u5ea6 (MECE):")
    print("  \u2460 AI \u63d0\u6548\u5de5\u5177 - \u7f8e\u672f/\u4ee3\u7801/QA/\u5173\u5361/\u672c\u5730\u5316")
    print("  \u2461 AI NPC - \u5bf9\u8bdd/\u60c5\u611f/\u8bb0\u5fc6/\u884c\u4e3a")
    print("  \u2462 AI \u539f\u751f\u6e38\u620f - \u5168 AI \u751f\u6210/\u65b0\u5f15\u64ce/UGC")
    print("  \u2463 AI+\u521b\u610f\u7ec4\u5408 - \u53d9\u4e8b/\u97f3\u4e50/\u793e\u4ea4/\u786c\u4ef6")
    print("  \u2464 \u884c\u4e1a\u751f\u6001 - \u5e73\u53f0\u7b56\u7565/\u4eba\u624d/\u8d5b\u4e8b")
