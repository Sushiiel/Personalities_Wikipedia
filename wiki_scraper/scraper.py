# wiki_scraper/scraper.py
import re
import scrapy
from scrapy.crawler import CrawlerProcess

class WikiSpider(scrapy.Spider):
    name = "wiki_spider"

    def __init__(self, person_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not person_name:
            raise ValueError("No name provided.")
        self.person_name = person_name
        formatted_name = person_name.strip().replace(" ", "_")
        self.start_urls = [f"https://en.wikipedia.org/wiki/{formatted_name}"]

    def parse(self, response):
        content_div = response.css("div#mw-content-text")
        paragraphs = content_div.css("p")
        full_text = []
        for para in paragraphs:
            text = "".join(para.xpath(".//text()").getall()).strip()
            if text:
                full_text.append(text)
        clean_text = re.sub(r"\[\d+\]", " ", " ".join(full_text)).replace("\n", " ")

        infobox_data = []
        infobox = response.css("table.infobox.vcard")
        for row in infobox.css("tr"):
            key = "".join(row.css("th *::text, th::text").getall()).strip()
            value = "".join(row.css("td *::text, td::text").getall()).strip()
            if key or value:
                infobox_data.append(f"{key}: {value}" if key else value)

        infobox_text = "\n".join(infobox_data)
        file_name = f"{self.person_name.replace(' ', '_')}_output.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            if infobox_text:
                f.write("### INFOBOX DATA ###\n")
                f.write(infobox_text + "\n\n")
            f.write("### ARTICLE TEXT ###\n")
            f.write(clean_text)
        self.log(f"✅ Written to file: {file_name}")

def run_scraper(person_name):
    process = CrawlerProcess(settings={"LOG_LEVEL": "ERROR"})
    process.crawl(WikiSpider, person_name=person_name)
    process.start()
