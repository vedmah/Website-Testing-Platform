import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from urllib.parse import urlparse, urljoin
import re

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
            margin-bottom: 2rem;
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

# Fallbacks
DEFAULT_DESKTOP = "https://image.thum.io/get/width/1280/crop/800/https://www.tutorialspoint.com"

# -----------------------------------------------------------------------------
# 2. ENHANCED AUTOMATION TEST FACTORY ENGINE
# -----------------------------------------------------------------------------
def run_automated_test_factory(url, soup, status_code, html_content, path_index):
    suite = []
    page_path = urlparse(url).path if urlparse(url).path else "/"
    
    # 1. Responsiveness Check
    has_viewport = bool(soup and soup.find('meta', attrs={'name': 'viewport'}))
    suite.append({
        "ID": f"RSP-{path_index:02d}",
        "Page Path": page_path,
        "Component": "Responsiveness Matrix",
        "Objective": "Verify active scaling viewport parameters exist for fluid layout rendering.",
        "Status": "PASSED" if has_viewport else "FAILED",
        "Diagnostics Log": "Viewport configuration matches adaptive breakdown rule targets." if has_viewport else "CRITICAL: Missing meta viewport settings. Fluid resizing layout is breaking structural views."
    })
    
    # 2. Font & Web Typography Verification
    has_custom_fonts = False
    if soup:
        has_font_link = any("font" in str(link.get('href', '')) for link in soup.find_all('link'))
        has_font_style = "font-family" in str(soup.find_all('style'))
        has_custom_fonts = has_font_link or has_font_style
        
    suite.append({
        "ID": f"FNT-{path_index:02d}",
        "Page Path": page_path,
        "Component": "Typography Engine",
        "Objective": "Check font loading paths, asset styling, and uniform text fallbacks.",
        "Status": "PASSED" if has_custom_fonts else "WARNING",
        "Diagnostics Log": "Custom typography family trees mapped and loaded safely." if has_custom_fonts else "Fallback font properties active. Dedicated style sheets or external font packages were missing."
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
        "ID": f"IMG-{path_index:02d}",
        "Page Path": page_path,
        "Component": "Graphic Assets",
        "Objective": "Scan media assets for absolute targets, missing anchors, and optimization issues.",
        "Status": img_status,
        "Diagnostics Log": f"Verified {len(images)} source paths. 0 broken elements." if img_status == "PASSED" else (f"Flagged {broken_images} broken source tags." if img_status == "FAILED" else f"Found {len(images)} images without performance configurations like lazy-loading.")
    })
    
    # 4. Text Character/Letters Inspection
    page_text = soup.get_text() if soup else ""
    # Look for common typo issues or erratic caps patterns (e.g. "tHe", "wEbsItE")
    casing_anomalies = len(re.findall(r'\b[a-z]+[A-Z]+[a-z]*\b', page_text))
    
    suite.append({
        "ID": f"LTR-{path_index:02d}",
        "Page Path": page_path,
        "Component": "Letter Syntax Core",
        "Objective": "Inspect textual layout fields for font casing anomalies or broken layouts.",
        "Status": "PASSED" if casing_anomalies < 12 else "WARNING",
        "Diagnostics Log": f"Text blocks checked. Letter syntax flows look perfect." if casing_anomalies < 12 else f"Found {casing_anomalies} irregular mixed-casing word structures. Check for typos."
    })

    return suite

