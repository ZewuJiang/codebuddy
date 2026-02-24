#!/usr/bin/env python3
"""
四大工作流统一调度入口
用法:
  python3 run_all.py           # 运行所有每日工作流
  python3 run_all.py 1         # 仅运行工作流 1
  python3 run_all.py 1 2 4     # 运行工作流 1、2、4
  python3 run_all.py weekly    # 运行所有每周工作流
"""
import sys
import os
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import wf1_ai_frontier
import wf2_gaming_industry
import wf3_ai_gaming
import wf4_market_monitor
import wf5_game_ops_monitor
import wf6_investment_agent

DAILY_WORKFLOWS = {
    '1': ('AI 前沿资讯', wf1_ai_frontier),
    '2': ('游戏行业监控', wf2_gaming_industry),
    '4': ('二级市场监控', wf4_market_monitor),
    '6': ('投资Agent', wf6_investment_agent),
}

WEEKLY_WORKFLOWS = {
    '3': ('AI+游戏前沿', wf3_ai_gaming),
    '5': ('游戏竞品运营监控', wf5_game_ops_monitor),
}


def run_workflows(ids):
    print("=" * 60)
    print(f"  MBB 工作流调度器  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    results = []
    all_wf = {**DAILY_WORKFLOWS, **WEEKLY_WORKFLOWS}

    for wf_id in ids:
        if wf_id not in all_wf:
            print(f"\n⚠️  未知工作流 ID: {wf_id}")
            continue

        name, module = all_wf[wf_id]
        print(f"\n{'─'*60}")
        print(f"▶ 启动工作流 {wf_id}: {name}")
        print(f"{'─'*60}")

        try:
            filename = module.generate()
            results.append((wf_id, name, filename, "✅"))
        except Exception as e:
            print(f"❌ 工作流 {wf_id} 失败: {e}")
            results.append((wf_id, name, str(e), "❌"))

    # 汇总
    print(f"\n{'='*60}")
    print("  执行汇总")
    print(f"{'='*60}")
    for wf_id, name, filename, status in results:
        print(f"  {status}  工作流 {wf_id}: {name}")
        print(f"      → {filename}")
    print(f"\n{'='*60}")
    print(f"  完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        # 默认运行所有每日工作流
        run_workflows(['1', '2', '4', '6'])
    elif args[0] == 'weekly':
        run_workflows(['3', '5'])
    elif args[0] == 'all':
        run_workflows(['1', '2', '3', '4', '5', '6'])
    else:
        run_workflows(args)
