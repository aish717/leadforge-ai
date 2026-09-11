import json
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

from models import CrawledPage, CompanyResearch
from context import build_research_context
from ai_enrichment import enrich_company
from lead_scoring import build_lead_profile


HEADERS = {
    "User-Agent": "LeadForgeAI/1.0"
}


PAGE_PRIORITY = {
    "about": 100,
    "company": 95,
    "team": 90,
    "leadership": 90,
    "contact": 85,
    "pricing": 70,
    "customer": 65,
    "solution": 60,
    "product": 40,
}


# --------------------------------------------------
# URL helpers
# --------------------------------------------------

def normalize_url(url: str) -> str:
    """Normalize a company URL."""

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url.rstrip("/")


def get_output_filename(base_url: str) -> str:
    """Create a safe output filename from the domain."""

    domain = urlparse(base_url).netloc.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    filename = domain.replace(".", "_")

    return filename + "_research.json"


# --------------------------------------------------
# HTTP / Browser fetching
# --------------------------------------------------

def fetch_with_httpx(url: str) -> str:
    """Fetch a webpage using HTTPX."""

    response = httpx.get(
        url,
        timeout=15,
        follow_redirects=True,
        headers=HEADERS,
    )

    response.raise_for_status()

    return response.text


def fetch_with_playwright(url: str) -> str:
    """Fetch a webpage using Playwright."""

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            user_agent=HEADERS["User-Agent"]
        )

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        # Allow JavaScript content to render.
        page.wait_for_timeout(1500)

        html = page.content()

        browser.close()

        return html


def fetch_page(url: str) -> tuple[str, str]:
    """
    Fetch a webpage.

    Try HTTPX first because it is faster.
    Fall back to Playwright if HTTPX fails.
    """

    try:

        html = fetch_with_httpx(url)

        print("  Method: HTTPX")

        return html, "httpx"

    except Exception as error:

        print(
            f"  HTTPX failed: {error}"
        )

        print(
            "  Trying Playwright..."
        )

        html = fetch_with_playwright(
            url
        )

        print(
            "  Method: Playwright"
        )

        return html, "playwright"


# --------------------------------------------------
# Text extraction
# --------------------------------------------------

def extract_text(html: str) -> str:
    """Extract readable text from HTML."""

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "iframe",
        ]
    ):
        element.decompose()

    return soup.get_text(
        " ",
        strip=True
    )


# --------------------------------------------------
# Link scoring
# --------------------------------------------------

def score_url(url: str) -> int:
    """Assign a relevance score to a URL."""

    path = urlparse(
        url
    ).path.lower()

    score = 0

    for keyword, points in PAGE_PRIORITY.items():

        if keyword in path:

            score = max(
                score,
                points
            )

    return score


def discover_links(
    base_url: str,
    html: str
) -> list[str]:
    """Discover and prioritize useful internal links."""

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    base_domain = urlparse(
        base_url
    ).netloc

    discovered = set()

    for link in soup.find_all(
        "a",
        href=True
    ):

        href = link["href"]

        absolute_url = urljoin(
            base_url,
            href
        )

        parsed = urlparse(
            absolute_url
        )

        # Only keep links belonging to
        # the same company domain.
        if parsed.netloc != base_domain:
            continue

        clean_url = (
            absolute_url
            .split("#")[0]
            .rstrip("/")
        )

        if clean_url == base_url.rstrip("/"):
            continue

        if score_url(clean_url) > 0:

            discovered.add(
                clean_url
            )

    return sorted(
        discovered,
        key=score_url,
        reverse=True
    )


# --------------------------------------------------
# Crawling
# --------------------------------------------------

def crawl_pages(
    urls: list[str],
    max_pages: int = 8
) -> dict[str, str]:
    """Crawl the highest-priority pages."""

    results = {}

    for url in urls[:max_pages]:

        print(
            f"\nCrawling: {url}"
        )

        print(
            f"Priority score: "
            f"{score_url(url)}"
        )

        try:

            html, method = fetch_page(
                url
            )

            text = extract_text(
                html
            )

            if text:

                results[url] = text

                print(
                    f"  ✓ Extracted "
                    f"{len(text):,} characters"
                )

            else:

                print(
                    "  ✗ No readable text found"
                )

        except Exception as error:

            print(
                f"  ✗ Failed completely: "
                f"{error}"
            )

    return results


# --------------------------------------------------
# Structured research
# --------------------------------------------------

def build_company_research(
    base_url: str,
    pages: dict[str, str]
) -> CompanyResearch:
    """Convert crawled pages into structured research."""

    return CompanyResearch(
        domain=urlparse(
            base_url
        ).netloc,
        pages=[
            CrawledPage(
                url=url,
                text=text,
                priority=score_url(url),
            )
            for url, text in pages.items()
        ],
    )


