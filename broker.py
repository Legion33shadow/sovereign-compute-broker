#!/usr/bin/env python3
"""
Sovereign Compute Broker (Operational v2)
Routes AI workloads based on strict geopolitical sovereignty and pricing.
"""
import sys
import json

def route(workload: dict) -> dict:
    # Simuler les providers disponibles issus du pricing-matrix et sovereignty-index de LEGION
    providers = [
        {"name": "openai", "jurisdiction": "US", "price_per_m_tokens": 0.0025, "sovereignty_score": 40},
        {"name": "google", "jurisdiction": "US", "price_per_m_tokens": 0.00375, "sovereignty_score": 40},
        {"name": "mistral", "jurisdiction": "EU", "price_per_m_tokens": 0.0015, "sovereignty_score": 85},
        {"name": "cohere", "jurisdiction": "CA", "price_per_m_tokens": 0.0015, "sovereignty_score": 75},
        {"name": "cyprus-edge", "jurisdiction": "CY", "price_per_m_tokens": 0.0010, "sovereignty_score": 95}
    ]
    
    sensitivity = workload.get("sensitivity", "MEDIUM")
    jurisdiction = workload.get("jurisdiction_required", "GLOBAL")
    budget = workload.get("budget_per_m_tokens", 0.005)
    min_sov = workload.get("min_sovereignty_score", 50)
    
    candidates = []
    for p in providers:
        if jurisdiction != "GLOBAL" and p["jurisdiction"] != jurisdiction:
            continue
        if p["price_per_m_tokens"] > budget:
            continue
        if p["sovereignty_score"] < min_sov:
            continue
        candidates.append(p)
        
    candidates.sort(key=lambda x: (-x["sovereignty_score"], x["price_per_m_tokens"]))
    
    if not candidates:
        return {"status": "REJECTED", "reason": "No provider matches sovereignty/budget constraints."}
    
    return {
        "status": "ROUTED",
        "selected_provider": candidates[0]["name"],
        "jurisdiction": candidates[0]["jurisdiction"],
        "cost_per_m_tokens": candidates[0]["price_per_m_tokens"],
        "sovereignty_score": candidates[0]["sovereignty_score"]
    }

if __name__ == "__main__":
    sample = {"sensitivity": "HIGH", "jurisdiction_required": "EU", "budget_per_m_tokens": 0.002, "min_sovereignty_score": 80}
    print(json.dumps(route(sample), indent=2))
