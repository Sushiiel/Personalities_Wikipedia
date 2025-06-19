# wiki_scraper/scraper.py
import requests
from bs4 import BeautifulSoup
import re

def run_scraper(person_name: str):
    formatted_name = person_name.strip().replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{formatted_name}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Wikipedia page not found.")

    soup = BeautifulSoup(response.text, "html.parser")


    content_div = soup.find("div", id="mw-content-text")
    paragraphs = content_div.find_all("p") if content_div else []
    full_text = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    clean_text = re.sub(r"\[\d+\]", "", full_text)


    infobox_data = []
    infobox = soup.find("table", class_="infobox")
    if infobox:
        for row in infobox.find_all("tr"):
            key = row.find("th")
            value = row.find("td")
            if key or value:
                k = key.get_text(strip=True) if key else ""
                v = value.get_text(strip=True) if value else ""
                infobox_data.append(f"{k}: {v}")

    file_name = f"{formatted_name}_output.txt"
    with open(file_name, "w", encoding="utf-8") as f:
        if infobox_data:
            f.write("### INFOBOX DATA ###\n")
            f.write("\n".join(infobox_data) + "\n\n")
        f.write("### ARTICLE TEXT ###\n")
        f.write(clean_text)

    print(f"Done! Saved as {file_name}")
