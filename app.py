import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from urllib.parse import urlparse, urljoin

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM RESPONSIVE CSS (Dark Tech Accent Theme)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="QA-X Streamlit AI Testing Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom injection for professional styling and adaptive mobile layouts
st.markdown("""
    <style>
        /* Base Theme Colors */
        :root {
            --primary: #00FFA3; /* Neon Teal */
            --bg-card: #1E222B;
            --text-main: #E2E8F0;
        }
        
        /* Main Container Responsiveness */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 100%;
        }
        
        /* Metric Card styling */
        .metric-card {
            background-color: #161920;
            border-left: 4px solid #00FFA3;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        /* Responsive Grid Adaptation for Mobile */
        @media (max-width: 768px) {
            .stHorizontalBlock {
                flex-direction: column !important;
            }
            .metric-card {
                padding: 1rem;
            }
        }
        
        /* Clean Headers */
        h1, h2, h3 {
            color: #FFFFFF !important;
            font-family: 'Inter', sans-serif;
        }
    </style>
""", unsafe_index=True)

# -----------------------------------------------------------------------------
# 2. CORE CORE UTILITY FUNCTIONS (Testing Engines)
# -----------------------------------------------------------------------------

async def run_playwright_test(url, viewport_width, viewport_height):
    """Handles core screenshot capture and layout verification asynchronously."""
    metrics = {"status": "Failed", "load_time_ms": 0, "screenshot": None, "console_logs": []}
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={'width': viewport_width, 'height': viewport_height})
            
            # Catch console errors
            page.on("pageerror", lambda exc: metrics["console_logs"].append(str(exc)))
            
            start_time = time.time()
            response = await page.goto(url, wait_until="load", timeout=15000)
            metrics["load_time_ms"] = int((time.time() - start_time) * 1000)
            
            if response and response.status < 400:
                metrics["status"] = "Passed"
                # Generate screenshot bytes
                metrics["screenshot"] = await page.screenshot(full_page=False)
            else:
                metrics["status"] = f"Failed (HTTP {response.status if response else 'No Response'})"
                
            await browser.close()
    except Exception as e:
        metrics["status"] = f"Error: {str(e)}"
    return metrics


