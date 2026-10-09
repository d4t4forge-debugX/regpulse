import re
from config import RISK_FACTORS_TEXT_FILE, TEN_K_FOOTER, TEN_K_HTML_FILE

def find_section_start(document_text, item_number, section_name):
    """
    Find the position where a section heading actually starts,
    distinguishing it from table-of-contents links and cross-references.
    """
    pattern = re.escape(item_number) + r"[.\s&#0-9;]*" + re.escape(section_name)
    matches = list(re.finditer(pattern, document_text, re.IGNORECASE))

    for m in matches:
        # Real headings are followed by actual paragraph content,
        # not by "</a>" (a link, meaning it's the table of contents)
        following_text = document_text[m.end():m.end() + 20]
        if "</a>" not in following_text:
            return m.start()

    return None

from bs4 import BeautifulSoup


def remove_footer_noise(text):
    """
    Removes repeating footer noise like "Apple Inc. | 2025 Form 10-K | 5"
    """
    pattern = re.escape(TEN_K_FOOTER) + r" \| \d+"
    text = re.sub(pattern, "", text)
    text = re.sub(r"\s+", " ", text)


    return text.strip()

def clean_html_to_text(raw_html):
    """
    Strip HTML tags and normalize whitespace to get plain, readable text.
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ")

    # Collapse multiple spaces/newlines into single spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()

if __name__ == "__main__":
    with open(TEN_K_HTML_FILE, "r", encoding="utf-8") as f:
        document_text = f.read()

    start_pos = find_section_start(document_text, "Item 1A", "Risk Factors")
    end_pos = find_section_start(document_text, "Item 1B", "Unresolved Staff Comments")

    print("Start position:", start_pos)
    print("End position:", end_pos)

    if start_pos is not None and end_pos is not None:
        risk_factors_raw = document_text[start_pos:end_pos]
        risk_factors_clean = clean_html_to_text(risk_factors_raw)
        risk_factors_clean = remove_footer_noise(risk_factors_clean)

        print("Raw length:", len(risk_factors_raw))
        print("Clean length:", len(risk_factors_clean))
        print("First 500 characters of clean text:")
        print(risk_factors_clean[:500])

        with open(RISK_FACTORS_TEXT_FILE, "w", encoding="utf-8") as f:
            f.write(risk_factors_clean)
        print(f"Saved to {RISK_FACTORS_TEXT_FILE}")
    else:
        print("Could not find one or both boundaries.")