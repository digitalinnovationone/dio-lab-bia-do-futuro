from dataclasses import replace
from pathlib import Path

from invest_ai.adapters import FixtureInvestmentRepository
from invest_ai.analysis import AnalysisContext, InvestmentAnalysisEngine
from invest_ai.domain import AnalysisStatus, Compatibility, InvestorNeed


FIXTURE_PATH = Path("data/fixtures/fii_snapshot.json")


def _motor():
    return InvestmentAnalysisEngine(FixtureInvestmentRepository(FIXTURE_PATH))


def test_motor_calcula_quantidade_acessivel_sem_delegar_calculo_ao_llm():
    analise = _motor().analisar(
        InvestorNeed(available_capital=450.0),
        AnalysisContext.LABORATORY,
    )

    fii_a = next(item for item in analise.candidates if item.asset_id == "FIIA11")
    evidencia = next(
        item for item in fii_a.evidence if item.metric == "affordableShares"
    )

    assert evidencia.value == 4
    assert evidencia.methodology == "FLOOR(AVAILABLE_CAPITAL / REFERENCE_PRICE)"


def test_motor_exclui_ativo_que_nao_cabe_no_capital_informado():
    analise = _motor().analisar(
        InvestorNeed(available_capital=90.0),
        AnalysisContext.LABORATORY,
    )

    excluido = next(item for item in analise.excluded_candidates if item.asset_id == "FIIA11")

    assert excluido.compatibility is Compatibility.INCOMPATIBLE
    assert "AVAILABLE_CAPITAL" in excluido.unmatched_criteria


def test_motor_usa_renda_historica_e_separa_amortizacao():
    analise = _motor().analisar(
        InvestorNeed(objective="INCOME", periodic_income=True),
        AnalysisContext.LABORATORY,
    )

    fii_b = next(item for item in analise.candidates if item.asset_id == "FIIB11")
    metricas = {item.metric: item.value for item in fii_b.evidence}

    assert metricas["income12mPerShare"] == 8.4
    assert metricas["lastDividend"] == 0.7
    assert metricas["amortization12mPerShare"] == 0.2


def test_motor_marca_analise_parcial_quando_usuario_pede_risco():
    analise = _motor().analisar(
        InvestorNeed(
            available_capital=500.0,
            objective="INCOME",
            periodic_income=True,
            risk_tolerance="LOW",
        ),
        AnalysisContext.LABORATORY,
    )

    assert analise.status is AnalysisStatus.PARTIAL_ANALYSIS
    assert "RISK" in analise.unsupported_criteria


def test_motor_nao_confunde_renda_mensal_com_garantia_de_recorrencia():
    analise = _motor().analisar(
        InvestorNeed(
            objective="INCOME",
            periodic_income=True,
            income_frequency="MONTHLY",
        ),
        AnalysisContext.LABORATORY,
    )

    assert analise.status is AnalysisStatus.PARTIAL_ANALYSIS
    assert "MONTHLY_INCOME_REGULARITY" in analise.unsupported_criteria


def test_motor_sinaliza_explicitamente_uso_de_dados_ficticios_no_laboratorio():
    analise = _motor().analisar(
        InvestorNeed(available_capital=500.0),
        AnalysisContext.LABORATORY,
    )

    assert "DADOS_FICTICIOS_PARA_DEMONSTRACAO" in analise.warnings
    assert all(
        evidencia.data_source_type == "MOCK"
        for evidencia in analise.evidence
    )


def test_motor_bloqueia_fixture_mock_quando_executado_em_producao():
    analise = _motor().analisar(
        InvestorNeed(available_capital=500.0),
        AnalysisContext.PRODUCTION,
    )

    assert analise.status is AnalysisStatus.DATA_QUALITY_FAILURE
    assert not analise.candidates
    assert len(analise.excluded_candidates) == 2


def test_motor_nao_cria_evidencia_de_renda_quando_dado_esta_ausente():
    repositorio_base = FixtureInvestmentRepository(FIXTURE_PATH)
    candidato = repositorio_base.obter_por_ticker("FIIA11")
    assert candidato is not None

    candidato_sem_renda = replace(candidato, income_12m_per_share=None)

    class RepositorioSemRenda:
        def listar_candidatos(self):
            return (candidato_sem_renda,)

        def obter_por_ticker(self, ticker: str):
            return candidato_sem_renda if ticker.upper() == "FIIA11" else None

    analise = InvestmentAnalysisEngine(RepositorioSemRenda()).analisar(
        InvestorNeed(objective="INCOME", periodic_income=True),
        AnalysisContext.LABORATORY,
    )

    candidato_analisado = analise.candidates[0]
    assert candidato_analisado.compatibility is Compatibility.INSUFFICIENT_DATA
    assert "RENDA_HISTORICA_INDISPONIVEL" in candidato_analisado.warnings
    assert not candidato_analisado.evidence
