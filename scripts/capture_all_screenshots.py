"""
Automated Screenshot Capture Utility for ThreatGraph AI
Connects to running Chrome via CDP on port 9222, navigates the live application,
interacts with components, and saves high-resolution screenshots.
"""

import time
import os
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "assets"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

def capture_all():
    with sync_playwright() as p:
        print("Connecting to Chrome on CDP port 9222...")
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        # 1. GRAPH VIEW
        print("Navigating to http://localhost:5173/ ...")
        page.goto("http://localhost:5173/", wait_until="networkidle")
        time.sleep(2)

        # Ensure benchmarks are loaded if needed
        try:
            seed_btn = page.query_selector("button:has-text('Load Benchmarks')")
            if seed_btn:
                print("Clicking 'Load Benchmarks'...")
                seed_btn.click()
                time.sleep(3)
        except Exception as e:
            print("Seed button click note:", e)

        time.sleep(3) # Wait for Cytoscape to settle force-directed layout
        path_graph = os.path.join(OUTPUT_DIR, "live_graph_explorer.png")
        page.screenshot(path=path_graph)
        print(f"Captured: {path_graph}")

        # 2. CLICK A NODE FOR DETAILS INSPECTOR
        try:
            # Let's see if we can click near center or find a node canvas interaction
            # Or inspect canvas
            canvas = page.query_selector("canvas")
            if canvas:
                box = canvas.bounding_box()
                if box:
                    # Click slightly off-center to select a node
                    page.mouse.click(box["x"] + box["width"] * 0.45, box["y"] + box["height"] * 0.45)
                    time.sleep(1.5)
                    path_inspector = os.path.join(OUTPUT_DIR, "live_node_inspector.png")
                    page.screenshot(path=path_inspector)
                    print(f"Captured: {path_inspector}")
        except Exception as e:
            print("Inspector capture note:", e)

        # 3. CLUSTERS & GDS VIEW
        try:
            cluster_tab = page.query_selector("button:has-text('Campaign Clusters'), button:has-text('Clusters')")
            if cluster_tab:
                print("Clicking Clusters tab...")
                cluster_tab.click()
                time.sleep(2.5)
                path_clusters = os.path.join(OUTPUT_DIR, "live_clusters_gds.png")
                page.screenshot(path=path_clusters)
                print(f"Captured: {path_clusters}")
        except Exception as e:
            print("Clusters tab note:", e)

        # 4. LINK PREDICTION VIEW
        try:
            pred_tab = page.query_selector("button:has-text('Link Prediction')")
            if pred_tab:
                print("Clicking Link Prediction tab...")
                pred_tab.click()
                time.sleep(2.5)
                path_pred = os.path.join(OUTPUT_DIR, "live_link_prediction.png")
                page.screenshot(path=path_pred)
                print(f"Captured: {path_pred}")
        except Exception as e:
            print("Prediction tab note:", e)

        # 5. IOC SEARCH & REGISTRY
        try:
            ioc_tab = page.query_selector("button:has-text('IoC Registry'), button:has-text('Search'), button:has-text('IoC')")
            if ioc_tab:
                print("Clicking IoC Registry tab...")
                ioc_tab.click()
                time.sleep(1.5)
                
                # Type a search filter
                search_input = page.query_selector("input[type='text'], input[placeholder*='Search']")
                if search_input:
                    search_input.fill("azure")
                    time.sleep(1)

                path_ioc = os.path.join(OUTPUT_DIR, "live_ioc_registry.png")
                page.screenshot(path=path_ioc)
                print(f"Captured: {path_ioc}")
        except Exception as e:
            print("IoC tab note:", e)

        # 6. INGESTION WORKBENCH
        try:
            ingest_tab = page.query_selector("button:has-text('Ingestion Workbench'), button:has-text('Ingest')")
            if ingest_tab:
                print("Clicking Ingestion Workbench tab...")
                ingest_tab.click()
                time.sleep(2)
                path_ingest = os.path.join(OUTPUT_DIR, "live_ingestion_workbench.png")
                page.screenshot(path=path_ingest)
                print(f"Captured: {path_ingest}")
        except Exception as e:
            print("Ingestion tab note:", e)

        # 7. FASTAPI SWAGGER DOCS
        try:
            print("Navigating to http://localhost:8000/docs ...")
            page.goto("http://localhost:8000/docs", wait_until="networkidle")
            time.sleep(2)
            # Expand first operation tag
            first_op = page.query_selector(".opblock-tag")
            if first_op:
                first_op.click()
                time.sleep(1)
            path_swagger = os.path.join(OUTPUT_DIR, "live_swagger_api.png")
            page.screenshot(path=path_swagger)
            print(f"Captured: {path_swagger}")
        except Exception as e:
            print("Swagger docs note:", e)

        page.close()
        print("All live screenshots captured successfully!")

if __name__ == "__main__":
    capture_all()
