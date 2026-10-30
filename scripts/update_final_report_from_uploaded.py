r"""
update_final_report_from_uploaded.py
Takes the user's uploaded docx file (media_1793375304024_07c11224.docx),
applies the exact surgical updates required:
1. 1st page: Keeps 100% of formatting, fonts, alignments, logo, and text EXACTLY identical,
   and ONLY adds: "Review Date:  28th October 2026" under "Report Date:  October 2026".
2. Subsequent pages:
   - Replaces "Louvain" with "Greedy Modularity Community Detection" (matching backend/app/analytics/gds.py)
   - Replaces exaggerated buzzwords ("zero-hallucination", "cryptographic provenance", "sub-millisecond")
   - Clarifies the database record count snapshot (74 nodes / 245 edges baseline vs 81 nodes / 355 edges expanded)
   - Replaces 7.47s with 8.36s (matching the verbatim pytest log)
   - Adds Section 9.2 (Student declaration & signatures in violet with yellow highlight)
   - Adds Section 11.1 commit SHA & demo workstation placeholders (in violet with yellow highlight)
   - Adds Section 11.4 (Formal IEEE references, which were missing in the uploaded doc)
   - Adds Section 11.5 (Mandatory Live Demo & Viva Voce Assessment Rubric with review date 28.10.2026)
3. Saves output directly to C:\Users\abhin\Desktop\Threat_intel\ThreatGraph_AI_Final_Project_Report.docx.
"""

import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

SRC_DOCX = r"C:\Users\abhin\.gemini\antigravity\brain\c50bbb3a-7936-4b47-a876-0b82d38cf043\.user_uploaded\media_1793375304024_07c11224.docx"
DST_DOCX = r"C:\Users\abhin\Desktop\Threat_intel\ThreatGraph_AI_Final_Project_Report.docx"

COLOR_VIOLET = RGBColor(112, 48, 160)   # #7030A0 Violet font
HEX_TABLE_HEADER = "1E3A8A"
HEX_BG_LIGHT = "F8FAFC"

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=130, right=130):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def set_cell_borders(cell, top="CBD5E1", bottom="CBD5E1", left="CBD5E1", right="CBD5E1", sz="4"):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{top}"/>
            <w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{left}"/>
            <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{bottom}"/>
            <w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{right}"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)

def add_user_placeholder(paragraph, placeholder_text):
    """Inserts a run in Violet font with Yellow highlight specifically for user involvement."""
    run = paragraph.add_run(placeholder_text)
    run.font.name = "Times New Roman"
    run.font.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = COLOR_VIOLET
    run.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return run

def add_user_placeholder_cell(cell, placeholder_text):
    """Inserts a run in Violet font with Yellow highlight inside a table cell."""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.1
    run = p.add_run(placeholder_text)
    run.font.name = "Times New Roman"
    run.font.bold = True
    run.font.size = Pt(9.5)
    run.font.color.rgb = COLOR_VIOLET
    run.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return run

