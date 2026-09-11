import json
import re

from ollama_client import generate


# --------------------------------------------------
# Prompt
# --------------------------------------------------

def build_company_prompt(
    domain: str,
    research_text: str
) -> str:
    """Build a compact structured company research prompt."""

    return f"""
You are a sales intelligence analyst.

Analyze the website research provided below for {domain}.

Return ONLY ONE VALID JSON OBJECT.
NO markdown.
NO explanation.
NO extra text before or after the JSON.

Use EXACTLY these fields:

{{
  "company_name": "",
  "industry": "",
  "company_description": "",
  "products_and_services": [],
  "target_customers": [],
  "business_model": "",
  "value_proposition": "",
  "pain_points": [],
  "outreach_angle": "",
  "personalized_message": ""
}}

STRICT OUTPUT LIMITS:

- company_name: maximum 5 words
- industry: maximum 5 words
- company_description: maximum 30 words
- products_and_services: maximum 8 items
- target_customers: maximum 6 items
- business_model: maximum 25 words
- value_proposition: maximum 30 words
- pain_points: maximum 5 items
- outreach_angle: maximum 30 words
- personalized_message: maximum 60 words

IMPORTANT:

1. Use ONLY information supported by the website research.
2. Do NOT invent company facts.
3. Do NOT repeat items.
4. Keep every answer concise.
5. Arrays must contain strings.
6. If information is unavailable, use "" or [].
7. Return the JSON object and STOP.

PERSONALIZED MESSAGE RULES:

8. Write a short, natural external sales outreach message.
9. The message MUST mention the actual company_name.
10. The message MUST mention at least ONE real product, service,
   customer type, business characteristic, or value proposition
   supported by the research.
11. Do NOT pretend that the sender works for the researched company.
12. Do NOT address an unknown person by name.
13. Do NOT use placeholders.
14. Do NOT use square brackets anywhere in personalized_message.
15. NEVER use:
   [Name]
   [Your Name]
   [Company Name]
   [company_name]
   [industry]
   [Industry]
   [Product]
   [products]
   [products_and_services]
   or anything else inside square brackets.
16. Do NOT use "your company", "the company", or "the business"
   when the actual company name is available.
17. Do not write a generic description of the researched company.
18. Start with an observation about the actual researched company.
19. Keep the message professional and concise.
20. The message must sound like a real external sales outreach message.
21. Do NOT write as if you are Stripe, Microsoft, Google, etc.
22. The sender is an external company offering a potential solution.
23. Do not use "we noticed your business has been growing" unless
    the research explicitly supports that claim.
24. Do not invent growth, revenue, customers, partnerships,
    problems, or business needs.

GOOD EXAMPLE:

"Stripe's global payments platform and support for businesses
across multiple markets create strong opportunities for payment
optimization. We'd be interested in exploring how our solution
could complement Stripe's existing infrastructure."

Use the actual researched company facts instead of copying
the example.

Domain:
{domain}

Website Research:
{research_text}
"""


# --------------------------------------------------
# JSON cleaning
# --------------------------------------------------

