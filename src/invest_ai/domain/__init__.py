"""Contratos de domínio do Assistente Invest Aê."""

from .models import (
    AnalysisStatus,
    CandidateAnalysis,
    Compatibility,
    EvidenceReference,
    FiiAnalysisCandidate,
    InvestmentAnalysis,
    InvestorNeed,
    NeedAssessment,
)
from .capabilities import Capability, CapabilitySupport, RecommendationCapabilityMatrix

__all__ = [
    "AnalysisStatus",
    "CandidateAnalysis",
    "Capability",
    "CapabilitySupport",
    "Compatibility",
    "EvidenceReference",
    "FiiAnalysisCandidate",
    "InvestmentAnalysis",
    "InvestorNeed",
    "NeedAssessment",
    "RecommendationCapabilityMatrix",
]
