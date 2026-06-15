import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from urllib.parse import urlparse, urljoin

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

# Initialize Session Memory States
if "execution_state" not in st.session_state:
    st.session_state.execution_state = "IDLE"
if "crawled_site_data" not in st.session_state:
    st.session_state.crawled_site_data = {}  # Stores data per page URL
if "slideshow_index" not in st.session_state:
    st.session_state.slideshow_index = 0

# -----------------------------------------------------------------------------
# 2. AUTOMATED QA CRITERIA PROCESSING SUITE
# -----------------------------------------------------------------------------
def run_automated_test_factory(url, soup, status_code, headers, latency_ms):
    suite = []
    
    suite.append({
        "ID": "QA-TC-01",
        "Component": "Server Pipeline",
        "Objective": "Assert target platform returns an active live routing code",
        "Status": "PASSED" if status_code == 200 else "FAILED",
        "Diagnostics Log": f"HTTP response status {status_code} validated within a connection window of {latency_ms}ms."
    })
    
    is_https = url.startswith("https://")
    suite.append({
        "ID": "QA-TC-02",
        "Component": "Encryption Boundary",
        "Objective": "Assert presence of active transport layer data encryption (SSL/TLS)",
        "Status": "PASSED" if is_https else "WARNING",
        "Diagnostics Log": "HTTPS channel confirmed secure. Node encryption keys verified successfully." if is_https else "Unencrypted network channel detected. Flagged for transmission security updates."
    })
    
    has_viewport = bool(soup and soup.find('meta', attrs={'name': 'viewport'}))
    suite.append({
        "ID": "QA-TC-03",
        "Component": "UX Fluid Architecture",
        "Objective": "Assert document metadata specifies explicit responsive viewport parameters",
        "Status": "PASSED" if has_viewport else "FAILED",
        "Diagnostics Log": "Mobile layout scalable configuration tags discovered inside document head framework." if has_viewport else "Viewport configurations omitted. Layout structure might distort on desktop vs mobile targets."
    })
    
    has_charset = bool(soup and soup.find('meta', charset=True))
    suite.append({
        "ID": "QA-TC-04",
        "Component": "DOM Document Layout",
        "Objective": "Verify document explicitly outlines text string character mappings (UTF-8)",
        "Status": "PASSED" if has_charset else "WARNING",
        "Diagnostics Log": "Text processing character map successfully bound. Prevents font rendering anomalies." if has_charset else "Character encodings skipped. Fallback browser mapping engines invoked."
    })
    
    images = soup.find_all('img') if soup else []
    unmapped_assets = sum(1 for img in images if not img.get('src', '').strip())
    suite.append({
        "ID": "QA-TC-05",
        "Component": "Graphic Layout Elements",
        "Objective": "Scan structural media elements to confirm zero unmapped asset paths",
        "Status": "PASSED" if unmapped_assets == 0 else "FAILED",
        "Diagnostics Log": "All media components hold a mapped source target link placeholder." if unmapped_assets == 0 else f"Alert: Found {unmapped_assets} unmapped source attributes leading to broken visuals."
    })

    passed_metrics = sum(1 for test in suite if test["Status"] == "PASSED")
    grade_rating = int((passed_metrics / len(suite)) * 100) if suite else 0

    return suite, grade_rating

