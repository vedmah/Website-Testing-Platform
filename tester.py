"""
WebSentinel - Core Testing Engine
Handles: UI checks, broken links, performance, security, screenshots
"""

import time
import ssl
import socket
import urllib.parse
import urllib.request
import urllib.error
import http.client
import re
import json
import base64
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Data Models ────────────────────────────────────────────────────────────────

@dataclass
class LinkResult:
    url: str
    status_code: int
    is_broken: bool
    response_time_ms: float
    error: Optional[str] = None
    anchor_text: Optional[str] = None

@dataclass
class PerformanceMetrics:
    dns_lookup_ms: float = 0.0
    tcp_connect_ms: float = 0.0
    ttfb_ms: float = 0.0          # Time To First Byte
    total_load_ms: float = 0.0
    page_size_bytes: int = 0
    num_requests: int = 0
    performance_score: int = 0
    grade: str = "N/A"

@dataclass
class SecurityCheck:
    name: str
    passed: bool
    severity: str          # critical / high / medium / low / info
    detail: str
    recommendation: str = ""

@dataclass
class UICheck:
    name: str
    passed: bool
    detail: str
    category: str          # accessibility / seo / best-practices

@dataclass
class TestReport:
    url: str
    timestamp: str
    summary_score: int
    broken_links: list = field(default_factory=list)
    all_links: list = field(default_factory=list)
    performance: Optional[PerformanceMetrics] = None
    security_checks: list = field(default_factory=list)
    ui_checks: list = field(default_factory=list)
    screenshot_b64: Optional[str] = None
    page_title: str = ""
    status_code: int = 0
    errors: list = field(default_factory=list)
    raw_html: str = ""

# ── HTTP Session ───────────────────────────────────────────────────────────────

def _make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=2, backoff_factor=0.3, status_forcelist=[500, 502, 503])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })
    return session

# ── Link Extraction ────────────────────────────────────────────────────────────

def _extract_links(html: str, base_url: str) -> list[tuple[str, str]]:
    """Return list of (absolute_url, anchor_text) from HTML."""
    links = []
    pattern = re.compile(
        r'<a[^>]+href=["\']([^"\'#][^"\']*)["\'][^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    parsed_base = urllib.parse.urlparse(base_url)

    for match in pattern.finditer(html):
        href = match.group(1).strip()
        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()[:80]
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        abs_url = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlparse(abs_url)
        if parsed.scheme in ("http", "https"):
            links.append((abs_url, text or href[:50]))

    # Deduplicate by URL
    seen = set()
    unique = []
    for url, text in links:
        if url not in seen:
            seen.add(url)
            unique.append((url, text))
    return unique[:80]   # cap at 80 to stay fast

# ── Single Link Check ──────────────────────────────────────────────────────────

def _check_single_link(url: str, anchor: str, session: requests.Session) -> LinkResult:
    t0 = time.perf_counter()
    try:
        resp = session.head(url, timeout=8, allow_redirects=True)
        # Some servers reject HEAD — fall back to GET with streaming
        if resp.status_code in (405, 403, 400):
            resp = session.get(url, timeout=8, stream=True, allow_redirects=True)
        elapsed = (time.perf_counter() - t0) * 1000
        broken = resp.status_code >= 400
        return LinkResult(
            url=url,
            status_code=resp.status_code,
            is_broken=broken,
            response_time_ms=round(elapsed, 1),
            error=None if not broken else f"HTTP {resp.status_code}",
            anchor_text=anchor,
        )
    except requests.exceptions.Timeout:
        return LinkResult(url=url, status_code=0, is_broken=True,
                          response_time_ms=8000, error="Timeout", anchor_text=anchor)
    except requests.exceptions.SSLError as e:
        return LinkResult(url=url, status_code=0, is_broken=True,
                          response_time_ms=(time.perf_counter()-t0)*1000,
                          error=f"SSL Error: {str(e)[:60]}", anchor_text=anchor)
    except Exception as e:
        return LinkResult(url=url, status_code=0, is_broken=True,
                          response_time_ms=(time.perf_counter()-t0)*1000,
                          error=str(e)[:80], anchor_text=anchor)

# ── Broken Link Detection ──────────────────────────────────────────────────────

def check_links(html: str, base_url: str, progress_cb=None) -> list[LinkResult]:
    links = _extract_links(html, base_url)
    results = []
    session = _make_session()

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(_check_single_link, url, anchor, session): (url, anchor)
                   for url, anchor in links}
        done = 0
        for future in as_completed(futures):
            done += 1
            result = future.result()
            results.append(result)
            if progress_cb:
                progress_cb(done, len(links))

    results.sort(key=lambda r: (not r.is_broken, r.url))
    return results

