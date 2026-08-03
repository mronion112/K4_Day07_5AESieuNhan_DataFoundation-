from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    page.goto("https://help.shopee.vn/portal/4/article/79465-%5BTr%E1%BA%A3-h%C3%A0ng%2F-Ho%C3%A0n-ti%E1%BB%81n%5D-S%E1%BA%A3n-ph%E1%BA%A9m-h%E1%BA%A1n-ch%E1%BA%BF-tr%E1%BA%A3-h%C3%A0ng-l%C3%A0-g%C3%AC?previousPage=secondary%20category", wait_until="networkidle")

    data = page.evaluate("window.FORGE_SSR_DATA_MAP")

    article = data["4"]          # hoặc data["6"]
    title = article["title"]
    content_html = article["content"]

    # print(title)
    # print(content_html)

    browser.close()
    soup = BeautifulSoup(content_html, "html.parser")

    text = soup.get_text("\n", strip=True)

    print(text)



