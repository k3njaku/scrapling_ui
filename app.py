import json
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from scrapling.fetchers import DynamicFetcher, Fetcher, StealthyFetcher


st.set_page_config(page_title="ScraplingUI", page_icon="🕷️", layout="wide")


if "results" not in st.session_state:
    st.session_state.results = None
if "last_url" not in st.session_state:
    st.session_state.last_url = ""
if "history" not in st.session_state:
    st.session_state.history = []


st.markdown(
    """
<style>
    .block-container { max-width: 1200px; }
    .stButton > button { width: 100%; }
</style>
""",
    unsafe_allow_html=True,
)


st.markdown("# 🕷️ ScraplingUI")
st.markdown("*Web Scraping Made Easy - Powered by Scrapling*")
st.divider()


QUICK_MAP = {
    "All links": "a::attr(href)",
    "All images": "img::attr(src)",
    "All paragraphs": "p::text",
    "All headings": "h1, h2, h3::text",
    "Table cells": "td::text",
}


def scrape(url, fetcher_type, selector, selector_type, options):
    """
    Main scraping function

    Returns: (success: bool, data: list, error: str)
    """
    try:
        if fetcher_type == "Fetcher":
            page = Fetcher.get(
                url,
                stealthy_headers=True,
                timeout=options.get("timeout", 30),
            )
        elif fetcher_type == "StealthyFetcher":
            page = StealthyFetcher.fetch(
                url,
                headless=options.get("headless", True),
                solve_cloudflare=options.get("solve_cloudflare", False),
                network_idle=True,
            )
        elif fetcher_type == "DynamicFetcher":
            page = DynamicFetcher.fetch(
                url,
                headless=options.get("headless", True),
                network_idle=options.get("network_idle", True),
            )
        else:
            return False, [], f"Unknown fetcher type: {fetcher_type}"

        if selector_type == "CSS":
            elements = page.css(selector)
        else:
            elements = page.xpath(selector)

        data = []
        for el in elements:
            if "::text" in selector:
                text = el.text if hasattr(el, "text") else str(el)
                if text and text.strip():
                    data.append({"text": text.strip()})
            elif "::attr(" in selector:
                data.append({"value": str(el)})
            else:
                text = el.text if hasattr(el, "text") else ""
                html = el.html if hasattr(el, "html") else str(el)
                data.append(
                    {
                        "text": text.strip() if text else "",
                        "html": html[:200],
                    }
                )

        return True, data, ""

    except Exception as exc:
        return False, [], str(exc)


def to_csv(data):
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode("utf-8")


def to_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")


def to_excel(data):
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Scraped Data")
    return output.getvalue()


def add_to_history(url, fetcher, selector, count, status):
    st.session_state.history.insert(
        0,
        {
            "url": url[:50] + "..." if len(url) > 50 else url,
            "fetcher": fetcher,
            "selector": selector[:30] + "..." if len(selector) > 30 else selector,
            "count": count,
            "status": status,
            "time": datetime.now().strftime("%H:%M:%S"),
        },
    )
    st.session_state.history = st.session_state.history[:20]


with st.sidebar:
    st.header("⚙️ Settings")

    fetcher_type = st.radio(
        "Fetcher Type",
        ["Fetcher", "StealthyFetcher", "DynamicFetcher"],
        help="Fetcher=Fast, Stealthy=Anti-bot, Dynamic=JavaScript",
    )

    options = {}

    if fetcher_type == "Fetcher":
        options["timeout"] = st.slider("Timeout (seconds)", 10, 60, 30)
    elif fetcher_type == "StealthyFetcher":
        options["headless"] = st.checkbox("Headless", value=True)
        options["solve_cloudflare"] = st.checkbox("Solve Cloudflare", value=False)
    elif fetcher_type == "DynamicFetcher":
        options["headless"] = st.checkbox("Headless", value=True)
        options["network_idle"] = st.checkbox("Wait for network idle", value=True)

    st.divider()

    st.subheader("📋 Quick Selectors")
    quick = st.selectbox(
        "Common patterns",
        ["(select)", "All links", "All images", "All paragraphs", "All headings", "Table cells"],
    )

    st.divider()
    with st.expander("📜 Job History", expanded=False):
        if st.session_state.history:
            for job in st.session_state.history[:10]:
                st.markdown(
                    f"`{job['time']}` {job['status']} {job['count']} items\n\n"
                    f"URL: {job['url']}\n\n"
                    f"Fetcher: {job['fetcher']}\n\n"
                    f"Selector: {job['selector']}"
                )
                st.divider()
        else:
            st.caption("No jobs yet")


url = st.text_input("🔗 URL to scrape", placeholder="https://quotes.toscrape.com")

col1, col2 = st.columns([3, 1])
with col1:
    default_selector = QUICK_MAP.get(quick, "")
    selector = st.text_input(
        "🎯 CSS Selector",
        value=default_selector,
        placeholder=".quote .text::text",
    )
with col2:
    selector_type = st.radio("Type", ["CSS", "XPath"], horizontal=True)


if st.button("🚀 Scrape", type="primary", use_container_width=True):
    if not url:
        st.error("Please enter a URL")
    elif not selector:
        st.error("Please enter a selector")
    else:
        with st.spinner(f"Scraping with {fetcher_type}..."):
            success, data, error = scrape(
                url,
                fetcher_type,
                selector,
                selector_type,
                options,
            )

        if success:
            st.session_state.results = data
            st.success(f"✅ Found {len(data)} items!")
            add_to_history(url, fetcher_type, selector, len(data), "✅")
        else:
            st.error(f"❌ Error: {error}")
            add_to_history(url, fetcher_type, selector, 0, "❌")


if st.session_state.results:
    st.divider()
    st.subheader(f"📊 Results ({len(st.session_state.results)} items)")

    df = pd.DataFrame(st.session_state.results)
    st.dataframe(df, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📥 Download CSV",
            to_csv(st.session_state.results),
            "scraped_data.csv",
            "text/csv",
        )
    with col2:
        st.download_button(
            "📥 Download JSON",
            to_json(st.session_state.results),
            "scraped_data.json",
            "application/json",
        )
    with col3:
        st.download_button(
            "📥 Download Excel",
            to_excel(st.session_state.results),
            "scraped_data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
