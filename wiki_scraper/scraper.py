# wiki_scraper/scraper.py
import requests
import re
from bs4 import BeautifulSoup

API_URL = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "wiki-rag-chatbot/1.0 (mailto:your-email@example.com)"

def run_scraper(person_name: str, timeout: int = 15) -> dict:
    """
    Search Wikipedia for person_name, fetch best match, and return a dict:
    {
      "title": <page title>,
      "infobox": "<infobox text or ''>",
      "extract": "<plain article extract>",
      "full_text": "<combined infobox + extract>"
    }
    Does NOT write any files.
    """
    if not person_name or not person_name.strip():
        raise ValueError("No name provided to run_scraper.")

    headers = {"User-Agent": USER_AGENT}
    # 1) Find best match using search
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": person_name,
        "format": "json",
        "srlimit": 1
    }
    r = requests.get(API_URL, params=search_params, headers=headers, timeout=timeout)
    r.raise_for_status()
    search_hits = r.json().get("query", {}).get("search", [])
    if not search_hits:
        raise Exception(f"No Wikipedia results for '{person_name}'.")

    best_title = search_hits[0]["title"]

    # 2) Get plaintext extract (good for RAG)
    extract_params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "format": "json",
        "titles": best_title
    }
    e = requests.get(API_URL, params=extract_params, headers=headers, timeout=timeout)
    e.raise_for_status()
    pages = e.json().get("query", {}).get("pages", {})
    extract_text = ""
    if pages:
        extract_text = next(iter(pages.values())).get("extract", "") or ""

    # 3) Fetch HTML and parse infobox (if present)
    html_params = {
        "action": "parse",
        "page": best_title,
        "format": "json",
        "prop": "text"
    }
    h = requests.get(API_URL, params=html_params, headers=headers, timeout=timeout)
    h.raise_for_status()
    html = h.json().get("parse", {}).get("text", {}).get("*", "")
    infobox_text = ""
    if html:
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table", {"class": lambda c: c and "infobox" in c})
        if infobox:
            rows = []
            for tr in infobox.find_all("tr"):
                th = tr.find("th")
                td = tr.find("td")
                key = th.get_text(" ", strip=True) if th else ""
                value = td.get_text(" ", strip=True) if td else ""
                if key or value:
                    rows.append(f"{key}: {value}" if key else value)
            infobox_text = "\n".join(rows)

    # 4) Compose full_text for embedding
    parts = []
    if infobox_text:
        parts.append("### INFOBOX DATA ###\n" + infobox_text)
    if extract_text:
        parts.append("### ARTICLE TEXT ###\n" + extract_text.strip())
    full_text = "\n\n".join(parts).strip()

    return {
        "title": best_title,
        "infobox": infobox_text,
        "extract": extract_text,
        "full_text": full_text
    }