# ── Performance Measurement ────────────────────────────────────────────────────

def measure_performance(url: str) -> PerformanceMetrics:
    m = PerformanceMetrics()
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    # DNS
    t0 = time.perf_counter()
    try:
        socket.getaddrinfo(host, port)
        m.dns_lookup_ms = round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        m.dns_lookup_ms = -1

    # TCP connect
    t1 = time.perf_counter()
    try:
        sock = socket.create_connection((host, port), timeout=5)
        m.tcp_connect_ms = round((time.perf_counter() - t1) * 1000, 1)
        sock.close()
    except Exception:
        m.tcp_connect_ms = -1

    # TTFB + total load via requests
    session = _make_session()
    t2 = time.perf_counter()
    try:
        with session.get(url, timeout=15, stream=True) as resp:
            m.ttfb_ms = round((time.perf_counter() - t2) * 1000, 1)
            content = b""
            for chunk in resp.iter_content(8192):
                content += chunk
            m.total_load_ms = round((time.perf_counter() - t2) * 1000, 1)
            m.page_size_bytes = len(content)
            m.status_code = resp.status_code  # type: ignore[attr-defined]
    except Exception:
        pass

    # Count sub-resources from HTML (img/script/link)
    try:
        session2 = _make_session()
        r = session2.get(url, timeout=10)
        html = r.text
        m.num_requests = (
            1
            + len(re.findall(r'<img\b', html, re.I))
            + len(re.findall(r'<script\b', html, re.I))
            + len(re.findall(r'<link\b[^>]+stylesheet', html, re.I))
        )
    except Exception:
        m.num_requests = 1

    # Score (0–100)
    score = 100
    if m.ttfb_ms > 800:   score -= 30
    elif m.ttfb_ms > 400: score -= 15
    if m.total_load_ms > 3000:  score -= 20
    elif m.total_load_ms > 1500: score -= 10
    if m.page_size_bytes > 3_000_000: score -= 20
    elif m.page_size_bytes > 1_000_000: score -= 10
    if m.num_requests > 80: score -= 15
    elif m.num_requests > 40: score -= 7
    m.performance_score = max(0, score)

    if score >= 90:   m.grade = "A+"
    elif score >= 80: m.grade = "A"
    elif score >= 70: m.grade = "B"
    elif score >= 60: m.grade = "C"
    elif score >= 50: m.grade = "D"
    else:             m.grade = "F"

    return m

# ── Security Checks ────────────────────────────────────────────────────────────

