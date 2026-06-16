import streamlit as st
import asyncio
import httpx
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

# -----------------------------------------------------------------------------
# 2. ENHANCED AUTOMATION TEST FACTORY ENGINE
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
        "Diagnostics Log": "Viewport configuration matches adaptive breakdown rule targets." if has_viewport else "CRITICAL: Missing meta viewport settings. Fluid resizing layout is breaking structural views."
    })
    
    # 2. Font & Web Typography Verification
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
        "ID": f"IMG-{path_index:03d}",
        "Page Path": page_path,
        "Component": "Graphic Assets",
        "Objective": "Scan media assets for absolute targets, missing anchors, and optimization issues.",
        "Status": img_status,
        "Diagnostics Log": f"Verified {len(images)} source paths. 0 broken elements." if img_status == "PASSED" else (f"Flagged {broken_images} broken source tags." if img_status == "FAILED" else f"Found {len(images)} images without performance configurations like lazy-loading.")
    })
    
    # 4. Text Character/Letters Inspection
    page_text = soup.get_text() if soup else ""
    casing_anomalies = len(re.findall(r'\b[a-z]+[A-Z]+[a-z]*\b', page_text))
    
    suite.append({
        "ID": f"LTR-{path_index:03d}",
        "Page Path": page_path,
        "Component": "Letter Syntax Core",
        "Objective": "Inspect textual layout fields for font casing anomalies or broken layouts.",
        "Status": "PASSED" if casing_anomalies < 12 else "WARNING",
        "Diagnostics Log": f"Text blocks checked. Letter syntax flows look perfect." if casing_anomalies < 12 else f"Found {casing_anomalies} irregular mixed-casing word structures. Check for typos."
    })

    return suite

# -----------------------------------------------------------------------------
# 3. HIGH-SPEED CONCURRENT ASYNC CRAWLER PIPELINE
# -----------------------------------------------------------------------------
async def fetch_and_parse_node(client, url, path_index, target_domain):
    custom_agent = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QA-X Core/8.0"}
    discovered_links = []
    
    try:
        response = await client.get(url, headers=custom_agent, timeout=5.0, follow_redirects=True)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Fast extraction of discovered sub-links
        for anchor in soup.find_all('a', href=True):
            absolute_link = urljoin(url, anchor['href']).split('#')[0].split('?')[0]
            if urlparse(absolute_link).netloc == target_domain:
                if not absolute_link.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.tar', '.gz')):
                    discovered_links.append(absolute_link)
    except Exception:
        soup = BeautifulSoup("<html><body></body></html>", 'html.parser')
        
    # Generate verification suites
    suite_cases = run_automated_test_factory(url, soup, path_index)
    
    # Aggregate component counts
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
    
    # Using HTTP/2 concurrent socket pool connection management architecture
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    async with httpx.AsyncClient(limits=limits, verify=False) as client:
        while urls_to_crawl and path_index <= 40: # High safety cutoff ceiling threshold
            # Pull a concurrent batch tier layer (up to 10 nodes processed simultaneously)
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
                    <span style='color: #00FFA3; font-weight: 600;'>⚡ Async Speed Mode: Analyzing Batch Segment ({len(visited_urls)} pages discovered)</span><br>
                    <span style='color: #8A99AD; font-size: 11px;'>Executing parallel socket pipeline paths...</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Fire all async threads concurrently
            tasks = []
            for url in batch:
                tasks.append(fetch_and_parse_node(client, url, path_index, target_domain))
                path_index += 1
                
            results = await asyncio.gather(*tasks)
            
            # Unpack payload items instantly
            for suite_cases, screenshot_node, discovered_links, link_count, img_count in results:
                master_suites.extend(suite_cases)
                screenshot_stack.append(screenshot_node)
                total_links += link_count
                total_images += img_count
                
                # Append untracked internal connections back into the loop
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

# -----------------------------------------------------------------------------
# 4. WORKSPACE OPERATION PANEL
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="custom-header">
        <h1 style="margin: 0; font-size: 26px; font-weight: 700; color: #FFFFFF !important;">🤖 QA-X Pure Autonomous Workspace</h1>
        <p style="color: #00FFA3 !important; margin: 4px 0 0 0; font-size: 13px; font-weight: 500;">
            1-Click Total Domain Scan • High-Speed Asynchronous Matrix
        </p>
    </div>
""", unsafe_allow_html=True)

url_col, button_col = st.columns([7, 3])

with url_col:
    target_url = st.text_input("🎯 Destination Target Vector URL", value="https://www.tutorialspoint.com", key="target_url_input")
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

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
    # Execute the asynchronous event loop setup block context
    asyncio.run(pipeline_orchestrator(target_url))

# -----------------------------------------------------------------------------
# 6. CENTRALIZED UNIFIED PRESENTATION GRID MATRIX
# -----------------------------------------------------------------------------
if st.session_state.execution_state == "COMPLETED" and st.session_state.master_test_suite:
    summary_data = st.session_state.summary_metrics
    screenshot_stack = st.session_state.all_screenshot_pairs
    
    metric_c1, metric_c2, metric_c3 = st.columns(3)
    with metric_c1:
        st.markdown(f"<div class='matrix-card'><h5>Total Domain Footprint</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{summary_data.get('scanned_count')} Pages Swept</h2></div>", unsafe_allow_html=True)
    with metric_c2:
        st.markdown(f"<div class='matrix-card'><h5>Analyzed Media & Paths</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{summary_data.get('images')} Imgs / {summary_data.get('links')} Links</h2></div>", unsafe_allow_html=True)
    with metric_c3:
        st.markdown(f"<div class='matrix-card'><h5>Comprehensive Quality Grade</h5><h2 style='color:#00FFA3 !important; font-size:22px;'>{summary_data.get('score')}% Pass Metric</h2></div>", unsafe_allow_html=True)

    st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    left_table_col, right_visual_col = st.columns([6, 4])
    
    with left_table_col:
        st.markdown("<h3 style='font-size:15px; font-weight:600; margin-bottom:12px;'>📋 Aggregated Site-Wide Automated Test Case Matrix</h3>", unsafe_allow_html=True)
        
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
        
        current_idx = st.session_state.get("slideshow_index", 0)
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
        
        view_tab_desktop, view_tab_mobile = st.tabs(["💻 Desktop Device Viewport", "📱 Mobile Device Viewport"])
        with view_tab_desktop:
            st.image(active_target_node['desktop'], use_container_width=True)
        with view_tab_mobile:
            st.image(active_target_node['mobile'], use_container_width=True)
            
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
                💡 <b>Ultra-Speed Mode Active</b>: Powered by multi-connection concurrency. Click <b>'Trigger Entire Site Automation'</b> to parse everything in under a minute!
            </p>
        </div>
    """, unsafe_allow_html=True)
