#!/usr/bin/env python3
"""每日羊毛 - 数据管道

封装「薅羊毛助手」技能脚本，抓取数据并生成 src/data/YYYY-MM-DD.json。

用法：
    python3 scripts/fetch_data.py              # 抓今日数据（真实 API）
    python3 scripts/fetch_data.py --demo       # 生成示例数据（Token 未配时用）
    python3 scripts/fetch_data.py --date 2026-09-14 --demo

数据来源：
    - 羊毛福利流：wool-hunter/scripts/call_bot.py（Coze API，需 COZE_TOKEN）
    - 电商券搜索：wool-hunter/scripts/search.py（需 ~/.coupon_search_config.json）

注意：本脚本只在本地/CI 跑，产出的 JSON 才会进仓库；脚本本身不携带任何 Token。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data"
WOOL_HUNTER = Path.home() / ".workbuddy" / "skills" / "wool-hunter__skillhub" / "scripts"

# 热词榜：每日预搜的电商关键词（可按季节/热点调整）
HOT_KEYWORDS = ["纸巾", "洗衣液", "手机壳", "零食", "牛奶"]

CATEGORIES = ["电商券", "外卖红包", "签到福利", "白嫖活动"]


def config_ready() -> bool:
    """检查薅羊毛助手配置是否就绪。"""
    return (Path.home() / ".coupon_search_config.json").exists() and bool(
        os.environ.get("COZE_TOKEN")
    )


def run_wool_query(query: str) -> str:
    """调用羊毛福利查询（call_bot.py），返回原始文本。"""
    result = subprocess.run(
        [sys.executable, str(WOOL_HUNTER / "call_bot.py"), query],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"call_bot.py 失败: {result.stderr[:200]}")
    return result.stdout


def parse_items(raw_text: str, category: str) -> list[dict]:
    """把羊毛助手的文本结果解析为标准条目。

    TODO(S2 联调): 真实 API 的返回格式确认后补全解析逻辑。
    当前按行解析，含链接的行提取为条目。
    """
    items = []
    for i, line in enumerate(raw_text.splitlines()):
        line = line.strip()
        if not line or len(line) < 6:
            continue
        link = ""
        for token in line.split():
            if token.startswith("http"):
                link = token
                break
        items.append(
            {
                "id": f"{category}-{i:03d}",
                "title": line[:60],
                "category": category,
                "platform": "",
                "summary": line,
                "link": link,
                "coupon": "",
                "originalPrice": None,
                "finalPrice": None,
                "expireAt": "",
                "isHot": False,
            }
        )
    return items


def fetch_real(target: date) -> dict:
    """真实抓取：羊毛福利流 + 热词电商券。"""
    items: list[dict] = []
    for query, category in [
        ("今日外卖红包 美团 饿了么", "外卖红包"),
        ("今日签到福利 白嫖活动", "签到福利"),
    ]:
        try:
            items.extend(parse_items(run_wool_query(query), category))
        except Exception as exc:  # 单源失败不阻塞整体
            print(f"[warn] {category} 抓取失败: {exc}", file=sys.stderr)
    # TODO(S2 联调): search.py 热词预搜接入（SSE 流式，需 uv 环境）
    return {"date": target.isoformat(), "items": items}


def fetch_demo(target: date) -> dict:
    """示例数据：结构与真实数据一致，供 P0 页面开发用。"""
    d = target.isoformat()
    items = [
        {
            "id": "waimai-001",
            "title": "美团外卖 天天神券 25-8",
            "category": "外卖红包",
            "platform": "美团",
            "summary": "每日可领，满25减8，全国通用，限外卖频道使用。",
            "link": "https://example.com/meituan-25-8",
            "coupon": "8元券",
            "originalPrice": None,
            "finalPrice": None,
            "expireAt": f"{d} 23:59",
            "isHot": True,
        },
        {
            "id": "waimai-002",
            "title": "饿了么 爆红包 30-10",
            "category": "外卖红包",
            "platform": "饿了么",
            "summary": "整点抢，满30减10，部分城市可用。",
            "link": "https://example.com/eleme-30-10",
            "coupon": "10元券",
            "originalPrice": None,
            "finalPrice": None,
            "expireAt": f"{d} 23:59",
            "isHot": False,
        },
        {
            "id": "ds-001",
            "title": "抽纸整箱 24包 多平台比价",
            "category": "电商券",
            "platform": "拼多多",
            "summary": "拼多多百亿补贴最低，叠加5元券到手24.9。",
            "link": "https://example.com/pdd-tissue",
            "coupon": "5元券",
            "originalPrice": 39.9,
            "finalPrice": 24.9,
            "expireAt": "",
            "isHot": True,
        },
        {
            "id": "ds-002",
            "title": "抽纸整箱 24包",
            "category": "电商券",
            "platform": "淘宝",
            "summary": "淘宝同款，店铺券后29.9。",
            "link": "https://example.com/taobao-tissue",
            "coupon": "10元券",
            "originalPrice": 39.9,
            "finalPrice": 29.9,
            "expireAt": "",
            "isHot": False,
        },
        {
            "id": "ds-003",
            "title": "蓝月亮洗衣液 3kg 瓶装",
            "category": "电商券",
            "platform": "京东",
            "summary": "京东自营，PLUS券后33.9，次日达。",
            "link": "https://example.com/jd-laundry",
            "coupon": "6元券",
            "originalPrice": 39.9,
            "finalPrice": 33.9,
            "expireAt": "",
            "isHot": False,
        },
        {
            "id": "qd-001",
            "title": "支付宝 签到领现金 连签7天翻倍",
            "category": "签到福利",
            "platform": "支付宝",
            "summary": "首页搜「签到」，每日0.1-1元，连签7天额外奖励。",
            "link": "https://example.com/alipay-checkin",
            "coupon": "",
            "originalPrice": None,
            "finalPrice": None,
            "expireAt": "",
            "isHot": False,
        },
        {
            "id": "qd-002",
            "title": "淘宝 芭芭农场 浇水领水果",
            "category": "签到福利",
            "platform": "淘宝",
            "summary": "每日浇水，约15天可兑一箱水果包邮。",
            "link": "https://example.com/babafarm",
            "coupon": "",
            "originalPrice": None,
            "finalPrice": None,
            "expireAt": "",
            "isHot": False,
        },
        {
            "id": "bp-001",
            "title": "腾讯视频 会员日 免费领3天VIP",
            "category": "白嫖活动",
            "platform": "腾讯视频",
            "summary": "每月18日会员日，参与活动免费领3天VIP。",
            "link": "https://example.com/qqvideo-vip",
            "coupon": "",
            "originalPrice": None,
            "finalPrice": None,
            "expireAt": f"{d} 23:59",
            "isHot": True,
        },
        {
            "id": "bp-002",
            "title": "网易云音乐 听歌打卡 兑黑胶周卡",
            "category": "白嫖活动",
            "platform": "网易云音乐",
            "summary": "连续打卡7天可兑黑胶VIP周卡。",
            "link": "https://example.com/netease-vip",
            "coupon": "",
            "originalPrice": None,
            "finalPrice": None,
            "expireAt": "",
            "isHot": False,
        },
    ]
    return {"date": d, "items": items}


def main() -> None:
    parser = argparse.ArgumentParser(description="每日羊毛数据管道")
    parser.add_argument("--demo", action="store_true", help="生成示例数据")
    parser.add_argument("--date", default=date.today().isoformat(), help="目标日期 YYYY-MM-DD")
    args = parser.parse_args()

    target = date.fromisoformat(args.date)
    if args.demo:
        payload = fetch_demo(target)
    else:
        if not config_ready():
            sys.exit(
                "错误：薅羊毛助手未配置（缺 ~/.coupon_search_config.json 或 COZE_TOKEN）。\n"
                "配置前请使用 --demo 生成示例数据。"
            )
        payload = fetch_real(target)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / f"{target.isoformat()}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {out}（{len(payload['items'])} 条）")


if __name__ == "__main__":
    main()
