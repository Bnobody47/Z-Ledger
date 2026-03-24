"""
Applicant Registry — read-only client for company/financial data.
Agents use this to load historical financials, compliance flags, loan history.
"""
from __future__ import annotations

from dataclasses import dataclass

import asyncpg


@dataclass
class CompanyProfile:
    company_id: str
    name: str
    industry: str
    naics: str
    jurisdiction: str
    legal_type: str
    founded_year: int
    employee_count: int
    risk_segment: str
    trajectory: str
    submission_channel: str
    ip_region: str


@dataclass
class FinancialYear:
    fiscal_year: int
    total_revenue: float
    gross_profit: float
    operating_income: float
    ebitda: float
    net_income: float
    total_assets: float
    total_liabilities: float
    total_equity: float
    long_term_debt: float
    cash_and_equivalents: float
    debt_to_equity: float | None
    current_ratio: float | None
    debt_to_ebitda: float | None


@dataclass
class ComplianceFlag:
    flag_type: str
    severity: str
    is_active: bool
    added_date: str
    note: str | None


class ApplicantRegistryClient:
    """Read-only access to applicant_registry schema."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get_company(self, company_id: str) -> CompanyProfile | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT company_id, name, industry, naics, jurisdiction, legal_type,
                          founded_year, employee_count, risk_segment, trajectory,
                          submission_channel, ip_region
                   FROM applicant_registry.companies WHERE company_id = $1""",
                company_id,
            )
        if row is None:
            return None
        return CompanyProfile(
            company_id=row["company_id"],
            name=row["name"],
            industry=row["industry"],
            naics=row["naics"],
            jurisdiction=row["jurisdiction"],
            legal_type=row["legal_type"],
            founded_year=row["founded_year"],
            employee_count=row["employee_count"],
            risk_segment=row["risk_segment"],
            trajectory=row["trajectory"],
            submission_channel=row["submission_channel"],
            ip_region=row["ip_region"],
        )

    async def get_financial_history(
        self, company_id: str, years: list[int] | None = None
    ) -> list[FinancialYear]:
        async with self._pool.acquire() as conn:
            if years:
                rows = await conn.fetch(
                    """SELECT fiscal_year, total_revenue, gross_profit, operating_income,
                              ebitda, net_income, total_assets, total_liabilities,
                              total_equity, long_term_debt, cash_and_equivalents,
                              debt_to_equity, current_ratio, debt_to_ebitda
                       FROM applicant_registry.financial_history
                       WHERE company_id = $1 AND fiscal_year = ANY($2::int[])
                       ORDER BY fiscal_year ASC""",
                    company_id,
                    years,
                )
            else:
                rows = await conn.fetch(
                    """SELECT fiscal_year, total_revenue, gross_profit, operating_income,
                              ebitda, net_income, total_assets, total_liabilities,
                              total_equity, long_term_debt, cash_and_equivalents,
                              debt_to_equity, current_ratio, debt_to_ebitda
                       FROM applicant_registry.financial_history
                       WHERE company_id = $1 ORDER BY fiscal_year ASC""",
                    company_id,
                )
        return [
            FinancialYear(
                fiscal_year=r["fiscal_year"],
                total_revenue=float(r["total_revenue"]),
                gross_profit=float(r["gross_profit"]),
                operating_income=float(r["operating_income"]),
                ebitda=float(r["ebitda"]),
                net_income=float(r["net_income"]),
                total_assets=float(r["total_assets"]),
                total_liabilities=float(r["total_liabilities"]),
                total_equity=float(r["total_equity"]),
                long_term_debt=float(r["long_term_debt"]),
                cash_and_equivalents=float(r["cash_and_equivalents"]),
                debt_to_equity=float(r["debt_to_equity"]) if r["debt_to_equity"] else None,
                current_ratio=float(r["current_ratio"]) if r["current_ratio"] else None,
                debt_to_ebitda=float(r["debt_to_ebitda"]) if r["debt_to_ebitda"] else None,
            )
            for r in rows
        ]

    async def get_compliance_flags(
        self, company_id: str, active_only: bool = False
    ) -> list[ComplianceFlag]:
        async with self._pool.acquire() as conn:
            if active_only:
                rows = await conn.fetch(
                    """SELECT flag_type, severity, is_active, added_date::text, note
                       FROM applicant_registry.compliance_flags
                       WHERE company_id = $1 AND is_active = TRUE""",
                    company_id,
                )
            else:
                rows = await conn.fetch(
                    """SELECT flag_type, severity, is_active, added_date::text, note
                       FROM applicant_registry.compliance_flags WHERE company_id = $1""",
                    company_id,
                )
        return [
            ComplianceFlag(
                flag_type=r["flag_type"],
                severity=r["severity"],
                is_active=r["is_active"],
                added_date=r["added_date"],
                note=r["note"],
            )
            for r in rows
        ]

    async def get_loan_relationships(self, company_id: str) -> list[dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT loan_amount, loan_year, was_repaid, default_occurred, note
                   FROM applicant_registry.loan_relationships WHERE company_id = $1""",
                company_id,
            )
        return [dict(r) for r in rows]
