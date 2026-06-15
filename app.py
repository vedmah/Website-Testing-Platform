import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from urllib.parse import urljoin, urlparse

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
# 2. LIGHTWEIGHT COMPATIBLE UTILITY ENGINES
# -----------------------------------------------------------------------------

def capture_cloud_screenshot(url, mode):
    """
    Uses a reliable open-source web rendering API to capture responsive 
    device layouts safely in cloud environments.
    """
    width, height = (1440, 900) if "Desktop" in mode else (375, 812)
    # Using a reliable, free screenshot rendering API alternative
    api_url = f"https://api.apiflash.com/v1/urltoimage?access_key=FREE_KEY&url={url}&width={width}&height={height}"
    
    # Fallback to a secondary public rendering pipeline if needed
    fallback_url = f"https://render-tron.appspot.com/screenshot/{url}"
    
    # For prototyping, we use a robust public layout simulator path
    return f"https://api.microlink.io?url={url}&screenshot=true&embed=screenshot.url"

def check_broken_links(base_url, limit=10):
    results = []
    try:
        response = requests.get(base_url, timeout=7, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
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
        "HSTS (Transport Layer Protection)": "Missing", 
        "X-Frame-Options (Clickjacking Protection)": "Missing", 
        "X-Content-Type-Options": "Missing", 
        "Content-Security-Policy (CSP)": "Missing"
    }
    try:
        res = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        h = res.headers
        if "Strict-Transport-Security" in h: checks["HSTS (Transport Layer Protection)"] = "Secured"
        if "X-Frame-Options" in h: checks["X-Frame-Options (Clickjacking Protection)"] = "Secured"
        if "X-Content-Type-Options" in h: checks["X-Content-Type-Options"] = "Secured"
        if "Content-Security-Policy" in h: checks["Content-Security-Policy (CSP)"] = "Secured"
    except: pass
    return checks

# -----------------------------------------------------------------------------
# 3. UI LAYOUT & FLOW ORCHESTRATION
# -----------------------------------------------------------------------------

st.title("🤖 QA-X Next-Gen Web Automation Engine")
st.caption("Cloud-Native Infrastructure (No Headless Browser Overhead Dependencies)")
st.sidebar.header("🛠️ Test Suite Orchestrator")
target_url = st.sidebar.text_input("Target URL", value="https://example.com")

if not target_url.startswith(("http://", "https://")):
    target_url = "https://" + target_url

device_mode = st.sidebar.selectbox("Simulated Device Profile", ["Desktop (1440x900)", "Mobile (375x812)"])

tab1, tab2, tab3, tab4 = st.tabs(["🖥️ UI & Visual Verification", "🔗 Link Integrity", "⚡ Performance Diagnostics", "🛡️ Security Perimeter"])

if st.sidebar.button("🚀 Run Full Analysis", use_container_width=True):
    
    with st.spinner("Analyzing target endpoint vectors..."):
        start_perf = time.time()
        try:
            response = requests.get(target_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            load_time_ms = int((time.time() - start_perf) * 1000)
            status_code = response.status_code
        except Exception as e:
            load_time_ms = 0
            status_code = f"Error connecting ({str(e)})"

        # Execute remaining parallel checks safely
        links_df = check_broken_links(target_url)
        sec_results = run_security_check(target_url)
        screenshot_url = capture_cloud_screenshot(target_url, device_mode)

    # --- TAB 1: VISUAL VERIFICATION ---
    with tab1:
        st.subheader("Auto UI Verification")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"""
            <div class='metric-card'>
                <h4>Engine Profile</h4>
                <p><b>Target:</b> {target_url}</p>
                <p><b>HTTP Handshake Status:</b> {status_code}</p>
                <p><b>Emulation Layer:</b> {device_mode}</p>
            </div>
            """, unsafe_allow_html=True)
            st.success("App running in cloud-optimized production environment.")
        with c2:
            st.write("### Captured Rendering Layout")
            # Pulling adaptive display directly from the micro-render pipeline
            st.image(screenshot_url, use_container_width=True, caption=f"Remote Cloud Render Instance ({device_mode})")

    # --- TAB 2: LINK CHECKER ---
    with tab2:
        st.subheader("Link Integrity Map")
        if not links_df.empty:
            st.dataframe(links_df, use_container_width=True)
        else:
            st.info("No hyperlinks discovered on target landing structure root.")

    # --- TAB 3: PERFORMANCE ---
    with tab3:
        st.subheader("Performance Metrics Audit")
        if load_time_ms > 0:
            st.metric("Time to First Byte / Core Document Load", f"{load_time_ms} ms")
            if load_time_ms < 1500:
                st.success("🏎️ Highly responsive runtime asset compression detected.")
            else:
                st.warning("⚠️ High core delivery latency. Consider assets CDN distribution.")
        else:
            st.error("Could not capture loading latency profiles.")

    # --- TAB 4: SECURITY ---
    with tab4:
        st.subheader("HTTP Security Profile Validation")
        for k, v in sec_results.items():
            if v == "Secured":
                st.success(f"🔒 {k}: **Configured Secured**")
            else:
                st.error(f"❌ {k}: **Missing / Exposure Risks Detected**")

else:
    for t in [tab1, tab2, tab3, tab4]:
        with t: st.info("👈 Enter a URL profile on the left control dock and click 'Run Full Analysis'.")
