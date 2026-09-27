"""Regras determinísticas de análise do Assistente Invest Aê."""

from .eligibility import (
    AnalysisContext,
    AnalysisEligibilityGate,
    EligibilityReason,
    EligibilityResult,
)
from .engine import InvestmentAnalysisEngine

__all__ = [
    "AnalysisContext",
    "AnalysisEligibilityGate",
    "EligibilityReason",
    "EligibilityResult",
    "InvestmentAnalysisEngine",
]