# --------------------------------------------------
# Main pipeline
# --------------------------------------------------

def main():

    # --------------------------------------------------
    # 0. Read company URL
    # --------------------------------------------------

    if len(sys.argv) < 2:

        print(
            "\nUsage:"
        )

        print(
            "  python app\\main.py <company_url>"
        )

        print(
            "\nExample:"
        )

        print(
            "  python app\\main.py https://postman.com"
        )

        print(
            "  python app\\main.py https://stripe.com"
        )

        return

    base_url = normalize_url(
        sys.argv[1]
    )

    parsed = urlparse(
        base_url
    )

    if not parsed.netloc:

        print(
            "Error: Invalid company URL."
        )

        return

    print(
        f"Fetching homepage: "
        f"{base_url}\n"
    )

    # --------------------------------------------------
    # 1. Crawl homepage
    # --------------------------------------------------

    try:

        homepage_html, _ = fetch_page(
            base_url
        )

    except Exception as error:

        print(
            "\nFailed to fetch company website:"
        )

        print(error)

        return

    homepage_text = extract_text(
        homepage_html
    )

    print(
        f"Homepage HTML: "
        f"{len(homepage_html):,} characters"
    )

    print(
        f"Homepage text: "
        f"{len(homepage_text):,} characters"
    )

    # --------------------------------------------------
    # 2. Discover useful pages
    # --------------------------------------------------

    links = discover_links(
        base_url,
        homepage_html
    )

    print(
        f"\nDiscovered "
        f"{len(links)} prioritized pages."
    )

    print("\nTop pages:")

    for link in links[:15]:

        print(
            f"[{score_url(link):3}] "
            f"{link}"
        )

    # --------------------------------------------------
    # 3. Crawl selected pages
    # --------------------------------------------------

    pages = crawl_pages(
        links,
        max_pages=8
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "CRAWL SUMMARY"
    )

    print(
        "=" * 60
    )

    print(
        f"Pages successfully crawled: "
        f"{len(pages)}"
    )

    total_characters = sum(
        len(text)
        for text in pages.values()
    )

    print(
        f"Total extracted characters: "
        f"{total_characters:,}"
    )

    # --------------------------------------------------
    # 4. Build structured research
    # --------------------------------------------------

    research = build_company_research(
        base_url,
        pages
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STRUCTURED RESEARCH"
    )

    print(
        "=" * 60
    )

    print(
        f"Domain: "
        f"{research.domain}"
    )

    print(
        f"Pages: "
        f"{len(research.pages)}"
    )

    # --------------------------------------------------
    # 5. Build compact AI context
    # --------------------------------------------------

    research_context = build_research_context(
        research
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "AI CONTEXT"
    )

    print(
        "=" * 60
    )

    print(
        f"Original characters: "
        f"{total_characters:,}"
    )

    print(
        f"AI context characters: "
        f"{len(research_context):,}"
    )

    # --------------------------------------------------
    # 6. Run local AI enrichment
    # --------------------------------------------------

    print(
        "\n"
        + "=" * 60
    )

    print(
        "RUNNING LOCAL AI"
    )

    print(
        "=" * 60
    )

    print(
        "Model: qwen2.5:3b"
    )

    print(
        "This may take a little while..."
    )

    try:

        enrichment = enrich_company(
            research.domain,
            research_context
        )

    except Exception as error:

        print(
            "\nAI enrichment failed:"
        )

        print(error)

        return

    # --------------------------------------------------
    # 7. Display final result
    # --------------------------------------------------

    print(
        "\n"
        + "=" * 60
    )

    print(
        "AI ENRICHMENT RESULT"
    )

    print(
        "=" * 60
    )

    print(
        json.dumps(
            enrichment,
            indent=2,
            ensure_ascii=False
        )
    )

    # --------------------------------------------------
    # 8. Build lead profile
    # --------------------------------------------------

    print(
        "\n"
        + "=" * 60
    ) 

    print(
        "LEAD ANALYSIS"
    )

    print(
        "=" * 60
    )

    lead_profile = build_lead_profile(
        enrichment
    )

    print(
        json.dumps(
            lead_profile,
            indent=2,
            ensure_ascii=False
        )
    )

    # Add lead profile to final enrichment.
    enrichment["lead_profile"] = lead_profile

    # --------------------------------------------------
    # 9. Save JSON output
    # --------------------------------------------------

    output_dir = Path(
        "outputs"
    )

    output_dir.mkdir(
        exist_ok=True
    )

    output_filename = get_output_filename(
        base_url
    )

    output_path = (
        output_dir /
        output_filename
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            enrichment,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        "\n✓ JSON output saved to:"
    )

    print(
        output_path
    )


if __name__ == "__main__":
    main()