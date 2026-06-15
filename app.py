"""
WebSentinel — AI Website Testing Platform
Streamlit frontend with cyber-dark theme
"""

import base64
import json
import time
import re
from datetime import datetime
from io import StringIO
import streamlit as st
from tester import run_full_test, TestReport, LinkResult

# ── Page Config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="WebSentinel — AI Website Testing",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
    background: #0A0E1A !important;
    color: #E2E8F0;
    font-family: 'Inter', sans-serif;
}
[data-testid="stAppViewContainer"] > .main { background: #0A0E1A !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: #0D1221 !important; }

/* ── Hero ── */
.hero-wrap {
    text-align: center;
    padding: 3rem 1rem 2rem;
}
.hero-badge {
    display: inline-block;
    background: rgba(0,212,255,0.08);
    border: 1px solid rgba(0,212,255,0.25);
    color: #00D4FF;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 0.3rem 1rem;
    border-radius: 2rem;
    margin-bottom: 1.2rem;
}
.hero-title {
    font-size: clamp(2.2rem, 5vw, 3.8rem);
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin: 0 0 0.6rem;
    background: linear-gradient(135deg, #FFFFFF 0%, #00D4FF 50%, #7B5EA7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    color: #64748B;
    font-size: 1.05rem;
    font-weight: 300;
    max-width: 520px;
    margin: 0 auto;
}

/* ── URL Input Box ── */
.url-container {
    max-width: 720px;
    margin: 2.5rem auto 0;
    position: relative;
}
.scan-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #00D4FF;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
[data-testid="stTextInput"] > div > div > input {
    background: #0D1221 !important;
    border: 1.5px solid rgba(0,212,255,0.35) !important;
    border-radius: 10px !important;
    color: #E2E8F0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.95rem !important;
    padding: 0.85rem 1.2rem !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
[data-testid="stTextInput"] > div > div > input:focus {
    border-color: #00D4FF !important;
    box-shadow: 0 0 0 3px rgba(0,212,255,0.12) !important;
    outline: none !important;
}

/* ── Buttons ── */
[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #00D4FF 0%, #0088CC 100%) !important;
    color: #0A0E1A !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.04em !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 2rem !important;
    transition: opacity 0.15s, transform 0.12s !important;
    width: 100%;
}
[data-testid="stButton"] > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}

/* ── Score Ring ── */
.score-ring-wrap {
    text-align: center;
    padding: 1.5rem;
}
.score-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 4rem;
    font-weight: 700;
    line-height: 1;
}
.score-label {
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #64748B;
    margin-top: 0.3rem;
}

/* ── Metric Cards ── */
.metric-card {
    background: #0D1221;
    border: 1px solid #1E2A42;
    border-radius: 12px;
    padding: 1.25rem 1.4rem;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00D4FF, transparent);
}
.metric-card-label {
    font-size: 0.7rem;
    color: #64748B;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 0.4rem;
}
.metric-card-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #E2E8F0;
    line-height: 1;
}
.metric-card-unit {
    font-size: 0.8rem;
    color: #64748B;
    margin-left: 0.25rem;
}
.metric-card-sub {
    font-size: 0.72rem;
    color: #475569;
    margin-top: 0.35rem;
}