def clean_json_response(response: str) -> str:
    """Extract and clean JSON returned by the model."""

    cleaned = response.strip()

    # Remove markdown code fences.
    cleaned = re.sub(
        r"^```json\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"^```\s*",
        "",
        cleaned,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    cleaned = cleaned.strip()

    # Extract the JSON object if the model added text.
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]

    return cleaned.strip()


# --------------------------------------------------
# Validation / normalization
# --------------------------------------------------

def validate_enrichment(
    result: dict
) -> dict:
    """
    Validate and normalize AI enrichment.

    This function also enforces all output limits so
    the local model cannot produce oversized lists
    or excessively long messages.
    """

    required_fields = [
        "company_name",
        "industry",
        "company_description",
        "products_and_services",
        "target_customers",
        "business_model",
        "value_proposition",
        "pain_points",
        "outreach_angle",
        "personalized_message",
    ]

    # --------------------------------------------------
    # Add missing fields
    # --------------------------------------------------

    for field in required_fields:

        if field not in result:

            if field in [
                "products_and_services",
                "target_customers",
                "pain_points",
            ]:
                result[field] = []

            else:
                result[field] = ""

    # --------------------------------------------------
    # Normalize arrays
    # --------------------------------------------------

    array_limits = {
        "products_and_services": 8,
        "target_customers": 6,
        "pain_points": 5,
    }

    for field, limit in array_limits.items():

        value = result.get(field)

        if isinstance(value, str):

            value = [
                value.strip()
            ] if value.strip() else []

        elif isinstance(value, list):

            value = [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

        else:

            value = []

        # Remove duplicates while preserving order.
        unique_values = []
        seen = set()

        for item in value:

            key = item.lower()

            if key not in seen:

                seen.add(key)
                unique_values.append(item)

        # IMPORTANT:
        # Enforce the hard maximum.
        result[field] = unique_values[:limit]

    # --------------------------------------------------
    # Normalize text fields
    # --------------------------------------------------

    text_fields = [
        "company_name",
        "industry",
        "company_description",
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

    # --------------------------------------------------
    # Enforce personalized message limit
    # --------------------------------------------------

    message = result.get(
        "personalized_message",
        ""
    ).strip()

    words = message.split()

    if len(words) > 60:

        # Keep complete sentences where possible.
        shortened = " ".join(words[:60])

        # Avoid ending on an obvious incomplete word sequence.
        last_sentence = max(
            shortened.rfind("."),
            shortened.rfind("!"),
            shortened.rfind("?"),
        )

        if last_sentence >= 20:

            shortened = shortened[
                :last_sentence + 1
            ]

        else:

            shortened = shortened.rstrip(
                " ,;:-"
            ) + "."

        result["personalized_message"] = shortened

    return result


# --------------------------------------------------
# Personalized message fallback
# --------------------------------------------------

def build_fallback_personalized_message(
    result: dict
) -> str:
    """
    Build a deterministic personalized outreach message.

    This is used when the local LLM produces:
    - placeholders
    - generic wording
    - missing company name
    - invalid message content
    """

    company_name = str(
        result.get(
            "company_name",
            ""
        )
    ).strip()

    industry = str(
        result.get(
            "industry",
            ""
        )
    ).strip()

    products = result.get(
        "products_and_services",
        []
    )

    customers = result.get(
        "target_customers",
        []
    )

    value_proposition = str(
        result.get(
            "value_proposition",
            ""
        )
    ).strip()

    business_model = str(
        result.get(
            "business_model",
            ""
        )
    ).strip()

    # --------------------------------------------------
    # Select real researched facts
    # --------------------------------------------------

    product = ""

    if isinstance(products, list) and products:
        product = str(products[0]).strip()

    customer = ""

    if isinstance(customers, list) and customers:
        customer = str(customers[0]).strip()

    # --------------------------------------------------
    # Build external sales message
    # --------------------------------------------------

    if company_name and product:

        message = (
            f"{company_name}'s work with {product} caught our "
            f"attention. We'd be interested in exploring how "
            f"our solution could complement {company_name}'s "
            f"existing capabilities and support continued growth."
        )

    elif company_name and customer:

        message = (
            f"{company_name}'s focus on serving {customer} "
            f"caught our attention. We'd be interested in "
            f"exploring how our solution could complement "
            f"{company_name}'s existing capabilities and "
            f"support continued growth."
        )

    elif company_name and industry:

        message = (
            f"{company_name}'s position in {industry} caught "
            f"our attention. We'd be interested in exploring "
            f"how our solution could complement "
            f"{company_name}'s capabilities and support "
            f"continued growth."
        )

    elif company_name and value_proposition:

        short_value = value_proposition.rstrip(". ")

        message = (
            f"{company_name}'s approach to {short_value} "
            f"caught our attention. We'd be interested in "
            f"exploring how our solution could complement "
            f"{company_name}'s capabilities."
        )

    elif company_name and business_model:

        short_model = business_model.rstrip(". ")

        message = (
            f"{company_name}'s {short_model} model caught "
            f"our attention. We'd be interested in exploring "
            f"how our solution could complement "
            f"{company_name}'s capabilities and support "
            f"continued growth."
        )

    elif company_name:

        message = (
            f"{company_name}'s capabilities caught our "
            f"attention. We'd be interested in exploring "
            f"how our solution could complement "
            f"{company_name}'s existing capabilities."
        )

    else:

        message = (
            "The researched company's capabilities caught "
            "our attention. We'd be interested in exploring "
            "potential opportunities to work together."
        )

    # --------------------------------------------------
    # Final hard limit
    # --------------------------------------------------

    words = message.split()

    if len(words) > 60:

        message = " ".join(
            words[:60]
        )

        if not message.endswith(
            (".", "!", "?")
        ):
            message += "."

    return message


# --------------------------------------------------
# Personalized message validation
# --------------------------------------------------

def personalized_message_is_valid(
    result: dict
) -> bool:
    """
    Check whether the AI-generated message is safe
    and appropriate to display.
    """

    message = str(
        result.get(
            "personalized_message",
            ""
        )
    ).strip()

    company_name = str(
        result.get(
            "company_name",
            ""
        )
    ).strip()

    if not message:
        return False

    if not company_name:
        return False

    message_lower = message.lower()

    # --------------------------------------------------
    # Hard 60-word limit
    # --------------------------------------------------

    if len(message.split()) > 60:
        return False

    # --------------------------------------------------
    # Reject square-bracket placeholders
    # --------------------------------------------------

    if re.search(
        r"\[[^\]]+\]",
        message
    ):
        return False

    # --------------------------------------------------
    # Reject common template placeholders
    # --------------------------------------------------

    forbidden_phrases = [
        "[name]",
        "[your name]",
        "[company name]",
        "[company_name]",
        "[industry]",
        "[industry name]",
        "[product]",
        "[products]",
        "[products_and_services]",
        "your name",
        "your company",
        "the company",
        "the business",
    ]

    for phrase in forbidden_phrases:

        if phrase in message_lower:
            return False

    # --------------------------------------------------
    # Must mention actual company
    # --------------------------------------------------

    if company_name.lower() not in message_lower:
        return False

    # --------------------------------------------------
    # Reject pretending to be the researched company
    # --------------------------------------------------

    impersonation_patterns = [
        "we are " + company_name.lower(),
        "we're " + company_name.lower(),
        "at " + company_name.lower() + ", we",
        "our " + company_name.lower() + " platform",
        "our " + company_name.lower() + " products",
        "our " + company_name.lower() + " services",
    ]

    for phrase in impersonation_patterns:

        if phrase in message_lower:
            return False

    return True


# --------------------------------------------------
# Main enrichment
# --------------------------------------------------

def enrich_company(
    domain: str,
    research_text: str
) -> dict:
    """Use the local LLM to enrich company research."""

    prompt = build_company_prompt(
        domain,
        research_text
    )

    response = generate(
        prompt
    )

    cleaned = clean_json_response(
        response
    )

    # --------------------------------------------------
    # Parse JSON
    # --------------------------------------------------

    try:

        result = json.loads(
            cleaned
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            "The AI did not return valid JSON.\n"
            f"AI response:\n{response}"
        ) from error

    if not isinstance(result, dict):

        raise ValueError(
            "The AI response must be a JSON object."
        )

    # --------------------------------------------------
    # Normalize and enforce limits
    # --------------------------------------------------

    result = validate_enrichment(
        result
    )

    # --------------------------------------------------
    # Automatically fix bad AI messages
    # --------------------------------------------------

    if not personalized_message_is_valid(
        result
    ):

        result["personalized_message"] = (
            build_fallback_personalized_message(
                result
            )
        )

    # --------------------------------------------------
    # Final safety check
    # --------------------------------------------------

    # The deterministic fallback should always be valid.
    # If the company name is genuinely unavailable,
    # keep the message rather than failing the entire
    # company analysis.

    if result.get("company_name"):

        if not personalized_message_is_valid(
            result
        ):

            result["personalized_message"] = (
                build_fallback_personalized_message(
                    result
                )
            )

    return result