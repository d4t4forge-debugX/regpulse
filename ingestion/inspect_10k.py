with open("apple_10k_raw.html", "r", encoding="utf-8") as f:
    document_text = f.read()

# Find every place the text "Item 1A" appears
import re

matches = [m.start() for m in re.finditer("Item 1A", document_text)]
print("Number of matches:", len(matches))
print("Positions:", matches[:10])

for pos in matches:
    snippet = document_text[pos:pos + 150]
    print("---")
    print("Position:", pos)
    print(snippet)

# Find every place "Item 1B" appears, to locate where Risk Factors ends
item_1b_matches = [m.start() for m in re.finditer("Item 1B", document_text)]
print("Item 1B matches:", item_1b_matches)

for pos in item_1b_matches:
    snippet = document_text[pos:pos + 150]
    print("---")
    print("Position:", pos)
    print(snippet)

risk_factors_raw = document_text[201696:296152]
print("Sliced length:", len(risk_factors_raw))

with open("apple_risk_factors_raw.html", "w", encoding="utf-8") as f:
    f.write(risk_factors_raw)

print("Saved to apple_risk_factors_raw.html")