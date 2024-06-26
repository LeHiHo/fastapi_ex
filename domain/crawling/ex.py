from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator
import threading
import time
from bs4 import BeautifulSoup

router = APIRouter(prefix="/api/products")

class ProductQuery(BaseModel):
    keyword: str

    @validator('keyword')
    def validate_keyword(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9\s\uAC00-\uD7A3]+$', v):
            raise ValueError('Keyword must only contain letters, numbers, spaces, and Korean characters')
        if len(v) > 50:
            raise ValueError('Keyword must be under 50 characters')
        return v

def setup_driver():
    options = Options()
    options.headless = True
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36")
    service = Service(executable_path='/path/to/chromedriver')  # chromedriver 경로 설정
    driver = webdriver.Chrome(service=service, options=options)
    # DevTools Protocol 사용
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.navigator.chrome = {runtime: {}};
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """
    })
    return driver

def crawl_site(driver, url, find_all_args, name_args, price_args, img_args):
    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    products = []
    for item in soup.find_all(*find_all_args):
        name = item.find(*name_args)
        price = item.find(*price_args)
        img = item.find(*img_args)
        if name and price and img:
            img_url = img['src']
            if not img_url.startswith(('http:', 'https:')):
                img_url = 'https:' + img_url
            products.append({
                'title': name.text.strip(),
                'price': price.text.strip(),
                'image_url': img_url
            })
    driver.quit()
    return products

def run_selenium(keyword):
    driver = setup_driver()
    temu_url = f"https://www.temu.com/kr"
    temu_products = crawl_site(driver, temu_url, ['div', {'class': '_6q6qVUF5 _1QhQr8pq _1ak1dai3 _3AbcHYoU'}], ['h2', {'class': '_2BvQbnbN'}], ['div', {'class': 'LiwdOzUs'}], ['img'])
    return {'temu': temu_products}

@router.get("/")
async def search(query: ProductQuery = Depends()):
    product_data = run_in_thread(run_selenium, query.keyword)
    return product_data

def run_in_thread(func, *args):
    result_holder = []
    def run():
        result = func(*args)
        if result is not None:
            result_holder.append(result)
        else:
            print("No data returned from the function.")
    thread = threading.Thread(target=run)
    thread.start()
    thread.join()
    if result_holder:
        return result_holder[0]
    else:
        return "No results available"