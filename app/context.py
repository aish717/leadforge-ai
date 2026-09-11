from models import CompanyResearch


MAX_CHARS = 8000


def build_research_context(
    research: CompanyResearch,
    max_chars: int = MAX_CHARS,
) -> str:
    """
    Build a compact research context for the LLM.

    Higher-priority pages are included first.
    """

    pages = sorted(
        research.pages,
        key=lambda page: page.priority,
        reverse=True,
    )

    sections = []
    total_chars = 0

    for page in pages:

        section = (
            f"\n\n--- SOURCE: {page.url} "
            f"(priority={page.priority}) ---\n"
            f"{page.text}"
        )

        remaining = max_chars - total_chars

        if remaining <= 0:
            break

        if len(section) > remaining:
            section = section[:remaining]

        sections.append(section)

        total_chars += len(section)

    return "".join(sections)