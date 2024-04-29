import threading
import time
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fastapi import APIRouter, Depends
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from pydantic import BaseModel, validator
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
    options.add_argument("--disable-gpu")
    driver = webdriver.Firefox(options=options)
    driver.implicitly_wait(10)
    return driver

def crawl_site(driver, url, find_all_args, name_args, price_args, img_args):
    driver.get(url)
    products = []
    while True:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, find_all_args[1]['class'])))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
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

        try:
            next_button = driver.find_element_by_css_selector("a.next-link-selector")
            if next_button:
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(5)
            else:
                break
        except NoSuchElementException:
            break
    return products

def run_selenium(keyword):
    driver = setup_driver()
    try:
        aliExpress_url = f"https://ko.aliexpress.com/w/wholesale-{keyword}.html?spm=a2g0o.productlist.search.0"
        aliExpress_products = crawl_site(driver, aliExpress_url, ['div', {'class': 'list--gallery--C2f2tvm search-item-card-wrapper-gallery'}], ['h3', {'class': 'multi--titleText--nXeOvyr'}], ['div', {'class': 'multi--price-sale--U-S0jtj'}], ['img',{'class':'images--item--3XZa6xf'}])
    finally:
        driver.quit()
    return {'Ali': aliExpress_products}

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