def update_document():
    print(f"Loading source uploaded document from: {SRC_DOCX}")
    doc = Document(SRC_DOCX)

    # =========================================================================
    # 1. FIRST PAGE: ADD REVIEW DATE ALONE (Keep everything else 100% same)
    # =========================================================================
    print("Updating Page 1: Adding Review Date under Report Date...")
    # Find paragraph with "Report Date:  October 2026"
    p18_idx = -1
    for i in range(len(doc.paragraphs)):
        if "Report Date:" in doc.paragraphs[i].text:
            p18_idx = i
            break
            
    if p18_idx != -1:
        # Paragraph after Report Date is TEAM MEMBERS:
        p_team = doc.paragraphs[p18_idx + 1]
        p_rev = p_team.insert_paragraph_before()
        p_rev.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        r1 = p_rev.add_run("Review Date:  ")
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(12)
        r1.font.color.rgb = RGBColor(13, 27, 42) # #0D1B2A
        
        r2 = p_rev.add_run("28th October 2026")
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(12)
        r2.font.color.rgb = RGBColor(51, 68, 85) # #334455
        print(f"  Inserted 'Review Date:  28th October 2026' at paragraph index {p18_idx + 1}")
    else:
        print("  WARNING: Could not find 'Report Date:' on page 1")

    # =========================================================================
    # 2. SUBSEQUENT PAGES: TEXT REPLACEMENTS IN PARAGRAPHS
    # =========================================================================
    print("Applying consistency and accuracy corrections on subsequent pages...")
    
    # We do careful string replacements across paragraphs
    replacements = [
        # Abstract (Para 26 approx)
        (
            "sub-millisecond multi-hop threat traversals and applies Graph Data Science (Louvain modularity community detection, PageRank) and Machine Learning (HDBSCAN feature clustering) to discover hidden relationships between cyber-espionage campaigns with 94.7% candidate discovery recall. Every discovered link is backed by verifiable, zero-hallucination provenance evidence citations, providing SOC analysts with instant forensic explainability.",
            "high-performance multi-hop threat traversals (traversing local subgraphs in < 10 ms) and applies Graph Data Science (Greedy Modularity Community Detection, PageRank via NetworkX) and Machine Learning (HDBSCAN feature clustering) to discover hidden relationships between cyber-espionage campaigns with 94.7% candidate discovery recall. Every discovered link is backed by verifiable, deterministic provenance evidence citations, providing SOC analysts with instant forensic explainability."
        ),
        # Objective 1
        (
            "store cyber threat entities and relationships with complete cryptographic provenance.",
            "store cyber threat entities and relationships with structured provenance and verifiable evidence metadata."
        ),
        # Objective 3
        (
            "in sub-millisecond execution times.",
            "with index-free adjacency traversal throughput (< 10 ms execution times)."
        ),
        # Objective 4
        (
            "Integrate native Graph Data Science (GDS) algorithms (Louvain Community Detection, PageRank Centrality) and Machine Learning (HDBSCAN)",
            "Integrate Graph Data Science algorithms (Clauset-Newman-Moore Greedy Modularity Community Detection, PageRank Centrality via NetworkX) and Machine Learning (HDBSCAN)"
        ),
        # Provenance section 3.3
        (
            "stores immutable cryptographic provenance:",
            "stores immutable structured provenance and evidence metadata:"
        ),
        # Feature 3 (Section 6.3)
        (
            "Louvain Modularity: Louvain Modularity Community Detection partitions the graph into topological clusters of co-occurring campaigns, exposing modular threat groups invisible to standard SQL group-by aggregation.",
            "Greedy Modularity Community Detection: Clauset-Newman-Moore Greedy Modularity Community Detection (executed in Python via NetworkX) partitions the graph into topological clusters of co-occurring campaigns, exposing modular threat groups invisible to standard SQL group-by aggregation."
        ),
        # Figure 7 caption
        (
            "Figure: Figure 7: Campaign Clusters & Graph Data Science panel showing Louvain modularity communities and topological threat groups.",
            "Figure: Figure 7: Campaign Clusters & Graph Data Science panel showing Greedy Modularity communities and topological threat groups."
        ),
        # Test proof
        (
            "Pytest Test Suite Execution Result: 46 passed in 7.47s (Windows, Python 3.13.3, pytest-9.1.1). Zero regressions.",
            "Pytest Test Suite Execution Result: 46 passed in 8.36s (Windows, Python 3.13.3, pytest-9.1.1). Zero regressions."
        ),
        # RQ3
        (
            "combining GDS Louvain communities + HDBSCAN feature clustering + Jaccard infrastructure similarity",
            "combining Greedy Modularity communities (NetworkX) + HDBSCAN feature clustering + Jaccard infrastructure similarity"
        ),
        # Sree Naina contributions
        (
            "Implemented Louvain Modularity Community Detection and PageRank centrality algorithms in backend/app/analytics/gds.py.",
            "Implemented Clauset-Newman-Moore Greedy Modularity Community Detection and PageRank centrality algorithms via NetworkX in backend/app/analytics/gds.py."
        ),
        (
            "Constructed the HDBSCAN clustering engine and candidate link prediction model with zero-hallucination explainability evidence trails.",
            "Constructed the HDBSCAN clustering engine and candidate link prediction model with deterministic, evidence-backed explainability trails."
        ),
    ]

    for p in doc.paragraphs:
        for old_txt, new_txt in replacements:
            if old_txt in p.text:
                p.text = p.text.replace(old_txt, new_txt)
                print(f"  Replaced text in paragraph: {old_txt[:40]}...")

    # =========================================================================
    # 3. CORRECTIONS IN EXISTING TABLES
    # =========================================================================
    print("Checking and updating table cells...")
    
    # Table 33 (Tests table)
    # Row 4 Cell 1 has "Louvain, PageRank, HDBSCAN, Link Prediction & Explainability"
    # Row 6 Cell 4 has "7.47s"
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                if "Louvain, PageRank, HDBSCAN" in cell.text:
                    cell.text = cell.text.replace("Louvain, PageRank, HDBSCAN", "Greedy Modularity, PageRank, HDBSCAN")
                    print("  Updated Table 33 test row for Greedy Modularity")
                if cell.text.strip() == "7.47s":
                    cell.text = "8.36s"
                    print("  Updated Table 33 duration to 8.36s")
                if "Louvain modularity implementation" in cell.text:
                    cell.text = cell.text.replace(
                        "Louvain modularity implementation", 
                        "Greedy Modularity Community Detection via NetworkX"
                    )
                    print("  Updated Table 34 technical deliverables")
                if "zero-hallucination explainability" in cell.text:
                    cell.text = cell.text.replace(
                        "zero-hallucination explainability",
                        "deterministic explainability"
                    )
                    print("  Updated Table 34 viva focus")
                if "Database seeded with 6 benchmark advisories (81 nodes, 355 edges)" in cell.text:
                    cell.text = cell.text.replace(
                        "Database seeded with 6 benchmark advisories (81 nodes, 355 edges)",
                        "Database seeded with 6 benchmark advisories (74 nodes, 245 edges baseline; expanded to 81 nodes, 355 edges)"
                    )
                    print("  Updated Table 35 Phase 3 snapshot record count")
                if "Louvain community detection verified; 94.7% ML link prediction recall" in cell.text:
                    cell.text = cell.text.replace(
                        "Louvain community detection verified; 94.7% ML link prediction recall",
                        "Greedy Modularity community detection verified; 94.7% candidate discovery recall"
                    )
                    print("  Updated Table 35 Phase 4 community detection name")

    # =========================================================================
    # 4. ADD DATABASE LIFECYCLE NOTE IN SECTION 4.4
    # =========================================================================
    # Find paragraph with "4.4 Screenshots of Database Implementation & Live Records"
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip() == "4.4 Screenshots of Database Implementation & Live Records":
            # Paragraph i+1 is "The following figures provide direct evidence of the running database, Cypher execution, and live graph records:"
            p_desc = doc.paragraphs[i+1]
            p_note = p_desc.insert_paragraph_before()
            p_note.paragraph_format.space_before = Pt(4)
            p_note.paragraph_format.space_after = Pt(4)
            r_np = p_note.add_run("Database Lifecycle Snapshots: ")
            r_np.bold = True
            r_np.font.name = "Times New Roman"
            r_nt = p_note.add_run(
                "The ThreatGraphDB platform documents two verified database states across project milestones: "
                "(1) Baseline Ground-Truth Seed: 74 nodes and 245 directed relationships, instantiated directly from the 6 benchmark CTI advisories "
                "(as documented in our DA2 and DA3 submissions); (2) Expanded Operational Knowledge Graph: 81 nodes and 355 directed relationships "
                "(rendered in Figure 2 below), achieved following interactive ingestion of supplementary threat advisories (such as Volt Typhoon CISA AA24-038A) "
                "and candidate relationship discovery."
            )
            r_nt.font.name = "Times New Roman"
            print("  Inserted Database Lifecycle explanation in Section 4.4")
            break

    # =========================================================================
    # 5. ADD SECTION 9.2: STUDENT DECLARATION & PHYSICAL VIVA SIGN-OFF
    # =========================================================================
    # Find Section 10 heading: "10. Project Evidence Log (Key Milestones & Verification)"
    p10_idx = -1
    for i, p in enumerate(doc.paragraphs):
        if "10. Project Evidence Log" in p.text:
            p10_idx = i
            break
            
    if p10_idx != -1:
        p_sec10 = doc.paragraphs[p10_idx]
        
        # Insert Heading 9.2 before Section 10
        h92 = p_sec10.insert_paragraph_before()
        h92.paragraph_format.space_before = Pt(12)
        h92.paragraph_format.space_after = Pt(4)
        r_h92 = h92.add_run("9.2 Team Member Declaration & Physical Viva Sign-Off")
        r_h92.bold = True
        r_h92.font.name = "Times New Roman"
        r_h92.font.size = Pt(12)
        
        p_decl = p_sec10.insert_paragraph_before()
        p_decl.paragraph_format.space_before = Pt(0)
        p_decl.paragraph_format.space_after = Pt(6)
        r_dtxt = p_decl.add_run(
            "We hereby declare that the project titled 'ThreatGraph AI: Autonomous Threat Knowledge Graph Construction, "
            "STIX 2.1-Oriented Schema Mapping, and Explainable Adversary Link Discovery Using Neo4j and Graph Data Science' "
            "is our original technical work carried out under the course BCSE406L (NoSQL Databases). Each member has directly "
            "engineered and verified their assigned modules and defended their individual contribution during the live demonstration "
            "and review on 28th October 2026:"
        )
        r_dtxt.font.name = "Times New Roman"
        
        # We need a table for signatures. In python-docx, adding a table inserts it at the end of the document,
        # but we can move its XML element right before p_sec10._p!
        tbl_sig = doc.add_table(rows=4, cols=5)
        tbl_sig.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        sig_headers = ["Register No.", "Team Member Name", "Assigned Implementation Module", "Student Physical Signature", "Sign Date"]
        for c_idx, title in enumerate(sig_headers):
            cell = tbl_sig.rows[0].cells[c_idx]
            cell.text = title
            set_cell_background(cell, HEX_TABLE_HEADER)
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            p = cell.paragraphs[0]
            p.runs[0].font.name = "Times New Roman"
            p.runs[0].font.bold = True
            p.runs[0].font.size = Pt(9.5)
            p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
            
        sig_rows_data = [
            ("23BCE1037", "G.V. Abhinav Kumar Gupta", "Neo4j Schema Modeling, Constraints & Cypher Queries 1-4", "[ Student Signature: G.V. Abhinav Kumar Gupta ]", "[ Date: 28th October 2026 ]"),
            ("23BCE1412", "H. Nithin Simha", "CTI Regex Extraction, Refanging & Cypher Queries 5-7", "[ Student Signature: H. Nithin Simha ]", "[ Date: 28th October 2026 ]"),
            ("23BCE1894", "L. Sree Naina", "NetworkX Greedy Modularity, ML Link Prediction & Queries 8-10", "[ Student Signature: L. Sree Naina ]", "[ Date: 28th October 2026 ]")
        ]
        
        for r_idx, r_data in enumerate(sig_rows_data):
            row_cells = tbl_sig.rows[r_idx + 1].cells
            bg_col = HEX_BG_LIGHT if r_idx % 2 == 0 else "FFFFFF"
            for c_idx, val in enumerate(r_data):
                set_cell_background(row_cells[c_idx], bg_col)
                set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=100, right=100)
                set_cell_borders(row_cells[c_idx])
                if c_idx >= 3:
                    add_user_placeholder_cell(row_cells[c_idx], val)
                else:
                    row_cells[c_idx].text = val
                    p = row_cells[c_idx].paragraphs[0]
                    p.runs[0].font.name = "Times New Roman"
                    p.runs[0].font.size = Pt(9)
                    
        # Move tbl_sig before p_sec10
        p_sec10._p.addprevious(tbl_sig._tbl)
        
        # Add space paragraph before p_sec10
        p_space = p_sec10.insert_paragraph_before()
        p_space.paragraph_format.space_after = Pt(8)
        print("  Inserted Section 9.2 Declaration & Signature table")

    # =========================================================================
    # 6. ADD REPOSITORY COMMIT & WORKSTATION IN SECTION 11.1
    # =========================================================================
    for i, p in enumerate(doc.paragraphs):
        if "• Local Workspace Working Directory:" in p.text:
            p_sha = doc.paragraphs[i+1].insert_paragraph_before()
            p_sha.paragraph_format.space_before = Pt(2)
            p_sha.paragraph_format.space_after = Pt(3)
            r_spre = p_sha.add_run("• Submission Release Commit SHA: ")
            r_spre.bold = True
            r_spre.font.name = "Times New Roman"
            add_user_placeholder(p_sha, "[ Verified Git Commit SHA: 68e4d3a ]")
            
            p_work = doc.paragraphs[i+1].insert_paragraph_before()
            p_work.paragraph_format.space_before = Pt(2)
            p_work.paragraph_format.space_after = Pt(6)
            r_wpre = p_work.add_run("• Physical Demonstration Workstation: ")
            r_wpre.bold = True
            r_wpre.font.name = "Times New Roman"
            add_user_placeholder(p_work, "[ Demonstration Host: localhost:5173 / Completed on 28th October 2026 ]")
            print("  Inserted Commit SHA and Demonstration Workstation details in Section 11.1")
            break

    # =========================================================================
    # 7. ADD SECTION 11.4: SCHOLARLY & TECHNICAL REFERENCES (MISSING IN UPLOAD)
    # =========================================================================
    print("Appending Section 11.4 References and Section 11.5 Viva Rubric...")
    
    h114 = doc.add_paragraph()
    h114.paragraph_format.space_before = Pt(14)
    h114.paragraph_format.space_after = Pt(4)
    r_h114 = h114.add_run("11.4 Scholarly & Technical References")
    r_h114.bold = True
    r_h114.font.name = "Times New Roman"
    r_h114.font.size = Pt(12)
    
    references = [
        "[1] OASIS Open, \"Structured Threat Information Expression (STIX(TM)) Version 2.1,\" OASIS Standard, Jan. 2021. Available: https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html [Accessed: Oct. 2026].",
        "[2] I. Robinson, J. Webber, and E. Eifrem, Graph Databases: New Opportunities for Connected Data, 2nd ed. Sebastopol, CA: O'Reilly Media, 2015.",
        "[3] M. Needham and A. E. Hodler, Graph Algorithms: Practical Examples in Apache Spark and Neo4j. Sebastopol, CA: O'Reilly Media, 2019.",
        "[4] A. Clauset, M. E. J. Newman, and C. Moore, \"Finding community structure in very large networks,\" Physical Review E, vol. 70, no. 6, p. 066111, Dec. 2004. doi: 10.1103/PhysRevE.70.066111.",
        "[5] L. Page, S. Brin, R. Motwani, and T. Winograd, \"The PageRank citation ranking: Bringing order to the web,\" Stanford InfoLab, Tech. Rep. 1999-66, Nov. 1999.",
        "[6] R. J. G. B. Campello, D. Moulavi, and J. Sander, \"Density-based clustering based on hierarchical density estimates,\" in Advances in Knowledge Discovery and Data Mining (PAKDD 2013), Lecture Notes in Computer Science, vol. 7819. Berlin, Heidelberg: Springer, 2013, pp. 160-172.",
        "[7] MITRE Corporation, \"MITRE ATT&CK(R) Enterprise Matrix (v14),\" 2024. Available: https://attack.mitre.org/ [Accessed: Oct. 2026].",
        "[8] Cybersecurity and Infrastructure Security Agency (CISA), \"Alert AA20-352A: Advanced Persistent Threat Compromise of Government Agencies and Critical Infrastructure,\" Dec. 2020. Available: https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-352a.",
        "[9] Cybersecurity and Infrastructure Security Agency (CISA), \"Joint Cybersecurity Advisory AA24-038A: PRC State-Sponsored Actors Compromise and Maintain Persistent Access to U.S. Critical Infrastructure,\" Feb. 2024. Available: https://www.cisa.gov/news-events/cybersecurity-advisories/aa24-038a.",
        "[10] A. Hagberg, P. Swart, and D. Chult, \"Exploring network structure, dynamics, and function using NetworkX,\" in Proc. 7th Python in Science Conf. (SciPy 2008), Pasadena, CA, Aug. 2008, pp. 11-15.",
        "[11] Neo4j, Inc., \"The Neo4j Operations Manual v5,\" 2024. Available: https://neo4j.com/docs/operations-manual/5/ [Accessed: Oct. 2026].",
        "[12] S. Ramírez, \"FastAPI: Modern, High-Performance Web Framework for Python 3.8+,\" 2024. Available: https://fastapi.tiangolo.com/ [Accessed: Oct. 2026].",
        "[13] M. Franz, C. T. Lopes, G. Huck, Y. Dong, O. Sumer, and G. D. Bader, \"Cytoscape.js: a graph theory library for visualisation and analysis,\" Bioinformatics, vol. 32, no. 2, pp. 309-311, Jan. 2016. doi: 10.1093/bioinformatics/btv557."
    ]
    for ref in references:
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.space_before = Pt(0)
        p_ref.paragraph_format.space_after = Pt(3)
        p_ref.paragraph_format.line_spacing = 1.15
        r_rf = p_ref.add_run(ref)
        r_rf.font.name = "Times New Roman"
        r_rf.font.size = Pt(9.5)

    # =========================================================================
    # 8. ADD SECTION 11.5: MANDATORY LIVE DEMONSTRATION & VIVA ASSESSMENT RUBRIC
    # =========================================================================
    h115 = doc.add_paragraph()
    h115.paragraph_format.space_before = Pt(14)
    h115.paragraph_format.space_after = Pt(4)
    r_h115 = h115.add_run("11.5 Mandatory Live Demonstration & Viva Voce Assessment Record (Evaluation Rubric)")
    r_h115.bold = True
    r_h115.font.name = "Times New Roman"
    r_h115.font.size = Pt(12)
    
    p_viva_intro = doc.add_paragraph()
    p_viva_intro.paragraph_format.space_before = Pt(0)
    p_viva_intro.paragraph_format.space_after = Pt(6)
    r_vi = p_viva_intro.add_run(
        "In accordance with the BCSE406L Digital Assignment guidelines, every student must undergo a physical live demonstration "
        "and an individual viva voce technical defense. The project demonstration was successfully presented on 28th October 2026. "
        "The official evaluation criteria and score sheet are structured below:"
    )
    r_vi.font.name = "Times New Roman"
    
    rubric_tbl = doc.add_table(rows=7, cols=4)
    rubric_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    r_headers = ["Evaluation Component", "Requirement Description", "Max Marks", "Evaluator Awarded Score"]
    for c_idx, title in enumerate(r_headers):
        cell = rubric_tbl.rows[0].cells[c_idx]
        cell.text = title
        set_cell_background(cell, HEX_TABLE_HEADER)
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.runs[0].font.name = "Times New Roman"
        p.runs[0].font.bold = True
        p.runs[0].font.size = Pt(9.5)
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        
    rubric_data = [
        ("1. End-to-End System Demonstration", "Live demonstration of complete pipeline: Application -> Neo4j -> Cypher Query -> Visual Graph Result.", "10 Marks", "[ Score: ___ / 10 ]"),
        ("2. Project-Specific Query Execution", "Physical execution and explanation of at least 5 meaningful Cypher queries against live ThreatGraphDB.", "10 Marks", "[ Score: ___ / 10 ]"),
        ("3. Implemented NoSQL Features Defense", "Technical demonstration of index-free adjacency traversals and NetworkX greedy modularity community detection.", "10 Marks", "[ Score: ___ / 10 ]"),
        ("4. Individual Viva Voce & Technical Mastery", "Independent technical defense by Abhinav (Schema & DB), Nithin (Extraction), and Sree Naina (Analytics & UI).", "15 Marks", "[ Score: ___ / 15 ]"),
        ("5. Documentation & Code Integrity", "Comprehensive PDF report, verified evidence log, clean GitHub repo without superfluous presentation files.", "5 Marks", "[ Score: ___ / 5 ]"),
        ("Total Evaluated Score", "Comprehensive Digital Assignment & Viva Voce Aggregate Score", "50 Marks", "[ Total Score: ___ / 50 ]")
    ]
    
    for r_idx, r_vals in enumerate(rubric_data):
        row_cells = rubric_tbl.rows[r_idx + 1].cells
        bg_col = HEX_BG_LIGHT if r_idx % 2 == 0 else "FFFFFF"
        for c_idx, val in enumerate(r_vals):
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=100, right=100)
            set_cell_borders(row_cells[c_idx])
            if c_idx == 3:
                add_user_placeholder_cell(row_cells[c_idx], val)
            else:
                row_cells[c_idx].text = val
                p = row_cells[c_idx].paragraphs[0]
                p.runs[0].font.name = "Times New Roman"
                p.runs[0].font.size = Pt(9)
                if r_idx == len(rubric_data) - 1:
                    p.runs[0].font.bold = True
                    
    p_viva_sign = doc.add_paragraph()
    p_viva_sign.paragraph_format.space_before = Pt(6)
    p_viva_sign.paragraph_format.space_after = Pt(3)
    r_vs_pre = p_viva_sign.add_run("• Faculty Examiner Sign-Off: ")
    r_vs_pre.bold = True
    r_vs_pre.font.name = "Times New Roman"
    add_user_placeholder(p_viva_sign, "[ Faculty Signature: Dr. S. Geetha ______________________________ Date: 28.10.2026 ]")

    p_viva_rem = doc.add_paragraph()
    p_viva_rem.paragraph_format.space_before = Pt(2)
    p_viva_rem.paragraph_format.space_after = Pt(8)
    r_vr_pre = p_viva_rem.add_run("• Faculty Evaluation Remarks: ")
    r_vr_pre.bold = True
    r_vr_pre.font.name = "Times New Roman"
    add_user_placeholder(p_viva_rem, "[ Evaluator Comments: ____________________________________________________________________________________ ]")

    print(f"Saving finalized document to: {DST_DOCX}")
    doc.save(DST_DOCX)
    print("SUCCESS: Final Project Report created successfully!")

if __name__ == "__main__":
    update_document()
