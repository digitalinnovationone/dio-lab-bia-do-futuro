"""Avaliação determinística da necessidade informada pela pessoa usuária.

Este componente não interpreta linguagem natural. Ele recebe um InvestorNeed
já estruturado e decide se existe informação mínima para uma análise útil ou
se a conversa precisa solicitar dados adicionais antes de consultar o motor.
"""

from invest_ai.domain.models import InvestorNeed, NeedAssessment


class InvestorNeedAssessment:
    """Verifica se a necessidade contém o mínimo necessário para análise."""

    def avaliar(self, necessidade: InvestorNeed) -> NeedAssessment:
        campos_ausentes: list[str] = []

        if not self._capital_valido(necessidade.available_capital):
            campos_ausentes.append("available_capital")

        if not self._objetivo_valido(necessidade.objective):
            campos_ausentes.append("objective")

        return NeedAssessment(
            sufficient=not campos_ausentes,
            missing_fields=tuple(campos_ausentes),
        )

    @staticmethod
    def _capital_valido(capital: float | None) -> bool:
        return capital is not None and capital > 0

    @staticmethod
    def _objetivo_valido(objetivo: str | None) -> bool:
        return objetivo is not None and bool(objetivo.strip())
