from src.invest_ai.domain import (
    AnalysisStatus,
    CandidateAnalysis,
    Capability,
    CapabilitySupport,
    Compatibility,
    EvidenceReference,
    InvestmentAnalysis,
    InvestorNeed,
    NeedAssessment,
    RecommendationCapabilityMatrix,
)


def test_investor_need_preserves_unknown_information_as_none():
    need = InvestorNeed(available_capital=500.0, objective="INCOME", periodic_income=True)

    assert need.available_capital == 500.0
    assert need.objective == "INCOME"
    assert need.risk_tolerance is None
    assert need.liquidity_need is None


def test_need_assessment_explicitly_reports_missing_information():
    assessment = NeedAssessment(
        sufficient=False,
        missing_fields=("risk_tolerance", "liquidity_need"),
    )

    assert assessment.sufficient is False
    assert assessment.missing_fields == ("risk_tolerance", "liquidity_need")


def test_capability_matrix_supports_only_documented_capabilities():
    assert RecommendationCapabilityMatrix.is_supported(Capability.AVAILABLE_CAPITAL)
    assert RecommendationCapabilityMatrix.is_supported(Capability.HISTORICAL_INCOME)
    assert not RecommendationCapabilityMatrix.is_supported(Capability.RISK)
    assert not RecommendationCapabilityMatrix.is_supported(Capability.LIQUIDITY)


def test_capability_matrix_marks_monthly_income_as_partial():
    rule = RecommendationCapabilityMatrix.get(Capability.MONTHLY_INCOME_REGULARITY)

    assert rule.support == CapabilitySupport.PARTIAL


def test_unsupported_capabilities_are_explicit():
    unsupported = RecommendationCapabilityMatrix.unsupported(
        (
            Capability.AVAILABLE_CAPITAL,
            Capability.RISK,
            Capability.FUTURE_INCOME,
        )
    )

    assert unsupported == (Capability.RISK, Capability.FUTURE_INCOME)


def test_analysis_can_link_candidate_claims_to_evidence():
    evidence = EvidenceReference(
        asset_id="TEST11",
        metric="income12mPerShare",
        value=10.50,
        source_name="Fundos.NET",
        data_source_type="SNAPSHOT",
        reference_date="2026-09-01",
    )
    candidate = CandidateAnalysis(
        asset_id="TEST11",
        compatibility=Compatibility.COMPATIBLE,
        matched_criteria=("HISTORICAL_INCOME",),
        evidence=(evidence,),
    )
    analysis = InvestmentAnalysis(
        status=AnalysisStatus.READY,
        user_need=InvestorNeed(objective="INCOME"),
        candidates=(candidate,),
        supported_criteria=("HISTORICAL_INCOME",),
        evidence=(evidence,),
    )

    assert analysis.candidates[0].evidence[0].metric == "income12mPerShare"
    assert analysis.evidence[0].data_source_type == "SNAPSHOT"


def test_partial_analysis_can_expose_unsupported_user_criteria():
    analysis = InvestmentAnalysis(
        status=AnalysisStatus.PARTIAL_ANALYSIS,
        user_need=InvestorNeed(
            available_capital=500,
            objective="INCOME",
            risk_tolerance="LOW",
            liquidity_need="HIGH",
        ),
        supported_criteria=("AVAILABLE_CAPITAL", "HISTORICAL_INCOME"),
        unsupported_criteria=("RISK", "LIQUIDITY"),
    )

    assert analysis.status == AnalysisStatus.PARTIAL_ANALYSIS
    assert analysis.unsupported_criteria == ("RISK", "LIQUIDITY")
