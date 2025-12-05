# core/parser.py
import io
import json
from typing import List
import pandas as pd
from .models import Quote

RENAME_MAP = {
    'plan_name': 'plan_name', 'plan': 'plan_name', 'name': 'plan_name',
    'premium': 'premium', 'annual_premium': 'premium',
    'deductible': 'deductible',
    'coinsurance': 'coinsurance', 'coin': 'coinsurance',
    'oop_max': 'out_of_pocket_max', 'out_of_pocket_max': 'out_of_pocket_max',
    'coverage_limit': 'coverage_limit', 'sum_insured': 'coverage_limit',
    'annual_benefit_max': 'annual_benefit_max',
    'network_size': 'network_size', 'network': 'network_size'
}

def _safe_float(x, default=0.0):
    try:
        if pd.isna(x) or x is None or x == "":
            return default
        return float(str(x).replace(",", ""))
    except Exception:
        return default

def read_quotes_from_df(df: pd.DataFrame) -> List[Quote]:
    df = df.rename(columns={c: RENAME_MAP.get(c.lower().strip(), c) for c in df.columns})
    quotes = []
    for _, row in df.iterrows():
        quotes.append(Quote(
            plan_name=str(row.get('plan_name', f"Plan {_+1}")),
            premium=_safe_float(row.get('premium')),
            deductible=_safe_float(row.get('deductible')),
            coinsurance=_safe_float(row.get('coinsurance'), 0.2),
            out_of_pocket_max=_safe_float(row.get('out_of_pocket_max')),
            coverage_limit=_safe_float(row.get('coverage_limit'), None),
            annual_benefit_max=_safe_float(row.get('annual_benefit_max'), None),
            network_size=_safe_float(row.get('network_size'), None),
        ))
    return quotes

def read_uploaded_file(uploaded_file) -> List[Quote]:
    name = uploaded_file.name.lower()
    if name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif name.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(uploaded_file)
    elif name.endswith('.json'):
        data = json.load(io.StringIO(uploaded_file.getvalue().decode('utf-8')))
        df = pd.DataFrame(data if isinstance(data, list) else [data])
    else:
        raise ValueError("Unsupported file format.")
    return read_quotes_from_df(df)