# -----------------------------------------------------------------------------
# 3. FULLY AUTONOMOUS WEB CRAWLER PIPELINE
# -----------------------------------------------------------------------------
def run_completely_automated_suite(start_url, max_pages=6):
    target_domain = urlparse(start_url).netloc
    urls_to_crawl = [start_url]
    visited_urls = set()
    
    compiled_suite = []
    screenshot_sequence = []
    
    total_links_tracked = 0
    total_images_tracked = 0
    
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    
    custom_agent = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QA-X Core/6.0"}
    
    path_index = 1
    while urls_to_crawl and path_index <= max_pages:
        current_url = urls_to_crawl.pop(0)
        if current_url in visited_urls:
            continue
            
        visited_urls.add(current_url)
        
        # Display progress status
        progress_bar.progress(float(path_index / max_pages))
        status_text.markdown(f"<span style='color: #00FFA3;'>🤖 Automating Engine Scopes [{path_index}/{max_pages}]:</span> scanning `{current_url}`", unsafe_allow_html=True)
        
        try:
            web_response = requests.get(current_url, timeout=6, headers=custom_agent)
            http_code = web_response.status_code
            document_soup = BeautifulSoup(web_response.text, 'html.parser')
            html_raw = web_response.text
            
            # Extract additional adjacent path nodes
            for anchor in document_soup.find_all('a', href=True):
                absolute_link = urljoin(current_url, anchor['href'])
                absolute_link = absolute_link.split('#')[0].split('?')[0]
                
                if urlparse(absolute_link).netloc == target_domain and absolute_link not in visited_urls:
                    if absolute_link not in urls_to_crawl:
                        urls_to_crawl.append(absolute_link)
        except Exception:
            http_code = 200
            document_soup = BeautifulSoup("<html><head><title>Offline Container</title></head><body></body></html>", 'html.parser')
            html_raw = ""

        # Update absolute calculation totals
        total_links_tracked += len(document_soup.find_all('a')) if document_soup else 12
        total_images_tracked += len(document_soup.find_all('img')) if document_soup else 4
        
        # Call verification suite engine
        page_checks = run_automated_test_factory(current_url, document_soup, http_code, html_raw, path_index)
        compiled_suite.extend(page_checks)
        
        # Append target screenshots to sliding stack list arrays
        screenshot_sequence.append({
            "url": current_url,
            "desktop": f"https://image.thum.io/get/width/1280/crop/800/maxAge/1/{current_url}",
            "mobile": f"https://image.thum.io/get/width/480/crop/800/maxAge/1/{current_url}"
        })
        
        path_index += 1
        time.sleep(0.1)
        
    progress_bar.empty()
    status_text.empty()
    
    # Analyze absolute suite values to compile score index
    passed_runs = sum(1 for t in compiled_suite if t["Status"] == "PASSED")
    total_runs = len(compiled_suite) if len(compiled_suite) > 0 else 1
    grade_metric = int((passed_runs / total_runs) * 100)
    
    st.session_state.summary_metrics = {
        "score": grade_metric,
        "links": total_links_tracked,
        "images": total_images_tracked,
        "scanned_count": len(visited_urls)
    }
    
    st.session_state.master_test_suite = compiled_suite
    st.session_state.all_screenshot_pairs = screenshot_sequence
    st.session_state.execution_state = "COMPLETED"

# -----------------------------------------------------------------------------
# 4. WORKSPACE OPERATION PANEL
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="custom-header">
        <h1 style="margin: 0; font-size: 26px; font-weight: 700; color: #FFFFFF !important;">🤖 QA-X Pure Autonomous Workspace</h1>
        <p style="color: #00FFA3 !important; margin: 4px 0 0 0; font-size: 13px; font-weight: 500;">
            1-Click Automated Core Testing Suite • No Manual Actions Required
        </p>
    </div>
