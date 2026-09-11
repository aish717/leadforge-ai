import json
import sys
from pathlib import Path

import streamlit as st


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="LeadForge AI",
    page_icon="🚀",
    layout="wide",
)


# --------------------------------------------------
# Styling
# --------------------------------------------------

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 30px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Header
# --------------------------------------------------

st.markdown(
    '<div class="main-title">🚀 LeadForge AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "AI-powered company intelligence and lead qualification"
    "</div>",
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Input
# --------------------------------------------------

company_url = st.text_input(
    "Company website",
    placeholder="https://stripe.com",
)

analyze = st.button(
    "🔍 Analyze Company",
    type="primary",
    use_container_width=True,
)


# --------------------------------------------------
# Analysis
# --------------------------------------------------

if analyze:

    if not company_url.strip():

        st.error(
            "Please enter a company website."
        )

        st.stop()

    # Make sure Python can import the app package.
    project_root = Path(__file__).resolve().parent.parent

    if str(project_root) not in sys.path:
        sys.path.insert(
            0,
            str(project_root)
        )

    try:

        from main import (
            normalize_url,
            fetch_page,
            extract_text,
            discover_links,
            crawl_pages,
            build_company_research,
            build_research_context,
            enrich_company,
            build_lead_profile,
        )

    except ImportError as error:

        st.error(
            f"Could not load LeadForge modules: {error}"
        )

        st.stop()

    base_url = normalize_url(
        company_url
    )

    # --------------------------------------------------
    # Run pipeline
    # --------------------------------------------------

    progress = st.progress(0)
    status = st.empty()

    try:

        # Fetch homepage
        status.write(
            "🌐 Fetching company website..."
        )

        progress.progress(10)

        homepage_html, _ = fetch_page(
            base_url
        )

        homepage_text = extract_text(
            homepage_html
        )

        # Discover pages
        status.write(
            "🔎 Discovering relevant pages..."
        )

        progress.progress(25)

        links = discover_links(
            base_url,
            homepage_html
        )

        # Crawl pages
        status.write(
            f"📄 Crawling {min(len(links), 8)} relevant pages..."
        )

        progress.progress(40)

        pages = crawl_pages(
            links,
            max_pages=8
        )

        # Build research
        status.write(
            "🧠 Building research context..."
        )

        progress.progress(60)

        research = build_company_research(
            base_url,
            pages
        )

        research_context = build_research_context(
            research
        )

        # AI enrichment
        status.write(
            "🤖 Running local AI enrichment..."
        )

        progress.progress(70)

        enrichment = enrich_company(
            research.domain,
            research_context
        )

        # Lead scoring
        status.write(
            "📊 Calculating lead score..."
        )

        progress.progress(90)

        lead_profile = build_lead_profile(
            enrichment
        )

        enrichment["lead_profile"] = lead_profile

        progress.progress(100)

        status.success(
            "Analysis complete!"
        )

    except Exception as error:

        progress.empty()
        status.empty()

        st.error(
            f"Analysis failed: {error}"
        )

        st.stop()


    # --------------------------------------------------
    # Company overview
    # --------------------------------------------------

    st.divider()

    company_name = enrichment.get(
        "company_name",
        "Unknown Company"
    )

    industry = enrichment.get(
        "industry",
        "Unknown industry"
    )

    description = enrichment.get(
        "company_description",
        ""
    )

    st.header(
        company_name
    )

    st.caption(
        industry
    )

    if description:
        st.write(
            description
        )


    # --------------------------------------------------
    # Lead score
    # --------------------------------------------------

    st.divider()

    st.subheader(
        "🎯 Lead Analysis"
    )

    col1, col2, col3 = st.columns(3)

    score = lead_profile.get(
        "fit_score",
        0
    )

    fit_level = lead_profile.get(
        "fit_level",
        "Unknown"
    )

    lead_type = lead_profile.get(
        "lead_type",
        "Unknown"
    )

    with col1:

        st.metric(
            "Fit Score",
            f"{score}/100"
        )

    with col2:

        st.metric(
            "Fit Level",
            fit_level
        )

    with col3:

        st.metric(
            "Lead Type",
            lead_type
        )


    # --------------------------------------------------
    # Products and customers
    # --------------------------------------------------

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "🛠 Products & Services"
        )

        products = enrichment.get(
            "products_and_services",
            []
        )

        if isinstance(products, list):

            for product in products:

                st.write(
                    f"• {product}"
                )

        elif products:

            st.write(
                products
            )

        else:

            st.caption(
                "No product information available."
            )


    with col2:

        st.subheader(
            "👥 Target Customers"
        )

        customers = enrichment.get(
            "target_customers",
            []
        )

        if isinstance(customers, list):

            for customer in customers:

                st.write(
                    f"• {customer}"
                )

        elif customers:

            st.write(
                customers
            )

        else:

            st.caption(
                "No customer information available."
            )


    # --------------------------------------------------
    # Business information
    # --------------------------------------------------

    st.divider()

    st.subheader(
        "💼 Business Information"
    )

    business_model = enrichment.get(
        "business_model",
        ""
    )

    value_proposition = enrichment.get(
        "value_proposition",
        ""
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            "**Business Model**"
        )

        if business_model:

            st.write(
                business_model
            )

        else:

            st.caption(
                "No business model information available."
            )

    with col2:

        st.markdown(
            "**Value Proposition**"
        )

        if value_proposition:

            st.write(
                value_proposition
            )

        else:

            st.caption(
                "No value proposition available."
            )


    # --------------------------------------------------
    # Potential pain points
    # --------------------------------------------------

    pain_points = enrichment.get(
        "pain_points",
        []
    )

    if pain_points:

        st.divider()

        st.subheader(
            "⚠️ Potential Pain Points"
        )

        if isinstance(pain_points, list):

            for pain_point in pain_points:

                st.write(
                    f"• {pain_point}"
                )

        else:

            st.write(
                pain_points
            )


    # --------------------------------------------------
    # Recommended outreach angle
    # --------------------------------------------------

    outreach_angle = enrichment.get(
        "outreach_angle",
        ""
    )

    if outreach_angle:

        st.divider()

        st.subheader(
            "🎯 Recommended Outreach Angle"
        )

        st.info(
            outreach_angle
        )


    # --------------------------------------------------
    # Personalized outreach message
    # --------------------------------------------------

    personalized_message = enrichment.get(
        "personalized_message",
        ""
    )

    if personalized_message:

        st.divider()

        st.subheader(
            "✉️ Personalized Outreach Message"
        )

        # Clean text display.
        # No empty rectangular HTML box.
        st.write(
            personalized_message
        )

        st.caption(
            "AI-generated message based on the researched company."
        )


    # --------------------------------------------------
    # Key business areas
    # --------------------------------------------------

    key_areas = enrichment.get(
        "key_business_areas",
        []
    )

    if key_areas:

        st.divider()

        st.subheader(
            "📌 Key Business Areas"
        )

        if isinstance(key_areas, list):

            for area in key_areas:

                st.write(
                    f"• {area}"
                )

        else:

            st.write(
                key_areas
            )


    # --------------------------------------------------
    # Download JSON
    # --------------------------------------------------

    st.divider()

    json_data = json.dumps(
        enrichment,
        indent=2,
        ensure_ascii=False
    )

    st.download_button(
        label="⬇️ Download Research JSON",
        data=json_data,
        file_name="company_research.json",
        mime="application/json",
        use_container_width=True,
    )


    # --------------------------------------------------
    # Raw JSON
    # --------------------------------------------------

    with st.expander(
        "View raw JSON"
    ):

        st.json(
            enrichment
        )