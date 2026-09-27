"""Contrato de integração com modelos de linguagem.

A porta limita a responsabilidade do modelo à interpretação da mensagem da
pessoa usuária. Dados financeiros, cálculos e decisões analíticas continuam
fora do LLM e pertencem às camadas determinísticas do Assistente Invest Aê.
"""

from typing import Any, Protocol


class LlmGateway(Protocol):
    """Porta mínima para interpretar uma necessidade em linguagem natural."""

    def interpretar_necessidade(self, mensagem: str) -> dict[str, Any]:
        """Retorna somente campos estruturados derivados da mensagem recebida."""
        ...
