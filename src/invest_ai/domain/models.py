"""Contratos de domínio do Assistente Invest Aê.

Estes modelos representam necessidade, evidências e resultado da análise.
Eles não substituem o contrato financeiro do Invest Aê e não são uma
segunda fonte de verdade para dados de mercado.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AnalysisStatus(str, Enum):
    READY = "READY"
    PARTIAL_ANALYSIS = "PARTIAL_ANALYSIS"
    NEEDS_MORE_USER_INFORMATION = "NEEDS_MORE_USER_INFORMATION"
    INSUFFICIENT_MARKET_DATA = "INSUFFICIENT_MARKET_DATA"
    NO_COMPATIBLE_OPTIONS = "NO_COMPATIBLE_OPTIONS"
    DATA_QUALITY_FAILURE = "DATA_QUALITY_FAILURE"


class Compatibility(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    PARTIALLY_COMPATIBLE = "PARTIALLY_COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class InvestorNeed:
    available_capital: float | None = None
    objective: str | None = None
    risk_tolerance: str | None = None
    investment_horizon_months: int | None = None
    liquidity_need: str | None = None
    periodic_income: bool | None = None
    income_frequency: str | None = None
    experience_level: str | None = None
    restrictions: tuple[str, ...] = ()


@dataclass(frozen=True)
class NeedAssessment:
    sufficient: bool
    missing_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class FiiAnalysisCandidate:
    """Projeção analítica transitória de um FII disponível para o motor.

    O objeto não é persistido como uma nova fonte financeira. Ele apenas
    transporta os campos necessários à análise e mantém a proveniência.
    """

    ticker: str
    name: str
    type: str
    segment: str
    price: float | None
    vp: float | None = None
    pvp: float | None = None
    pl: float | None = None
    dividend_yield_12m: float | None = None
    last_dividend: float | None = None
    last_dividend_base_date: str | None = None
    last_dividend_payment_date: str | None = None
    last_dividend_payment_status: str | None = None
    income_12m_per_share: float | None = None
    amortization_12m_per_share: float | None = None
    fundamentals_reference: str | None = None
    dy_method: str | None = None
    market_reference_generated_at: str | None = None
    source_name: str | None = None
    data_source_type: str | None = None
    last_updated_at: str | None = None
    quality_eligible: bool = False


@dataclass(frozen=True)
class EvidenceReference:
    """Referência rastreável a um dado fornecido pela camada do Invest Aê."""

    asset_id: str
    metric: str
    value: Any
    source_name: str | None = None
    data_source_type: str | None = None
    reference_date: str | None = None
    methodology: str | None = None


@dataclass(frozen=True)
class CandidateAnalysis:
    asset_id: str
    compatibility: Compatibility
    matched_criteria: tuple[str, ...] = ()
    unmatched_criteria: tuple[str, ...] = ()
    evidence: tuple[EvidenceReference, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class InvestmentAnalysis:
    status: AnalysisStatus
    user_need: InvestorNeed
    candidates: tuple[CandidateAnalysis, ...] = ()
    excluded_candidates: tuple[CandidateAnalysis, ...] = ()
    supported_criteria: tuple[str, ...] = ()
    unsupported_criteria: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    evidence: tuple[EvidenceReference, ...] = field(default_factory=tuple)
