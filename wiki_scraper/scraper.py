# wiki_scraper/scraper.py
import requests
import re
import os
from bs4 import BeautifulSoup

API_URL = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "wiki-rag-chatbot/1.0 (mailto:your-email@example.com)"

def _sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

def run_scraper(person_name: str, output_dir: str = ".") -> str:
    """
    Search Wikipedia for `person_name`, fetch the top article,
    and save both infobox + article text into <Title>_output.txt.
    Returns full filepath.
    """
    if not person_name.strip():
        raise ValueError("No name provided.")

    headers = {"User-Agent": USER_AGENT}

    # 🔎 Step 1: Search for the best page
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": person_name,
        "format": "json"
    }
    r = requests.get(API_URL, params=search_params, headers=headers, timeout=15)
    r.raise_for_status()
    results = r.json().get("query", {}).get("search", [])
    if not results:
        raise Exception(f"No Wikipedia results for '{person_name}'.")

    best_title = results[0]["title"]  # top result
    print(f"✅ Found best match page: {best_title}")

    # 🔗 Step 2: Get plain text extract
    extract_params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "format": "json",
        "titles": best_title
    }
    e = requests.get(API_URL, params=extract_params, headers=headers, timeout=15)
    e.raise_for_status()
    pages = e.json()["query"]["pages"]
    extract_text = next(iter(pages.values())).get("extract", "")

    # 📑 Step 3: Get HTML for infobox
    html_params = {
        "action": "parse",
        "page": best_title,
        "format": "json",
        "prop": "text"
    }
    h = requests.get(API_URL, params=html_params, headers=headers, timeout=15)
    h.raise_for_status()
    html = h.json().get("parse", {}).get("text", {}).get("*", "")
    infobox_text = ""
    if html:
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table", {"class": lambda c: c and "infobox" in c})
        if infobox:
            rows = []
            for tr in infobox.find_all("tr"):
                th, td = tr.find("th"), tr.find("td")
                key = th.get_text(" ", strip=True) if th else ""
                value = td.get_text(" ", strip=True) if td else ""
                if key or value:
                    rows.append(f"{key}: {value}" if key else value)
            infobox_text = "\n".join(rows)

    # 📝 Step 4: Write output file
    safe_title = _sanitize_filename(best_title.replace(" ", "_"))
    filepath = os.path.join(output_dir, f"{safe_title}_output.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        if infobox_text:
            f.write("### INFOBOX DATA ###\n" + infobox_text + "\n\n")
        f.write("### ARTICLE TEXT ###\n" + extract_text.strip())

    return filepath
