import json
import re

from ollama_client import generate


MAX_LIMITS = {
    "target_audience": 6,
    "contact_points": 8,
    "leadership_team": 8,
    "products_and_services": 8,
    "pain_points": 5,
}


def build_company_prompt(
    domain: str,
    research_text: str,
) -> str:
    """Build a structured company research prompt."""

    return f"""
You are a sales intelligence analyst.

Analyze the website research below for {domain}.

Return ONLY ONE VALID JSON OBJECT.
NO markdown.
NO explanation.
NO extra text before or after the JSON.

Use EXACTLY these fields:

{{
  "company_name": "",
  "industry": "",
  "company_overview": "",
  "target_audience": [],
  "contact_points": [],
  "leadership_team": [],
  "products_and_services": [],
  "business_model": "",
  "value_proposition": "",
  "pain_points": [],
  "outreach_angle": "",
  "personalized_message": "",
  "data_confidence_score": 0.0
}}

STRICT LIMITS:

- company_name: maximum 5 words
- industry: maximum 5 words
- company_overview: maximum 40 words
- target_audience: maximum 6 items
- contact_points: maximum 8 items
- leadership_team: maximum 8 items
- products_and_services: maximum 8 items
- business_model: maximum 25 words
- value_proposition: maximum 30 words
- pain_points: maximum 5 items
- outreach_angle: maximum 30 words
- personalized_message: maximum 60 words
- data_confidence_score: number between 0.0 and 1.0

LEADERSHIP TEAM:

Each item must be:

"Name - Role - LinkedIn URL"

If LinkedIn is unavailable:

"Name - Role"

Do NOT invent LinkedIn URLs.

CONTACT POINTS:

Include only actual public contact information found
in the research.

Examples:

contact@example.com
sales@example.com
support@example.com

Do NOT invent email addresses.

IMPORTANT:

1. Use ONLY information supported by the research.
2. Do NOT invent company facts.
3. Do NOT repeat information.
4. Keep everything concise.
5. Arrays must contain strings.
6. If information is unavailable, use "" or [].
7. data_confidence_score must be between 0.0 and 1.0.
8. Return the JSON object and STOP.

PERSONALIZED MESSAGE RULES:

9. Write personalized_message specifically for the researched company.
10. Mention the ACTUAL company name.
11. Mention at least ONE actual product, service, customer type,
    or business characteristic from the research.
12. Write a natural external sales/outreach message.
13. Do NOT pretend the sender works for the researched company.
14. Do NOT write a generic company description.
15. Do NOT address an unknown person by name.
16. NEVER use placeholders.
17. NEVER use square brackets.
18. NEVER use text such as:
    [Name]
    [Your Name]
    [Company Name]
    [company_name]
    [industry]
    [Industry]
    [Product]
    [products_and_services]
19. Do NOT use generic template phrases such as:
    "your company"
    "your business"
    "the company"
    "the business"
    when the actual company name can be used.
20. The final message must sound like real personalized outreach.

GOOD EXAMPLE:

"Stripe's global payments platform and support for multiple
payment methods create strong opportunities to improve
payment experiences. We would be interested in exploring
how our solution could complement Stripe's existing
infrastructure."

BAD EXAMPLE:

"Dear [Name], as a [industry] professional, I understand
your company's needs."

RESEARCH:

{research_text}
"""


def clean_json_response(response: str) -> str:
    """Extract JSON from the model response."""

    cleaned = response.strip()

    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1]

    if "```" in cleaned:
        cleaned = cleaned.split("```", 1)[0]

    cleaned = cleaned.strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]

    return cleaned.strip()


def validate_enrichment(result: dict) -> dict:
    """Validate and normalize AI enrichment."""

    required_fields = [
        "company_name",
        "industry",
        "company_overview",
        "target_audience",
        "contact_points",
        "leadership_team",
        "products_and_services",
        "business_model",
        "value_proposition",
        "pain_points",
        "outreach_angle",
        "personalized_message",
        "data_confidence_score",
    ]

    for field in required_fields:

        if field not in result:

            if field in [
                "target_audience",
                "contact_points",
                "leadership_team",
                "products_and_services",
                "pain_points",
            ]:
                result[field] = []

            elif field == "data_confidence_score":
                result[field] = 0.0

            else:
                result[field] = ""

    array_fields = [
        "target_audience",
        "contact_points",
        "leadership_team",
        "products_and_services",
        "pain_points",
    ]

    for field in array_fields:

        value = result.get(field)

        if isinstance(value, str):

            if value.strip():
                result[field] = [value.strip()]
            else:
                result[field] = []

        elif isinstance(value, list):

            cleaned_items = []

            for item in value:

                text = str(item).strip()

                if text:
                    cleaned_items.append(text)

            result[field] = cleaned_items

        else:
            result[field] = []

    # Enforce maximum array sizes.
    for field, limit in MAX_LIMITS.items():
        result[field] = result[field][:limit]

    text_fields = [
        "company_name",
        "industry",
        "company_overview",
        "business_model",
        "value_proposition",
        "outreach_angle",
        "personalized_message",
    ]

    for field in text_fields:

        value = result.get(field, "")

        if value is None:
            result[field] = ""

        else:
            result[field] = str(value).strip()

    # Normalize confidence score.
    try:
        confidence = float(
            result.get(
                "data_confidence_score",
                0.0,
            )
        )

    except (TypeError, ValueError):
        confidence = 0.0

    result["data_confidence_score"] = min(
        max(confidence, 0.0),
        1.0,
    )

    return result