def check_security(url: str, html: str, response_headers: dict) -> list[SecurityCheck]:
    checks = []
    parsed = urllib.parse.urlparse(url)

    # 1. HTTPS
    checks.append(SecurityCheck(
        name="HTTPS / TLS",
        passed=parsed.scheme == "https",
        severity="critical",
        detail="Site uses HTTPS encryption" if parsed.scheme == "https"
               else "Site is served over HTTP — all traffic is unencrypted.",
        recommendation="" if parsed.scheme == "https"
                       else "Redirect all traffic to HTTPS and obtain a valid TLS certificate.",
    ))

    # 2. SSL Certificate validity
    if parsed.scheme == "https":
        try:
            ctx = ssl.create_default_context()
            conn = ctx.wrap_socket(
                socket.socket(socket.AF_INET), server_hostname=parsed.hostname
            )
            conn.settimeout(5)
            conn.connect((parsed.hostname, 443))
            cert = conn.getpeercert()
            conn.close()
            expire_str = cert.get("notAfter", "")
            if expire_str:
                expire_dt = datetime.strptime(expire_str, "%b %d %H:%M:%S %Y %Z")
                days_left = (expire_dt - datetime.utcnow()).days
                passed = days_left > 14
                checks.append(SecurityCheck(
                    name="SSL Certificate",
                    passed=passed,
                    severity="critical" if days_left < 0 else ("high" if days_left < 14 else "info"),
                    detail=f"Certificate expires in {days_left} days ({expire_str})",
                    recommendation="" if passed else "Renew the SSL certificate immediately.",
                ))
        except Exception as e:
            checks.append(SecurityCheck(
                name="SSL Certificate",
                passed=False, severity="critical",
                detail=f"Could not verify certificate: {str(e)[:80]}",
                recommendation="Check your SSL certificate configuration.",
            ))

    # 3. Security Headers
    header_checks = [
        ("Strict-Transport-Security", "HSTS Header", "high",
         "Protects against protocol-downgrade attacks.",
         "Add: Strict-Transport-Security: max-age=31536000; includeSubDomains"),
        ("X-Frame-Options", "Clickjacking Protection (X-Frame-Options)", "medium",
         "Prevents your site being embedded in iframes.",
         "Add: X-Frame-Options: DENY or SAMEORIGIN"),
        ("X-Content-Type-Options", "MIME Sniffing Protection", "medium",
         "Prevents MIME type sniffing.",
         "Add: X-Content-Type-Options: nosniff"),
        ("Content-Security-Policy", "Content Security Policy", "medium",
         "Controls which resources can be loaded.",
         "Define a Content-Security-Policy header to mitigate XSS risks."),
        ("Referrer-Policy", "Referrer Policy", "low",
         "Controls referrer information sent with requests.",
         "Add: Referrer-Policy: strict-origin-when-cross-origin"),
        ("Permissions-Policy", "Permissions Policy", "low",
         "Controls browser feature access.",
         "Add a Permissions-Policy header to restrict unnecessary browser features."),
    ]
    for h_name, check_name, severity, good_detail, reco in header_checks:
        present = h_name.lower() in {k.lower() for k in response_headers}
        checks.append(SecurityCheck(
            name=check_name,
            passed=present,
            severity=severity,
            detail=f"Header present: {response_headers.get(h_name, response_headers.get(h_name.lower(), ''))}" 
                   if present else f"Missing header: {h_name}",
            recommendation="" if present else reco,
        ))

    # 4. Server information disclosure
    server_h = response_headers.get("Server", response_headers.get("server", ""))
    x_powered = response_headers.get("X-Powered-By", response_headers.get("x-powered-by", ""))
    info_leak = bool(server_h or x_powered)
    checks.append(SecurityCheck(
        name="Server Information Disclosure",
        passed=not info_leak,
        severity="low",
        detail=f"Server: {server_h}, X-Powered-By: {x_powered}" if info_leak
               else "No server version information exposed",
        recommendation="Remove or obscure Server and X-Powered-By headers." if info_leak else "",
    ))

    # 5. Mixed content
    if parsed.scheme == "https":
        http_resources = re.findall(r'src=["\']http://[^"\']+["\']', html, re.I)
        has_mixed = len(http_resources) > 0
        checks.append(SecurityCheck(
            name="Mixed Content",
            passed=not has_mixed,
            severity="high",
            detail=f"Found {len(http_resources)} HTTP resource(s) on HTTPS page" if has_mixed
                   else "No mixed content detected",
            recommendation="Change all resource URLs to HTTPS or use protocol-relative URLs." if has_mixed else "",
        ))

    # 6. Forms with autocomplete
    form_passwords = re.findall(r'<input[^>]+type=["\']password["\'][^>]*>', html, re.I)
    autocomplete_missing = [f for f in form_passwords if "autocomplete" not in f.lower()]
    checks.append(SecurityCheck(
        name="Password Field Autocomplete",
        passed=len(autocomplete_missing) == 0,
        severity="low",
        detail=f"{len(autocomplete_missing)} password field(s) missing autocomplete attribute"
               if autocomplete_missing else "All password fields have autocomplete configured",
        recommendation='Add autocomplete="new-password" or autocomplete="off" to password fields.' 
                       if autocomplete_missing else "",
    ))

    # 7. robots.txt
    try:
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        r = requests.get(robots_url, timeout=5, headers={"User-Agent": "WebSentinelBot/1.0"})
        has_robots = r.status_code == 200 and len(r.text) > 10
    except Exception:
        has_robots = False
    checks.append(SecurityCheck(
        name="robots.txt",
        passed=has_robots,
        severity="info",
        detail="robots.txt found and accessible" if has_robots else "No robots.txt found",
        recommendation="Create a /robots.txt file to guide web crawlers." if not has_robots else "",
    ))

    return checks

# ── UI / Accessibility / SEO Checks ───────────────────────────────────────────

