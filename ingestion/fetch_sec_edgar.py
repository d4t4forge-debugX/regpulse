import requests
import os
from dotenv import load_dotenv
from config import COMPANY_CIK, TEN_K_HTML_FILE

load_dotenv()

LOCAL_FILE = TEN_K_HTML_FILE
# The SEC asks every automated client to identify itself with a real contact email.
# It is read from .env so it never appears in the public repo.
headers = {
    "User-Agent": f"Rohit Personal Project {os.environ['SEC_CONTACT_EMAIL']}"
}

# Step 1: Get the company's filing history from SEC EDGAR
submissions_url = f"https://data.sec.gov/submissions/CIK{COMPANY_CIK}.json"
response = requests.get(submissions_url, headers=headers, timeout=30)
response.raise_for_status()
data = response.json()

# Step 2: Find the most recent 10-K in that history
recent = data["filings"]["recent"]

for i in range(len(recent["form"])):
    if recent["form"][i] == "10-K":
        accession_number = recent["accessionNumber"][i]
        filing_date = recent["filingDate"][i]
        primary_document = recent["primaryDocument"][i]
        break

print("Accession Number:", accession_number)
print("Filing Date:", filing_date)
print("Primary Document:", primary_document)

# Step 3: Get the document — from local cache if we have it, otherwise fetch from SEC
if os.path.exists(LOCAL_FILE):
    print(f"Found local copy: {LOCAL_FILE}")
    with open(LOCAL_FILE, "r", encoding="utf-8") as f:
        document_text = f.read()
else:
    print("No local copy found — fetching from SEC EDGAR...")
    accession_no_dashes = accession_number.replace("-", "")
    cik = data["cik"]
    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{primary_document}"

    doc_response = requests.get(doc_url, headers=headers, timeout=30)
    doc_response.raise_for_status()
    document_text = doc_response.text

    with open(LOCAL_FILE, "w", encoding="utf-8") as f:
        f.write(document_text)
    print(f"Fetched and saved to {LOCAL_FILE}")

print("Document length:", len(document_text))