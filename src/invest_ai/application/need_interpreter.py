"""Interpretação segura da necessidade expressa em linguagem natural.

O LLM atua somente como extrator semântico. A saída é validada contra uma
lista fechada de campos antes de ser convertida em InvestorNeed. Qualquer
campo financeiro ou analítico não autorizado provoca falha controlada.
"""

from typing import Any

from invest_ai.domain.models import InvestorNeed
from invest_ai.ports import LlmGateway


class InvalidLlmInterpretationError(ValueError):
    """Indica que o LLM devolveu uma estrutura fora do contrato permitido."""


class InvestorNeedInterpreter:
    """Converte a interpretação estruturada do LLM em InvestorNeed."""

    _CAMPOS_PERMITIDOS = frozenset(
        {
            "available_capital",
            "objective",
            "risk_tolerance",
            "investment_horizon_months",
            "liquidity_need",
            "periodic_income",
            "income_frequency",
            "experience_level",
            "restrictions",
        }
    )

    def __init__(self, llm_gateway: LlmGateway) -> None:
        self._llm_gateway = llm_gateway

    def interpretar(self, mensagem: str) -> InvestorNeed:
        if not mensagem or not mensagem.strip():
            raise ValueError("A mensagem da pessoa usuária não pode estar vazia.")

        payload = self._llm_gateway.interpretar_necessidade(mensagem)
        self._validar_payload(payload)

        restrictions = payload.get("restrictions")
        if restrictions is None:
            restrictions = ()
        elif isinstance(restrictions, list):
            restrictions = tuple(restrictions)

        return InvestorNeed(
            available_capital=payload.get("available_capital"),
            objective=payload.get("objective"),
            risk_tolerance=payload.get("risk_tolerance"),
            investment_horizon_months=payload.get("investment_horizon_months"),
            liquidity_need=payload.get("liquidity_need"),
            periodic_income=payload.get("periodic_income"),
            income_frequency=payload.get("income_frequency"),
            experience_level=payload.get("experience_level"),
            restrictions=restrictions,
        )

    def _validar_payload(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            raise InvalidLlmInterpretationError(
                "A interpretação do LLM deve ser um objeto estruturado."
            )

        campos_desconhecidos = set(payload) - self._CAMPOS_PERMITIDOS
        if campos_desconhecidos:
            raise InvalidLlmInterpretationError(
                "O LLM retornou campos não autorizados: "
                + ", ".join(sorted(campos_desconhecidos))
            )

        self._validar_numero_positivo_ou_nulo(payload, "available_capital")
        self._validar_inteiro_positivo_ou_nulo(payload, "investment_horizon_months")
        self._validar_booleano_ou_nulo(payload, "periodic_income")
        self._validar_restricoes(payload.get("restrictions"))

    @staticmethod
    def _validar_numero_positivo_ou_nulo(payload: dict[str, Any], campo: str) -> None:
        valor = payload.get(campo)
        if valor is None:
            return
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
            raise InvalidLlmInterpretationError(
                f"O campo '{campo}' deve ser um número positivo ou nulo."
            )

    @staticmethod
    def _validar_inteiro_positivo_ou_nulo(payload: dict[str, Any], campo: str) -> None:
        valor = payload.get(campo)
        if valor is None:
            return
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise InvalidLlmInterpretationError(
                f"O campo '{campo}' deve ser um inteiro positivo ou nulo."
            )

    @staticmethod
    def _validar_booleano_ou_nulo(payload: dict[str, Any], campo: str) -> None:
        valor = payload.get(campo)
        if valor is not None and not isinstance(valor, bool):
            raise InvalidLlmInterpretationError(
                f"O campo '{campo}' deve ser booleano ou nulo."
            )

    @staticmethod
    def _validar_restricoes(valor: Any) -> None:
        if valor is None:
            return
        if not isinstance(valor, (list, tuple)) or not all(
            isinstance(item, str) for item in valor
        ):
            raise InvalidLlmInterpretationError(
                "O campo 'restrictions' deve conter somente textos."
            )
