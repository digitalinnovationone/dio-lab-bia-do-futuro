"""Repositório local usado somente no laboratório e nos testes.

A fixture permite demonstrar o assistente sem acoplar o domínio ao arquivo
JSON. Em produção, esta implementação será substituída por um adaptador da
camada de dados validada do Invest Aê.
"""

import json
from pathlib import Path
from typing import Any

from invest_ai.domain.models import FiiAnalysisCandidate


class FixtureInvestmentRepository:
    """Lê candidatos de um snapshot local controlado."""

    def __init__(self, fixture_path: str | Path) -> None:
        self._fixture_path = Path(fixture_path)

    def listar_candidatos(self) -> tuple[FiiAnalysisCandidate, ...]:
        payload = self._carregar_payload()
        items = payload.get("items", [])
        return tuple(self._converter_item(item) for item in items)

    def obter_por_ticker(self, ticker: str) -> FiiAnalysisCandidate | None:
        ticker_normalizado = ticker.strip().upper()
        for candidato in self.listar_candidatos():
            if candidato.ticker.upper() == ticker_normalizado:
                return candidato
        return None

    def _carregar_payload(self) -> dict[str, Any]:
        with self._fixture_path.open("r", encoding="utf-8") as arquivo:
            payload = json.load(arquivo)

        if not isinstance(payload, dict):
            raise ValueError("A fixture de investimentos deve conter um objeto JSON na raiz.")

        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError("A fixture de investimentos deve conter uma lista no campo 'items'.")

        return payload

    @staticmethod
    def _converter_item(item: dict[str, Any]) -> FiiAnalysisCandidate:
        campos_obrigatorios = ("ticker", "name", "type", "segment")
        ausentes = [campo for campo in campos_obrigatorios if not item.get(campo)]
        if ausentes:
            raise ValueError(
                "Item da fixture sem campos obrigatórios: " + ", ".join(ausentes)
            )

        return FiiAnalysisCandidate(
            ticker=item["ticker"],
            name=item["name"],
            type=item["type"],
            segment=item["segment"],
            price=item.get("price"),
            vp=item.get("vp"),
            pvp=item.get("pvp"),
            pl=item.get("pl"),
            dividend_yield_12m=item.get("dividendYield12m"),
            last_dividend=item.get("lastDividend"),
            last_dividend_base_date=item.get("lastDividendBaseDate"),
            last_dividend_payment_date=item.get("lastDividendPaymentDate"),
            last_dividend_payment_status=item.get("lastDividendPaymentStatus"),
            income_12m_per_share=item.get("income12mPerShare"),
            amortization_12m_per_share=item.get("amortization12mPerShare"),
            fundamentals_reference=item.get("fundamentalsReference"),
            dy_method=item.get("dyMethod"),
            market_reference_generated_at=item.get("marketReferenceGeneratedAt"),
            source_name=item.get("sourceName"),
            data_source_type=item.get("dataSourceType"),
            last_updated_at=item.get("lastUpdatedAt"),
            quality_eligible=item.get("qualityEligible", False) is True,
        )
