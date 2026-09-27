from invest_ai.application import InvestorNeedAssessment
from invest_ai.domain import InvestorNeed


def test_necessidade_com_capital_e_objetivo_e_suficiente():
    resultado = InvestorNeedAssessment().avaliar(
        InvestorNeed(
            available_capital=500.0,
            objective="INCOME",
        )
    )

    assert resultado.sufficient is True
    assert resultado.missing_fields == ()


def test_necessidade_sem_capital_solicita_capital():
    resultado = InvestorNeedAssessment().avaliar(
        InvestorNeed(objective="INCOME")
    )

    assert resultado.sufficient is False
    assert resultado.missing_fields == ("available_capital",)


def test_necessidade_sem_objetivo_solicita_objetivo():
    resultado = InvestorNeedAssessment().avaliar(
        InvestorNeed(available_capital=500.0)
    )

    assert resultado.sufficient is False
    assert resultado.missing_fields == ("objective",)


def test_necessidade_vazia_informa_todos_os_campos_minimos_ausentes():
    resultado = InvestorNeedAssessment().avaliar(InvestorNeed())

    assert resultado.sufficient is False
    assert resultado.missing_fields == ("available_capital", "objective")


def test_capital_zero_nao_e_tratado_como_informacao_valida():
    resultado = InvestorNeedAssessment().avaliar(
        InvestorNeed(
            available_capital=0.0,
            objective="INCOME",
        )
    )

    assert resultado.sufficient is False
    assert resultado.missing_fields == ("available_capital",)


def test_objetivo_vazio_nao_e_tratado_como_informacao_valida():
    resultado = InvestorNeedAssessment().avaliar(
        InvestorNeed(
            available_capital=500.0,
            objective="   ",
        )
    )

    assert resultado.sufficient is False
    assert resultado.missing_fields == ("objective",)


def test_criterio_nao_suportado_nao_torna_necessidade_incompreensivel():
    resultado = InvestorNeedAssessment().avaliar(
        InvestorNeed(
            available_capital=500.0,
            objective="INCOME",
            risk_tolerance="LOW",
            liquidity_need="HIGH",
        )
    )

    assert resultado.sufficient is True
    assert resultado.missing_fields == ()
