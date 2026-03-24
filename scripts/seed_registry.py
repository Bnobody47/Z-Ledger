"""
Seed applicant_registry with sample companies for testing.
Run: python scripts/seed_registry.py [--db-url postgresql://...]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


SAMPLE_COMPANIES = [
    {
        "company_id": "COMP-001",
        "name": "Acme Corp",
        "industry": "technology",
        "naics": "541512",
        "jurisdiction": "CA",
        "legal_type": "LLC",
        "founded_year": 2018,
        "employee_count": 45,
        "ein": "12-3456789",
        "address_city": "San Francisco",
        "address_state": "CA",
        "relationship_start": "2022-01-15",
        "account_manager": "Jane Smith",
        "risk_segment": "MEDIUM",
        "trajectory": "STABLE",
        "submission_channel": "api",
        "ip_region": "US-WEST",
    },
    {
        "company_id": "COMP-002",
        "name": "Beta Industries",
        "industry": "manufacturing",
        "naics": "333120",
        "jurisdiction": "TX",
        "legal_type": "Corp",
        "founded_year": 2015,
        "employee_count": 120,
        "ein": "98-7654321",
        "address_city": "Houston",
        "address_state": "TX",
        "relationship_start": "2020-06-01",
        "account_manager": "John Doe",
        "risk_segment": "LOW",
        "trajectory": "GROWING",
        "submission_channel": "portal",
        "ip_region": "US-SOUTH",
    },
]

SAMPLE_FINANCIALS = [
    {
        "company_id": "COMP-001",
        "fiscal_year": 2024,
        "total_revenue": 2_500_000,
        "gross_profit": 1_250_000,
        "operating_expenses": 800_000,
        "operating_income": 450_000,
        "ebitda": 500_000,
        "depreciation_amortization": 50_000,
        "interest_expense": 30_000,
        "income_before_tax": 420_000,
        "tax_expense": 100_000,
        "net_income": 320_000,
        "total_assets": 3_000_000,
        "current_assets": 1_200_000,
        "cash_and_equivalents": 400_000,
        "accounts_receivable": 500_000,
        "inventory": 300_000,
        "total_liabilities": 1_500_000,
        "current_liabilities": 600_000,
        "long_term_debt": 900_000,
        "total_equity": 1_500_000,
        "operating_cash_flow": 400_000,
        "investing_cash_flow": -100_000,
        "financing_cash_flow": -50_000,
        "free_cash_flow": 350_000,
        "debt_to_equity": 0.6,
        "current_ratio": 2.0,
        "debt_to_ebitda": 1.8,
        "interest_coverage_ratio": 16.7,
        "gross_margin": 0.5,
        "ebitda_margin": 0.2,
        "net_margin": 0.13,
        "balance_sheet_check": True,
    },
    {
        "company_id": "COMP-002",
        "fiscal_year": 2024,
        "total_revenue": 8_000_000,
        "gross_profit": 3_200_000,
        "operating_expenses": 2_000_000,
        "operating_income": 1_200_000,
        "ebitda": 1_350_000,
        "depreciation_amortization": 150_000,
        "interest_expense": 80_000,
        "income_before_tax": 1_120_000,
        "tax_expense": 280_000,
        "net_income": 840_000,
        "total_assets": 6_000_000,
        "current_assets": 2_500_000,
        "cash_and_equivalents": 800_000,
        "accounts_receivable": 1_000_000,
        "inventory": 700_000,
        "total_liabilities": 2_500_000,
        "current_liabilities": 1_000_000,
        "long_term_debt": 1_500_000,
        "total_equity": 3_500_000,
        "operating_cash_flow": 1_100_000,
        "investing_cash_flow": -200_000,
        "financing_cash_flow": -100_000,
        "free_cash_flow": 900_000,
        "debt_to_equity": 0.43,
        "current_ratio": 2.5,
        "debt_to_ebitda": 1.1,
        "interest_coverage_ratio": 16.9,
        "gross_margin": 0.4,
        "ebitda_margin": 0.17,
        "net_margin": 0.105,
        "balance_sheet_check": True,
    },
]


async def seed(db_url: str):
    import asyncpg

    conn = await asyncpg.connect(db_url)
    try:
        for c in SAMPLE_COMPANIES:
            await conn.execute(
                """INSERT INTO applicant_registry.companies
                (company_id, name, industry, naics, jurisdiction, legal_type, founded_year,
                 employee_count, ein, address_city, address_state, relationship_start,
                 account_manager, risk_segment, trajectory, submission_channel, ip_region)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
                ON CONFLICT(company_id) DO NOTHING""",
                c["company_id"], c["name"], c["industry"], c["naics"], c["jurisdiction"],
                c["legal_type"], c["founded_year"], c["employee_count"], c["ein"],
                c["address_city"], c["address_state"],
                date.fromisoformat(c["relationship_start"]), c["account_manager"],
                c["risk_segment"], c["trajectory"], c["submission_channel"], c["ip_region"],
            )
        for f in SAMPLE_FINANCIALS:
            await conn.execute(
                """INSERT INTO applicant_registry.financial_history
                (company_id, fiscal_year, total_revenue, gross_profit, operating_expenses,
                 operating_income, ebitda, depreciation_amortization, interest_expense,
                 income_before_tax, tax_expense, net_income, total_assets, current_assets,
                 cash_and_equivalents, accounts_receivable, inventory, total_liabilities,
                 current_liabilities, long_term_debt, total_equity, operating_cash_flow,
                 investing_cash_flow, financing_cash_flow, free_cash_flow, debt_to_equity,
                 current_ratio, debt_to_ebitda, interest_coverage_ratio, gross_margin,
                 ebitda_margin, net_margin, balance_sheet_check)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26,$27,$28,$29,$30,$31,$32,$33)
                ON CONFLICT(company_id, fiscal_year) DO NOTHING""",
                f["company_id"], f["fiscal_year"], f["total_revenue"], f["gross_profit"],
                f["operating_expenses"], f["operating_income"], f["ebitda"],
                f["depreciation_amortization"], f["interest_expense"], f["income_before_tax"],
                f["tax_expense"], f["net_income"], f["total_assets"], f["current_assets"],
                f["cash_and_equivalents"], f["accounts_receivable"], f["inventory"],
                f["total_liabilities"], f["current_liabilities"], f["long_term_debt"],
                f["total_equity"], f["operating_cash_flow"], f["investing_cash_flow"],
                f["financing_cash_flow"], f["free_cash_flow"], f["debt_to_equity"],
                f["current_ratio"], f["debt_to_ebitda"], f["interest_coverage_ratio"],
                f["gross_margin"], f["ebitda_margin"], f["net_margin"], f["balance_sheet_check"],
            )
        print(f"Seeded {len(SAMPLE_COMPANIES)} companies, {len(SAMPLE_FINANCIALS)} financial records")
    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()
    if not args.db_url:
        print("Set DATABASE_URL or use --db-url")
        sys.exit(1)
    asyncio.run(seed(args.db_url))


if __name__ == "__main__":
    main()
