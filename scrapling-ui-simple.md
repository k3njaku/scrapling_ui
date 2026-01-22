# ScraplingUI - MVP Build Instructions (UI Only)

## Goal
Build a clean Streamlit UI wrapper around Scrapling. No AI yet - just a functional, good-looking scraping tool.

---

## Tech Stack

- **Streamlit** - UI
- **Scrapling** - Scraping engine  
- **SQLite** - Job history
- **pandas** - Data handling + exports

---

## Install

```bash
pip install streamlit scrapling pandas openpyxl
pip install "scrapling[fetchers]"
scrapling install
```

---

## Project Structure

```
scrapling-ui/
├── app.py              # Main app (single file MVP)
├── requirements.txt
└── .streamlit/
    └── config.toml     # Theme
```

---

## File 1: requirements.txt

```
streamlit>=1.28.0
scrapling
pandas
openpyxl
```

---

## File 2: .streamlit/config.toml

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#1a1a2e"
font = "sans serif"
```

---

## File 3: app.py (THE MAIN FILE)

Build a single-file Streamlit app with these sections:

### Header
- Title: "🕷️ ScraplingUI"
- Subtitle: "Web Scraping Made Easy"

### Sidebar
- **Fetcher Selection**: Radio buttons
  - Fetcher (Fast HTTP)
  - StealthyFetcher (Anti-bot bypass)
  - DynamicFetcher (JavaScript sites)
  
- **Fetcher Options** (show/hide based on selection):
  - Fetcher: timeout slider (10-60, default 30)
  - StealthyFetcher: headless checkbox, solve_cloudflare checkbox
  - DynamicFetcher: headless checkbox, network_idle checkbox

- **Quick Selectors** dropdown:
  - All links: `a::attr(href)`
  - All images: `img::attr(src)`
  - All paragraphs: `p::text`
  - All headings: `h1, h2, h3::text`
  - Table cells: `td::text`

- **Job History**: Show last 10 jobs (expandable)

### Main Content

**Step 1: URL Input**
```python
url = st.text_input("🔗 URL to scrape", placeholder="https://quotes.toscrape.com")
```

**Step 2: Selector Input**
```python
col1, col2 = st.columns([3, 1])
with col1:
    selector = st.text_input("🎯 CSS Selector", placeholder=".quote .text::text")
with col2:
    selector_type = st.radio("Type", ["CSS", "XPath"], horizontal=True)
```

**Step 3: Scrape Button**
```python
if st.button("🚀 Scrape", type="primary", use_container_width=True):
    # Do the scraping
```

**Step 4: Results Section**
- Show success/error message
- Display results count
- Show data in `st.dataframe()`
- Export buttons: CSV, JSON, Excel

---

## Core Scraping Logic

```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher

def scrape(url, fetcher_type, selector, selector_type, options):
    """
    Main scraping function
    
    Returns: (success: bool, data: list, error: str)
    """
    try:
        # Step 1: Fetch the page
        if fetcher_type == "Fetcher":
            page = Fetcher.get(url, stealthy_headers=True, timeout=options.get('timeout', 30))
        
        elif fetcher_type == "StealthyFetcher":
            page = StealthyFetcher.fetch(
                url,
                headless=options.get('headless', True),
                solve_cloudflare=options.get('solve_cloudflare', False),
                network_idle=True
            )
        
        elif fetcher_type == "DynamicFetcher":
            page = DynamicFetcher.fetch(
                url,
                headless=options.get('headless', True),
                network_idle=options.get('network_idle', True)
            )
        
        # Step 2: Extract data
        if selector_type == "CSS":
            elements = page.css(selector)
        else:
            elements = page.xpath(selector)
        
        # Step 3: Process results
        data = []
        for el in elements:
            # Handle ::text pseudo-element
            if '::text' in selector:
                text = el.text if hasattr(el, 'text') else str(el)
                if text and text.strip():
                    data.append({"text": text.strip()})
            # Handle ::attr(x) pseudo-element
            elif '::attr(' in selector:
                data.append({"value": str(el)})
            # Default: get text content
            else:
                text = el.text if hasattr(el, 'text') else ""
                html = el.html if hasattr(el, 'html') else str(el)
                data.append({
                    "text": text.strip() if text else "",
                    "html": html[:200]  # Truncate HTML preview
                })
        
        return True, data, ""
    
    except Exception as e:
        return False, [], str(e)
```

---

## Export Functions

```python
import pandas as pd
from io import BytesIO
import json

def to_csv(data):
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')

def to_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')

def to_excel(data):
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Scraped Data')
    return output.getvalue()
```

---

## Session State (Remember Results)

```python
# At top of app.py
if 'results' not in st.session_state:
    st.session_state.results = None
if 'last_url' not in st.session_state:
    st.session_state.last_url = ""
