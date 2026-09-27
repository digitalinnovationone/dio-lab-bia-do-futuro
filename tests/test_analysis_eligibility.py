from dataclasses import replace
from pathlib import Path

from invest_ai.adapters import FixtureInvestmentRepository
from invest_ai.analysis import (
    AnalysisContext,
    AnalysisEligibilityGate,
    EligibilityReason,
)


FIXTURE_PATH = Path("data/fixtures/fii_snapshot.json")


def _candidato_mock():
    repositorio = FixtureInvestmentRepository(FIXTURE_PATH)
    candidato = repositorio.obter_por_ticker("FIIA11")
    assert candidato is not None
    return candidato


def test_mock_e_permitido_no_laboratorio_sem_ser_promovido_a_dado_real():
    resultado = AnalysisEligibilityGate().avaliar(
        _candidato_mock(),
        AnalysisContext.LABORATORY,
    )

    assert resultado.eligible is True
    assert resultado.demonstration_only is True
    assert resultado.reason is EligibilityReason.ELIGIBLE_LABORATORY_MOCK


def test_mock_e_bloqueado_em_producao():
    resultado = AnalysisEligibilityGate().avaliar(
        _candidato_mock(),
        AnalysisContext.PRODUCTION,
    )

    assert resultado.eligible is False
    assert resultado.demonstration_only is False
    assert resultado.reason is EligibilityReason.NON_PRODUCTION_DATA


def test_fallback_e_bloqueado_em_producao():
    candidato = replace(
        _candidato_mock(),
        data_source_type="FALLBACK",
        quality_eligible=True,
    )

    resultado = AnalysisEligibilityGate().avaliar(
        candidato,
        AnalysisContext.PRODUCTION,
    )

    assert resultado.eligible is False
    assert resultado.reason is EligibilityReason.NON_PRODUCTION_DATA


def test_fonte_desconhecida_e_bloqueada():
    candidato = replace(
        _candidato_mock(),
        data_source_type="UNKNOWN",
        quality_eligible=True,
    )

    resultado = AnalysisEligibilityGate().avaliar(
        candidato,
        AnalysisContext.PRODUCTION,
    )

    assert resultado.eligible is False
    assert resultado.reason is EligibilityReason.UNKNOWN_DATA_SOURCE


def test_snapshot_sem_quality_gate_e_bloqueado():
    candidato = replace(
        _candidato_mock(),
        data_source_type="SNAPSHOT",
        quality_eligible=False,
    )

    resultado = AnalysisEligibilityGate().avaliar(
        candidato,
        AnalysisContext.PRODUCTION,
    )

    assert resultado.eligible is False
    assert resultado.reason is EligibilityReason.DATA_QUALITY_FAILURE


def test_snapshot_validado_e_elegivel_em_producao():
    candidato = replace(
        _candidato_mock(),
        data_source_type="SNAPSHOT",
        quality_eligible=True,
    )

    resultado = AnalysisEligibilityGate().avaliar(
        candidato,
        AnalysisContext.PRODUCTION,
    )

    assert resultado.eligible is True
    assert resultado.demonstration_only is False
    assert resultado.reason is EligibilityReason.ELIGIBLE_PRODUCTION_DATA


def test_real_validado_permanece_compativel_com_contrato_existente():
    candidato = replace(
        _candidato_mock(),
        data_source_type="REAL",
        quality_eligible=True,
    )

    resultado = AnalysisEligibilityGate().avaliar(
        candidato,
        AnalysisContext.PRODUCTION,
    )

    assert resultado.eligible is True
    assert resultado.reason is EligibilityReason.ELIGIBLE_PRODUCTION_DATA
