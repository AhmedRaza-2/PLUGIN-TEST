from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

visited = set()

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")
    return webdriver.Chrome(options=chrome_options)

def is_valid(url, base_domain):
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and base_domain in parsed.netloc

def extract_links(driver, base_url, base_domain):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = urljoin(base_url, a_tag["href"])
        href = href.split("#")[0].rstrip("/")
        if is_valid(href, base_domain):
            links.add(href)
    return links

def extract_visible_text(driver):
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        return body.text
    except:
        return ""

def crawl_site(start_url, max_pages=30):
    driver = setup_driver()
    base_domain = urlparse(start_url).netloc
    to_visit = [start_url]
    all_text = {}

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        print(f"[+] Visiting: {url}")
        try:
            driver.get(url)
            time.sleep(2)

            text = extract_visible_text(driver)
            all_text[url] = text
            visited.add(url)

            links = extract_links(driver, url, base_domain)
            to_visit.extend(link for link in links if link not in visited and link not in to_visit)

        except Exception as e:
            print(f"[-] Failed to load {url}: {e}")
            continue

    driver.quit()
    return all_text

if __name__ == "__main__":
    start_url = input("Enter full website URL (e.g. https://example.com): ").strip()
    all_text = crawl_site(start_url, max_pages=30)  # Increase if needed

    domain = urlparse(start_url).netloc.replace('.', '_')
    out_file = f"{domain}_full_website_text.txt"

    with open(out_file, "w", encoding="utf-8") as f:
        for url, text in all_text.items():
            f.write(f"URL: {url}\n{'=' * 80}\n{text}\n\n\n")

    print(f"\n[✓] Extracted text from {len(all_text)} pages.")
    print(f"[✓] Saved to: {out_file}")
