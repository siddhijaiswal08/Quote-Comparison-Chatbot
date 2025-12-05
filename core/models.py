from dataclasses import dataclass
from typing import Optional

@dataclass
class Quote:
    """Represents one insurance quote entry."""
    plan_name: str
    premium: float                  # annual premium
    deductible: float               # annual deductible
    coinsurance: float              # fraction (0.2 = 20%)
    out_of_pocket_max: float        # max annual OOP
    coverage_limit: Optional[float] = None
    annual_benefit_max: Optional[float] = None
    network_size: Optional[float] = None
