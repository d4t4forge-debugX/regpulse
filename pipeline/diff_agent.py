ADMINISTRATIVE_PHRASES = [
    "Technical Amendment",
    "Delegation of Authority",
    "Delegations of Authority",
    "Delegated Authority",
    "List of Rules To Be Reviewed",
    "Extension of Compliance Date",
    "Correction",
    "EDGAR Filer Manual",
]

def classify_document(title, abstract):
    abstract = abstract or ""
    combined_text = (title + " " + abstract).lower()
    for phrase in ADMINISTRATIVE_PHRASES:
        if phrase.lower() in combined_text:
            return "administrative"
    return "substantive"

