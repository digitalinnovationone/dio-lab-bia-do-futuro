"""Matriz de capacidades de recomendacao do Assistente Invest Ae.

Uma necessidade informada pelo usuario so pode participar da decisao quando
existe uma capacidade explicitamente suportada. Isso evita transformar
conhecimento geral do LLM em dado financeiro ou metodologia inexistente.
"""

from dataclasses import dataclass
from enum import Enum


class Capability(str, Enum):
    AVAILABLE_CAPITAL = "AVAILABLE_CAPITAL"
    HISTORICAL_INCOME = "HISTORICAL_INCOME"
    MONTHLY_INCOME_REGULARITY = "MONTHLY_INCOME_REGULARITY"
    DIVIDEND_YIELD = "DIVIDEND_YIELD"
    PVP = "PVP"
    FUNDAMENTALS = "FUNDAMENTALS"
    RISK = "RISK"
    LIQUIDITY = "LIQUIDITY"
    INVESTMENT_HORIZON = "INVESTMENT_HORIZON"
    FUTURE_APPRECIATION = "FUTURE_APPRECIATION"
    FUTURE_INCOME = "FUTURE_INCOME"


class CapabilitySupport(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class CapabilityRule:
    capability: Capability
    support: CapabilitySupport
    reason: str


class RecommendationCapabilityMatrix:
    """Fonte unica das capacidades que o MVP pode afirmar ou analisar."""

    _RULES = {
        Capability.AVAILABLE_CAPITAL: CapabilityRule(
            Capability.AVAILABLE_CAPITAL,
            CapabilitySupport.SUPPORTED,
            "O preco de referencia permite avaliar acessibilidade pelo capital.",
        ),
        Capability.HISTORICAL_INCOME: CapabilityRule(
            Capability.HISTORICAL_INCOME,
            CapabilitySupport.SUPPORTED,
            "A base possui renda historica por cota e ultimo rendimento.",
        ),
        Capability.MONTHLY_INCOME_REGULARITY: CapabilityRule(
            Capability.MONTHLY_INCOME_REGULARITY,
            CapabilitySupport.PARTIAL,
            "Pagamentos conhecidos podem ser apresentados, mas nao garantem recorrencia futura.",
        ),
        Capability.DIVIDEND_YIELD: CapabilityRule(
            Capability.DIVIDEND_YIELD,
            CapabilitySupport.SUPPORTED,
            "O DY historico pode ser comparado quando metodologia e evidencia sao validas.",
        ),
        Capability.PVP: CapabilityRule(
            Capability.PVP,
            CapabilitySupport.SUPPORTED,
            "P/VP pode ser explicado e comparado a partir dos fundamentos validados.",
        ),
        Capability.FUNDAMENTALS: CapabilityRule(
            Capability.FUNDAMENTALS,
            CapabilitySupport.SUPPORTED,
            "VP e PL podem ser apresentados quando disponiveis na camada validada.",
        ),
        Capability.RISK: CapabilityRule(
            Capability.RISK,
            CapabilitySupport.UNSUPPORTED,
            "O MVP ainda nao possui metodologia documentada para classificar risco.",
        ),
        Capability.LIQUIDITY: CapabilityRule(
            Capability.LIQUIDITY,
            CapabilitySupport.UNSUPPORTED,
            "O MVP ainda nao possui dados e metodologia suficientes de liquidez.",
        ),
        Capability.INVESTMENT_HORIZON: CapabilityRule(
            Capability.INVESTMENT_HORIZON,
            CapabilitySupport.PARTIAL,
            "O horizonte pode contextualizar a conversa, mas ainda nao classifica adequacao do ativo.",
        ),
        Capability.FUTURE_APPRECIATION: CapabilityRule(
            Capability.FUTURE_APPRECIATION,
            CapabilitySupport.UNSUPPORTED,
            "Dados historicos nao autorizam previsao de valorizacao futura.",
        ),
        Capability.FUTURE_INCOME: CapabilityRule(
            Capability.FUTURE_INCOME,
            CapabilitySupport.UNSUPPORTED,
            "Rendimentos historicos nao autorizam promessa de renda futura.",
        ),
    }

    @classmethod
    def get(cls, capability: Capability) -> CapabilityRule:
        return cls._RULES[capability]

    @classmethod
    def is_supported(cls, capability: Capability) -> bool:
        return cls.get(capability).support == CapabilitySupport.SUPPORTED

    @classmethod
    def unsupported(cls, capabilities: tuple[Capability, ...]) -> tuple[Capability, ...]:
        return tuple(
            capability
            for capability in capabilities
            if cls.get(capability).support == CapabilitySupport.UNSUPPORTED
        )