/* ── Section Headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    margin: 2rem 0 1rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid #1E2A42;
}
.section-header-icon {
    font-size: 1.2rem;
}
.section-header-text {
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: -0.01em;
}
.section-header-count {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #00D4FF;
    background: rgba(0,212,255,0.08);
    border: 1px solid rgba(0,212,255,0.2);
    padding: 0.15rem 0.5rem;
    border-radius: 1rem;
    margin-left: auto;
}

/* ── Check Rows ── */
.check-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.7rem 0;
    border-bottom: 1px solid rgba(30,42,66,0.6);
}
.check-row:last-child { border-bottom: none; }
.check-icon { font-size: 1rem; flex-shrink: 0; margin-top: 0.05rem; }
.check-name {
    font-weight: 500;
    font-size: 0.88rem;
    color: #CBD5E1;
}
.check-detail {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #64748B;
    margin-top: 0.15rem;
    word-break: break-word;
}
.check-reco {
    font-size: 0.72rem;
    color: #F59E0B;
    margin-top: 0.15rem;
    font-style: italic;
}
.check-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    flex-shrink: 0;
    margin-left: auto;
    align-self: flex-start;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-critical { background: rgba(239,68,68,0.15); color: #F87171; border: 1px solid rgba(239,68,68,0.25); }
.badge-high     { background: rgba(249,115,22,0.15); color: #FB923C; border: 1px solid rgba(249,115,22,0.25); }
.badge-medium   { background: rgba(234,179,8,0.15);  color: #FDE047; border: 1px solid rgba(234,179,8,0.25); }
.badge-low      { background: rgba(100,116,139,0.15);color: #94A3B8; border: 1px solid rgba(100,116,139,0.25); }
.badge-info     { background: rgba(59,130,246,0.12); color: #60A5FA; border: 1px solid rgba(59,130,246,0.2); }
.badge-seo      { background: rgba(139,92,246,0.12); color: #A78BFA; border: 1px solid rgba(139,92,246,0.2); }
.badge-accessibility { background: rgba(16,185,129,0.12); color: #34D399; border: 1px solid rgba(16,185,129,0.2); }
.badge-best-practices { background: rgba(59,130,246,0.12); color: #60A5FA; border: 1px solid rgba(59,130,246,0.2); }

/* ── Link rows ── */
.link-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid rgba(30,42,66,0.5);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
}
.link-row:last-child { border-bottom: none; }
.link-status {
    font-weight: 700;
    min-width: 2.8rem;
    text-align: center;
    padding: 0.1rem 0.3rem;
    border-radius: 4px;
    font-size: 0.7rem;
}
.link-status-ok    { color: #00FF88; background: rgba(0,255,136,0.08); }
.link-status-error { color: #F87171; background: rgba(239,68,68,0.1); }
.link-url { color: #94A3B8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 55%; }
.link-anchor { color: #64748B; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 22%; }
.link-time { color: #475569; margin-left: auto; min-width: 4rem; text-align: right; }

/* ── Progress Bar ── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #00D4FF, #7B5EA7) !important;
    border-radius: 4px !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] button {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    color: #64748B !important;
    border-radius: 6px 6px 0 0 !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #00D4FF !important;
    border-bottom: 2px solid #00D4FF !important;
    background: transparent !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: #0D1221 !important;
    border: 1px solid #1E2A42 !important;
    border-radius: 10px !important;
}

/* ── Screenshot box ── */
.screenshot-frame {
    border: 1.5px solid #1E2A42;
    border-radius: 12px;
    overflow: hidden;
    background: #0D1221;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.browser-bar {
    background: #161B2E;
    padding: 0.5rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Divider ── */
hr { border-color: #1E2A42 !important; }

/* ── Footer ── */
.footer {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
    color: #334155;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #00D4FF !important; }

/* ── Info/Warning/Error boxes ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def score_color(score: int) -> str:
    if score >= 80: return "#00FF88"
    if score >= 60: return "#FFB800"
    if score >= 40: return "#FB923C"
    return "#F87171"

def grade_color(grade: str) -> str:
    return {"A+": "#00FF88","A": "#00FF88","B": "#A3E635","C": "#FFB800",
            "D": "#FB923C","F": "#F87171"}.get(grade, "#94A3B8")

def fmt_bytes(n: int) -> str:
    if n >= 1_000_000: return f"{n/1_000_000:.1f} MB"
    if n >= 1_000:     return f"{n/1_000:.0f} KB"
    return f"{n} B"

def validate_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

def render_score_ring(score: int):
    color = score_color(score)
    pct = score / 100
    # SVG ring
    r = 54; cx = 70; cy = 70; stroke = 10
    circ = 2 * 3.14159 * r
    dash = circ * pct
    svg = f"""
    <svg width="140" height="140" viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg">
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1E2A42" stroke-width="{stroke}"/>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke}"
              stroke-dasharray="{dash:.1f} {circ:.1f}" stroke-dashoffset="{circ/4:.1f}"
              stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>
      <text x="{cx}" y="{cy+6}" text-anchor="middle"
            font-family="JetBrains Mono, monospace" font-size="28" font-weight="700"
            fill="{color}">{score}</text>
      <text x="{cx}" y="{cy+24}" text-anchor="middle"
            font-family="Inter, sans-serif" font-size="10" fill="#64748B" letter-spacing="1">SCORE</text>
    </svg>"""
    st.markdown(svg, unsafe_allow_html=True)

def render_check_row(icon, name, detail, badge_text, badge_class, reco=""):
    reco_html = f'<div class="check-reco">→ {reco}</div>' if reco else ""
    st.markdown(f"""
    <div class="check-row">
      <div class="check-icon">{icon}</div>
      <div style="flex:1;min-width:0;">
        <div class="check-name">{name}</div>
        <div class="check-detail">{detail}</div>
        {reco_html}
      </div>
      <span class="check-badge {badge_class}">{badge_text}</span>
    </div>""", unsafe_allow_html=True)

def render_metric_card(label, value, unit="", sub="", accent="#00D4FF"):
    st.markdown(f"""
    <div class="metric-card" style="border-top-color:{accent}">
      <div class="metric-card-label">{label}</div>
      <div class="metric-card-value">{value}<span class="metric-card-unit">{unit}</span></div>
      <div class="metric-card-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

# ── UI Sections ───────────────────────────────────────────────────────────────

def render_hero():
    st.markdown("""
    <div class="hero-wrap">
      <div class="hero-badge">⚡ AI-Powered · Real-Time · Free</div>
      <h1 class="hero-title">WebSentinel</h1>
      <p class="hero-sub">Full-stack website testing — security, performance, accessibility &amp; broken links in one scan.</p>
    </div>
    """, unsafe_allow_html=True)

def render_performance_tab(perf):
    if not perf:
        st.info("No performance data.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        color = "#00FF88" if perf.ttfb_ms < 400 else "#FFB800" if perf.ttfb_ms < 800 else "#F87171"
        render_metric_card("Time to First Byte", f"{perf.ttfb_ms:.0f}", "ms",
                           "< 400ms = fast", color)
    with c2:
        color = "#00FF88" if perf.total_load_ms < 1500 else "#FFB800" if perf.total_load_ms < 3000 else "#F87171"
        render_metric_card("Total Load Time", f"{perf.total_load_ms:.0f}", "ms",
                           "< 1.5s = fast", color)
    with c3:
        color = "#00FF88" if perf.page_size_bytes < 1_000_000 else "#FFB800"
        render_metric_card("Page Size", fmt_bytes(perf.page_size_bytes), "",
                           "< 1 MB recommended", color)
    with c4:
        color = "#00FF88" if perf.num_requests < 40 else "#FFB800" if perf.num_requests < 80 else "#F87171"
        render_metric_card("Resource Requests", str(perf.num_requests), "",
                           "< 40 = lean", color)

    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, c7 = st.columns([1, 1, 2])
    with c5:
        render_metric_card("DNS Lookup", f"{perf.dns_lookup_ms:.0f}", "ms", "", "#7B5EA7")
    with c6:
        render_metric_card("TCP Connect", f"{perf.tcp_connect_ms:.0f}", "ms", "", "#7B5EA7")
    with c7:
        grade_c = grade_color(perf.grade)
        st.markdown(f"""
        <div class="metric-card" style="border-top-color:{grade_c}">
          <div class="metric-card-label">Performance Grade</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:3rem;font-weight:700;color:{grade_c};line-height:1;">{perf.grade}</div>
          <div class="metric-card-sub">Score: {perf.performance_score}/100</div>
        </div>""", unsafe_allow_html=True)

def render_security_tab(checks):
    if not checks:
        st.info("No security data.")
        return

    passed = sum(1 for c in checks if c.passed)
    total  = len(checks)
    st.markdown(f"""
    <div style="margin-bottom:1rem;padding:1rem 1.2rem;background:#0D1221;border:1px solid #1E2A42;border-radius:10px;display:flex;align-items:center;gap:1rem;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:1.8rem;font-weight:700;color:{'#00FF88' if passed/total>=0.8 else '#FFB800' if passed/total>=0.5 else '#F87171'};">{passed}/{total}</div>
      <div>
        <div style="font-weight:600;font-size:0.9rem;">Security Checks Passed</div>
        <div style="color:#64748B;font-size:0.75rem;">{'Excellent security posture' if passed/total>=0.8 else 'Some issues need attention' if passed/total>=0.5 else 'Critical issues found'}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_checks = sorted(checks, key=lambda c: (c.passed, sev_order.get(c.severity, 5)))

    for c in sorted_checks:
        icon = "✅" if c.passed else ("🚨" if c.severity == "critical" else
                                      "⚠️" if c.severity == "high" else
                                      "⚡" if c.severity == "medium" else "ℹ️")
        badge_class = f"badge-{c.severity}"
        render_check_row(icon, c.name, c.detail, c.severity.upper(), badge_class,
                         c.recommendation if not c.passed else "")

def render_ui_tab(checks):
    if not checks:
        st.info("No UI data.")
        return

    categories = {"seo": "🔎 SEO", "accessibility": "♿ Accessibility", "best-practices": "✨ Best Practices"}
    for cat_key, cat_label in categories.items():
        cat_checks = [c for c in checks if c.category == cat_key]
        if not cat_checks:
            continue
        passed = sum(1 for c in cat_checks if c.passed)
        st.markdown(f"""
        <div class="section-header">
          <span class="section-header-text">{cat_label}</span>
          <span class="section-header-count">{passed}/{len(cat_checks)} passed</span>
        </div>""", unsafe_allow_html=True)

        for c in cat_checks:
            icon = "✅" if c.passed else "❌"
            render_check_row(icon, c.name, c.detail, cat_key.upper(),
                             f"badge-{cat_key}", "" if c.passed else "Review & fix this issue")

def render_links_tab(all_links, broken_links):
    broken = [l for l in all_links if l.is_broken]
    healthy = [l for l in all_links if not l.is_broken]

    # Stats row
    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card("Total Links", str(len(all_links)), "", "", "#00D4FF")
    with c2:
        color = "#00FF88" if len(broken) == 0 else "#F87171"
        render_metric_card("Broken Links", str(len(broken)), "", "", color)
    with c3:
        health_pct = int((len(healthy)/len(all_links))*100) if all_links else 100
        color = "#00FF88" if health_pct >= 95 else "#FFB800" if health_pct >= 80 else "#F87171"
        render_metric_card("Link Health", f"{health_pct}", "%", "", color)

    st.markdown("<br>", unsafe_allow_html=True)

    if broken:
        st.markdown("""<div class="section-header">
          <span class="section-header-icon">🔴</span>
          <span class="section-header-text">Broken Links</span>
        </div>""", unsafe_allow_html=True)
        for l in broken[:50]:
            status_cls = "link-status-error"
            status_text = l.error or str(l.status_code) or "ERR"
            anchor = l.anchor_text or "—"
            st.markdown(f"""
            <div class="link-row">
              <span class="link-status {status_cls}">{status_text[:10]}</span>
              <span class="link-url" title="{l.url}">{l.url}</span>
              <span class="link-anchor" title="{anchor}">{anchor[:35]}</span>
              <span class="link-time">{l.response_time_ms:.0f}ms</span>
            </div>""", unsafe_allow_html=True)

    with st.expander(f"✅ Healthy Links ({len(healthy)})", expanded=False):
        for l in healthy[:100]:
            anchor = l.anchor_text or "—"
            t_color = "#00FF88" if l.response_time_ms < 500 else "#FFB800" if l.response_time_ms < 1500 else "#F87171"
            st.markdown(f"""
            <div class="link-row">
              <span class="link-status link-status-ok">{l.status_code}</span>
              <span class="link-url" title="{l.url}">{l.url}</span>
              <span class="link-anchor" title="{anchor}">{anchor[:35]}</span>
              <span class="link-time" style="color:{t_color}">{l.response_time_ms:.0f}ms</span>
            </div>""", unsafe_allow_html=True)

def render_screenshot_tab(b64: str, page_title: str, url: str):
    if not b64:
        st.info("No screenshot available.")
        return

    img_data = base64.b64decode(b64)
    is_svg = img_data[:4] == b"<svg" or b"<svg" in img_data[:10]

    st.markdown(f"""
    <div class="screenshot-frame">
      <div class="browser-bar">
        <span style="font-size:0.7rem;color:#475569;font-family:'JetBrains Mono',monospace;">● ● ●</span>
        <span style="flex:1;background:#0A0E1A;border-radius:6px;padding:0.3rem 0.8rem;margin:0 0.5rem;font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#64748B;">{url[:80]}</span>
      </div>
    </div>""", unsafe_allow_html=True)

    if is_svg:
        st.image(f"data:image/svg+xml;base64,{b64}", use_container_width=True)
    else:
        st.image(f"data:image/png;base64,{b64}", use_container_width=True)

    st.info("💡 **Production tip:** Install Playwright (`pip install playwright && playwright install chromium`) "
            "and replace `capture_screenshot_placeholder()` in `tester.py` with real browser rendering.")

def render_report_summary(report: TestReport):
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""<div class="section-header" style="margin-top:0.5rem;">
      <span class="section-header-text" style="font-size:1.2rem;">📊 Test Results</span>
    </div>""", unsafe_allow_html=True)

    # Top row: score + key stats
    col_score, col_meta = st.columns([1, 3])
    with col_score:
        render_score_ring(report.summary_score)
        color = score_color(report.summary_score)
        label = ("Excellent" if report.summary_score >= 80 else
                 "Good" if report.summary_score >= 65 else
                 "Needs Work" if report.summary_score >= 45 else "Poor")
        st.markdown(f"""<div style="text-align:center;margin-top:0.3rem;">
          <span style="color:{color};font-weight:600;font-size:0.9rem;">{label}</span><br>
          <span style="color:#475569;font-size:0.72rem;font-family:'JetBrains Mono',monospace;">{report.timestamp}</span>
        </div>""", unsafe_allow_html=True)

    with col_meta:
        st.markdown(f"""
        <div style="padding-top:0.5rem;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:#64748B;margin-bottom:0.3rem;">TARGET URL</div>
          <div style="font-family:'JetBrains Mono',monospace;color:#00D4FF;font-size:0.9rem;word-break:break-all;margin-bottom:1rem;">{report.url}</div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            status_c = "#00FF88" if report.status_code < 400 else "#F87171"
            st.markdown(f"""<div style="text-align:center;">
              <div style="font-size:1.5rem;font-weight:700;color:{status_c};font-family:'JetBrains Mono',monospace;">{report.status_code}</div>
              <div style="font-size:0.68rem;color:#64748B;text-transform:uppercase;">HTTP Status</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            p = report.performance
            val = f"{p.ttfb_ms:.0f}ms" if p else "—"
            st.markdown(f"""<div style="text-align:center;">
              <div style="font-size:1.5rem;font-weight:700;color:#E2E8F0;font-family:'JetBrains Mono',monospace;">{val}</div>
              <div style="font-size:0.68rem;color:#64748B;text-transform:uppercase;">TTFB</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            bl = len(report.broken_links)
            bl_c = "#00FF88" if bl == 0 else "#F87171"
            st.markdown(f"""<div style="text-align:center;">
              <div style="font-size:1.5rem;font-weight:700;color:{bl_c};font-family:'JetBrains Mono',monospace;">{bl}</div>
              <div style="font-size:0.68rem;color:#64748B;text-transform:uppercase;">Broken Links</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            sec_pass = sum(1 for c in report.security_checks if c.passed)
            sec_total = len(report.security_checks)
            st.markdown(f"""<div style="text-align:center;">
              <div style="font-size:1.5rem;font-weight:700;color:#E2E8F0;font-family:'JetBrains Mono',monospace;">{sec_pass}/{sec_total}</div>
              <div style="font-size:0.68rem;color:#64748B;text-transform:uppercase;">Security</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚡ Performance", "🔒 Security", "🎨 UI / SEO",
        "🔗 Links", "📸 Screenshot"
    ])
    with tab1: render_performance_tab(report.performance)
    with tab2: render_security_tab(report.security_checks)
    with tab3: render_ui_tab(report.ui_checks)
    with tab4: render_links_tab(report.all_links, report.broken_links)
    with tab5: render_screenshot_tab(report.screenshot_b64, report.page_title, report.url)

    # Export
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📥 Export Report (JSON)", expanded=False):
        def _serialisable(obj):
            from dataclasses import asdict
            import dataclasses
            if dataclasses.is_dataclass(obj):
                return asdict(obj)
            return str(obj)
        export = {
            "url": report.url,
            "timestamp": report.timestamp,
            "summary_score": report.summary_score,
            "status_code": report.status_code,
            "page_title": report.page_title,
            "performance": _serialisable(report.performance) if report.performance else {},
            "security": [_serialisable(c) for c in report.security_checks],
            "ui": [_serialisable(c) for c in report.ui_checks],
            "links": {
                "total": len(report.all_links),
                "broken": len(report.broken_links),
                "broken_list": [_serialisable(l) for l in report.broken_links],
            },
        }
        json_str = json.dumps(export, indent=2)
        st.code(json_str, language="json")
        st.download_button(
            "⬇️ Download JSON Report",
            data=json_str,
            file_name=f"websentinel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

# ── Feature Pills ─────────────────────────────────────────────────────────────

def render_feature_pills():
    features = [
        ("🔗", "Broken Link Detection"),
        ("⚡", "Performance Metrics"),
        ("🔒", "Security Audit"),
        ("♿", "Accessibility Checks"),
        ("🔎", "SEO Analysis"),
        ("📸", "Screenshot Capture"),
    ]
    cols = st.columns(len(features))
    for col, (icon, label) in zip(cols, features):
        with col:
            st.markdown(f"""
            <div style="text-align:center;padding:0.7rem 0.4rem;background:#0D1221;
                        border:1px solid #1E2A42;border-radius:10px;margin:0.2rem;">
              <div style="font-size:1.4rem;">{icon}</div>
              <div style="font-size:0.68rem;color:#64748B;margin-top:0.2rem;letter-spacing:0.03em;">{label}</div>
            </div>""", unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    render_hero()

    # URL input
    st.markdown("<br>", unsafe_allow_html=True)
    c_url, c_btn = st.columns([5, 1])
    with c_url:
        url_input = st.text_input(
            label="URL",
            placeholder="https://example.com",
            label_visibility="collapsed",
            key="url_input",
        )
    with c_btn:
        scan_btn = st.button("🔍 Scan", use_container_width=True)

    render_feature_pills()

    # ── Run scan ──
    if scan_btn and url_input.strip():
        url = validate_url(url_input)
        if not url:
            st.error("Please enter a valid URL.")
            return

        progress_bar = st.progress(0, text="Initialising scan…")
        status_text  = st.empty()

        def progress_cb(step: str, pct: int):
            progress_bar.progress(pct / 100, text=step)
            status_text.markdown(
                f'<p style="font-family:\'JetBrains Mono\',monospace;font-size:0.78rem;color:#64748B;">'
                f'⟶ {step}</p>', unsafe_allow_html=True
            )

        try:
            report = run_full_test(url, progress_cb=progress_cb)
            progress_bar.empty()
            status_text.empty()
            st.session_state["last_report"] = report
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Scan failed: {e}")
            return

    elif scan_btn:
        st.warning("Please enter a URL to scan.")

    # Render stored report
    if "last_report" in st.session_state:
        render_report_summary(st.session_state["last_report"])

    # Footer
    st.markdown("""
    <div class="footer">
      WebSentinel v1.0 · Built with Python &amp; Streamlit ·
      Tech: Requests · BeautifulSoup · Concurrent Futures · SSL ·
      <span style="color:#00D4FF;">Add Playwright for real screenshots</span>
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