def check_ui(html: str, url: str) -> list[UICheck]:
    checks = []

    # SEO
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = title_match.group(1).strip() if title_match else ""
    checks.append(UICheck("Page Title", bool(title and 10 <= len(title) <= 60),
                           f"'{title}' ({len(title)} chars)" if title else "No <title> tag found",
                           "seo"))

    desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
                            html, re.I)
    desc = desc_match.group(1).strip() if desc_match else ""
    checks.append(UICheck("Meta Description", bool(desc and 50 <= len(desc) <= 160),
                           f"'{desc[:80]}...' ({len(desc)} chars)" if desc else "Missing meta description",
                           "seo"))

    h1_tags = re.findall(r"<h1[^>]*>.*?</h1>", html, re.I | re.S)
    checks.append(UICheck("H1 Tag", len(h1_tags) == 1,
                           f"Found {len(h1_tags)} H1 tag(s) — exactly 1 recommended", "seo"))

    canonical = bool(re.search(r'<link[^>]+rel=["\']canonical["\']', html, re.I))
    checks.append(UICheck("Canonical URL", canonical,
                           "Canonical link tag present" if canonical else "No canonical link tag found", "seo"))

    og_title = bool(re.search(r'<meta[^>]+property=["\']og:title["\']', html, re.I))
    checks.append(UICheck("Open Graph Tags", og_title,
                           "og:title found" if og_title else "Missing Open Graph meta tags (og:title etc.)", "seo"))

    # Accessibility
    imgs = re.findall(r"<img[^>]*>", html, re.I)
    imgs_no_alt = [i for i in imgs if "alt=" not in i.lower()]
    checks.append(UICheck("Image Alt Attributes",
                           len(imgs_no_alt) == 0,
                           f"{len(imgs_no_alt)}/{len(imgs)} images missing alt attribute",
                           "accessibility"))

    lang_match = re.search(r'<html[^>]+lang=["\']([^"\']+)["\']', html, re.I)
    checks.append(UICheck("HTML lang Attribute", bool(lang_match),
                           f"lang=\"{lang_match.group(1)}\"" if lang_match else "Missing lang attribute on <html>",
                           "accessibility"))

    viewport = bool(re.search(r'<meta[^>]+name=["\']viewport["\']', html, re.I))
    checks.append(UICheck("Viewport Meta Tag", viewport,
                           "Viewport meta tag present" if viewport else "Missing viewport meta tag — poor mobile experience",
                           "accessibility"))

    skip_link = bool(re.search(r'href=["\']#(main|content|skip)["\']', html, re.I))
    checks.append(UICheck("Skip Navigation Link", skip_link,
                           "Skip link found" if skip_link else "No skip navigation link (important for screen readers)",
                           "accessibility"))

    # Best Practices
    charset = bool(re.search(r'<meta[^>]+charset[^>]*>', html, re.I))
    checks.append(UICheck("Charset Declaration", charset,
                           "Charset meta tag found" if charset else "Missing charset declaration", "best-practices"))

    favicons = re.findall(r'<link[^>]+rel=["\'][^"\']*icon[^"\']*["\']', html, re.I)
    checks.append(UICheck("Favicon", len(favicons) > 0,
                           f"{len(favicons)} favicon link(s) found" if favicons else "No favicon link tag found",
                           "best-practices"))

    inline_styles = len(re.findall(r'style=["\'][^"\']{50,}["\']', html, re.I))
    checks.append(UICheck("Minimal Inline Styles",
                           inline_styles < 5,
                           f"{inline_styles} large inline style block(s) found — prefer external CSS",
                           "best-practices"))

    deprecated = re.findall(r'<(font|center|marquee|blink|frame|frameset)\b', html, re.I)
    checks.append(UICheck("No Deprecated HTML Tags", len(deprecated) == 0,
                           f"Deprecated tags found: {list(set(t.lower() for t in deprecated))}" if deprecated
                           else "No deprecated HTML tags detected",
                           "best-practices"))

    return checks

# ── Page Screenshot via HTML canvas (placeholder base64) ──────────────────────

