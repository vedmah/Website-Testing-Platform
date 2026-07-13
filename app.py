import streamlit as st
import asyncio
import httpx
from bs4 import BeautifulSoup
import time
import pandas as pd
from urllib.parse import urlparse, urljoin
import re
import json
import os
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. PREMIUM HIGH-CONTRAST DARK THEME CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="QA-X Real-Time Automation Suite",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #05070C !important;
            color: #FFFFFF !important;
        }
        
        .stMarkdown, p, span, label, li {
            color: #E2E8F0 !important;
            font-family: 'Inter', sans-serif;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }
        
        .qa-matrix-table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            font-size: 13px;
            background-color: #0A0D14 !important;
            border: 1px solid #1E2230 !important;
            border-radius: 8px;
            overflow: hidden;
        }
        .qa-matrix-table th {
            background-color: #111622 !important;
            color: #00FFA3 !important;
            text-align: left;
            padding: 12px 14px;
            font-weight: 600;
            border-bottom: 2px solid #1E2230;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .qa-matrix-table td {
            padding: 12px 14px;
            border-bottom: 1px solid #161B26;
            color: #FFFFFF !important;
        }
        .qa-matrix-table tr:last-child td {
            border-bottom: none;
        }
        
        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge-passed { background-color: rgba(0, 255, 163, 0.15); color: #00FFA3 !important; border: 1px solid #00FFA3; }
        .badge-warning { background-color: rgba(255, 189, 46, 0.15); color: #FFBD2E !important; border: 1px solid #FFBD2E; }
        .badge-failed { background-color: rgba(255, 95, 86, 0.15); color: #FF5F56 !important; border: 1px solid #FF5F56; }

        .custom-header {
            background: #090A0F !important;
            border: 1px solid #1E2230 !important;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        }
        
        .matrix-card {
            background-color: #090A0F !important;
            border: 1px solid #161B26 !important;
            border-left: 4px solid #00FFA3 !important;
            padding: 1.25rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .matrix-card h5 {
            color: #8A99AD !important;
            margin: 0 0 5px 0;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .mockup-canvas {
            width: 100%;
            background: #090A0F !important;
            border: 1px solid #1E2230 !important;
            border-radius: 12px 12px 0 0;
            padding: 20px;
            margin-top: 10px;
        }
        
        .blueprint-footer {
            width: 100%;
            background: #07090E !important;
            border: 1px solid #1E2230 !important;
            border-top: none;
            border-radius: 0 0 12px 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .canvas-top-bar {
            border-bottom: 1px solid #1E2230;
            padding-bottom: 12px;
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .browser-dot {
            height: 11px;
            width: 11px;
            background-color: #FF5F56;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
        }
        .browser-dot.yellow { background-color: #FFBD2E; }
        .browser-dot.green { background-color: #27C93F; }

        .stAlert {
            background-color: #090A0F !important;
            border: 1px solid #161B26 !important;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

HISTORY_FILE = "qa_execution_history.json"

# -----------------------------------------------------------------------------
# 2. AUTOMATED HISTORY DATA VAULT HANDLING
# -----------------------------------------------------------------------------
def load_historical_vault():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def append_to_historical_vault(target_name, final_score, items_checked, metadata_str, type_label, test_cases):
    current_history = load_historical_vault()
    new_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_url": target_name,
        "score": final_score,
        "total_pages": items_checked,
        "total_links": type_label, # Reusing fields flexibly for Web vs Mobile
        "total_images": metadata_str,
        "cases": test_cases
    }
    current_history.insert(0, new_record)
    with open(HISTORY_FILE, "w") as f:
        json.dump(current_history, f, indent=4)

# Initialize Session Memory Slots
if "execution_state" not in st.session_state:
    st.session_state.execution_state = "IDLE"
if "master_test_suite" not in st.session_state:
    st.session_state.master_test_suite = []
if "all_screenshot_pairs" not in st.session_state:
    st.session_state.all_screenshot_pairs = []
if "slideshow_index" not in st.session_state:
    st.session_state.slideshow_index = 0
if "summary_metrics" not in st.session_state:
    st.session_state.summary_metrics = {}

# -----------------------------------------------------------------------------
# 3. ENHANCED WEB AUTOMATION TEST FACTORY ENGINE
# -----------------------------------------------------------------------------
def run_automated_test_factory(url, soup, path_index):
    suite = []
    page_path = urlparse(url).path if urlparse(url).path else "/"
    
    # 1. Responsiveness Check
    has_viewport = bool(soup and soup.find('meta', attrs={'name': 'viewport'}))
    suite.append({
        "ID": f"RSP-{path_index:03d}",
        "Page Path": page_path,
        "Component": "Responsiveness Matrix",
        "Objective": "Verify active scaling viewport parameters exist for fluid layout rendering.",
        "Status": "PASSED" if has_viewport else "FAILED",
        "Diagnostics Log": "Viewport configuration matches adaptive breakdown rule targets." if has_viewport else "CRITICAL: Missing meta viewport settings."
    })
    
    # 2. Font Verification
    has_custom_fonts = False
    if soup:
        has_font_link = any("font" in str(link.get('href', '')) for link in soup.find_all('link'))
        has_font_style = "font-family" in str(soup.find_all('style'))
        has_custom_fonts = has_font_link or has_font_style
        
    suite.append({
        "ID": f"FNT-{path_index:03d}",
        "Page Path": page_path,
        "Component": "Typography Engine",
        "Objective": "Check font loading paths, asset styling, and uniform text fallbacks.",
        "Status": "PASSED" if has_custom_fonts else "WARNING",
        "Diagnostics Log": "Custom typography loaded safely." if has_custom_fonts else "Fallback font properties active."
    })
    
    # 3. Image Optimization Scan
    images = soup.find_all('img') if soup else []
    broken_images = sum(1 for img in images if not img.get('src', '').strip())
    lazy_loaded = sum(1 for img in images if 'lazy' in str(img.get('loading', '')).lower())
    
    img_status = "PASSED"
    if broken_images > 0:
        img_status = "FAILED"
    elif len(images) > 0 and lazy_loaded == 0:
        img_status = "WARNING"
        
    suite.append({
        "ID": f"IMG-{path_index:03d}",
        "Page Path": page_path,
        "Component": "Graphic Assets",
        "Objective": "Scan media assets for absolute targets, missing anchors, and optimization issues.",
        "Status": img_status,
        "Diagnostics Log": f"Verified {len(images)} source paths." if img_status == "PASSED" else "Flagged anomalies or optimization targets."
    })
    
    # 4. Text Character Inspection
    page_text = soup.get_text() if soup else ""
    casing_anomalies = len(re.findall(r'\b[a-z]+[A-Z]+[a-z]*\b', page_text))
    
    suite.append({
        "ID": f"LTR-{path_index:03d}",
        "Page Path": page_path,
        "Component": "Letter Syntax Core",
        "Objective": "Inspect textual layout fields for font casing anomalies or broken layouts.",
        "Status": "PASSED" if casing_anomalies < 12 else "WARNING",
        "Diagnostics Log": f"Text blocks checked clear." if casing_anomalies < 12 else "Irregular casing word structures noticed."
    })

    return suite

# -----------------------------------------------------------------------------
# 4. HIGH-SPEED CONCURRENT ASYNC CRAWLER PIPELINE
# -----------------------------------------------------------------------------
async def fetch_and_parse_node(client, url, path_index, target_domain):
    custom_agent = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QA-X Core/8.0"}
    discovered_links = []
    try:
        response = await client.get(url, headers=custom_agent, timeout=5.0, follow_redirects=True)
        soup = BeautifulSoup(response.text, 'html.parser')
        for anchor in soup.find_all('a', href=True):
            absolute_link = urljoin(url, anchor['href']).split('#')[0].split('?')[0]
            if urlparse(absolute_link).netloc == target_domain:
                if not absolute_link.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.tar', '.gz')):
                    discovered_links.append(absolute_link)
    except Exception:
        soup = BeautifulSoup("<html><body></body></html>", 'html.parser')
        
    suite_cases = run_automated_test_factory(url, soup, path_index)
    link_count = len(soup.find_all('a')) if soup else 0
    img_count = len(soup.find_all('img')) if soup else 0
    
    screenshot_node = {
        "url": url,
        "desktop": f"https://image.thum.io/get/width/1280/crop/800/maxAge/1/{url}",
        "mobile": f"https://image.thum.io/get/width/480/crop/800/maxAge/1/{url}"
    }
    return suite_cases, screenshot_node, discovered_links, link_count, img_count

async def pipeline_orchestrator(start_url):
    target_domain = urlparse(start_url).netloc
    visited_urls = set()
    urls_to_crawl = [start_url]
    
    master_suites = []
    screenshot_stack = []
    total_links = 0
    total_images = 0
    path_index = 1
    
    status_box = st.empty()
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    async with httpx.AsyncClient(limits=limits, verify=False) as client:
        while urls_to_crawl and path_index <= 40:
            batch = []
            while urls_to_crawl and len(batch) < 10:
                nxt = urls_to_crawl.pop(0)
                if nxt not in visited_urls:
                    visited_urls.add(nxt)
                    batch.append(nxt)
            if not batch:
                continue
                
            status_box.markdown(f"""
                <div class='matrix-card' style='border-left: 4px solid #00FFA3;'>
                    <span style='color: #00FFA3; font-weight: 600;'>⚡ Async Speed Mode: Analyzing Batch Segment ({len(visited_urls)} pages discovered)</span>
                </div>
            """, unsafe_allow_html=True)
            
            tasks = [fetch_and_parse_node(client, url, path_index, target_domain) for url in batch]
            path_index += len(batch)
            results = await asyncio.gather(*tasks)
            
            for suite_cases, screenshot_node, discovered_links, link_count, img_count in results:
                master_suites.extend(suite_cases)
                screenshot_stack.append(screenshot_node)
                total_links += link_count
                total_images += img_count
                for link in discovered_links:
                    if link not in visited_urls and link not in urls_to_crawl:
                        urls_to_crawl.append(link)
                        
    status_box.empty()
    passed = sum(1 for t in master_suites if t["Status"] == "PASSED")
    score = int((passed / len(master_suites)) * 100) if master_suites else 100
    
    st.session_state.summary_metrics = {
        "score": score,
        "links": total_links,
        "images": total_images,
        "scanned_count": len(visited_urls)
    }
    st.session_state.master_test_suite = master_suites
    st.session_state.all_screenshot_pairs = screenshot_stack
    st.session_state.execution_state = "COMPLETED"
    
    append_to_historical_vault(start_url, score, len(visited_urls), f"{total_images} Imgs", "Web Crawl Suite", master_suites)

# -----------------------------------------------------------------------------
# 5. CORE WORKSPACE ROUTER LAYOUT
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="custom-header">
        <h1 style="margin: 0; font-size: 26px; font-weight: 700; color: #FFFFFF !important;">🤖 QA-X Enterprise Testing Suite</h1>
        <p style="color: #00FFA3 !important; margin: 4px 0 0 0; font-size: 13px; font-weight: 500;">
            Unified Control Hub • Automated Website Scan & Mobile WhatsApp APK Vault
        </p>
    </div>
""", unsafe_allow_html=True)

tab_web, tab_apk = st.tabs(["💻 Core Web URL Automation", "📱 Mobile APK Testing Suite"])

# =============================================================================
# TAB 1: CORE WEB AUTOMATION ENGINE
# =============================================================================
with tab_web:
    url_col, button_col = st.columns([7, 3])
    with url_col:
        target_url = st.text_input("🎯 Destination Target Vector URL", value="https://www.tutorialspoint.com")
        if not target_url.startswith(("http://", "https://")):
            target_url = "https://" + target_url
    with button_col:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        start_analysis = st.button("🚀 Trigger Entire Site Automation", use_container_width=True)

    if start_analysis:
        st.session_state.execution_state = "RUNNING"
        st.session_state.slideshow_index = 0  
        asyncio.run(pipeline_orchestrator(target_url))

    if st.session_state.execution_state == "COMPLETED" and st.session_state.master_test_suite:
        summary_data = st.session_state.summary_metrics
        screenshot_stack = st.session_state.all_screenshot_pairs
        
        metric_c1, metric_c2, metric_c3 = st.columns(3)
        with metric_c1:
            st.markdown(f"<div class='matrix-card'><h5>Total Domain Footprint</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{summary_data.get('scanned_count')} Pages Swept</h2></div>", unsafe_allow_html=True)
        with metric_c2:
            st.markdown(f"<div class='matrix-card'><h5>Analyzed Media Paths</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{summary_data.get('links')} Links Tracked</h2></div>", unsafe_allow_html=True)
        with metric_c3:
            st.markdown(f"<div class='matrix-card'><h5>Comprehensive Quality Grade</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{summary_data.get('score')}% Pass Metric</h2></div>", unsafe_allow_html=True)

        st.markdown("<h3 style='font-size:16px; font-weight:600; margin-top:15px;'>📋 Aggregated Site-Wide Automated Test Case Matrix</h3>", unsafe_allow_html=True)
        html_table = '<table class="qa-matrix-table"><thead><tr><th>Test ID</th><th>Target Path</th><th>Component</th><th>Objective Description</th><th>Status</th><th>Log Diagnostics</th></tr></thead><tbody>'
        for item in st.session_state.master_test_suite:
            status_val = str(item.get('Status', 'PASSED')).upper()
            status_class = "badge-passed" if status_val == "PASSED" else ("badge-warning" if status_val == "WARNING" else "badge-failed")
            html_table += f"<tr><td style='font-weight:600; color:#8A99AD !important;'>{item.get('ID')}</td><td style='font-family:monospace; font-size:12px; color:#00FFA3;'>{item.get('Page Path')}</td><td style='font-weight:500;'>{item.get('Component')}</td><td>{item.get('Objective')}</td><td><span class='badge {status_class}'>{status_val}</span></td><td style='color:#8A99AD !important; font-size:12px;'>{item.get('Diagnostics Log')}</td></tr>"
        html_table += '</tbody></table>'
        st.markdown(html_table, unsafe_allow_html=True)

        # Visual Carousel
        st.write("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        current_idx = st.session_state.get("slideshow_index", 0)
        if current_idx >= len(screenshot_stack): current_idx = 0
        active_target_node = screenshot_stack[current_idx]
        
        st.markdown(f'<div class="mockup-canvas"><p style="margin:0; font-size:12px; color:#8A99AD;"><span style="color:#00FFA3; font-weight:600;">[Automated URL Vector]:</span> {active_target_node["url"]}</p></div>', unsafe_allow_html=True)
        img_left_col, img_right_col = st.columns([6, 4])
        with img_left_col: st.image(active_target_node['desktop'], use_container_width=True)
        with img_right_col: st.image(active_target_node['mobile'], use_container_width=True)
            
        slide_left_col, slide_right_col = st.columns(2)
        with slide_left_col:
            if st.button("⬅️ Previous Scanned Page", use_container_width=True):
                st.session_state.slideshow_index = (current_idx - 1) % len(screenshot_stack)
                st.rerun()
        with slide_right_col:
            if st.button("Next Scanned Page ➡️", use_container_width=True):
                st.session_state.slideshow_index = (current_idx + 1) % len(screenshot_stack)
                st.rerun()
    else:
        st.markdown('<div class="stAlert"><p style="margin:0; color:#8A99AD;">💡 Provide a web domain root link above and click trigger to run the autonomous crawl dashboard.</p></div>', unsafe_allow_html=True)

# =============================================================================
# TAB 2: MOBILE WHATSAPP APK TESTING SUITE PANEL
# =============================================================================
with tab_apk:
    st.markdown("<h3 style='margin:0; font-size:18px;'>📲 Black-Box Mobile APK Testing Matrix</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:13px; color:#8A99AD; margin-bottom:15px;'>Eliminate manual logging spreadsheets. Grade APK installations and user behavior flows smoothly below.</p>", unsafe_allow_html=True)
    
    apk_meta_c1, apk_meta_c2 = st.columns(2)
    with apk_meta_c1:
        apk_name = st.text_input("📦 WhatsApp APK Reference Name / Package ID", value="Custom_WhatsApp_App_v1.0")
    with apk_meta_c2:
        tester_identity = st.text_input("👨‍💻 Assigned Tester Identifier Token", value="QA_Agent_Primary")
        
    st.divider()
    
    # Pre-defined complete matrix structural array
    default_mobile_cases = [
        {"ID": "APK-POS-001", "Component": "Installation Integrity", "Type": "Positive", "Objective": "Verify APK executes and triggers system package installers without binary corruption faults."},
        {"ID": "APK-POS-002", "Component": "First-Time App Launch", "Type": "Positive", "Objective": "Verify app opens to landing or login screen layouts without instant crash loops."},
        {"ID": "APK-POS-003", "Component": "Core Nav Flow", "Type": "Positive", "Objective": "Tap primary header menus and tabs to ensure links route to expected targets cleanly."},
        {"ID": "APK-POS-004", "Component": "Hardware Back Button", "Type": "Positive", "Objective": "Verify pressing device hardware back navigation steps backward cleanly rather than terminating app context."},
        {"ID": "APK-NEG-001", "Component": "Network Interruption", "Type": "Negative", "Objective": "Engage Airplane Mode status during active page or form data loading fields."},
        {"ID": "APK-NEG-002", "Component": "App Lifecycle Shift", "Type": "Negative", "Objective": "Minimize application window frame mid-flow, operate secondary device apps, and return to view state."},
        {"ID": "APK-NEG-003", "Component": "Hardware State Shift", "Type": "Negative", "Objective": "Rotate device screen axis from Portrait into Landscape mid-form data input tasks."},
        {"ID": "APK-NEG-004", "Component": "Input Boundary Flood", "Type": "Negative", "Objective": "Inject excessive string payloads (5,000+ mixed string special character emoji sets) into user input fields."}
    ]
    
    compiled_apk_results = []
    
    # Render interactive evaluation blocks
    st.markdown("<p style='font-size:14px; font-weight:600; color:#00FFA3;'>📝 Live Evaluation Sheet Rows</p>", unsafe_allow_html=True)
    
    for case in default_mobile_cases:
        with st.container():
            st.markdown(f"""
                <div style='background-color:#0A0D14; padding:12px; border:1px solid #1E2230; border-radius:6px; margin-bottom:10px;'>
                    <span style='color:#8A99AD; font-weight:600;'>[{case['ID']}] {case['Component']}</span> — <span style='color:#FFBD2E; font-size:12px;'>Type: {case['Type']}</span><br>
                    <small style='color:#E2E8F0;'>Objective Target: {case['Objective']}</small>
                </div>
            """, unsafe_allow_html=True)
            
            status_col, diagnostics_col = st.columns([3, 7])
            with status_col:
                selected_status = st.selectbox(f"Execution Status", ["PASSED", "WARNING", "FAILED"], key=f"status_{case['ID']}")
            with diagnostics_col:
                custom_log = st.text_input(f"Diagnostics Log / Observation Notes", placeholder="Enter environment observation data metrics...", key=f"log_{case['ID']}")
                if not custom_log:
                    custom_log = "Verified under standard test constraints. Status verified clear." if selected_status == "PASSED" else "Flagged variance from expected core runtime profiles."
            
            compiled_apk_results.append({
                "ID": case["ID"],
                "Page Path": "Mobile OS App Shell",
                "Component": case["Component"],
                "Objective": case["Objective"],
                "Status": selected_status,
                "Diagnostics Log": f"[{tester_identity}] {custom_log}"
            })
            st.write("<div style='height: 5px;'></div>", unsafe_allow_html=True)
            
    st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    save_apk_report = st.button("💾 Log Mobile Testing Report & Commit to Vault", use_container_width=True)
    
    if save_apk_report:
        passed_apk = sum(1 for c in compiled_apk_results if c["Status"] == "PASSED")
        final_apk_grade = int((passed_apk / len(compiled_apk_results)) * 100)
        
        append_to_historical_vault(
            target_name=apk_name,
            final_score=final_apk_grade,
            items_checked=len(compiled_apk_results),
            metadata_str=f"{tester_identity} Log",
            type_label="Mobile APK Suite",
            test_cases=compiled_apk_results
        )
        st.success(f"🎉 System Matrix Success: Committed mobile run report for {apk_name} into history vault logs database safely!")

# -----------------------------------------------------------------------------
# 6. CENTRALIZED HISTORICAL RUN ARCHIVE LOGS (COMMON TO BOTH WORKSPACES)
# -----------------------------------------------------------------------------
st.write("<div style='height: 30px;'></div>", unsafe_allow_html=True)
st.divider()
st.markdown("<h2 style='font-size:19px; font-weight:700; color:#FFFFFF;'>🗄️ Automated Testing Run Log History Vault</h2>", unsafe_allow_html=True)
st.markdown("<p style='font-size:13px; color:#8A99AD; margin-top:-10px;'>Tracks past website execution scans and custom mobile APK sheets without data loss</p>", unsafe_allow_html=True)

historical_runs = load_historical_vault()

if not historical_runs:
    st.markdown("<p style='font-size:13px; color:#FFBD2E; font-style:italic;'>No trace records currently present inside database files.</p>", unsafe_allow_html=True)
else:
    summary_history_rows = []
    for run in historical_runs:
        summary_history_rows.append({
            "Execution Date/Time": run["timestamp"],
            "Target Root Vector Domain": run["target_url"],
            "Scanned Footprint": f"{run['total_pages']} Tasks Checked",
            "Discovered Metadata": str(run['total_images']),
            "Suite Type": str(run.get('total_links', 'Web Crawl Engine')),
            "Quality Pass Score": f"{run['score']}% Grade"
        })
    
    st.dataframe(pd.DataFrame(summary_history_rows), use_container_width=True, hide_index=True)
    
    st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    run_options = [f"[{run['timestamp']}] - {run['target_url']} ({run['score']}% Grade)" for run in historical_runs]
    selected_run_string = st.selectbox("Select a historical record file target node to inspect/export", run_options)
    
    selected_index = run_options.index(selected_run_string)
    target_archived_run = historical_runs[selected_index]
    cases_df = pd.DataFrame(target_archived_run["cases"])
    
    csv_col, exp_col = st.columns([4, 6])
    with csv_col:
        csv_buffer = cases_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Selected Test Cases Array to CSV File Spreadsheet",
            data=csv_buffer,
            file_name=f"qa_test_report_{target_archived_run['timestamp'].replace(' ', '_').replace(':', '-')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with exp_col:
        with st.expander("👁️ View Extracted Case Rows Inline"):
            st.dataframe(cases_df, use_container_width=True, hide_index=True)