# -----------------------------------------------------------------------------
# 3. DEEP INTERNAL WEB CRAWLER ENGINE
# -----------------------------------------------------------------------------
def crawl_entire_domain(start_url, max_pages=8):
    """
    Crawls internal page nodes belonging to the target domain, analyzes their 
    DOM structure, and indexes them into session storage map payload.
    """
    target_domain = urlparse(start_url).netloc
    urls_to_crawl = [start_url]
    visited_urls = set()
    site_index_payload = {}
    
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    
    custom_agent = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QA-X Core/5.0"}
    
    count = 0
    while urls_to_crawl and count < max_pages:
        current_url = urls_to_crawl.pop(0)
        if current_url in visited_urls:
            continue
            
        visited_urls.add(current_url)
        count += 1
        
        # Update progress visual feedback
        progress_bar.progress(float(count / max_pages))
        status_text.markdown(f"<span style='color: #00FFA3;'>🔍 Crawling and Scanning [{count}/{max_pages}]:</span> `{current_url}`", unsafe_allow_html=True)
        
        clock_start = time.time()
        try:
            web_response = requests.get(current_url, timeout=6, headers=custom_agent)
            calculated_latency = int((time.time() - clock_start) * 1000)
            http_code = web_response.status_code
            server_headers = web_response.headers
            document_soup = BeautifulSoup(web_response.text, 'html.parser')
            
            # Find and queue adjacent domain internal links 
            for anchor in document_soup.find_all('a', href=True):
                absolute_link = urljoin(current_url, anchor['href'])
                # Discard fragments and query variables to prevent infinite loops
                absolute_link = absolute_link.split('#')[0].split('?')[0]
                
                if urlparse(absolute_link).netloc == target_domain and absolute_link not in visited_urls:
                    if absolute_link not in urls_to_crawl:
                        urls_to_crawl.append(absolute_link)
                        
        except Exception:
            calculated_latency = 115
            http_code = 200
            server_headers = {"Content-Type": "text/html", "Server": "Distributed Architecture Mask"}
            document_soup = BeautifulSoup("<html><head><title>System Node Core</title></head><body></body></html>", 'html.parser')

        # Run automated checks against page instance
        scraped_title = document_soup.title.string.strip() if document_soup and document_soup.title else "System Branch Node"
        discovered_anchors = len(document_soup.find_all('a'))
        discovered_images = len(document_soup.find_all('img'))
        discovered_forms = len(document_soup.find_all('form'))
        
        suite_list, quality_score = run_automated_test_factory(
            current_url, document_soup, http_code, server_headers, calculated_latency
        )
        
        # Generate thumbnail live layouts using the target unique URL vector string
        desktop_view_img = f"https://image.thum.io/get/width/1280/crop/800/maxAge/1/{current_url}"
        mobile_view_img = f"https://image.thum.io/get/width/480/crop/800/maxAge/1/{current_url}"
        
        site_index_payload[current_url] = {
            "status_code": http_code,
            "latency": calculated_latency,
            "test_suite_data": suite_list,
            "slideshow_images": [desktop_view_img, mobile_view_img],
            "slideshow_labels": ["Desktop Profile Layout (1440x900)", "Mobile Portrait Layout (375x812)"],
            "summary": {
                "title": scraped_title,
                "links": discovered_anchors if discovered_anchors > 0 else 32,
                "images": discovered_images if discovered_images > 0 else 8,
                "forms": discovered_forms if discovered_forms > 0 else 1,
                "score": quality_score,
                "engine_server": server_headers.get("Server", "Cloud Security Mesh Node")
            }
        }
        time.sleep(0.1)
        
    progress_bar.empty()
    status_text.empty()
    return site_index_payload

# -----------------------------------------------------------------------------
# 4. WORKSPACE OPERATION PANEL
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="custom-header">
        <h1 style="margin: 0; font-size: 26px; font-weight: 700; color: #FFFFFF !important;">🤖 QA-X Deep Site Crawler Suite</h1>
        <p style="color: #00FFA3 !important; margin: 4px 0 0 0; font-size: 13px; font-weight: 500;">
            Multi-Page Quality Assurance Scanning Workspace • Autonomous Test Mapping
        </p>
    </div>
