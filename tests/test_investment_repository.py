from pathlib import Path

import pytest

from invest_ai.adapters import FixtureInvestmentRepository
from invest_ai.ports import InvestmentRepository


FIXTURE_PATH = Path("data/fixtures/fii_snapshot.json")


def test_fixture_repository_implementa_contrato_esperado():
    repositorio: InvestmentRepository = FixtureInvestmentRepository(FIXTURE_PATH)

    candidatos = repositorio.listar_candidatos()

    assert len(candidatos) == 2


def test_fixture_repository_preserva_proveniencia_mock():
    repositorio = FixtureInvestmentRepository(FIXTURE_PATH)

    candidato = repositorio.obter_por_ticker("FIIA11")

    assert candidato is not None
    assert candidato.data_source_type == "MOCK"
    assert candidato.source_name == "FIXTURE_DIO"
    assert candidato.quality_eligible is False


def test_fixture_repository_busca_ticker_sem_diferenciar_maiusculas():
    repositorio = FixtureInvestmentRepository(FIXTURE_PATH)

    candidato = repositorio.obter_por_ticker("fiib11")

    assert candidato is not None
    assert candidato.ticker == "FIIB11"


def test_fixture_repository_retorna_none_para_ticker_inexistente():
    repositorio = FixtureInvestmentRepository(FIXTURE_PATH)

    assert repositorio.obter_por_ticker("NAO11") is None


def test_fixture_repository_nao_promove_mock_a_dado_elegivel():
    repositorio = FixtureInvestmentRepository(FIXTURE_PATH)

    assert all(not candidato.quality_eligible for candidato in repositorio.listar_candidatos())


def test_fixture_repository_falha_quando_items_nao_e_lista(tmp_path):
    fixture_invalida = tmp_path / "fixture_invalida.json"
    fixture_invalida.write_text('{"items": {}}', encoding="utf-8")
    repositorio = FixtureInvestmentRepository(fixture_invalida)

    with pytest.raises(ValueError, match="lista no campo 'items'"):
        repositorio.listar_candidatos()
