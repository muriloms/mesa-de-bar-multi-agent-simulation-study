"""Cálculo de custos de uma sessão a partir do llm_calls.jsonl.

Lê pricing.yaml dinamicamente — sem cache, sempre fresco. Permite
editar o yaml sem reiniciar.
"""
from typing import Any, Dict
from collections import defaultdict
import yaml

from core import config
from persistence import llm_log


def _load_pricing() -> dict:
    if not config.PRICING_FILE.exists():
        return {"_default": {"in": 1.0, "out": 3.0}}
    try:
        return yaml.safe_load(config.PRICING_FILE.read_text(encoding="utf-8")) or {}
    except Exception:
        return {"_default": {"in": 1.0, "out": 3.0}}


def _price_for(pricing: dict, provider: str, model: str) -> dict:
    """Devolve {in, out} em USD/1M tokens. Cai pra _default se não achar."""
    by_provider = pricing.get(provider, {})
    if isinstance(by_provider, dict) and model in by_provider:
        entry = by_provider[model]
        if isinstance(entry, dict):
            return {"in": float(entry.get("in", 0)), "out": float(entry.get("out", 0))}
    fallback = pricing.get("_default", {"in": 1.0, "out": 3.0})
    return {"in": float(fallback.get("in", 1.0)), "out": float(fallback.get("out", 3.0))}


def compute_session_costs(session_id: str) -> Dict[str, Any]:
    """Lê llm_calls.jsonl e devolve breakdown completo."""
    pricing = _load_pricing()
    calls = list(llm_log.read_all(session_id))

    if not calls:
        return {
            "session_id": session_id,
            "total": {"calls": 0, "tokens_in": 0, "tokens_out": 0,
                      "cost_usd": 0.0, "cost_in": 0.0, "cost_out": 0.0,
                      "avg_latency_ms": 0, "median_latency_ms": 0},
            "by_actor": {}, "by_model": {}, "by_prompt": {}, "recent": [],
            "pricing_loaded": bool(pricing),
        }

    by_actor = defaultdict(lambda: {"calls": 0, "tokens_in": 0, "tokens_out": 0,
                                    "cost_in": 0.0, "cost_out": 0.0, "cost_usd": 0.0})
    by_model = defaultdict(lambda: {"calls": 0, "tokens_in": 0, "tokens_out": 0,
                                    "cost_in": 0.0, "cost_out": 0.0, "cost_usd": 0.0,
                                    "provider": ""})
    by_prompt = defaultdict(lambda: {"calls": 0, "tokens_in": 0, "tokens_out": 0,
                                     "cost_usd": 0.0})

    total = {"calls": 0, "tokens_in": 0, "tokens_out": 0,
             "cost_in": 0.0, "cost_out": 0.0, "cost_usd": 0.0}
    latencies = []

    for c in calls:
        provider = c.provider
        model = c.model
        tin = c.tokens.get("in", 0)
        tout = c.tokens.get("out", 0)
        prc = _price_for(pricing, provider, model)
        cin = (tin / 1_000_000.0) * prc["in"]
        cout = (tout / 1_000_000.0) * prc["out"]
        ctotal = cin + cout

        actor = c.context.actor_role or "unknown"
        actor_id = c.context.actor_id or actor
        actor_key = f"{actor}:{actor_id}" if actor != actor_id else actor

        for bucket, key in [(by_actor, actor_key), (by_model, f"{provider}/{model}"),
                            (by_prompt, c.prompt_id)]:
            bucket[key]["calls"] += 1
            bucket[key]["tokens_in"] += tin
            bucket[key]["tokens_out"] += tout
            bucket[key]["cost_usd"] += ctotal
            if "cost_in" in bucket[key]:
                bucket[key]["cost_in"] += cin
                bucket[key]["cost_out"] += cout
        by_model[f"{provider}/{model}"]["provider"] = provider

        total["calls"] += 1
        total["tokens_in"] += tin
        total["tokens_out"] += tout
        total["cost_in"] += cin
        total["cost_out"] += cout
        total["cost_usd"] += ctotal

        if c.latency_ms is not None:
            latencies.append(c.latency_ms)

    if latencies:
        latencies.sort()
        total["avg_latency_ms"] = int(sum(latencies) / len(latencies))
        total["median_latency_ms"] = int(latencies[len(latencies) // 2])
    else:
        total["avg_latency_ms"] = 0
        total["median_latency_ms"] = 0

    # Lista as últimas 20 chamadas
    recent = []
    for c in calls[-20:]:
        prc = _price_for(pricing, c.provider, c.model)
        tin = c.tokens.get("in", 0)
        tout = c.tokens.get("out", 0)
        cost = (tin / 1e6) * prc["in"] + (tout / 1e6) * prc["out"]
        recent.append({
            "call_id": c.call_id,
            "timestamp": c.timestamp,
            "prompt_id": c.prompt_id,
            "actor": c.context.actor_role,
            "actor_id": c.context.actor_id,
            "round": c.context.round,
            "phase": c.context.phase,
            "provider": c.provider,
            "model": c.model,
            "tokens_in": tin,
            "tokens_out": tout,
            "cost_usd": round(cost, 6),
            "latency_ms": c.latency_ms,
            "parse_status": c.parse_status,
        })

    return {
        "session_id": session_id,
        "total": total,
        "by_actor": dict(by_actor),
        "by_model": dict(by_model),
        "by_prompt": dict(by_prompt),
        "recent": recent,
        "pricing_loaded": bool(pricing),
    }
