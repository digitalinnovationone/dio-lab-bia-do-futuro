import pytest

from invest_ai.application import (
    InvalidLlmInterpretationError,
    InvestorNeedInterpreter,
)


class LlmFake:
    """Fake determinístico usado para testar o contrato sem acessar uma API."""

    def __init__(self, resposta):
        self._resposta = resposta
        self.mensagem_recebida = None

    def interpretar_necessidade(self, mensagem: str):
        self.mensagem_recebida = mensagem
        return self._resposta


def test_interpretador_converte_saida_valida_em_investor_need():
    llm = LlmFake(
        {
            "available_capital": 500.0,
            "objective": "INCOME",
            "risk_tolerance": "LOW",
            "periodic_income": True,
            "income_frequency": "MONTHLY",
        }
    )

    necessidade = InvestorNeedInterpreter(llm).interpretar(
        "Tenho 500 reais e queria uma renda mensal com mais segurança."
    )

    assert necessidade.available_capital == 500.0
    assert necessidade.objective == "INCOME"
    assert necessidade.risk_tolerance == "LOW"
    assert necessidade.periodic_income is True
    assert necessidade.income_frequency == "MONTHLY"


def test_interpretador_preserva_campos_nao_informados_como_none():
    necessidade = InvestorNeedInterpreter(
        LlmFake({"available_capital": 500.0, "objective": "INCOME"})
    ).interpretar("Tenho 500 reais e quero renda.")

    assert necessidade.risk_tolerance is None
    assert necessidade.liquidity_need is None
    assert necessidade.investment_horizon_months is None


def test_interpretador_rejeita_campo_financeiro_inventado_pelo_llm():
    llm = LlmFake(
        {
            "available_capital": 500.0,
            "objective": "INCOME",
            "dividend_yield": 0.12,
        }
    )

    with pytest.raises(InvalidLlmInterpretationError, match="campos não autorizados"):
        InvestorNeedInterpreter(llm).interpretar("Tenho 500 reais e quero renda.")


def test_interpretador_rejeita_ticker_recomendado_pelo_llm():
    llm = LlmFake(
        {
            "available_capital": 500.0,
            "objective": "INCOME",
            "recommended_ticker": "FIIA11",
        }
    )

    with pytest.raises(InvalidLlmInterpretationError, match="recommended_ticker"):
        InvestorNeedInterpreter(llm).interpretar("Onde devo investir?")


def test_interpretador_rejeita_payload_que_nao_seja_objeto():
    with pytest.raises(InvalidLlmInterpretationError, match="objeto estruturado"):
        InvestorNeedInterpreter(LlmFake("resposta livre")).interpretar(
            "Tenho 500 reais."
        )


def test_interpretador_rejeita_capital_invalido():
    llm = LlmFake({"available_capital": -500.0, "objective": "INCOME"})

    with pytest.raises(InvalidLlmInterpretationError, match="número positivo"):
        InvestorNeedInterpreter(llm).interpretar("Tenho menos quinhentos reais.")


def test_interpretador_rejeita_periodic_income_com_tipo_invalido():
    llm = LlmFake(
        {
            "available_capital": 500.0,
            "objective": "INCOME",
            "periodic_income": "sim",
        }
    )

    with pytest.raises(InvalidLlmInterpretationError, match="booleano"):
        InvestorNeedInterpreter(llm).interpretar("Quero receber renda.")


def test_interpretador_converte_restricoes_em_tupla():
    necessidade = InvestorNeedInterpreter(
        LlmFake(
            {
                "available_capital": 500.0,
                "objective": "INCOME",
                "restrictions": ["NAO_USAR_ALAVANCAGEM"],
            }
        )
    ).interpretar("Não quero usar alavancagem.")

    assert necessidade.restrictions == ("NAO_USAR_ALAVANCAGEM",)


def test_interpretador_rejeita_mensagem_vazia_sem_chamar_llm():
    llm = LlmFake({})

    with pytest.raises(ValueError, match="não pode estar vazia"):
        InvestorNeedInterpreter(llm).interpretar("   ")

    assert llm.mensagem_recebida is None
