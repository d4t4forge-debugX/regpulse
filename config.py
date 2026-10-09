"""
config.py

Company-specific settings for RegPulse, kept in one place.
Switching companies (for example on the energy branch) means editing this file,
not hunting through the pipeline.
"""

# The company whose 10-K Risk Factors are the reference corpus
COMPANY_NAME = "Apple"

# Gemini model used by the judge and the memo writer
GEMINI_MODEL = "gemini-3.5-flash"

# Zero-shot domain labels used by classify_agent
DOMAIN_LABELS = [
    "Financial reporting and disclosure",
    "Corporate governance",
    "Data privacy and cybersecurity",
    "Digital assets and cryptocurrency",
    "International operations and trade",
    "Supply chain and operations",
    "Market and trading regulation",
    "Litigation and enforcement",
    "Recordkeeping and filing systems",
]


# SEC EDGAR company identifier (10-digit, zero-padded CIK)
COMPANY_CIK = "0000320193"

# Local files: the raw 10-K and the Risk Factors text extracted from it
TEN_K_HTML_FILE = "apple_10k_raw.html"
RISK_FACTORS_TEXT_FILE = "apple_risk_factors_clean.txt"

# Regex for repeating page furniture in the 10-K (page numbers plus running headers or footers),
# stripped during extraction. Apple's pages end with "Apple Inc. | 2025 Form 10-K | <page number>".
TEN_K_PAGE_NOISE_PATTERN = r"Apple Inc\. \| 2025 Form 10-K \| \d+"

# Chroma collection holding the embedded Risk Factors chunks
CHROMA_COLLECTION = "apple_risk_factors"

# Federal Register agencies whose final rules are fetched (API slugs)
FEDERAL_REGISTER_AGENCIES = ["securities-and-exchange-commission"]