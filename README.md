# LeadForge AI

AI-powered lead enrichment agent for researching company websites and generating structured lead intelligence.

## Features

- Company website crawling
- Relevant page discovery and prioritization
- Web content extraction and cleaning
- Local LLM-based company enrichment using Ollama
- Structured JSON output
- Deterministic lead-fit scoring
- Lead classification
- Personalized outreach message generation
- Streamlit web interface
- Automated tests for lead scoring

## Pipeline

Company URL
→ Web crawling
→ Relevant page discovery
→ Content extraction
→ Research context building
→ Local LLM enrichment
→ Structured JSON validation
→ Deterministic lead scoring
→ JSON output

## Setup

### 1. Create a virtual environment

    python -m venv .venv

Activate it:

    .venv\Scripts\Activate.ps1

### 2. Install dependencies

    pip install -r requirements.txt

### 3. Install Playwright Chromium

    playwright install chromium

### 4. Install and prepare Ollama

LeadForge AI uses a local Ollama model for company enrichment.

Make sure Ollama is installed and the configured model is available before running the application.

The application currently uses:

    qwen2.5:3b

Make sure the model is available in Ollama before running an analysis.

## Run the Application

Start the Streamlit interface:

    streamlit run app\ui.py

The terminal will display a local URL. Open that URL in your browser.

Enter a company website such as:

    https://stripe.com

Then click **Analyze Company**.

## Run from the Command Line

From the project root:

    $env:PYTHONPATH="."
    python app\main.py https://stripe.com

Replace the URL with the company website you want to analyze.

## Run Tests

From the project root:

    $env:PYTHONPATH="."
    pytest -q

Expected result:

    5 passed

## Output

Research results are saved as JSON files in the `outputs/` directory.

The generated output contains:

- Company name
- Industry
- Company description
- Products and services
- Target customers
- Business model
- Value proposition
- Potential pain points
- Recommended outreach angle
- Personalized outreach message
- Deterministic lead profile

Example output structure:

    {
      "company_name": "Stripe",
      "industry": "Technology",
      "company_description": "Stripe is a technology company focused on improving economic growth and prosperity by building programmable financial infrastructure.",
      "products_and_services": [
        "Payments",
        "Checkout"
      ],
      "target_customers": [
        "Solo founders",
        "Established enterprises"
      ],
      "business_model": "Pay-as-you-go pricing with volume discounts and multi-product discounts.",
      "value_proposition": "Global access, multiple currencies, payment methods, fraud prevention, and analytics.",
      "pain_points": [
        "Complex payment processing",
        "High transaction fees"
      ],
      "outreach_angle": "A company-specific outreach angle based on researched information.",
      "personalized_message": "A company-specific personalized outreach message.",
      "lead_profile": {
        "lead_type": "Enterprise / B2B",
        "fit_score": 100,
        "fit_level": "High",
        "scoring_method": "Deterministic rule-based scoring"
      }
    }

## Required Test Domains

The project specification lists the following required test domains:

- `postman.com`
- `supabase.com`
- `vapi.ai`

## Project Structure

    leadforge-ai/
    ├── app/
    │   ├── __init__.py
    │   ├── ai_enrichment.py
    │   ├── context.py
    │   ├── lead_scoring.py
    │   ├── main.py
    │   ├── models.py
    │   ├── ollama_client.py
    │   └── ui.py
    ├── outputs/
    ├── sample/
    ├── tests/
    │   └── test_lead_scoring.py
    ├── .gitignore
    ├── README.md
    ├── requirements.txt
    └── .venv/              # local virtual environment, excluded from Git

## Lead Scoring

LeadForge AI calculates a deterministic fit score from 0 to 100 using:

- Industry relevance
- Target customer fit
- B2B / enterprise signals
- Product / service fit

The score is classified as:

- **High:** 80-100
- **Medium:** 60-79
- **Low:** 0-59

The lead profile also identifies the lead type and records the deterministic scoring method.

## Technical Approach

### Web Research

The application crawls the target company website and prioritizes relevant pages such as:

- Sales pages
- Pricing pages
- Product pages
- Customer pages
- Documentation
- Other relevant company pages

### AI Enrichment

Website research is converted into a compact context before being sent to the local Ollama model.

The model extracts structured company information including products, customers, business model, value proposition, pain points, outreach angle, and personalized messaging.

### Validation

AI-generated enrichment is validated before being used by the application.

The application checks the expected structure and prevents malformed or placeholder-based personalized messages from reaching the final output.

### Deterministic Lead Scoring

Lead scoring is performed separately from the LLM.

The final fit score is calculated using deterministic rule-based logic based on:

- Industry relevance
- Target customer fit
- B2B / enterprise signals
- Product / service fit

This ensures that the lead score is reproducible and does not depend on the model's generated score.

## Notes

- AI enrichment runs locally through Ollama.
- Website research is converted into a compact context before being sent to the local model.
- Generated enrichment is validated before being used by the application.
- Lead scoring is deterministic and does not depend on the LLM.
- The `.venv/` directory is excluded from Git.
- Python cache files and local environment files are excluded from Git.

## Testing

The current automated test suite validates the deterministic lead scoring functionality.

Run:

    $env:PYTHONPATH="."
    pytest -q

Expected result:

    5 passed