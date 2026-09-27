#!/usr/bin/env python3
"""
Sovereign Compute Broker

Routes AI workloads to providers matching sovereignty, budget and risk constraints.

This is a decision helper, not an execution engine.
It does not buy compute or call cloud APIs.
"""

import json
import requests
from typing import Dict, Any, List

LEGION_API = "https://api.legion-api.com"

def safe_get(url: str, timeout: int = 8):
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return {"_error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"_error": type(e).__name__ + ":" + str(e)[:160]}

def extract_candidates() -> List[Dict[str, Any]]:
    """
    Pulls from LEGION public endpoints when available.
    Falls back to conservative static candidates if schema differs.
    """

    candidates = []

    # Try sovereignty endpoint.
    sov = safe_get(f"{LEGION_API}/sovereignty")
    if isinstance(sov, dict):
        rows = sov.get("results") or sov.get("providers") or sov.get("items") or []
        if isinstance(rows, list):
            for r in rows:
                if not isinstance(r, dict):
                    continue
                candidates.append({
                    "provider": r.get("provider") or r.get("name") or "unknown",
                    "region": r.get("region") or r.get("jurisdiction") or "GLOBAL",
                    "jurisdiction": r.get("jurisdiction") or r.get("region") or "GLOBAL",
                    "sovereignty_score": float(r.get("sovereignty_score") or r.get("score") or 50),
                    "raw_price_hr": float(r.get("raw_price_hr") or r.get("price_hr") or r.get("price") or 999),
                    "risk": r.get("risk") or r.get("risk_class") or "unknown",
                    "source": "/sovereignty"
                })

    # Try compute/pricing endpoint.
    comp = safe_get(f"{LEGION_API}/compute")
    if isinstance(comp, dict):
        rows = comp.get("results") or comp.get("providers") or comp.get("items") or []
        if isinstance(rows, list):
            for r in rows:
                if not isinstance(r, dict):
                    continue
                provider = r.get("provider") or r.get("name") or "unknown"
                candidates.append({
                    "provider": provider,
                    "region": r.get("region") or "GLOBAL",
                    "jurisdiction": r.get("jurisdiction") or r.get("region") or "GLOBAL",
                    "sovereignty_score": float(r.get("sovereignty_score") or 50),
                    "raw_price_hr": float(r.get("raw_price_hr") or r.get("price_hr") or r.get("hourly_price") or 999),
                    "risk": r.get("risk") or "unknown",
                    "source": "/compute"
                })

    # Safe fallback; clearly marked.
    if not candidates:
        candidates = [
            {"provider": "ovhcloud", "region": "EU", "jurisdiction": "EU", "sovereignty_score": 78, "raw_price_hr": 1.2, "risk": "medium", "source": "fallback"},
            {"provider": "scaleway", "region": "EU", "jurisdiction": "EU", "sovereignty_score": 74, "raw_price_hr": 1.0, "risk": "medium", "source": "fallback"},
            {"provider": "aws", "region": "US", "jurisdiction": "US", "sovereignty_score": 55, "raw_price_hr": 1.5, "risk": "medium", "source": "fallback"},
            {"provider": "gcp", "region": "GLOBAL", "jurisdiction": "GLOBAL", "sovereignty_score": 58, "raw_price_hr": 1.4, "risk": "medium", "source": "fallback"}
        ]

    # Deduplicate.
    seen = set()
    out = []
    for c in candidates:
        key = (c["provider"], c["region"], c["jurisdiction"])
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out

def route(workload: Dict[str, Any]) -> Dict[str, Any]:
    """
    workload = {
        "sensitivity": "HIGH"|"MEDIUM"|"LOW",
        "jurisdiction_required": "EU"|"US"|"GLOBAL",
        "budget_hr": float,
        "min_sovereignty_score": int
    }
    """
    sensitivity = workload.get("sensitivity", "MEDIUM")
    jurisdiction = workload.get("jurisdiction_required", "GLOBAL")
    budget = float(workload.get("budget_hr", 999))
    min_sov = float(workload.get("min_sovereignty_score", 50))

    candidates = extract_candidates()
    eligible = []
    rejected = []

    for c in candidates:
        reasons = []

        if jurisdiction != "GLOBAL" and c.get("jurisdiction") not in (jurisdiction, "GLOBAL"):
            reasons.append("jurisdiction_mismatch")

        if float(c.get("sovereignty_score", 0)) < min_sov:
            reasons.append("sovereignty_below_min")

        if float(c.get("raw_price_hr", 999)) > budget:
            reasons.append("over_budget")

        if sensitivity == "HIGH" and c.get("risk") in ("high", "avoid"):
            reasons.append("risk_too_high")

        if reasons:
            rejected.append({"candidate": c, "reasons": reasons})
            continue

        decision_score = (
            float(c.get("sovereignty_score", 0))
            - float(c.get("raw_price_hr", 0)) * 10
        )
        eligible.append({**c, "decision_score": round(decision_score, 3)})

    eligible.sort(key=lambda x: x["decision_score"], reverse=True)

    return {
        "status": "ok",
        "workload": workload,
        "recommended": eligible[0] if eligible else None,
        "eligible": eligible,
        "rejected_count": len(rejected),
        "rejected_sample": rejected[:5],
        "method": "filter by jurisdiction, sovereignty score, price, risk; no automatic purchase",
        "limitations": [
            "schema-dependent extraction from LEGION endpoints",
            "fallback candidates are illustrative if API data unavailable",
            "human approval required for procurement"
        ]
    }

if __name__ == "__main__":
    result = route({
        "sensitivity": "HIGH",
        "jurisdiction_required": "EU",
        "budget_hr": 2.0,
        "min_sovereignty_score": 45
    })
    print(json.dumps(result, indent=2, ensure_ascii=False))
