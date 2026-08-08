from score_cis import calculate_score


def test_full_equal_scores():
    result = calculate_score(
        {
            "fundamentals": 80,
            "growth": 80,
            "valuation": 80,
            "industry_competitive": 80,
            "technical": 80,
            "catalyst_macro": 80,
            "positioning": 80,
            "risk_resilience": 80,
        }
    )
    assert result.score == 80.0
    assert result.coverage_pct == 100.0
    assert result.grade == "decision_grade"
    assert result.research_posture == "进入深入研究"


def test_low_coverage_suppresses_total():
    result = calculate_score({"fundamentals": 90, "growth": 90, "valuation": 90})
    assert result.coverage_pct == 50.0
    assert result.score is None
    assert result.grade == "insufficient"
    assert result.research_posture == "证据不足"


def test_provisional_coverage():
    result = calculate_score(
        {
            "fundamentals": 90,
            "growth": 80,
            "valuation": 75,
            "industry_competitive": 80,
            "technical": 70,
        }
    )
    assert result.coverage_pct == 75.0
    assert result.grade == "provisional"
    assert result.score is not None


def test_risk_block_prevents_decision_grade():
    result = calculate_score({key: 90 for key in (
        "fundamentals",
        "growth",
        "valuation",
        "industry_competitive",
        "technical",
        "catalyst_macro",
        "positioning",
        "risk_resilience",
    )}, risk_override="block")
    assert result.grade == "provisional"
    assert "risk_override_block" in result.blocked_reasons
    assert "风险门未通过" in result.research_posture


def test_audit_unresolved_returns_insufficient_posture():
    result = calculate_score({key: 90 for key in (
        "fundamentals",
        "growth",
        "valuation",
        "industry_competitive",
        "technical",
        "catalyst_macro",
        "positioning",
        "risk_resilience",
    )}, audit_status="unresolved")
    assert result.grade == "provisional"
    assert result.research_posture == "证据不足"