def capture_screenshot_placeholder(url: str, page_title: str) -> str:
    """
    Returns a base64-encoded SVG that visually represents a browser screenshot.
    In a production deployment, replace this with Playwright:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            screenshot = await page.screenshot(full_page=True)
    """
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#0A0E1A"/>
  <rect x="0" y="0" width="1280" height="40" fill="#161B2E"/>
  <circle cx="20" cy="20" r="7" fill="#FF5F56"/>
  <circle cx="40" cy="20" r="7" fill="#FFBD2E"/>
  <circle cx="60" cy="20" r="7" fill="#27C93F"/>
  <rect x="200" y="8" width="880" height="24" rx="12" fill="#0A0E1A"/>
  <text x="640" y="25" font-family="monospace" font-size="12" fill="#00D4FF" text-anchor="middle">{url[:80]}</text>
  <rect x="40" y="80" width="1200" height="2" fill="#00D4FF" opacity="0.3"/>
  <text x="640" y="200" font-family="monospace" font-size="28" fill="#00D4FF" text-anchor="middle" opacity="0.8">🔍 WebSentinel Screenshot</text>
  <text x="640" y="250" font-family="monospace" font-size="16" fill="#888" text-anchor="middle">{page_title[:60]}</text>
  <text x="640" y="400" font-family="monospace" font-size="13" fill="#555" text-anchor="middle">
    Deploy with Playwright for real screenshots:
  </text>
  <text x="640" y="425" font-family="monospace" font-size="12" fill="#444" text-anchor="middle">
    pip install playwright &amp;&amp; playwright install chromium
  </text>
  <text x="640" y="460" font-family="monospace" font-size="11" fill="#333" text-anchor="middle">Captured at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}</text>
</svg>"""
    return base64.b64encode(svg.encode()).decode()

# ── Master Test Runner ─────────────────────────────────────────────────────────

def run_full_test(url: str, progress_cb=None) -> TestReport:
    """
    Run all tests and return a TestReport.
    progress_cb(step: str, pct: int) called throughout.
    """
    report = TestReport(
        url=url,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        summary_score=0,
    )

    def emit(step, pct):
        if progress_cb:
            progress_cb(step, pct)

    # ── Step 1: Fetch page ─────────────────────────────────────────────────────
    emit("Fetching page…", 5)
    session = _make_session()
    try:
        resp = session.get(url, timeout=15, allow_redirects=True)
        report.status_code = resp.status_code
        report.raw_html = resp.text
        response_headers = dict(resp.headers)

        title_match = re.search(r"<title[^>]*>(.*?)</title>", resp.text, re.I | re.S)
        report.page_title = title_match.group(1).strip() if title_match else ""

        if resp.status_code >= 400:
            report.errors.append(f"Page returned HTTP {resp.status_code}")
    except Exception as e:
        report.errors.append(f"Failed to fetch page: {str(e)}")
        response_headers = {}

    emit("Checking UI & SEO…", 20)
    # ── Step 2: UI checks ──────────────────────────────────────────────────────
    if report.raw_html:
        report.ui_checks = check_ui(report.raw_html, url)

    emit("Running security audit…", 35)
    # ── Step 3: Security ───────────────────────────────────────────────────────
    if report.raw_html:
        report.security_checks = check_security(url, report.raw_html, response_headers)

    emit("Measuring performance…", 55)
    # ── Step 4: Performance ────────────────────────────────────────────────────
    report.performance = measure_performance(url)

    emit("Scanning for broken links…", 70)
    # ── Step 5: Broken links ───────────────────────────────────────────────────
    if report.raw_html:
        def link_progress(done, total):
            pct = 70 + int((done / total) * 20) if total else 90
            emit(f"Checking links ({done}/{total})…", pct)
        report.all_links = check_links(report.raw_html, url, link_progress)
        report.broken_links = [l for l in report.all_links if l.is_broken]

    emit("Capturing screenshot…", 92)
    # ── Step 6: Screenshot ────────────────────────────────────────────────────
    report.screenshot_b64 = capture_screenshot_placeholder(url, report.page_title)

    # ── Step 7: Overall score ─────────────────────────────────────────────────
    emit("Computing scores…", 97)
    score = 0
    weights = {"performance": 25, "security": 35, "ui": 25, "links": 15}

    # Performance sub-score
    score += int((report.performance.performance_score / 100) * weights["performance"])

    # Security sub-score
    if report.security_checks:
        passed = sum(1 for c in report.security_checks if c.passed)
        score += int((passed / len(report.security_checks)) * weights["security"])

    # UI sub-score
    if report.ui_checks:
        passed = sum(1 for c in report.ui_checks if c.passed)
        score += int((passed / len(report.ui_checks)) * weights["ui"])

    # Links sub-score
    if report.all_links:
        healthy = sum(1 for l in report.all_links if not l.is_broken)
        score += int((healthy / len(report.all_links)) * weights["links"])
    else:
        score += weights["links"]   # no links → not penalised

    report.summary_score = min(100, score)
    emit("Done!", 100)
    return report
