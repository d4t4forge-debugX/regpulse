from playwright.sync_api import sync_playwright
from pathlib import Path

def convert_html_to_pdf(html_path, pdf_path):
    html_path = Path(html_path).resolve()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_path}")
        page.pdf(path=pdf_path, format="Letter")
        browser.close()

if __name__ == "__main__":
    convert_html_to_pdf("apple_10k_raw.html", "apple_10k.pdf")
