from app.lead_scoring import (
    calculate_fit_score,
    add_deterministic_lead_score,
)


def test_enterprise_technology_company_scores_high():
    enrichment = {
        "company_name": "ExampleTech",
        "industry": "Software Technology",
        "company_description": (
            "A cloud platform for enterprise developers."
        ),
        "products_and_services": [
            "API Platform",
            "AI Automation",
            "Cloud Software",
        ],
        "target_customers": [
            "Developers",
            "DevOps Engineers",
            "Enterprise Organizations",
        ],
        "business_model": "SaaS subscription",
    }

    score = calculate_fit_score(enrichment)

    assert score >= 70
    assert score <= 100


def test_irrelevant_company_scores_lower():
    enrichment = {
        "company_name": "ExampleStore",
        "industry": "Retail",
        "company_description": "A local retail store.",
        "products_and_services": [
            "Clothing",
            "Furniture",
        ],
        "target_customers": [
            "Consumers",
        ],
        "business_model": "Physical retail",
    }

    score = calculate_fit_score(enrichment)

    assert score < 70


def test_score_is_between_zero_and_hundred():
    enrichment = {
        "company_name": "Test",
        "industry": "",
        "company_description": "",
        "products_and_services": [],
        "target_customers": [],
        "business_model": "",
    }

    score = calculate_fit_score(enrichment)

    assert 0 <= score <= 100


def test_string_lists_are_supported():
    enrichment = {
        "industry": "Software",
        "company_description": "SaaS platform",
        "products_and_services": "API Platform",
        "target_customers": "Enterprise organizations",
        "business_model": "SaaS subscription",
    }

    score = calculate_fit_score(enrichment)

    assert isinstance(score, int)
    assert 0 <= score <= 100


def test_lead_profile_is_added():
    enrichment = {
        "industry": "Software",
        "company_description": "Enterprise SaaS platform",
        "products_and_services": [
            "API Platform",
        ],
        "target_customers": [
            "Enterprise organizations",
        ],
        "business_model": "SaaS subscription",
    }

    result = add_deterministic_lead_score(
        enrichment
    )

    assert "lead_profile" in result

    assert (
        result["lead_profile"]["scoring_method"]
        == "Deterministic rule-based scoring"
    )

    assert (
        0
        <= result["lead_profile"]["fit_score"]
        <= 100
    )