def check_personalized_message(result: dict) -> None:
    """Validate and clean the personalized outreach message."""

    message = result.get("personalized_message", "").strip()
    company_name = result.get("company_name", "").strip()

    if not message:
        raise ValueError(
            "The AI generated an empty personalized message."
        )

    # Remove common greeting placeholders.
    message = re.sub(
        r"\[name\]\s*,?\s*",
        "",
        message,
        flags=re.IGNORECASE,
    )

    # Remove other square-bracket placeholders.
    message = re.sub(
        r"\[[^\]]+\]",
        "",
        message,
    )

    # Remove common template phrases.
    message = re.sub(
        r"\bDear\s*,",
        "",
        message,
        flags=re.IGNORECASE,
    )

    message = re.sub(
        r"\bDear\s+professional\s*,?",
        "",
        message,
        flags=re.IGNORECASE,
    )

    message = re.sub(
        r"\s{2,}",
        " ",
        message,
    ).strip()

    # The message must contain the actual company name.
    if company_name and company_name.lower() not in message.lower():
        raise ValueError(
            "The personalized message does not mention "
            "the researched company name."
        )

    # Reject if anything resembling a placeholder remains.
    if re.search(r"\[[^\]]+\]", message):
        raise ValueError(
            "The personalized message still contains "
            "a placeholder."
        )

    # Save the cleaned message back into the result.
    result["personalized_message"] = message


def parse_and_validate_response(
    response: str,
) -> dict:
    """Parse, normalize and validate one AI response."""

    cleaned = clean_json_response(response)

    try:

        result = json.loads(cleaned)

    except json.JSONDecodeError as error:

        raise ValueError(
            "The AI did not return valid JSON.\n"
            f"AI response:\n{response}"
        ) from error

    if not isinstance(result, dict):

        raise ValueError(
            "The AI response must be a JSON object."
        )

    result = validate_enrichment(result)

    check_personalized_message(result)

    return result


def build_retry_prompt(
    domain: str,
    research_text: str,
) -> str:
    """
    Build a stricter retry prompt when the first AI response
    contains invalid personalized outreach.
    """

    return f"""
You previously generated invalid output.

Generate the company enrichment again for {domain}.

IMPORTANT:
The personalized_message MUST NOT contain ANY placeholders.

Do NOT use:
[Name]
[Your Name]
[Company Name]
[company_name]
[industry]
[Product]
[anything inside square brackets]

Do NOT use:
your company
your business
the company
the business

Use the ACTUAL researched company name.

The personalized message MUST:
- mention the actual company name
- mention at least one real product, service, customer type,
  or business characteristic from the research
- sound like external sales outreach
- contain no placeholders
- contain no square brackets
- be 60 words or fewer

Return ONLY valid JSON.

Use EXACTLY these fields:

{{
  "company_name": "",
  "industry": "",
  "company_overview": "",
  "target_audience": [],
  "contact_points": [],
  "leadership_team": [],
  "products_and_services": [],
  "business_model": "",
  "value_proposition": "",
  "pain_points": [],
  "outreach_angle": "",
  "personalized_message": "",
  "data_confidence_score": 0.0
}}

RESEARCH:

{research_text}
"""


def enrich_company(
    domain: str,
    research_text: str,
) -> dict:
    """Use the local LLM to enrich company research."""

    prompt = build_company_prompt(
        domain,
        research_text,
    )

    print("\nGenerating AI enrichment...")

    response = generate(prompt)

    try:
        result = parse_and_validate_response(response)

    except ValueError as error:

        raise ValueError(
            "AI enrichment returned invalid structured data.\n"
            f"{error}"
        ) from error
    
    result = validate_enrichment(result)
    check_personalized_message(result)
    return result