def check_broken_links(base_url, limit=15):
    """Scrapes the URL and validates internal/external links up to a safe limit."""
    results = []
    try:
        response = requests.get(base_url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a', href=True)][:limit]
        
        for link in links:
            full_url = urljoin(base_url, link)
            # Ensure it's web link
            if not full_url.startswith(('http://', 'https://')):
                continue
            try:
                link_resp = requests.head(full_url, timeout=3, allow_redirects=True)
                status_code = link_resp.status_code
            except requests.RequestException:
                status_code = "Unreachable"
                
            results.append({
                "URL": full_url,
                "Status": "Healthy" if isinstance(status_code, int) and status_code < 400 else "Broken",
                "HTTP Code": status_code
            })
    except Exception as e:
        st.error(f"Link Scraper Encountered an Issue: {e}")
    return pd.DataFrame(results)


def run_security_headers_check(url):
    """Evaluates crucial HTTP security headers for production configurations."""
    checks = {
        "Strict-Transport-Security (HSTS)": {"status": "Missing", "color": "red"},
        "X-Frame-Options (Clickjacking Protection)": {"status": "Missing", "color": "red"},
        "X-Content-Type-Options": {"status": "Missing", "color": "red"},
        "Content-Security-Policy (CSP)": {"status": "Missing", "color": "red"}
    }
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        headers = response.headers
        
        if "Strict-Transport-Security" in headers:
            checks["Strict-Transport-Security (HSTS)"] = {"status": "Configured Secured", "color": "green"}
        if "X-Frame-Options" in headers:
            checks["X-Frame-Options (Clickjacking Protection)"] = {"status": "Configured Secured", "color": "green"}
        if "X-Content-Type-Options" in headers:
            checks["X-Content-Type-Options"] = {"status": "Configured Secured", "color": "green"}
        if "Content-Security-Policy" in headers:
            checks["Content-Security-Policy (CSP)"] = {"status": "Configured Secured", "color": "green"}
    except Exception:
        pass
    return checks

# -----------------------------------------------------------------------------
# 3. STREAMLIT USER INTERFACE & FLOW CONTROL
# -----------------------------------------------------------------------------

st.title("🤖 QA-X Next-Gen Web Automation Engine")
st.caption("Enterprise UI Verification, Security Audits, and Cross-Platform Emulation")
st.hr()

# Sidebar Setup Configurations
st.sidebar.header("🛠️ Test Suite Orchestrator")
target_url = st.sidebar.text_input("Target URL", value="https://example.com")

# Ensure user adds scheme prefix safely
if not target_url.startswith(("http://", "https://")):
    target_url = "https://" + target_url

st.sidebar.subheader("Device Form-Factor Dimensions")
device_mode = st.sidebar.selectbox("Simulated Device Profile", ["Desktop (1440x900)", "Mobile Portrait (375x812)"])

if device_mode == "Desktop (1440x900)":
    width, height = 1440, 900
else:
    width, height = 375, 812

st.sidebar.info("💡 **Startup Architecture Note:** This UI is backed by FastAPI ready engines. To transition to production scale on AWS, deploy the execution models inside Docker containers running via AWS ECS / Fargate.")

# Main Application Tabs Setup
tab1, tab2, tab3, tab4 = st.tabs([
    "🖥️ Auto UI & Visual Verification", 
    "🔗 Link Integrity Scanner", 
    "⚡ Performance Diagnostics", 
    "🛡️ CyberSecurity Validation"
])

# Execute Orchestration Loop
if st.sidebar.button("🚀 Execute Comprehensive Analysis Pipelines", use_container_width=True):
    
    # -------------------------------------------------------------------------
    # TAB 1: Auto UI Testing & Screen Comparisons
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("Auto UI Verification Matrix")
        with st.spinner("Spawning headless execution workers..."):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    ui_metrics = loop.run_until_complete(run_playwright_test(target_url, width, height))
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"""
                <div class='metric-card'>
                    <h4>Automation Engine Profile</h4>
                    <p><b>Target:</b> {target_url}</p>
                    <p><b>Viewport Resolution:</b> {width}x{height}</p>
                    <p><b>Pipeline Assertions:</b> {ui_metrics['status']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if ui_metrics["console_logs"]:
                st.error("⚠️ Client-Side Exceptions detected in Console logs!")
                st.json(ui_metrics["console_logs"])
            else:
                st.success("✅ Zero client-side JavaScript execution exceptions captured.")
                
        with col2:
            st.write("### Captured Rendering Matrix Instance")
            if ui_metrics["screenshot"]:
                st.image(ui_metrics["screenshot"], use_container_width=True, caption=f"Emulated Render Viewport ({device_mode})")
            else:
                st.info("Render generation failed or target timed out.")

    # -------------------------------------------------------------------------
    # TAB 2: Broken Link Checker
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("Recursive Link Analysis Matrix")
        with st.spinner("Scraping root structure for references..."):
            links_df = check_broken_links(target_url)
            
        if not links_df.empty:
            broken_count = len(links_df[links_df["Status"] == "Broken"])
            
            c1, c2 = st.columns(2)
            c1.metric("Total Links Analyzed", len(links_df))
            c2.metric("Broken Links Identified", broken_count, delta=-broken_count, delta_color="inverse")
            
            st.write("#### Comprehensive Trace Log")
            st.dataframe(links_df, use_container_width=True)
        else:
            st.success("No validation paths extracted from the landing structure root.")

    # -------------------------------------------------------------------------
    # TAB 3: Performance Audit Reports
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("Server & Client Transaction Speed Audit")
        
        if ui_metrics["load_time_ms"] > 0:
            load_time = ui_metrics["load_time_ms"]
            st.metric("Time to Document Complete (DOM)", f"{load_time} ms")
            
            # Simple threshold assessment
            if load_time < 1500:
                st.success("🏎️ Exceptional performance score matching Core Web Vitals expectations.")
            elif load_time < 3500:
                st.warning("⚠️ Average latency thresholds. Minor structural asset reduction suggested.")
            else:
                st.error("🚨 Critical Performance Risk. Core TTFB or asset payloads are throttling pipeline thread loops.")
        else:
            st.info("Execute active profiling runs to generate metric telemetry.")

    # -------------------------------------------------------------------------
    # TAB 4: CyberSecurity Evaluation
    # -------------------------------------------------------------------------
    with tab4:
        st.subheader("Secured Headers & Target Perimeter Evaluation")
        with st.spinner("Evaluating HTTP structural configurations..."):
            security_matrix = run_security_headers_check(target_url)
            
        for key, val in security_matrix.items():
            if val["color"] == "green":
                st.success(f"🔒 {key}: **{val['status']}**")
            else:
                st.error(f"❌ {key}: **{val['status']}** — Exposure risks present.")

else:
    # Default State Message prior to execution trigger
    for tab in [tab1, tab2, tab3, tab4]:
        with tab:
            st.info("👈 Supply a URL vector target and press 'Execute Comprehensive Analysis Pipelines' inside the left deck control plane.")
