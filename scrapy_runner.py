# wiki_scraper/scraper.py
import requests
import re
import os
from bs4 import BeautifulSoup

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "wiki-rag-chatbot/1.0 (mailto:your-email@example.com)"  # set a contact email if possible

def _sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

def run_scraper(person_name: str, output_dir: str = ".") -> str:
    """
    Fetch Wikipedia content for person_name using MediaWiki API,
    write to <Person_Name>_output.txt in output_dir, and return the filename.
    Raises Exception with descriptive message if page not found or ambiguous.
    """
    if not person_name or not person_name.strip():
        raise ValueError("No name provided to run_scraper.")

    headers = {"User-Agent": USER_AGENT}
    title = person_name.strip()

    # First, try to get page info (this will follow redirects)
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "extracts|pageprops",
        "explaintext": 1,
        "redirects": 1,
        "ppprop": "disambiguation"
    }
    resp = requests.get(WIKIPEDIA_API, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    pages = data.get("query", {}).get("pages", {})
    if not pages:
        raise Exception("Wikipedia API returned no pages.")

    page = next(iter(pages.values()))
    if "missing" in page:
        # Try search fallback (approximate matches)
        search_params = {
            "action": "opensearch",
            "format": "json",
            "search": title,
            "limit": 5
        }
        s = requests.get(WIKIPEDIA_API.replace('/api.php','/w/api.php'), params=search_params, headers=headers, timeout=10)
        s.raise_for_status()
        suggestions = s.json()
        suggestions_list = suggestions[1] if isinstance(suggestions, list) and len(suggestions) > 1 else []
        if suggestions_list:
            raise Exception(f"Wikipedia page not found for '{title}'. Did you mean one of: {', '.join(suggestions_list)}?")
        else:
            raise Exception(f"Wikipedia page not found for '{title}'.")
    if page.get("pageprops", {}).get("disambiguation"):
        raise Exception(f"Wikipedia returned a disambiguation page for '{title}'. Try a more specific name (e.g. include middle name / birth year).")

    page_title = page.get("title")
    extract_text = page.get("extract", "")  # plaintext extract

    # For infobox, fetch HTML and parse the infobox table (if present)
    html_params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "prop": "text",
        "redirects": 1
    }
    h = requests.get(WIKIPEDIA_API, params=html_params, headers=headers, timeout=15)
    h.raise_for_status()
    hdata = h.json()
    html = hdata.get("parse", {}).get("text", {}).get("*", "")
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
                    if key:
                        rows.append(f"{key}: {value}")
                    else:
                        rows.append(value)
            infobox_text = "\n".join(rows)

    # Prepare file
    safe_title = _sanitize_filename(page_title.replace(" ", "_"))
    filename = f"{safe_title}_output.txt"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        if infobox_text:
            f.write("### INFOBOX DATA ###\n")
            f.write(infobox_text + "\n\n")
        f.write("### ARTICLE TEXT ###\n")
        f.write(extract_text.strip())

    return filepath
