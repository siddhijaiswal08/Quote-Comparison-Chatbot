# core/scoring.py
from typing import Dict, List
import pandas as pd
from .models import Quote

def expected_cost(q: Quote, expected_claims: int, avg_claim_amount: float) -> float:
    premium = q.premium or 0.0
    deductible = q.deductible or 0.0
    coins = q.coinsurance or 0.0
    oop = q.out_of_pocket_max or (deductible + coins * avg_claim_amount)
    per_claim = deductible + coins * max(0.0, avg_claim_amount - deductible)
    return premium + min(expected_claims * per_claim, oop)

def score_quotes(quotes: List[Quote], expected_claims: int, avg_claim_amount: float,
                 weights: Dict[str, float] | None = None) -> pd.DataFrame:
    if weights is None:
        weights = {"cost": 0.6, "coverage": 0.3, "network": 0.1}

    max_network = max([q.network_size or 0 for q in quotes]) or 1
    max_coverage = max([(q.coverage_limit or 0) + (q.annual_benefit_max or 0) for q in quotes]) or 1

    rows = []
    for q in quotes:
        exp_cost = expected_cost(q, expected_claims, avg_claim_amount)
        cost_score = 1 / (1 + exp_cost / 100000)
        coverage_score = ((q.coverage_limit or q.annual_benefit_max or 0) / max_coverage)
        network_score = (q.network_size or 0) / max_network

        composite = (weights["cost"] * cost_score +
                     weights["coverage"] * coverage_score +
                     weights["network"] * network_score)

        rows.append({
            "plan_name": q.plan_name,
            "expected_annual_cost": round(exp_cost, 2),
            "cost_score": round(cost_score, 3),
            "coverage_score": round(coverage_score, 3),
            "network_score": round(network_score, 3),
            "composite_score": round(composite, 3),
            "premium": q.premium,
            "deductible": q.deductible,
            "coinsurance": q.coinsurance,
            "out_of_pocket_max": q.out_of_pocket_max,
            "coverage_limit": q.coverage_limit,
            "annual_benefit_max": q.annual_benefit_max,
            "network_size": q.network_size,
        })

    df = pd.DataFrame(rows)
    return df.sort_values(by="composite_score", ascending=False)
