"""
config.py

Company-specific settings for RegPulse, kept in one place.
Switching companies (for example on the energy branch) means editing this file,
not hunting through the pipeline.
"""

# The company whose 10-K Risk Factors are the reference corpus
COMPANY_NAME = "Duke Energy"

# Gemini model used by the judge and the memo writer
GEMINI_MODEL = "gemini-3.5-flash"

# Zero-shot domain labels used by classify_agent
DOMAIN_LABELS = [
    "Air quality and emissions",
    "Climate and carbon regulation",
    "Nuclear safety and licensing",
    "Gas and pipeline safety",
    "Hazardous materials and waste",
    "Grid reliability and power markets",
    "Energy efficiency and appliance standards",
    "Chemical and pesticide regulation",
    "Recordkeeping, filings and agency procedure",
]


# SEC EDGAR company identifier (10-digit, zero-padded CIK)
COMPANY_CIK = "0001326160"

# Local files: the raw 10-K and the Risk Factors text extracted from it
TEN_K_HTML_FILE = "duke_10k_raw.html"
RISK_FACTORS_TEXT_FILE = "duke_risk_factors_clean.txt"

# Regex for repeating page furniture in the 10-K (page numbers plus running headers or footers),
# stripped during extraction. Duke's pages break as "<page number> RISK FACTORS" mid-text,
# and the section ends with the next page's header "<page number> UNRESOLVED STAFF COMMENTS".
TEN_K_PAGE_NOISE_PATTERN = r"\b\d{1,3} (?:RISK FACTORS|UNRESOLVED STAFF COMMENTS)\b"

# Chroma collection holding the embedded Risk Factors chunks
CHROMA_COLLECTION = "duke_risk_factors"

# Federal Register agencies whose final rules are fetched (API slugs)
FEDERAL_REGISTER_AGENCIES = [
    "federal-energy-regulatory-commission",
    "environmental-protection-agency",
    "nuclear-regulatory-commission",
    "energy-department",
    "pipeline-and-hazardous-materials-safety-administration",
]

# How far back the Federal Register fetch looks, in days
FETCH_DAYS_BACK = 90