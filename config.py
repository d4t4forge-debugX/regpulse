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