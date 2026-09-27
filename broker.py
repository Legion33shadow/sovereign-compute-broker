#!/usr/bin/env python3
"""
Sovereign Compute Broker
Routes AI workloads to providers matching sovereignty requirements.
"""
import requests, json

def route(workload: dict) -> dict:
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
    budget = workload.get("budget_hr", 1.0)
    min_sov = workload.get("min_sovereignty_score", 50)
    
    # Get risk-adjusted prices
    r = requests.get(f"https://api.legion-api.com/risk-price?limit=20", timeout=10)
    candidates = r.json().get("results", [])
    
    # Get sovereignty scores
    sov = requests.get("https://api.legion-api.com/sovereignty", timeout=10).json().get("results", [])
    sov_map = {s["country"]: s["score"] for s in sov}
    
    # Filter + rank
    PROVIDER_COUNTRY = {"openai":"US","anthropic":"US","google":"US","groq":"US","mistral":"FR","cohere":"CA"}
    
    filtered = []
    for c in candidates:
        prov = c["provider"].lower()
        country = PROVIDER_COUNTRY.get(prov, "US")
        sov_score = sov_map.get(country, 50)
        if sov_score < min_sov: continue
        if jurisdiction == "EU" and country not in ["FR","DE","GB","NL"]: continue
        if c["raw_price_hr"] > budget: continue
        filtered.append({**c, "country": country, "sovereignty_score": sov_score})
    
    if not filtered:
        return {"route": "NO_MATCH", "reason": "No provider meets all requirements"}
    
    best = sorted(filtered, key=lambda x: (-x["sovereignty_score"], x["adjusted_price"]))[0]
    return {"route": "PROCEED", "provider": best["provider"], "model": best["model"],
            "price": best["adjusted_price"], "sovereignty": best["sovereignty_score"],
            "country": best["country"]}

if __name__ == "__main__":
    result = route({"sensitivity":"HIGH","jurisdiction_required":"EU","budget_hr":2.0,"min_sovereignty_score":45})
    print(json.dumps(result, indent=2))
