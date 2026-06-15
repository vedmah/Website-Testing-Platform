import streamlit as st
import asyncio
from playwright.async_api import async_playwright
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from urllib.parse import urlparse, urljoin

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM RESPONSIVE CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="QA-X Streamlit AI Testing Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        :root {
            --primary: #00FFA3;
            --bg-card: #1E222B;
            --text-main: #E2E8F0;
        }
        .main .block-container { padding-top: 2rem; max-width: 100%; }
        .metric-card {
            background-color: #161920;
            border-left: 4px solid #00FFA3;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        @media (max-width: 768px) {
            .stHorizontalBlock { flex-direction: column !important; }
        }
        h1, h2, h3 { color: #FFFFFF !important; font-family: 'Inter', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CORE UTILITY FUNCTIONS
# -----------------------------------------------------------------------------

async def run_playwright_test(url, viewport_width, viewport_height):
    metrics = {"status": "Failed", "load_time_ms": 0, "screenshot": None, "console_logs": []}
    try:
        async with async_playwright() as p:
            # Note: SlowMo helps bypass some basic bot detection
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={'width': viewport_width, 'height': viewport_height})
            page = await context.new_page()
            
            page.on("pageerror", lambda exc: metrics["console_logs"].append(str(exc)))
            
            start_time = time.time()
            response = await page.goto(url, wait_until="load", timeout=20000)
            metrics["load_time_ms"] = int((time.time() - start_time) * 1000)
            
            if response and response.status < 400:
                metrics["status"] = "Passed"
                metrics["screenshot"] = await page.screenshot(full_page=False)
            else:
                metrics["status"] = f"Failed (HTTP {response.status if response else 'No Response'})"
                
            await browser.close()
    except Exception as e:
        metrics["status"] = f"Error: {str(e)}"
    return metrics

def check_broken_links(base_url, limit=10):
    results = []
    try:
        response = requests.get(base_url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a', href=True)][:limit]
        
        for link in links:
            full_url = urljoin(base_url, link)
            if not full_url.startswith(('http://', 'https://')): continue
            try:
                link_resp = requests.head(full_url, timeout=3, allow_redirects=True)
                status = link_resp.status_code
            except:
                status = "Unreachable"
            results.append({
                "URL": full_url,
                "Status": "Healthy" if isinstance(status, int) and status < 400 else "Broken",
                "Code": status
            })
    except Exception as e:
        st.error(f"Link Scraper Error: {e}")
    return pd.DataFrame(results)

def run_security_check(url):
    checks = {
        "HSTS": "Missing", "X-Frame-Options": "Missing", 
        "X-Content-Type": "Missing", "CSP": "Missing"
    }
    try:
        res = requests.head(url, timeout=5, allow_redirects=True)
        h = res.headers
        if "Strict-Transport-Security" in h: checks["HSTS"] = "Secured"
        if "X-Frame-Options" in h: checks["X-Frame-Options"] = "Secured"
        if "X-Content-Type-Options" in h: checks["X-Content-Type"] = "Secured"
        if "Content-Security-Policy" in h: checks["CSP"] = "Secured"
    except: pass
    return checks

# -----------------------------------------------------------------------------
# 3. UI LAYOUT
# -----------------------------------------------------------------------------

st.title("🤖 QA-X Next-Gen Web Automation")
st.sidebar.header("🛠️ Test Suite Orchestrator")
target_url = st.sidebar.text_input("Target URL", value="https://example.com")

if not target_url.startswith(("http://", "https://")):
    target_url = "https://" + target_url

device_mode = st.sidebar.selectbox("Simulated Device Profile", ["Desktop (1440x900)", "Mobile (375x812)"])
width, height = (1440, 900) if "Desktop" in device_mode else (375, 812)

tab1, tab2, tab3, tab4 = st.tabs(["🖥️ UI Verification", "🔗 Links", "⚡ Performance", "🛡️ Security"])

# --- EXECUTION ENGINE ---
if st.sidebar.button("🚀 Run Full Analysis", use_container_width=True):
    
    # 1. Setup Event Loop for Playwright
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    with st.spinner("Executing Automated Test Suite..."):
        # Playwright Run
        ui_metrics = loop.run_until_complete(run_playwright_test(target_url, width, height))
        # Requests Run
        links_df = check_broken_links(target_url)
        sec_results = run_security_check(target_url)

    # --- DISPLAY RESULTS ---
    with tab1:
        st.subheader("Auto UI Verification")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"<div class='metric-card'><h4>Engine Profile</h4><p>Status: {ui_metrics['status']}</p><p>Resolution: {width}x{height}</p></div>", unsafe_allow_html=True)
            if ui_metrics["console_logs"]:
                st.error("JS Errors Detected")
                st.json(ui_metrics["console_logs"])
            else:
                st.success("Clean Console Logs")
        with c2:
            if ui_metrics["screenshot"]:
                st.image(ui_metrics["screenshot"], use_container_width=True)

    with tab2:
        st.subheader("Link Integrity")
        st.dataframe(links_df, use_container_width=True)

    with tab3:
        st.subheader("Speed Audit")
        lt = ui_metrics["load_time_ms"]
        st.metric("DOM Load Time", f"{lt} ms")
        if lt < 2000: st.success("Fast Page Load")
        else: st.warning("Slow Response Time")

    with tab4:
        st.subheader("Security Headers")
        for k, v in sec_results.items():
            if v == "Secured": st.success(f"🔒 {k}: {v}")
            else: st.error(f"❌ {k}: {v}")

else:
    for t in [tab1, tab2, tab3, tab4]:
        with t: st.info("Enter a URL and click 'Run Full Analysis' to start.")
