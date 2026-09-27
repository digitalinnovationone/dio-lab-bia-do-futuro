"""Contrato de acesso aos candidatos de investimento.

O motor de análise depende desta porta, e não da origem física dos dados.
No laboratório ela será implementada por uma fixture local. No Invest Aê,
poderá ser implementada pela camada de dados validada do aplicativo.
"""

from typing import Protocol

from invest_ai.domain.models import FiiAnalysisCandidate


class InvestmentRepository(Protocol):
    """Porta de leitura dos candidatos disponíveis para análise."""

    def listar_candidatos(self) -> tuple[FiiAnalysisCandidate, ...]:
        """Retorna os candidatos disponíveis sem aplicar recomendação."""
        ...

    def obter_por_ticker(self, ticker: str) -> FiiAnalysisCandidate | None:
        """Retorna um candidato pelo ticker ou None quando ele não existir."""
        ...
