#!/usr/bin/env python3
"""One-time, deterministic migration to the structured homepage v5 contract."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry.json"

LEGACY_BACKFILL = [
    {
        "slug": "texas-industrial-os-20260820",
        "title": "Texas Industrial OS｜为什么得州正在成为 AI、航天与重资本的制度型平台？",
        "date": "2026年8月20日",
        "deck": "从公司法、税制、ERCOT 电力、土地、劳工、产业链与社区许可出发，把 Texas 作为一套把资本转化为物理产能的 Industrial OS 来研究。",
        "tag": "AI Infrastructure · U.S. State Policy · Texas Industrial OS",
        "category": "AI Infrastructure · U.S. State Policy",
        "source": "enya",
        "homepage_approved": True,
        "published_at": "2026-08-20T13:39:00+08:00",
        "layout_id": "kerwin-editorial-research-v1",
        "mobile_qa_version": "1.2.0",
        "desktop_qa_version": "1.0.0",
    },
    {
        "slug": "delaware-vs-texas-corporate-domicile-20260823",
        "title": "Delaware vs Texas｜美国公司法的迁册战争",
        "date": "2026年8月23日",
        "deck": "比较 Delaware 与 Texas 的公司法、专业法院、管理层自主权与少数股东保护，并建立 Governance WACC 与 Total Governance Cost 框架。",
        "tag": "U.S. State Policy · Corporate Domicile · Governance WACC",
        "category": "AI Infrastructure · U.S. State Policy · Corporate Law",
        "source": "enya",
        "homepage_approved": True,
        "published_at": "2026-08-23T13:58:00+08:00",
        "layout_id": "kerwin-editorial-research-v1",
        "mobile_qa_version": "1.2.0",
        "desktop_qa_version": "1.0.0",
    },
    {
        "slug": "us-ai-deployment-map-midterms-20260823",
        "title": "美国50州 AI Deployment Map｜2026中期选举前的算力基础设施地图",
        "date": "2026年8月23日",
        "deck": "以50州统一底表比较党派控制、电力、电网、土地、劳工、水资源、审批与社区许可，建立 Probability-adjusted Energized MW 框架。",
        "tag": "AI Infrastructure · U.S. State Policy · 2026 Midterms",
        "category": "AI Infrastructure · U.S. State Policy · 2026 Midterms",
        "source": "enya",
        "homepage_approved": True,
        "published_at": "2026-08-23T17:55:00+08:00",
        "layout_id": "kerwin-editorial-research-v1",
        "mobile_qa_version": "1.2.0",
        "desktop_qa_version": "1.0.0",
    },
    {
        "slug": "ai-factory-ballot-box-community-roi-20260824",
        "title": "AI Factory Meets the Ballot Box｜谁来为 AI 基础设施付账？",
        "date": "2026年8月24日",
        "deck": "以美国六州案例研究居民电费、水资源、社区收益与地方审批如何进入 Time-to-Power、WACC 与 ROIC。",
        "tag": "AI Infrastructure · Social License · 2026 Midterms",
        "category": "AI Infrastructure · U.S. State Policy · 2026 Midterms",
        "source": "enya",
        "homepage_approved": True,
        "published_at": "2026-08-24T13:19:00+08:00",
        "layout_id": "kerwin-editorial-research-v1",
        "mobile_qa_version": "1.2.0",
        "desktop_qa_version": "1.0.0",
    },
]

SERIES_BY_SLUG = {
    "cloverleaf-powered-land-lps-20260822": ("ai-factory-production-function", "AI Factory生产函数", 1),
    "ai-infrastructure-capital-stack-20260823": ("ai-factory-production-function", "AI Factory生产函数", 2),
    "nvidia-physical-cuda-ai-factory-20260824": ("ai-factory-production-function", "AI Factory生产函数", 3),
    "nvidia-dynamo-kv-cache-context-memory-20260824": ("ai-factory-production-function", "AI Factory生产函数", 4),
    "ai-factory-tokens-per-mw-benchmark-20260824": ("ai-factory-production-function", "AI Factory生产函数", 5),
    "ai-factory-agent-production-function-20260824": ("ai-factory-production-function", "AI Factory生产函数", 6),
    "ai-convertible-financing-capex-20260814": ("ai-financing-structure", "AI融资结构", 1),
    "ai-gpu-asset-financing-20260818": ("ai-financing-structure", "AI融资结构", 2),
    "ai-customer-capital-financing-20260818": ("ai-financing-structure", "AI融资结构", 3),
    "ai-institutional-capital-financing-20260819": ("ai-financing-structure", "AI融资结构", 4),
    "ai-capital-stress-test-20260820": ("ai-financing-structure", "AI融资结构", 5),
    "musk-state-competition-social-license-20260820": ("us-state-competition", "美国州际政策竞争", 1),
    "texas-industrial-os-20260820": ("us-state-competition", "美国州际政策竞争", 2),
    "delaware-vs-texas-corporate-domicile-20260823": ("us-state-competition", "美国州际政策竞争", 3),
    "us-ai-deployment-map-midterms-20260823": ("us-state-competition", "美国州际政策竞争", 4),
    "ai-factory-ballot-box-community-roi-20260824": ("us-state-competition", "美国州际政策竞争", 5),
    "us-ai-execution-capacity-labor-epc-20260824": ("us-state-competition", "美国州际政策竞争", 6),
    "hyperliquid-financial-market-infrastructure-20260718": ("hyperliquid-market-structure", "Hyperliquid市场结构", 1),
    "hyperliquid-series-2-competitive-encirclement-20260719": ("hyperliquid-market-structure", "Hyperliquid市场结构", 2),
    "hyperliquid-weekend-stock-signal-20260803": ("hyperliquid-market-structure", "Hyperliquid市场结构", 3),
    "edge-computing-series": ("nvidia-edge-computing", "NVIDIA Edge Computing", 0),
    "nvidia-edge-autonomous-machines": ("nvidia-edge-computing", "NVIDIA Edge Computing", 2),
    "nvidia-edge-ai-ran-6g": ("nvidia-edge-computing", "NVIDIA Edge Computing", 3),
    "nvidia-edge-vision-ai-video-agent": ("nvidia-edge-computing", "NVIDIA Edge Computing", 4),
    "nvidia-edge-ai-pc-local-agent": ("nvidia-edge-computing", "NVIDIA Edge Computing", 5),
}

AXIS_OVERRIDES = {
    "physical-infrastructure": {
        "us-ai-execution-capacity-labor-epc-20260824",
        "musk-state-competition-social-license-20260820",
        "ai-cloud-unit-economics-dashboard-20260817",
        "ai-supply-chain-power-bottlenecks-20260731",
        "compute-rental-lens-supplement",
        "compute-rental-lens-2026",
        "colossus-compute-revaluation",
        "cloverleaf-powered-land-lps-20260822",
        "texas-industrial-os-20260820",
        "us-ai-deployment-map-midterms-20260823",
        "ai-factory-ballot-box-community-roi-20260824",
    },
    "compute-chain": {
        "nvidia-dynamo-kv-cache-context-memory-20260824",
        "nvidia-physical-cuda-ai-factory-20260824",
        "ai-optical-interconnect-flashlight",
        "ai-full-chain-earnings-20260815",
        "qualcomm-mediatek-ai-native-device-20260812",
        "axti-china-inp-ai-optical-chokepoint-20260810",
        "google-ai-hypercomputer-tpu-virgo-optics-20260723",
        "nokia-q2-2026-earnings-call-20260724",
        "ai-memory-hbm-nand-cmx-20260722",
        "storage-memory-thesis-dashboard-20260720",
        "us-ai-semiconductor-reshoring-memory-fabs-20260717",
        "agent-compute-infrastructure",
        "korea-ai-chip-plan-20260629",
        "ai-optical-interconnect-industry-chain-20260627",
        "nvidia-rubin-five-racks-sive-aaoi",
        "edge-computing-series",
        "nvidia-edge-ai-pc-local-agent",
        "nvidia-edge-vision-ai-video-agent",
        "nvidia-edge-ai-ran-6g",
        "nvidia-edge-autonomous-machines",
        "arm-holdings-fy2026-brief",
        "amd-system-level-turn-20260805",
    },
    "agent-economy": {
        "agent-economy-server-audit-cost-20260825",
        "ai-factory-agent-production-function-20260824",
        "ai-factory-tokens-per-mw-benchmark-20260824",
        "stripe-openrouter-token-new-dollars-20260820",
        "ai-physical-world-infrastructure-stack-20260812",
        "physical-ai-connectivity-tesla-20260812",
        "microsoft-enterprise-ai-barriers-solutions-20260730",
        "openrouter-ai-model-exchange-stripe-20260726",
        "yu-deng-complex-systems-markets-ai-20260724",
        "ineffable-superlearner-rubin-a5x-20260723",
        "google-ai-industry-use-cases-20260723",
        "tesla-q2-2026-earnings-call-20260723",
        "alphabet-q2-2026-earnings-call-20260723",
        "china-open-model-global-token-value-chain-20260722",
        "global-financial-ai-adoption-capex-2026",
        "nvidia-agent-platform-2026",
        "dissect-enya-openclaw-investment-brief",
    },
    "capital-macro": {
        "ai-infrastructure-capital-stack-20260823",
        "ai-capital-stress-test-20260820",
        "ai-institutional-capital-financing-20260819",
        "ai-customer-capital-financing-20260818",
        "ai-gpu-asset-financing-20260818",
        "ai-capital-cycle-after-july-deleveraging-20260817",
        "ai-convertible-financing-capex-20260814",
        "delaware-vs-texas-corporate-domicile-20260823",
        "offshore-trust-tax-china-ipo-20260724",
        "shadow-of-leverage-ai-gold-liquidation-20260724",
        "fed-five-task-forces-20260715",
        "gold-btc-dollar-leash-royalty-streaming-2026",
        "us-estate-tax-hk-investor-guide",
        "anti-corruption-casefiles-2021-2026",
    },
    "frontier-infrastructure": {
        "golden-dome-defense-investment-map-20260815",
        "spacex-vs-rocket-lab-defense-launch-20260815",
        "starlink-hybrid-mobile-network-20260812",
        "future-payment-infrastructure-stablecoin-agentic-commerce-20260809",
        "hyperliquid-weekend-stock-signal-20260803",
        "coinbase-new-positioning-everything-exchange-agentic-finance-20260731",
        "stablecoin-profit-war-dollar-treasury-20260719",
        "hyperliquid-series-2-competitive-encirclement-20260719",
        "hyperliquid-financial-market-infrastructure-20260718",
        "xiaoxiao-block-world",
        "stripe-payment-ecosystem-2026",
        "spcx-review",
        "solar-system-3d-explorer",
        "spacex-new-beginning-20260805",
        "spacex-product-system-20260816",
    },
}

FEATURED = {
    "agent-economy-server-audit-cost-20260825": 1,
    "ai-factory-agent-production-function-20260824": 2,
    "us-ai-execution-capacity-labor-epc-20260824": 3,
}


def axis_for(slug: str) -> str:
    for axis, slugs in AXIS_OVERRIDES.items():
        if slug in slugs:
            return axis
    raise ValueError(f"missing explicit axis mapping for {slug}")


def content_type_for(item: dict) -> str:
    haystack = " ".join(str(item.get(key, "")) for key in ("slug", "title", "tag", "category")).lower()
    if re.search(r"earnings|财报|电话会|业绩会|results call", haystack):
        return "earnings"
    if re.search(r"daily|weekly|tracker|tracking|portfolio|dashboard|看板|跟踪", haystack):
        return "tracker"
    if re.search(r"interactive|explorer|game|游戏|漫游|案件汇编|科普", haystack):
        return "interactive"
    if re.search(r"brief|简报|盲区|第一课", haystack):
        return "brief"
    return "deep-dive"


def homepage_deck(item: dict) -> str:
    text = re.sub(r"\s+", " ", str(item.get("deck", "")).strip())
    if len(text) <= 118:
        return text
    return text[:117].rstrip("，。；、 ") + "…"


def migrate() -> None:
    items = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_slug = {item["slug"]: item for item in items}
    for backfill in LEGACY_BACKFILL:
        by_slug.setdefault(backfill["slug"], backfill)

    migrated = []
    for item in by_slug.values():
        item = dict(item)
        slug = item["slug"]
        item["axis"] = axis_for(slug)
        item["content_type"] = content_type_for(item)
        item["homepage_deck"] = homepage_deck(item)
        item["status"] = "tracking" if item["content_type"] == "tracker" else "evergreen"
        published = item.get("published_at")
        if published:
            when = datetime.fromisoformat(published)
            if when.date().isoformat() >= "2026-08-17":
                item["status"] = "new"
        item["updated_at"] = item.get("updated_at") or published
        item.pop("featured_rank", None)
        if slug in FEATURED:
            item["featured_rank"] = FEATURED[slug]
        if slug in SERIES_BY_SLUG:
            series_id, series_title, series_order = SERIES_BY_SLUG[slug]
            item["series_id"] = series_id
            item["series_title"] = series_title
            item["series_order"] = series_order
        migrated.append(item)

    migrated.sort(key=lambda item: item.get("published_at", ""), reverse=True)
    REGISTRY.write_text(json.dumps(migrated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"migrated homepage registry: {len(migrated)} entries")


if __name__ == "__main__":
    migrate()
