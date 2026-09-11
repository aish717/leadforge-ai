from typing import Any


def _to_list(value: Any) -> list[str]:
    """Convert a string or list into a clean list of strings."""

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str) and value.strip():
        return [value.strip()]

    return []


def calculate_fit_score(
    enrichment: dict[str, Any]
) -> int:
    """
    Calculate a deterministic lead-fit score from company enrichment.

    Score breakdown:
    - Industry relevance:       0-25
    - Target customer fit:     0-25
    - B2B/enterprise signals:  0-25
    - Product/service fit:     0-25

    Total: 0-100
    """

    industry = str(
        enrichment.get("industry", "")
    ).lower()

    description = str(
        enrichment.get("company_description", "")
    ).lower()

    business_model = str(
        enrichment.get("business_model", "")
    ).lower()

    products = _to_list(
        enrichment.get("products_and_services", [])
    )

    customers = _to_list(
        enrichment.get("target_customers", [])
    )

    customer_text = " ".join(
        customers
    ).lower()

    product_text = " ".join(
        products
    ).lower()

    full_text = " ".join([
        industry,
        description,
        business_model,
        customer_text,
        product_text,
    ])

    # --------------------------------------------------
    # 1. Industry relevance: 0-25
    # --------------------------------------------------

    industry_score = 5

    relevant_industries = [
        "software",
        "technology",
        "saas",
        "financial",
        "fintech",
        "artificial intelligence",
        "ai",
        "cloud",
        "cybersecurity",
        "developer",
        "api",
        "data",
        "automation",
    ]

    if any(
        keyword in industry
        for keyword in relevant_industries
    ):
        industry_score = 25

    elif industry:
        industry_score = 15

    else:
        industry_score = 5

    # --------------------------------------------------
    # 2. Target customer fit: 0-25
    # --------------------------------------------------

    customer_score = 5

    enterprise_keywords = [
        "enterprise",
        "enterprises",
        "business",
        "businesses",
        "organization",
        "organizations",
        "developer",
        "developers",
        "devops",
        "companies",
        "platforms",
        "marketplaces",
        "startups",
        "saas",
    ]

    customer_matches = sum(
        1
        for keyword in enterprise_keywords
        if keyword in customer_text
    )

    if customer_matches >= 4:
        customer_score = 25

    elif customer_matches >= 2:
        customer_score = 20

    elif customer_matches >= 1:
        customer_score = 15

    else:
        customer_score = 5

    # --------------------------------------------------
    # 3. B2B / Enterprise signals: 0-25
    # --------------------------------------------------

    b2b_keywords = [
        "enterprise",
        "business",
        "businesses",
        "developer",
        "developers",
        "api",
        "platform",
        "software",
        "organization",
        "organizations",
        "saas",
        "devops",
        "companies",
        "marketplace",
    ]

    b2b_matches = sum(
        1
        for keyword in b2b_keywords
        if keyword in full_text
    )

    if b2b_matches >= 6:
        b2b_score = 25

    elif b2b_matches >= 4:
        b2b_score = 20

    elif b2b_matches >= 2:
        b2b_score = 15

    elif b2b_matches >= 1:
        b2b_score = 10

    else:
        b2b_score = 5

    # --------------------------------------------------
    # 4. Product/service fit: 0-25
    # --------------------------------------------------

    product_score = 5

    if len(products) >= 6:
        product_score = 25

    elif len(products) >= 4:
        product_score = 20

    elif len(products) >= 2:
        product_score = 15

    elif len(products) == 1:
        product_score = 10

    # Strong technology/product signals
    product_signals = [
        "api",
        "platform",
        "software",
        "cloud",
        "automation",
        "ai",
        "payment",
        "payments",
        "security",
        "analytics",
        "developer",
    ]

    if any(
        keyword in product_text
        for keyword in product_signals
    ):
        product_score = min(
            product_score + 5,
            25
        )

    # --------------------------------------------------
    # Final score
    # --------------------------------------------------

    score = (
        industry_score
        + customer_score
        + b2b_score
        + product_score
    )

    return min(
        max(score, 0),
        100
    )


def classify_lead(
    company_description: str,
    target_customers: list[str],
) -> str:
    """Classify the company into a simple lead category."""

    text = (
        str(company_description)
        + " "
        + " ".join(
            str(item)
            for item in target_customers
        )
    ).lower()

    enterprise_keywords = [
        "enterprise",
        "large organizations",
        "large organization",
        "businesses",
        "companies",
        "corporations",
    ]

    b2b_keywords = [
        "business",
        "developer",
        "developers",
        "api",
        "software",
        "platform",
        "enterprise",
        "organization",
    ]

    if any(
        keyword in text
        for keyword in enterprise_keywords
    ):
        return "Enterprise / B2B"

    if any(
        keyword in text
        for keyword in b2b_keywords
    ):
        return "B2B"

    return "General"


def get_fit_level(
    score: int
) -> str:
    """Convert numeric score into a fit level."""

    if score >= 80:
        return "High"

    if score >= 60:
        return "Medium"

    return "Low"


def build_lead_profile(
    enrichment: dict[str, Any]
) -> dict[str, Any]:
    """
    Build a deterministic lead profile from AI enrichment.
    """

    description = str(
        enrichment.get(
            "company_description",
            ""
        )
    )

    customers = _to_list(
        enrichment.get(
            "target_customers",
            []
        )
    )

    score = calculate_fit_score(
        enrichment
    )

    fit_level = get_fit_level(
        score
    )

    lead_type = classify_lead(
        description,
        customers,
    )

    return {
        "lead_type": lead_type,
        "fit_score": score,
        "fit_level": fit_level,
        "scoring_method": (
            "Deterministic rule-based scoring"
        ),
    }


def add_deterministic_lead_score(
    enrichment: dict[str, Any]
) -> dict[str, Any]:
    """
    Add the deterministic lead profile to an
    enrichment dictionary.

    The original dictionary is not modified.
    """

    result = dict(
        enrichment
    )

    result["lead_profile"] = (
        build_lead_profile(
            enrichment
        )
    )

    return result