"""Gate de elegibilidade dos dados usados pelo motor de análise.

A regra separa explicitamente produção e laboratório. Dados fictícios podem
ser usados em demonstrações controladas, mas nunca são promovidos a dados
reais ou autorizados silenciosamente em produção.
"""

from dataclasses import dataclass
from enum import Enum

from invest_ai.domain.models import FiiAnalysisCandidate


class AnalysisContext(str, Enum):
    """Contexto em que a análise será executada."""

    LABORATORY = "LABORATORY"
    PRODUCTION = "PRODUCTION"


class EligibilityReason(str, Enum):
    """Motivos rastreáveis para autorização ou bloqueio de um candidato."""

    ELIGIBLE_PRODUCTION_DATA = "ELIGIBLE_PRODUCTION_DATA"
    ELIGIBLE_LABORATORY_MOCK = "ELIGIBLE_LABORATORY_MOCK"
    NON_PRODUCTION_DATA = "NON_PRODUCTION_DATA"
    DATA_QUALITY_FAILURE = "DATA_QUALITY_FAILURE"
    UNKNOWN_DATA_SOURCE = "UNKNOWN_DATA_SOURCE"


@dataclass(frozen=True)
class EligibilityResult:
    """Resultado determinístico da avaliação de elegibilidade."""

    eligible: bool
    reason: EligibilityReason
    demonstration_only: bool = False


class AnalysisEligibilityGate:
    """Decide se um candidato pode alimentar o motor de análise."""

    _FONTES_PRODUCAO = frozenset({"SNAPSHOT", "REAL"})
    _FONTES_NAO_PRODUCAO = frozenset({"MOCK", "FALLBACK"})

    def avaliar(
        self,
        candidato: FiiAnalysisCandidate,
        contexto: AnalysisContext,
    ) -> EligibilityResult:
        fonte = (candidato.data_source_type or "").strip().upper()

        if contexto is AnalysisContext.LABORATORY and fonte == "MOCK":
            return EligibilityResult(
                eligible=True,
                reason=EligibilityReason.ELIGIBLE_LABORATORY_MOCK,
                demonstration_only=True,
            )

        if fonte in self._FONTES_NAO_PRODUCAO:
            return EligibilityResult(
                eligible=False,
                reason=EligibilityReason.NON_PRODUCTION_DATA,
            )

        if fonte not in self._FONTES_PRODUCAO:
            return EligibilityResult(
                eligible=False,
                reason=EligibilityReason.UNKNOWN_DATA_SOURCE,
            )

        if not candidato.quality_eligible:
            return EligibilityResult(
                eligible=False,
                reason=EligibilityReason.DATA_QUALITY_FAILURE,
            )

        return EligibilityResult(
            eligible=True,
            reason=EligibilityReason.ELIGIBLE_PRODUCTION_DATA,
        )
