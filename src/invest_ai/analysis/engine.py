"""Motor determinístico de análise do Assistente Invest Aê.

O motor transforma necessidades suportadas e dados elegíveis em evidências e
análises estruturadas. Ele não prevê valorização, não promete renda futura e
não cria classificações de risco ou liquidez sem metodologia documentada.
"""

from math import floor

from invest_ai.analysis.eligibility import AnalysisContext, AnalysisEligibilityGate
from invest_ai.domain.capabilities import Capability
from invest_ai.domain.models import (
    AnalysisStatus,
    CandidateAnalysis,
    Compatibility,
    EvidenceReference,
    InvestmentAnalysis,
    InvestorNeed,
)
from invest_ai.ports import InvestmentRepository


class InvestmentAnalysisEngine:
    """Executa a primeira análise objetiva sobre os candidatos disponíveis."""

    def __init__(
        self,
        repositorio: InvestmentRepository,
        eligibility_gate: AnalysisEligibilityGate | None = None,
    ) -> None:
        self._repositorio = repositorio
        self._eligibility_gate = eligibility_gate or AnalysisEligibilityGate()

    def analisar(
        self,
        necessidade: InvestorNeed,
        contexto: AnalysisContext,
    ) -> InvestmentAnalysis:
        criterios_suportados, criterios_nao_suportados = self._classificar_criterios(
            necessidade
        )
        candidatos: list[CandidateAnalysis] = []
        excluidos: list[CandidateAnalysis] = []
        evidencias_gerais: list[EvidenceReference] = []
        demonstracao = False

        for candidato in self._repositorio.listar_candidatos():
            elegibilidade = self._eligibility_gate.avaliar(candidato, contexto)
            demonstracao = demonstracao or elegibilidade.demonstration_only

            if not elegibilidade.eligible:
                excluidos.append(
                    CandidateAnalysis(
                        asset_id=candidato.ticker,
                        compatibility=Compatibility.INSUFFICIENT_DATA,
                        warnings=(elegibilidade.reason.value,),
                    )
                )
                continue

            analise = self._analisar_candidato(candidato, necessidade)
            evidencias_gerais.extend(analise.evidence)

            if analise.compatibility is Compatibility.INCOMPATIBLE:
                excluidos.append(analise)
            else:
                candidatos.append(analise)

        avisos: list[str] = []
        if demonstracao:
            avisos.append("DADOS_FICTICIOS_PARA_DEMONSTRACAO")

        if not candidatos:
            status = (
                AnalysisStatus.DATA_QUALITY_FAILURE
                if excluidos
                and all(
                    candidato.compatibility is Compatibility.INSUFFICIENT_DATA
                    for candidato in excluidos
                )
                else AnalysisStatus.NO_COMPATIBLE_OPTIONS
            )
        elif criterios_nao_suportados:
            status = AnalysisStatus.PARTIAL_ANALYSIS
        else:
            status = AnalysisStatus.READY

        return InvestmentAnalysis(
            status=status,
            user_need=necessidade,
            candidates=tuple(candidatos),
            excluded_candidates=tuple(excluidos),
            supported_criteria=tuple(criterio.value for criterio in criterios_suportados),
            unsupported_criteria=tuple(
                criterio.value for criterio in criterios_nao_suportados
            ),
            warnings=tuple(avisos),
            evidence=tuple(evidencias_gerais),
        )

    def _analisar_candidato(self, candidato, necessidade: InvestorNeed) -> CandidateAnalysis:
        criterios_atendidos: list[str] = []
        criterios_nao_atendidos: list[str] = []
        evidencias: list[EvidenceReference] = []
        avisos: list[str] = []

        if necessidade.available_capital is not None:
            if candidato.price is None or candidato.price <= 0:
                avisos.append("PRECO_DE_REFERENCIA_INDISPONIVEL")
            else:
                quantidade = floor(necessidade.available_capital / candidato.price)
                evidencias.append(
                    self._evidencia(candidato, "price", candidato.price)
                )
                evidencias.append(
                    self._evidencia(
                        candidato,
                        "affordableShares",
                        quantidade,
                        metodologia="FLOOR(AVAILABLE_CAPITAL / REFERENCE_PRICE)",
                    )
                )
                if quantidade >= 1:
                    criterios_atendidos.append(Capability.AVAILABLE_CAPITAL.value)
                else:
                    criterios_nao_atendidos.append(Capability.AVAILABLE_CAPITAL.value)

        if necessidade.periodic_income is True or necessidade.objective == "INCOME":
            if candidato.income_12m_per_share is None:
                avisos.append("RENDA_HISTORICA_INDISPONIVEL")
            else:
                criterios_atendidos.append(Capability.HISTORICAL_INCOME.value)
                evidencias.append(
                    self._evidencia(
                        candidato,
                        "income12mPerShare",
                        candidato.income_12m_per_share,
                    )
                )
                if candidato.last_dividend is not None:
                    evidencias.append(
                        self._evidencia(
                            candidato,
                            "lastDividend",
                            candidato.last_dividend,
                            reference_date=candidato.last_dividend_base_date,
                        )
                    )
                if candidato.amortization_12m_per_share is not None:
                    evidencias.append(
                        self._evidencia(
                            candidato,
                            "amortization12mPerShare",
                            candidato.amortization_12m_per_share,
                        )
                    )

        if criterios_nao_atendidos:
            compatibilidade = Compatibility.INCOMPATIBLE
        elif avisos and not criterios_atendidos:
            compatibilidade = Compatibility.INSUFFICIENT_DATA
        elif avisos:
            compatibilidade = Compatibility.PARTIALLY_COMPATIBLE
        else:
            compatibilidade = Compatibility.COMPATIBLE

        return CandidateAnalysis(
            asset_id=candidato.ticker,
            compatibility=compatibilidade,
            matched_criteria=tuple(criterios_atendidos),
            unmatched_criteria=tuple(criterios_nao_atendidos),
            evidence=tuple(evidencias),
            warnings=tuple(avisos),
        )

    @staticmethod
    def _classificar_criterios(
        necessidade: InvestorNeed,
    ) -> tuple[list[Capability], list[Capability]]:
        suportados: list[Capability] = []
        nao_suportados: list[Capability] = []

        if necessidade.available_capital is not None:
            suportados.append(Capability.AVAILABLE_CAPITAL)

        if necessidade.periodic_income is True or necessidade.objective == "INCOME":
            suportados.append(Capability.HISTORICAL_INCOME)

        if necessidade.risk_tolerance is not None:
            nao_suportados.append(Capability.RISK)

        if necessidade.liquidity_need is not None:
            nao_suportados.append(Capability.LIQUIDITY)

        if necessidade.investment_horizon_months is not None:
            nao_suportados.append(Capability.INVESTMENT_HORIZON)

        if necessidade.income_frequency == "MONTHLY":
            nao_suportados.append(Capability.MONTHLY_INCOME_REGULARITY)

        return suportados, nao_suportados

    @staticmethod
    def _evidencia(
        candidato,
        metrica: str,
        valor,
        reference_date: str | None = None,
        metodologia: str | None = None,
    ) -> EvidenceReference:
        return EvidenceReference(
            asset_id=candidato.ticker,
            metric=metrica,
            value=valor,
            source_name=candidato.source_name,
            data_source_type=candidato.data_source_type,
            reference_date=reference_date or candidato.fundamentals_reference,
            methodology=metodologia,
        )