if 'history' not in st.session_state:
    st.session_state.history = []
```

---

## Job History (Simple List)

```python
def add_to_history(url, fetcher, selector, count, status):
    st.session_state.history.insert(0, {
        'url': url[:50] + '...' if len(url) > 50 else url,
        'fetcher': fetcher,
        'selector': selector[:30] + '...' if len(selector) > 30 else selector,
        'count': count,
        'status': status,
        'time': datetime.now().strftime('%H:%M:%S')
    })
    # Keep only last 20
    st.session_state.history = st.session_state.history[:20]
```

---

## UI Flow Example

```python
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ScraplingUI", page_icon="🕷️", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .block-container { max-width: 1200px; }
    .stButton > button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 🕷️ ScraplingUI")
st.markdown("*Web Scraping Made Easy - Powered by Scrapling*")
st.divider()

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    fetcher_type = st.radio(
        "Fetcher Type",
        ["Fetcher", "StealthyFetcher", "DynamicFetcher"],
        help="Fetcher=Fast, Stealthy=Anti-bot, Dynamic=JavaScript"
    )
    
    # Dynamic options based on fetcher
    options = {}
    
    if fetcher_type == "Fetcher":
        options['timeout'] = st.slider("Timeout (seconds)", 10, 60, 30)
    
    elif fetcher_type == "StealthyFetcher":
        options['headless'] = st.checkbox("Headless", value=True)
        options['solve_cloudflare'] = st.checkbox("Solve Cloudflare", value=False)
    
    elif fetcher_type == "DynamicFetcher":
        options['headless'] = st.checkbox("Headless", value=True)
        options['network_idle'] = st.checkbox("Wait for network idle", value=True)
    
    st.divider()
    
    # Quick selectors
    st.subheader("📋 Quick Selectors")
    quick = st.selectbox(
        "Common patterns",
        ["(select)", "All links", "All images", "All paragraphs", "All headings", "Table cells"]
    )
    
    quick_map = {
        "All links": "a::attr(href)",
        "All images": "img::attr(src)",
        "All paragraphs": "p::text",
        "All headings": "h1, h2, h3::text",
        "Table cells": "td::text"
    }

# Main content
url = st.text_input("🔗 URL", placeholder="https://quotes.toscrape.com")

col1, col2 = st.columns([4, 1])
with col1:
    default_selector = quick_map.get(quick, "")
    selector = st.text_input("🎯 Selector", value=default_selector, placeholder=".quote .text::text")
with col2:
    selector_type = st.radio("Type", ["CSS", "XPath"])

# Scrape button
if st.button("🚀 Scrape", type="primary", use_container_width=True):
    if not url:
        st.error("Please enter a URL")
    elif not selector:
        st.error("Please enter a selector")
    else:
        with st.spinner(f"Scraping with {fetcher_type}..."):
            success, data, error = scrape(url, fetcher_type, selector, selector_type, options)
        
        if success:
            st.session_state.results = data
            st.success(f"✅ Found {len(data)} items!")
            add_to_history(url, fetcher_type, selector, len(data), "✅")
        else:
            st.error(f"❌ Error: {error}")
            add_to_history(url, fetcher_type, selector, 0, "❌")

# Results
if st.session_state.results:
    st.divider()
    st.subheader(f"📊 Results ({len(st.session_state.results)} items)")
    
    df = pd.DataFrame(st.session_state.results)
    st.dataframe(df, use_container_width=True)
    
    # Export buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📥 Download CSV",
            to_csv(st.session_state.results),
            "scraped_data.csv",
            "text/csv"
        )
    with col2:
        st.download_button(
            "📥 Download JSON", 
            to_json(st.session_state.results),
            "scraped_data.json",
            "application/json"
        )
    with col3:
        st.download_button(
            "📥 Download Excel",
            to_excel(st.session_state.results),
            "scraped_data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# History in sidebar
with st.sidebar:
    st.divider()
    st.subheader("📜 History")
    if st.session_state.history:
        for job in st.session_state.history[:10]:
            st.markdown(f"`{job['time']}` {job['status']} {job['count']} items")
    else:
        st.caption("No jobs yet")
```

---

## Test Sites

Use these to verify it works:

| Site | Test Selector | Fetcher |
|------|---------------|---------|
| `https://quotes.toscrape.com` | `.quote .text::text` | Fetcher |
| `https://books.toscrape.com` | `.product_pod h3 a::attr(title)` | Fetcher |
| `https://news.ycombinator.com` | `.titleline a::text` | Fetcher |

---

## Run It

```bash
cd scrapling-ui
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## That's It!

This gives you a working MVP. Once this works, we add:
1. AI-powered selector generation
2. Saved configurations
3. Scheduled jobs
4. Batch URL processing