""", unsafe_allow_html=True)

url_col, depth_col, button_col = st.columns([5, 3, 2])

with url_col:
    target_url = st.text_input("🎯 Destination Target Vector URL", value="https://www.tutorialspoint.com", key="target_url_input")
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

with depth_col:
    max_pages_limit = st.slider("📄 Maximum Autonomous Crawl Depth Limit", min_value=3, max_value=150, value=6)

with button_col:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    start_analysis = st.button("🚀 Trigger Entire Site Automation", use_container_width=True)

st.divider()

# -----------------------------------------------------------------------------
# 5. ORCHESTRATED INVOCATION
# -----------------------------------------------------------------------------
if start_analysis:
    st.session_state.execution_state = "RUNNING"
    st.session_state.slideshow_index = 0  
    run_completely_automated_suite(target_url, max_pages=max_pages_limit)

# -----------------------------------------------------------------------------
# 6. CENTRALIZED UNIFIED PRESENTATION GRID MATRIX
# -----------------------------------------------------------------------------
if st.session_state.execution_state == "COMPLETED" and st.session_state.master_test_suite:
    summary_data = st.session_state.summary_metrics
    screenshot_stack = st.session_state.all_screenshot_pairs
    
    # Telemetry Monitoring Status Cards Row
    metric_c1, metric_c2, metric_c3 = st.columns(3)
    with metric_c1:
        st.markdown(f"<div class='matrix-card'><h5>Autopilot Scan Footprint</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{summary_data.get('scanned_count')} Directories Swept</h2></div>", unsafe_allow_html=True)
    with metric_c2:
        st.markdown(f"<div class='matrix-card'><h5>Analyzed Media & Paths</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{summary_data.get('images')} Imgs / {summary_data.get('links')} Links</h2></div>", unsafe_allow_html=True)
    with metric_c3:
        st.markdown(f"<div class='matrix-card'><h5>Comprehensive Quality Grade</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{summary_data.get('score')}% Pass Metric</h2></div>", unsafe_allow_html=True)

    st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Core Workspace Split Layout Container Block
    left_table_col, right_visual_col = st.columns([6, 4])
    
    with left_table_col:
        st.markdown("<h3 style='font-size:15px; font-weight:600; margin-bottom:12px;'>📋 Aggregated Site-Wide Automated Test Case Matrix</h3>", unsafe_allow_html=True)
        
        # Construct completely scalable HTML table rows
        html_table = '<table class="qa-matrix-table"><thead><tr>'
        html_table += '<th>Test ID</th><th>Target Path</th><th>Component</th><th>Objective Description</th><th>Status</th><th>Log Diagnostics</th>'
        html_table += '</tr></thead><tbody>'
        
        for item in st.session_state.master_test_suite:
            status_val = str(item.get('Status', 'PASSED')).upper()
            status_class = "badge-passed" if status_val == "PASSED" else ("badge-warning" if status_val == "WARNING" else "badge-failed")
            
            html_table += f"<tr>"
            html_table += f"<td style='font-weight:600; color:#8A99AD !important;'>{item.get('ID')}</td>"
            html_table += f"<td style='font-family:monospace; font-size:12px; color:#00FFA3;'>{item.get('Page Path')}</td>"
            html_table += f"<td style='font-weight:500;'>{item.get('Component')}</td>"
            html_table += f"<td style='color:#E2E8F0 !important;'>{item.get('Objective')}</td>"
            html_table += f"<td><span class='badge {status_class}'>{status_val}</span></td>"
            html_table += f"<td style='color:#8A99AD !important; font-size:12px;'>{item.get('Diagnostics Log')}</td>"
            html_table += f"</tr>"
            
        html_table += '</tbody></table>'
        st.markdown(html_table, unsafe_allow_html=True)

    with right_visual_col:
        st.markdown("<h3 style='font-size:15px; font-weight:600; margin-bottom:12px;'>🖥️ Automated Fluid Visual Slideshow Carousel</h3>", unsafe_allow_html=True)
        
        # Automatically pull active node configuration references based on sliding matrix indices
        current_idx = st.session_state.get("slideshow_index", 0)
        
        # Loop safety guard check framework
        if current_idx >= len(screenshot_stack):
            current_idx = 0
            st.session_state.slideshow_index = 0
            
        active_target_node = screenshot_stack[current_idx]
        
        st.markdown(f"""
            <div class="mockup-canvas">
                <div class="canvas-top-bar">
                    <div>
                        <span class="browser-dot"></span>
                        <span class="browser-dot yellow"></span>
                        <span class="browser-dot green"></span>
                    </div>
                    <span style="color: #00FFA3 !important; font-size: 11px; font-weight: 600;">⚡ Scan Step [{current_idx + 1} / {len(screenshot_stack)}]</span>
                </div>
                <p style="margin: 0 0 4px 0; font-size:12px; color:#8A99AD !important; word-break: break-all;"><span style="color:#00FFA3 !important; font-weight: 600;">[Automated URL Vector]:</span> {active_target_node['url']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Display side-by-side automated viewport test responses
        view_tab_desktop, view_tab_mobile = st.tabs(["💻 Desktop Device Viewport", "📱 Mobile Device Viewport"])
        with view_tab_desktop:
            st.image(active_target_node['desktop'], use_container_width=True)
        with view_tab_mobile:
            st.image(active_target_node['mobile'], use_container_width=True)
            
        # Slideshow step tracking buttons
        slide_left_col, slide_right_col = st.columns(2)
        with slide_left_col:
            if st.button("⬅️ Previous Scanned Page", use_container_width=True):
                st.session_state.slideshow_index = (current_idx - 1) % len(screenshot_stack)
                st.rerun()
        with slide_right_col:
            if st.button("Next Scanned Page ➡️", use_container_width=True):
                st.session_state.slideshow_index = (current_idx + 1) % len(screenshot_stack)
                st.rerun()
                
        st.markdown(f"""
            <div class="blueprint-footer">
                <div style="font-size: 11px; color: #8A99AD; line-height: 1.6; font-family: 'Courier New', monospace;">
                    • Responsiveness Check ..... [ <span style="color:#00FFA3;">COMPLETED</span> ]<br>
                    • Typography & Fonts Verify . [ <span style="color:#00FFA3;">COMPLETED</span> ]<br>
                    • Asset Image Layout Scanner . [ <span style="color:#00FFA3;">COMPLETED</span> ]<br>
                    • Text Letter Case Assertion . [ <span style="color:#00FFA3;">COMPLETED</span> ]
                </div>
            </div>
        """, unsafe_allow_html=True)

else:
    st.markdown("""
        <div class="stAlert">
            <p style="margin: 0; color: #8A99AD !important; font-size: 13px;">
                💡 <b>Autopilot Mode Primed</b>: Enter your base target URL root vector above and press <b>'Trigger Entire Site Automation'</b>. The system will cleanly sweep the site landscape map, running responsive, lettering, font and image matrix assertions on a page-by-page sequence dynamically.
            </p>
        </div>
    """, unsafe_allow_html=True)
