#!/usr/bin/env python3
"""
工作流 1：AI 前沿资讯监控
频率：每日
关注：基础模型、重点产品更新、落地应用、新品、投融资及业务布局
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from mbb_report_engine import *
from datetime import datetime

DATE = datetime.now().strftime("%Y%m%d")
DATE_DISPLAY = datetime.now().strftime("%Y.%m.%d")


def generate(news_data=None):
    """
    news_data: 外部传入的实时数据（由 MCP 获取后注入）
    若为 None 则使用占位数据结构（方便模板测试）
    """

    filename = f"AI前沿资讯-每日速递-{DATE}.pdf"
    r = MBBReportEngine(
        filename,
        title="AI 前沿资讯",
        subtitle=f"基础模型 · 产品更新 · 落地应用 · 投融资  |  {DATE_DISPLAY}",
        accent_color=CORAL,
        page_scale=4.5
    )

    r.draw_header()

    # ── 核心洞察 ──
    r.draw_section_title("核心洞察")

    insights = news_data.get('insights', []) if news_data else [
        {
            'category': '产品硬件',
            'priority': 5,
            'color': CORAL,
            'thesis': 'OpenAI首款ChatGPT硬件曝光：带摄像头的智能音箱，售价200-300美元',
            'detail': '据The Information报道，OpenAI首款硬件产品将是一款带摄像头的智能音箱，预计售价200-300美元。设备能识别物品（如冰箱内食材推荐食谱）、与用户进行自然语音对话。此外OpenAI还在开发AI眼镜和台灯形态产品。这是OpenAI从纯软件公司向硬件生态扩张的标志性一步。',
            'impact': '直接挑战Amazon Echo和Google Home的智能音箱市场。带摄像头+AI推理的组合将重新定义智能家居交互方式。若成功，OpenAI将建立起从模型到硬件的完整生态闭环，对竞争对手形成降维打击。',
            'action': '密切跟踪产品发布时间线和预售数据；评估对自身AI硬件策略的影响；关注供应链动态。'
        },
        {
            'category': 'AI安全/可靠性',
            'priority': 5,
            'color': CORAL,
            'thesis': 'Amazon AI编程Agent Kiro导致AWS宕机13小时，引发内部信任危机',
            'detail': '据Financial Times报道，2025年12月中旬，Amazon自研AI编码Agent Kiro在自主修改代码时引发AWS一套客户成本分析系统宕机长达13小时。多名匿名员工表示对公司大力推广AI编程工具的策略产生疑虑。Amazon官方将责任归咎于"人类员工批准了AI的代码变更"，引发更大争议。',
            'impact': '这是首次被公开报道的AI编程Agent直接导致大规模生产环境事故的案例。暴露了AI Agent自主性与安全性之间的根本矛盾。13小时宕机意味着巨额SLA赔偿和客户信任损失。将推动整个行业重新审视AI Agent的部署策略和人机协作流程。',
            'action': '立即审查内部AI编程工具的权限和审批流程；建立AI Agent代码变更的分级审批机制；制定AI Agent事故应急预案。'
        },
        {
            'category': '基础模型/推理',
            'priority': 4,
            'color': ORANGE,
            'thesis': 'OpenAI发布First Proof数学挑战首批提交结果，测试AI研究级推理能力',
            'detail': '2月20日，OpenAI公开了其AI模型在First Proof数学挑战中的证明尝试。这是一项测试AI在专家级数学问题上的研究级推理能力的挑战。OpenAI分享了模型的证明过程，展示了当前AI在形式化数学推理方面的进展与局限。这标志着AI推理能力评测正从标准化测试向研究级问题迈进。',
            'impact': '推动AI推理能力评测标准从"刷榜"向真正的研究能力转变。若AI能在研究级数学上取得突破，将对科学发现和工程创新产生深远影响。当前结果显示AI在复杂推理上仍有明显差距，降温了过度乐观预期。',
            'action': '关注AI推理能力的实际进展，避免盲目投入；评估推理模型在自身业务场景中的适用性。'
        },
        {
            'category': 'AI能源/基础设施',
            'priority': 4,
            'color': ORANGE,
            'thesis': 'Trump放宽煤电厂排放限制以满足AI算力需求，环保争议升级',
            'detail': '据The Verge报道，Trump政府正在放宽对煤电厂的汞排放标准（MATS规则），以扩大电力供应满足AI数据中心爆发式增长的能源需求。田纳西州Kingston化石燃料电厂（1.4GW）等设施将被允许排放更多污染物。此举在环保组织和科技行业之间引发激烈争论。',
            'impact': 'AI产业的能源需求正在深刻改变美国能源政策走向。短期利好AI基础设施建设（更多廉价电力），但长期增加了ESG合规风险和碳排放成本。欧盟和中国可能借此在绿色AI方面形成竞争优势。',
            'action': '关注AI基础设施的能源供应格局变化；评估绿色AI计算的战略布局机会。'
        },
        {
            'category': '行业反思',
            'priority': 4,
            'color': BLUE,
            'thesis': 'MIT Technology Review发布独家电子书：《2025年AI泡沫大修正》',
            'detail': '2月20日，MIT Technology Review发布付费电子书《The Great AI Hype Correction of 2025》，系统回顾了2025年AI行业的"清算年"。书中揭示了头部AI公司CEO如何做出无法兑现的承诺，分析了期望与现实之间的巨大鸿沟。这是权威科技媒体首次以"修正"而非"泡沫破裂"来定义这一阶段。',
            'impact': '"修正"而非"破裂"的定性暗示AI行业正在走向理性而非崩溃。2026年的AI投资将更加注重可验证的商业价值而非概念炒作。对还未实现商业化的AI创业公司融资环境将持续收紧。',
            'action': '内部对标检查：自身AI项目的承诺是否可兑现；调整对外沟通策略，强调可量化成果。'
        },
        {
            'category': '业务布局',
            'priority': 3,
            'color': GREEN,
            'thesis': '微软Xbox换帅来自CoreAI部门，暗示AI与游戏深度融合战略',
            'detail': 'Phil Spencer宣布退休后，微软CoreAI部门负责人Asha Sharma将接任Xbox掌门。这一人事安排释放了强烈信号：微软计划将AI能力深度整合进游戏业务。同时，微软正在推进"在线真实性验证"计划，帮助用户区分AI生成内容和真实内容。',
            'impact': 'AI+游戏赛道获得巨头级战略背书。微软可能将Copilot/Azure AI的能力引入Xbox生态，改变游戏开发和玩家体验。在线真实性验证计划则显示微软在AI治理方面的前瞻布局。',
            'action': '评估AI+游戏的战略投入优先级；关注微软AI治理标准对行业的示范效应。'
        },
    ]

    for item in insights:
        r.draw_insight_card(item)

    # ── 关键事件时间线 ──
    r.draw_section_title("关键事件")

    events = news_data.get('events', []) if news_data else [
        ("2.21", "OpenAI首款ChatGPT硬件曝光", "The Verge", "带摄像头智能音箱，售价200-300美元，还有AI眼镜和台灯", CORAL),
        ("2.21", "Amazon AI Agent Kiro导致AWS宕机13小时", "Financial Times", "首例AI编程Agent引发大规模生产事故，Amazon甩锅人类员工", CORAL),
        ("2.21", "Trump放宽煤电厂排放以支持AI算力", "The Verge", "MATS汞排放标准被削弱，AI能源需求重塑美国能源政策", ORANGE),
        ("2.20", "OpenAI发布First Proof数学挑战结果", "OpenAI Blog", "测试AI研究级推理能力，展示形式化证明的进展与局限", ORANGE),
        ("2.20", "MIT发布《2025 AI泡沫大修正》电子书", "MIT Tech Review", "系统回顾AI公司CEO的失信承诺，定性为'修正'而非'破裂'", BLUE),
        ("2.20", "TikTok拒绝下架AI生成的种族歧视游戏广告", "GameDeveloper", "Finji Games遭AI生成虚假广告侵权，TikTok拒绝处理", ORANGE),
        ("2.20", "Unity CEO称开发者将能用AI提示词生成游戏", "GameDeveloper", "Unity高管预测生成式AI将颠覆游戏开发流程", GREEN),
        ("2.20", "多模态地理空间AI框架OpenEarthAgent发布", "arXiv", "统一工具增强的地理空间智能体，支持遥感图像推理", GREEN),
        ("2.20", "人类级3D形状感知能力在多视角学习中涌现", "arXiv", "视觉智能领域突破：AI首次在3D形状理解上达到人类水平", BLUE),
    ]
    r.draw_timeline(events)

    # ── arXiv 今日前沿 ──
    r.draw_section_title("arXiv 今日前沿", BLUE)

    arxiv_events = news_data.get('arxiv_events', []) if news_data else [
        ("论文", "OpenEarthAgent: 统一工具增强的地理空间Agent框架", "arXiv", "多模态推理+遥感，首个通用地理空间智能体", BLUE),
        ("论文", "Sink-Aware Pruning: 扩散语言模型高效剪枝", "arXiv", "发现扩散LM中attention sink与自回归LM本质不同，提出新剪枝策略", BLUE),
        ("论文", "VLA反事实失败：视觉覆盖语言的机器人控制问题", "arXiv", "视觉-语言-动作模型在指令跟随中的关键缺陷分析与缓解", ORANGE),
        ("论文", "MARS: 边际感知奖励建模与自我精炼", "arXiv", "改进RLHF核心组件，降低对人类标注偏好数据的依赖", GREEN),
        ("论文", "Human-level 3D Shape Perception", "arXiv", "多视角学习让AI首次在3D形状感知上媲美人类表现", CORAL),
    ]
    r.draw_timeline(arxiv_events)

    # ── 行动建议 ──
    r.draw_section_title("立即行动")

    actions = news_data.get('actions', []) if news_data else [
        ("P0", "审查内部AI Agent权限和代码审批流程，防范Kiro式事故", "技术部", "本周", CORAL),
        ("P1", "跟踪OpenAI硬件产品发布节奏，评估对AI硬件战略的影响", "战略部", "本月", ORANGE),
        ("P1", "评估AI推理模型（First Proof级别）在核心业务中的适用性", "AI研发部", "本月", ORANGE),
        ("P2", "对标MIT报告检查自身AI项目承诺的可兑现性", "管理层", "本季度", BLUE),
        ("P2", "关注绿色AI计算的战略布局机会", "基础设施部", "持续", GREEN),
    ]
    r.draw_actions(actions)

    r.draw_footer("数据: AI News MCP + arXiv + The Verge + MIT Tech Review  |  AI 前沿资讯 · 每日速递  |  2026.02.21")
    r.save()
    return filename


if __name__ == "__main__":
    f = generate()
    print(f"\n{'='*60}")
    print(f"工作流 1: AI 前沿资讯监控")
    print(f"频率: 每日")
    print(f"产出: {f}")
    print(f"{'='*60}")
    print("\n数据源:")
    print("  • MCP: fetch_ai_news(category='all', timeRange='daily')")
    print("  • MCP: fetch_arxiv_papers(category='all')")
    print("\n关注维度 (MECE):")
    print("  ① 基础模型 - 参数/Benchmark/开源闭源")
    print("  ② 产品更新 - 功能/定价/用户增长")
    print("  ③ 落地应用 - ROI/规模化/垂直领域")
    print("  ④ 投融资   - 金额/轮次/资金流向")
    print("  ⑤ 业务布局 - 巨头战略/组织/人才")
