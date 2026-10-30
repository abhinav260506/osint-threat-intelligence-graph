import docx

doc_path = r"C:\Users\abhin\Desktop\Threat_intel\ThreatGraph_AI_Final_Project_Report.docx"
doc = docx.Document(doc_path)

print("=== DOCUMENT VERIFICATION ===")
print("Total Paragraphs:", len(doc.paragraphs))
print("Total Tables:", len(doc.tables))

# Check images
images = [r.target_ref for r in doc.part.rels.values() if "image" in r.target_ref]
print("Total Images in package:", len(images))

# Check Page 1
print("\n--- PAGE 1 VERIFICATION ---")
for i in range(25):
    p = doc.paragraphs[i]
    if "Review Date" in p.text or "Report Date" in p.text or "TEAM MEMBERS" in p.text:
        print(f"P{i} ({p.alignment}): {p.text}")

# Check Term Occurrences
full_text = "\n".join([p.text for p in doc.paragraphs])
for t in doc.tables:
    for row in t.rows:
        for cell in row.cells:
            full_text += "\n" + cell.text

print("\n--- TERM OCCURRENCES ---")
print("Louvain count (should be 0):", full_text.count("Louvain"))
print("Greedy Modularity count:", full_text.count("Greedy Modularity"))
print("Zero-hallucination count (should be 0):", full_text.count("Zero-hallucination") + full_text.count("zero-hallucination"))
print("Cryptographic provenance count (should be 0):", full_text.count("Cryptographic provenance") + full_text.count("cryptographic provenance"))
print("7.47s count (should be 0):", full_text.count("7.47s"))
print("8.36s count:", full_text.count("8.36s"))
print("References section present?:", "11.4 Scholarly & Technical References" in full_text)
print("Section 9.2 present?:", "9.2 Team Member Declaration & Physical Viva Sign-Off" in full_text)
print("Section 11.5 present?:", "11.5 Mandatory Live Demonstration & Viva Voce Assessment Record" in full_text)

# Check Violet / Yellow Highlighted Runs
violet_yellow_runs = []
for p in doc.paragraphs:
    for r in p.runs:
        if r.font.color and r.font.color.rgb == docx.shared.RGBColor(112, 48, 160):
            violet_yellow_runs.append(r.text)

for t in doc.tables:
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    if r.font.color and r.font.color.rgb == docx.shared.RGBColor(112, 48, 160):
                        violet_yellow_runs.append(r.text)

print(f"\n--- USER INVOLVEMENT ITEMS (Violet text with Yellow highlight): {len(violet_yellow_runs)} ---")
for idx, item in enumerate(violet_yellow_runs, 1):
    print(f"  {idx}. {item.strip()}")

