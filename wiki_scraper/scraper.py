# wiki_scraper/scraper.py
import requests
from bs4 import BeautifulSoup
import re
import os

def run_scraper(person_name: str):
    if not person_name:
        raise ValueError("No person name provided")

    formatted_name = person_name.strip().replace(' ', '_')
    url = f"https://en.wikipedia.org/wiki/{formatted_name}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception("Failed to fetch Wikipedia page.")

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract paragraphs
    content_div = soup.find('div', id='mw-content-text')
    paragraphs = content_div.find_all('p') if content_div else []
    full_text = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    # Remove reference numbers like [1], [2]
    clean_text = re.sub(r'\[\d+\]', '', full_text)

    # Extract infobox data
    infobox_text = ""
    infobox = soup.find('table', class_='infobox')
    if infobox:
        rows = infobox.find_all('tr')
        for row in rows:
            key = row.find('th')
            value = row.find('td')
            if key or value:
                k = key.get_text(strip=True) if key else ""
                v = value.get_text(strip=True) if value else ""
                infobox_text += f"{k}: {v}\n"

    file_name = f"{formatted_name}_output.txt"
    with open(file_name, "w", encoding="utf-8") as f:
        if infobox_text:
            f.write("### INFOBOX DATA ###\n")
            f.write(infobox_text + "\n")
        f.write("### ARTICLE TEXT ###\n")
        f.write(clean_text)

    print(f"✅ Done! Written to {file_name}")
