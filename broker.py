#!/usr/bin/env python3
"""Sovereign Compute Broker — LEGION.
Measured legs: risk composite (matrix.db, 13801 incidents).
Estimated legs: sov_score, est_cost_hr (declared per veritas policy)."""
import json, sqlite3
from pathlib import Path

MATRIX = Path("/mnt/legion/agents/agent-risk-matrix/matrix.db")
PROVIDERS = [
    {"provider":"mistral",   "hq":"EU", "sov_score":72, "est_cost_hr":0.9},
    {"provider":"cohere",    "hq":"CA", "sov_score":58, "est_cost_hr":0.8},
    {"provider":"groq",      "hq":"US", "sov_score":41, "est_cost_hr":0.4},
    {"provider":"openai",    "hq":"US", "sov_score":38, "est_cost_hr":1.4},
    {"provider":"anthropic", "hq":"US", "sov_score":38, "est_cost_hr":1.3},
    {"provider":"google",    "hq":"US", "sov_score":36, "est_cost_hr":1.1},
    {"provider":"meta",      "hq":"US", "sov_score":35, "est_cost_hr":0.3},
]
JUR = {"EU":{"EU"}, "US":{"US"}, "GLOBAL":{"EU","US","CA"}}

def route(workload):
    jur = workload.get("jurisdiction_required","GLOBAL")
    budget = float(workload.get("budget_hr", 99))
    min_sov = float(workload.get("min_sovereignty_score", 0))
    risks = {}
    if MATRIX.exists():
        with sqlite3.connect(MATRIX) as c:
            for p, s in c.execute("SELECT provider, composite_risk_score FROM composite_exposure"):
                risks[p] = s
    cands = []
    for p in PROVIDERS:
        if p["hq"] not in JUR.get(jur, {"EU","US","CA"}): continue
        if p["sov_score"] < min_sov: continue
        if p["est_cost_hr"] > budget: continue
        risk = risks.get(p["provider"], 50.0)
        cands.append({**p, "risk_composite_measured": risk,
                      "routing_score": round(100 - risk*0.6 - p["est_cost_hr"]*10 + p["sov_score"]*0.2, 2)})
    cands.sort(key=lambda c: -c["routing_score"])
    return {"workload": workload, "recommended": cands[0] if cands else None,
            "alternatives": cands[1:], "candidates_after_filters": len(cands),
            "measured_legs": ["risk_composite"], "estimated_legs": ["sov_score","est_cost_hr"]}

if __name__ == "__main__":
    import sys
    wl = json.loads(sys.argv[1]) if len(sys.argv)>1 else {"sensitivity":"HIGH","jurisdiction_required":"EU","budget_hr":2.0,"min_sovereignty_score":45}
    print(json.dumps(route(wl), indent=2))
