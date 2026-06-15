"""
AI Website Testing Platform
================================
A Streamlit dashboard that performs automated UI testing, broken link
detection, screenshot comparison, performance reporting and security
checks for any public website URL.

Run locally:
    streamlit run app.py

Author: Built as a portfolio / resume project.
"""

import os
import tempfile
import time
from datetime import datetime

import pandas as pd
import streamlit as st
import validators

from modules.broken_links import scan_links
from modules.compare import compare_images
from modules.performance import analyze_performance
from modules.screenshot import capture_screenshot
from modules.security import run_security_scan
from modules.ui_testing import run_ui_tests

# --------------------------------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Website Testing Platform",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------------
# CUSTOM CSS - light theme + responsive tweaks
# --------------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* Overall app background */
        .stApp {
            background-color: #F8FAFC;
        }

        /* Hero / header banner */
        .hero {
            background: linear-gradient(135deg, #E0F2FE 0%, #EFF6FF 50%, #F5F3FF 100%);
            border-radius: 16px;
            padding: 28px 32px;
            margin-bottom: 1.4rem;
            border: 1px solid #E2E8F0;
        }
        .hero h1 {
            color: #1E3A8A;
            font-size: 2.1rem;
            margin-bottom: 0.2rem;
        }
        .hero p {
            color: #475569;
            font-size: 1rem;
            margin: 0;
        }
        .tech-chip {
            display: inline-block;
            background-color: #FFFFFF;
            color: #2563EB;
            border: 1px solid #BFDBFE;
            border-radius: 20px;
            padding: 4px 14px;
            margin: 4px 6px 0 0;
            font-size: 0.8rem;
            font-weight: 600;
        }

        /* Section / card containers */
        .card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }

        /* Status badges */
        .badge {
            display: inline-block;
            padding: 3px 12px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
        }
        .badge-good { background-color: #DCFCE7; color: #166534; }
        .badge-warn { background-color: #FEF9C3; color: #854D0E; }
        .badge-bad  { background-color: #FEE2E2; color: #991B1B; }
        .badge-info { background-color: #DBEAFE; color: #1E40AF; }

        /* Metric tiles */
        .metric-tile {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 14px 16px;
            text-align: center;
        }
        .metric-tile .value {
            font-size: 1.6rem;
            font-weight: 800;
            color: #1E293B;
        }
        .metric-tile .label {
            font-size: 0.8rem;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        /* Section headers */
        .section-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #1E293B;
            margin-bottom: 0.4rem;
        }

        /* Footer */
        .footer-note {
            text-align: center;
            color: #94A3B8;
            font-size: 0.8rem;
            margin-top: 2rem;
        }

        /* ---------------- RESPONSIVE: TABLET & MOBILE ---------------- */
        @media (max-width: 768px) {
            .hero { padding: 18px 18px; }
            .hero h1 { font-size: 1.5rem; }
            .hero p { font-size: 0.9rem; }
            .metric-tile .value { font-size: 1.25rem; }
            .card { padding: 0.9rem 1rem; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------------
# SESSION STATE
# --------------------------------------------------------------------------------
for key, default in {
    "url": "",
    "ui_results": None,
    "link_results": None,
    "perf_results": None,
    "security_results": None,
    "current_shot": None,
    "baseline_shot": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

TEMP_DIR = tempfile.gettempdir()

# --------------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🧪 AI Website Testing Platform</h1>
        <p>Automated UI testing, broken link detection, screenshot comparison,
        performance reporting and security checks — all in one dashboard.</p>
        <div style="margin-top:10px;">
            <span class="tech-chip">Python</span>
            <span class="tech-chip">Selenium</span>
            <span class="tech-chip">Playwright</span>
            <span class="tech-chip">FastAPI</span>
            <span class="tech-chip">Docker</span>
            <span class="tech-chip">AWS</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------------
# SIDEBAR - URL input + global info
# --------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔗 Target Website")
    url_input = st.text_input(
        "Enter Website URL",
        value=st.session_state.url,
        placeholder="https://example.com",
        help="Include the full URL with https://",
    )
    st.session_state.url = url_input.strip()

    st.markdown("---")
    st.markdown("### ⚙️ How it works")
    st.markdown(
        """
        1. Enter a website URL above.
        2. Open any tab on the right.
        3. Click **Run** to execute that test module.
        4. Review results, tables and charts.
        """
    )

    st.markdown("---")
    st.markdown("### 🧱 Tech Stack")
    st.markdown(
        "- **Python** — core logic\n"
        "- **Playwright** — headless browser automation, UI tests & screenshots\n"
        "- **Selenium** — alternate browser automation engine\n"
        "- **FastAPI** — REST API layer (extendable)\n"
        "- **Docker** — containerized deployment\n"
        "- **AWS** — cloud hosting target"
    )

    st.markdown("---")
    st.caption("Built with ❤️ using Streamlit · Resume-ready portfolio project")


def is_valid_url(value: str) -> bool:
    return bool(value) and validators.url(value) is True


def require_url() -> bool:
    """Show a warning and return False if the URL is missing/invalid."""
    if not st.session_state.url:
        st.warning("👈 Please enter a website URL in the sidebar first.")
        return False
    if not is_valid_url(st.session_state.url):
        st.error("⚠️ That doesn't look like a valid URL. Make sure it starts with http:// or https://")
        return False
    return True


def score_badge(score: int) -> str:
    if score >= 80:
        return f'<span class="badge badge-good">{score}/100 · Excellent</span>'
    if score >= 50:
        return f'<span class="badge badge-warn">{score}/100 · Needs Improvement</span>'
    return f'<span class="badge badge-bad">{score}/100 · Poor</span>'


# --------------------------------------------------------------------------------
# TABS
# --------------------------------------------------------------------------------
tab_overview, tab_ui, tab_links, tab_screens, tab_perf, tab_security = st.tabs(
    [
        "🏠 Overview",
        "🖥️ UI Testing",
        "🔗 Broken Links",
        "📸 Screenshot Compare",
        "⚡ Performance",
        "🔒 Security",
    ]
)

# --------------------------------------------------------------------------------
# OVERVIEW TAB
# --------------------------------------------------------------------------------
with tab_overview:
    st.markdown('<div class="section-title">Welcome 👋</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card">
        This platform lets you run a full automated test suite against any
        public website. Enter a URL in the sidebar, then explore each tab:
        <ul>
        <li><b>🖥️ UI Testing</b> — counts key page elements and checks for layout
        overflow on desktop, tablet and mobile viewports using Playwright.</li>
        <li><b>🔗 Broken Links</b> — crawls the page's links, images, scripts and
        stylesheets and flags anything returning an error status.</li>
        <li><b>📸 Screenshot Compare</b> — captures a full-page screenshot and
        compares it against a previously saved baseline using SSIM.</li>
        <li><b>⚡ Performance</b> — measures load time, page size and gives an
        overall performance score.</li>
        <li><b>🔒 Security</b> — checks important HTTP security headers and the
        SSL certificate validity.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.url:
        st.markdown('<div class="section-title">Current Target</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="card">🌐 <b>{st.session_state.url}</b></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Quick Test (all modules)</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    run_all = st.button("🚀 Run Full Test Suite", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if run_all and require_url():
        url = st.session_state.url
        progress = st.progress(0, text="Starting full test suite...")

        progress.progress(10, text="Running performance analysis...")
        st.session_state.perf_results = analyze_performance(url)

        progress.progress(35, text="Scanning for broken links...")
        st.session_state.link_results = scan_links(url)

        progress.progress(60, text="Checking security headers & SSL...")
        st.session_state.security_results = run_security_scan(url)

        progress.progress(80, text="Running automated UI tests (this may take a moment)...")
        st.session_state.ui_results = run_ui_tests(url)

        progress.progress(95, text="Capturing screenshot...")
        shot_path = os.path.join(TEMP_DIR, "current_screenshot.png")
        shot_result = capture_screenshot(url, shot_path, device="Desktop")
        if shot_result.get("success"):
            st.session_state.current_shot = shot_path

        progress.progress(100, text="Done!")
        time.sleep(0.4)
        progress.empty()
        st.success("✅ Full test suite completed! Visit each tab to view detailed results.")

# --------------------------------------------------------------------------------
# UI TESTING TAB
# --------------------------------------------------------------------------------
with tab_ui:
    st.markdown('<div class="section-title">🖥️ Automated UI Testing</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card">Loads the page in a headless Chromium browser '
        "(Playwright) and checks the count of key elements plus whether the "
        "layout overflows horizontally on desktop, tablet and mobile "
        "viewports.</div>",
        unsafe_allow_html=True,
    )

    if st.button("▶️ Run UI Tests", key="run_ui_btn"):
        if require_url():
            with st.spinner("Launching headless browser and analyzing the page..."):
                st.session_state.ui_results = run_ui_tests(st.session_state.url)

    results = st.session_state.ui_results
    if results:
        if results.get("error"):
            st.error(f"UI test failed: {results['error']}")
        else:
            st.markdown(f"**Page Title:** {results.get('title', 'N/A')}")

            st.markdown('<div class="section-title">Element Counts</div>', unsafe_allow_html=True)
            elements = results.get("elements", {})
            cols = st.columns(len(elements)) if elements else []
            for col, (label, count) in zip(cols, elements.items()):
                with col:
                    st.markdown(
                        f"""
                        <div class="metric-tile">
                            <div class="value">{count}</div>
                            <div class="label">{label}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown('<div class="section-title">Responsive Layout Check</div>', unsafe_allow_html=True)
            viewport_rows = []
            for name, info in results.get("viewports", {}).items():
                overflow = info["horizontal_overflow"]
                status = (
                    '<span class="badge badge-bad">Overflow Detected</span>'
                    if overflow
                    else '<span class="badge badge-good">No Overflow</span>'
                )
                viewport_rows.append(
                    {
                        "Viewport": name,
                        "Content Width (px)": info["scroll_width"],
                        "Visible Width (px)": info["client_width"],
                        "Result": status,
                    }
                )
            if viewport_rows:
                vdf = pd.DataFrame(viewport_rows)
                st.markdown(
                    vdf.to_html(escape=False, index=False),
                    unsafe_allow_html=True,
                )
    else:
        st.info("Click **Run UI Tests** to analyze the page structure and responsiveness.")

# --------------------------------------------------------------------------------
# BROKEN LINKS TAB
# --------------------------------------------------------------------------------
with tab_links:
    st.markdown('<div class="section-title">🔗 Broken Link Detection</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card">Scans the page for links, images, scripts and '
        "stylesheets, then checks each one's HTTP response to flag broken or "
        "unreachable resources.</div>",
        unsafe_allow_html=True,
    )

    max_links = st.slider("Maximum resources to check", 10, 100, 40, step=10)

    if st.button("▶️ Scan for Broken Links", key="run_links_btn"):
        if require_url():
            with st.spinner("Crawling page and checking links... this can take a little while."):
                st.session_state.link_results = scan_links(st.session_state.url, max_links=max_links)

    results = st.session_state.link_results
    if results:
        if results.get("error"):
            st.error(f"Could not fetch page: {results['error']}")
        else:
            summary = results["summary"]
            c1, c2, c3, c4 = st.columns(4)
            for col, (label, value) in zip(
                [c1, c2, c3, c4],
                [
                    ("Total Checked", summary["total"]),
                    ("Working", summary["ok"]),
                    ("Broken (4xx/5xx)", summary["broken"]),
                    ("No Response", summary["failed"]),
                ],
            ):
                with col:
                    st.markdown(
                        f"""
                        <div class="metric-tile">
                            <div class="value">{value}</div>
                            <div class="label">{label}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown('<div class="section-title">Link Details</div>', unsafe_allow_html=True)
            df = results["links"]
            if df.empty:
                st.info("No links were found on this page.")
            else:
                def highlight_result(val):
                    if val == "Broken":
                        return "background-color: #FEE2E2; color: #991B1B; font-weight:600;"
                    if val == "Failed / No Response":
                        return "background-color: #FEF9C3; color: #854D0E; font-weight:600;"
                    return "background-color: #DCFCE7; color: #166534; font-weight:600;"

                styled = df.style.applymap(highlight_result, subset=["Result"])
                st.dataframe(styled, use_container_width=True, height=420)

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download Report as CSV",
                    data=csv,
                    file_name="broken_links_report.csv",
                    mime="text/csv",
                )
    else:
        st.info("Click **Scan for Broken Links** to start the crawl.")

# --------------------------------------------------------------------------------
# SCREENSHOT COMPARISON TAB
# --------------------------------------------------------------------------------
with tab_screens:
    st.markdown('<div class="section-title">📸 Screenshot Comparison</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card">Capture a full-page screenshot of the live site, '
        "then compare it against a previous baseline image (e.g. before vs. "
        "after a deployment) using a structural similarity score (SSIM).</div>",
        unsafe_allow_html=True,
    )

    device_choice = st.radio("Capture device", ["Desktop", "Mobile"], horizontal=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Step 1 — Capture current screenshot**")
        if st.button("📷 Capture Screenshot", key="capture_btn"):
            if require_url():
                with st.spinner("Opening headless browser and capturing screenshot..."):
                    shot_path = os.path.join(TEMP_DIR, "current_screenshot.png")
                    res = capture_screenshot(st.session_state.url, shot_path, device=device_choice)
                    if res.get("success"):
                        st.session_state.current_shot = shot_path
                        st.success("Screenshot captured!")
                    else:
                        st.error(f"Failed to capture screenshot: {res.get('error')}")

        if st.session_state.current_shot and os.path.exists(st.session_state.current_shot):
            st.image(st.session_state.current_shot, caption="Current Screenshot", use_container_width=True)
            with open(st.session_state.current_shot, "rb") as f:
                st.download_button(
                    "⬇️ Save as baseline (download)",
                    data=f,
                    file_name="baseline_screenshot.png",
                    mime="image/png",
                )

    with col_b:
        st.markdown("**Step 2 — Upload a baseline image to compare**")
        baseline_file = st.file_uploader(
            "Upload a previous screenshot (.png/.jpg)", type=["png", "jpg", "jpeg"]
        )
        if baseline_file is not None:
            st.image(baseline_file, caption="Baseline Screenshot", use_container_width=True)

    st.markdown('<div class="section-title">Step 3 — Compare</div>', unsafe_allow_html=True)
    if st.button("🔍 Compare Screenshots", key="compare_btn"):
        if not st.session_state.current_shot or not os.path.exists(st.session_state.current_shot):
            st.warning("Please capture a current screenshot first.")
        elif baseline_file is None:
            st.warning("Please upload a baseline screenshot to compare against.")
        else:
            with st.spinner("Comparing images with SSIM..."):
                comparison = compare_images(baseline_file, st.session_state.current_shot)

            score = comparison["score"]
            if score >= 98:
                badge = '<span class="badge badge-good">Identical / No Visual Change</span>'
            elif score >= 90:
                badge = '<span class="badge badge-warn">Minor Differences Detected</span>'
            else:
                badge = '<span class="badge badge-bad">Significant Differences Detected</span>'

            st.markdown(
                f"### Similarity Score: {score}% &nbsp; {badge}",
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                st.image(comparison["img1"], caption="Baseline", use_container_width=True)
            with c2:
                st.image(comparison["img2"], caption="Current", use_container_width=True)
            with c3:
                st.image(comparison["diff_image"], caption="Difference Map", use_container_width=True)

# --------------------------------------------------------------------------------
# PERFORMANCE TAB
# --------------------------------------------------------------------------------
with tab_perf:
    st.markdown('<div class="section-title">⚡ Performance Report</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card">Measures server response time and total page '
        "size for the requested URL, then converts those metrics into an "
        "easy-to-read overall score.</div>",
        unsafe_allow_html=True,
    )

    if st.button("▶️ Run Performance Test", key="run_perf_btn"):
        if require_url():
            with st.spinner("Measuring load time and page size..."):
                st.session_state.perf_results = analyze_performance(st.session_state.url)

    perf = st.session_state.perf_results
    if perf:
        if perf.get("error"):
            st.error(f"Performance test failed: {perf['error']}")
        else:
            st.markdown(
                f"### Overall Score: {score_badge(perf['overall_score'])}",
                unsafe_allow_html=True,
            )

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(
                    f"""<div class="metric-tile"><div class="value">{perf['load_time_ms']} ms</div>
                    <div class="label">Load Time</div></div>""",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f"""<div class="metric-tile"><div class="value">{perf['page_size_kb']} KB</div>
                    <div class="label">Page Size</div></div>""",
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    f"""<div class="metric-tile"><div class="value">{perf['redirects']}</div>
                    <div class="label">Redirects</div></div>""",
                    unsafe_allow_html=True,
                )
            with c4:
                st.markdown(
                    f"""<div class="metric-tile"><div class="value">{perf['status_code']}</div>
                    <div class="label">HTTP Status</div></div>""",
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="section-title">Details</div>', unsafe_allow_html=True)
            details_df = pd.DataFrame(
                {
                    "Metric": [
                        "Speed Grade",
                        "Size Grade",
                        "Server",
                        "Content Type",
                        "Content Encoding",
                        "Final URL (after redirects)",
                    ],
                    "Value": [
                        perf["speed_grade"],
                        perf["size_grade"],
                        perf["server"],
                        perf["content_type"],
                        perf["encoding"],
                        perf["final_url"],
                    ],
                }
            )
            st.table(details_df)
    else:
        st.info("Click **Run Performance Test** to measure load time and page size.")

# --------------------------------------------------------------------------------
# SECURITY TAB
# --------------------------------------------------------------------------------
with tab_security:
    st.markdown('<div class="section-title">🔒 Security Checks</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card">Checks for the presence of important HTTP '
        "security headers and validates the site's SSL certificate, then "
        "produces an overall security score.</div>",
        unsafe_allow_html=True,
    )

    if st.button("▶️ Run Security Scan", key="run_security_btn"):
        if require_url():
            with st.spinner("Checking security headers and SSL certificate..."):
                st.session_state.security_results = run_security_scan(st.session_state.url)

    sec = st.session_state.security_results
    if sec:
        if sec.get("error"):
            st.error(f"Security scan failed: {sec['error']}")
        else:
            st.markdown(
                f"### Overall Security Score: {score_badge(sec['score'])}",
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                https_badge = (
                    '<span class="badge badge-good">HTTPS Enabled</span>'
                    if sec["https"]
                    else '<span class="badge badge-bad">HTTPS Not Used</span>'
                )
                st.markdown(f"**Connection:** {https_badge}", unsafe_allow_html=True)
            with c2:
                st.markdown(
                    f"**Security Headers Present:** {sec['passed_headers']}/{sec['total_headers']}"
                )
            with c3:
                ssl_info = sec["ssl"]
                if ssl_info.get("valid"):
                    st.markdown(
                        f"**SSL Certificate:** ✅ Valid (expires {ssl_info['expires']}, "
                        f"{ssl_info['days_left']} days left)"
                    )
                else:
                    st.markdown(f"**SSL Certificate:** ❌ {ssl_info.get('error', 'Invalid')}")

            st.markdown('<div class="section-title">Security Headers</div>', unsafe_allow_html=True)
            headers_df = pd.DataFrame(sec["headers"])

            def highlight_status(val):
                if val == "Present":
                    return "background-color: #DCFCE7; color: #166534; font-weight:600;"
                return "background-color: #FEE2E2; color: #991B1B; font-weight:600;"

            styled_headers = headers_df.style.applymap(highlight_status, subset=["Status"])
            st.dataframe(styled_headers, use_container_width=True, height=300)
    else:
        st.info("Click **Run Security Scan** to check headers and SSL configuration.")

# --------------------------------------------------------------------------------
# FOOTER
# --------------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="footer-note">
        AI Website Testing Platform · Built with Streamlit, Playwright & Selenium ·
        Last run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """,
    unsafe_allow_html=True,
)