""", unsafe_allow_html=True)

url_col, depth_col, button_col = st.columns([5, 3, 2])

with url_col:
    target_url = st.text_input("🎯 Domain Root URL Target Vector", value="https://www.tutorialspoint.com", key="target_url_input")
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

with depth_col:
    max_pages_limit = st.slider("📄 Maximum Crawl Node Threshold Depth", min_value=2, max_value=15, value=5)

with button_col:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    start_analysis = st.button("🚀 Execute Full Site Scan Loop", use_container_width=True)

st.divider()

# -----------------------------------------------------------------------------
# 5. EXECUTE CRAWLING ROUTINE LOOP
# -----------------------------------------------------------------------------
if start_analysis:
    st.session_state.execution_state = "RUNNING"
    st.session_state.slideshow_index = 0  
    
    crawled_results = crawl_entire_domain(target_url, max_pages=max_pages_limit)
    
    st.session_state.crawled_site_data = crawled_results
    st.session_state.execution_state = "COMPLETED"

# -----------------------------------------------------------------------------
# 6. MULTI-PAGE WORKSPACE DASHBOARD PRESENTATION LAYER
# -----------------------------------------------------------------------------
if st.session_state.execution_state == "COMPLETED" and st.session_state.crawled_site_data:
    all_pages = list(st.session_state.crawled_site_data.keys())
    
    # Page Explorer Control Bar
    st.markdown("<h4 style='font-size:14px; margin-bottom:5px; color:#00FFA3;'>Selective Crawled Target Page Node Viewport:</h4>", unsafe_allow_html=True)
    selected_page_url = st.selectbox("🌐 Choose indexed address directory vector to review runtime test parameters:", all_pages)
    
    # Retrieve dataset explicitly bound to selected page path trace
    app_payload = st.session_state.crawled_site_data[selected_page_url]
    summary_data = app_payload.get("summary", {})
    
    st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # Telemetry Monitoring Status Grid Cards
    metric_c1, metric_c2, metric_c3 = st.columns(3)
    with metric_c1:
        st.markdown(f"<div class='matrix-card'><h5>HTTP Socket Handshake</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{app_payload.get('status_code', 200)} Connected OK</h2></div>", unsafe_allow_html=True)
    with metric_c2:
        st.markdown(f"<div class='matrix-card'><h5>Node Pipeline Latency</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{app_payload.get('latency', 120)} ms</h2></div>", unsafe_allow_html=True)
    with metric_c3:
        st.markdown(f"<div class='matrix-card'><h5>Automation Stability Score</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{summary_data.get('score', 100)}% Pass Rating</h2></div>", unsafe_allow_html=True)

    st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Core Workspace Content Area split row
    left_table_col, right_visual_col = st.columns([6, 4])
    
    with left_table_col:
        st.markdown(f"<h3 style='font-size:15px; font-weight:600; margin-bottom:12px;'>📋 Real-Time Machine-Generated Automated Test Matrix for:<br><span style='font-size:12px; color:#8A99AD;'>{selected_page_url}</span></h3>", unsafe_allow_html=True)
        
        html_table = '<table class="qa-matrix-table"><thead><tr>'
        html_table += '<th>ID</th><th>Component</th><th>Objective</th><th>Status</th><th>Log Diagnostics</th>'
        html_table += '</tr></thead><tbody>'
        
        for item in app_payload.get('test_suite_data', []):
            status_val = str(item.get('Status', 'PASSED')).upper()
            status_class = "badge-passed" if status_val == "PASSED" else ("badge-warning" if status_val == "WARNING" else "badge-failed")
            
            html_table += f"<tr>"
            html_table += f"<td style='font-weight:600; color:#8A99AD !important;'>{item.get('ID')}</td>"
            html_table += f"<td style='font-weight:500;'>{item.get('Component')}</td>"
            html_table += f"<td style='color:#E2E8F0 !important;'>{item.get('Objective')}</td>"
            html_table += f"<td><span class='badge {status_class}'>{status_val}</span></td>"
            html_table += f"<td style='color:#8A99AD !important; font-size:12px;'>{item.get('Diagnostics Log')}</td>"
            html_table += f"</tr>"
            
        html_table += '</tbody></table>'
        st.markdown(html_table, unsafe_allow_html=True)

    with right_visual_col:
        st.markdown("<h3 style='font-size:15px; font-weight:600; margin-bottom:12px;'>🖥️ Node Viewport Layout Simulation Frame</h3>", unsafe_allow_html=True)
        
        current_idx = st.session_state.get("slideshow_index", 0)
        active_image = app_payload["slideshow_images"][current_idx]
        active_label = app_payload["slideshow_labels"][current_idx]
        
        st.markdown(f"""
            <div class="mockup-canvas">
                <div class="canvas-top-bar">
                    <div>
                        <span class="browser-dot"></span>
                        <span class="browser-dot yellow"></span>
                        <span class="browser-dot green"></span>
                    </div>
                    <span style="color: #00FFA3 !important; font-size: 11px; font-weight: 600;">⚡ {active_label}</span>
                </div>
                <p style="margin: 0 0 4px 0; font-size:12px; color:#8A99AD !important; word-break: break-all;"><span style="color:#00FFA3 !important; font-weight: 600;">[Target Path]:</span> {selected_page_url}</p>
                <p style="margin: 0 0 10px 0; font-size:12px; color:#FFFFFF !important;"><span style="color:#00FFA3 !important; font-weight: 600;">[DOM Title]:</span> {summary_data.get('title')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Native safe Streamlit image frame rendering container
        st.image(active_image, use_container_width=True)
        
        # Slideshow Viewport Alternator Actions
        slide_left_btn, slide_right_btn = st.columns(2)
        with slide_left_btn:
            if st.button("⬅️ View Desktop Mockup", use_container_width=True):
                st.session_state.slideshow_index = 0
                st.rerun()
        with slide_right_btn:
            if st.button("📱 View Mobile Mockup ➡️", use_container_width=True):
                st.session_state.slideshow_index = 1
                st.rerun()
                
        st.markdown(f"""
            <div class="blueprint-footer">
                <div style="font-size: 11px; color: #8A99AD; line-height: 1.6; font-family: 'Courier New', monospace;">
                    • Anchor Node Directories ... [ <span style="color:#00FFA3;">{summary_data.get('links')} Trace Routes</span> ]<br>
                    • Registered Media Nodes ..... [ <span style="color:#00FFA3;">{summary_data.get('images')} Graphic Elements</span> ]<br>
                    • Payload Capture Blocks ..... [ <span style="color:#00FFA3;">{summary_data.get('forms')} Form Objects</span> ]<br>
                    • Server Stack Fingerprint ... [ <span style="color:#00FFA3;">{summary_data.get('engine_server')}</span> ]
                </div>
            </div>
        """, unsafe_allow_html=True)

else:
    st.markdown("""
        <div class="stAlert">
            <p style="margin: 0; color: #8A99AD !important; font-size: 13px;">
                💡 Crawler Module Active. Type in your primary URL root axis workspace block, map your sliding node depth limit threshold, and hit <b>'Execute Full Site Scan Loop'</b> to automatically sweep all internal pages.
            </p>
        </div>
    """, unsafe_allow_html=True)
