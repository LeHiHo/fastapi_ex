import threading
import time
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.chrome.options import Options


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
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    return webdriver.Firefox(options=options)


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
    return products

def run_selenium(keyword):
    driver = setup_driver()
    try:
        coupang_url = f"https://www.coupang.com/np/search?component=&q={keyword}"
        aliExpress_url = f"https://ko.aliexpress.com/w/wholesale-{keyword}.html"
        amazon_url = f"https://www.amazon.com/s?k={keyword}"
        # temu_url = f"https://www.google.com/search?q=site:temu.com+{keyword}84&sca_esv=45843383d781bdbb&rlz=1C5MACD_enKR1067KR1067&biw=1920&bih=934&udm=2&prmd=sivnbmz&sxsrf=ACQVn08jK64eyvGkZ0z3HzYkKbJ92UZOZw:1713965431454&source=lnms&ved=1t:200715&ictx=111"


        coupang_products = crawl_site(driver, coupang_url, ['li', {'class': 'search-product'}], ['div', {'class': 'name'}], ['strong', {'class': 'price-value'}],['img',{'class':'search-product-wrap-img'}])
        aliExpress_products = crawl_site(driver, aliExpress_url, ['div', {'class': 'list--gallery--C2f2tvm search-item-card-wrapper-gallery'}], ['h3', {'class': 'multi--titleText--nXeOvyr'}], ['div', {'class': 'multi--price-sale--U-S0jtj'}], ['img',{'class':'images--item--3XZa6xf'}])
        amazon_products = crawl_site(driver, amazon_url, ['div', {'data-component-type': 's-search-result'}], ['h2'], ['span', {'class':'a-offscreen'}],['img',{'class':'s-image'}])

        # temu_products = crawl_site(driver,temu_url, ['div', {'class': '_6q6qVUF5 _1QhQr8pq _1ak1dai3 _3AbcHYoU'}], ['h2', {'class': '_2BvQbnbN'}], ['div', {'class': 'LiwdOzUs'}])


    finally:
        driver.quit()

    return {'coupang': coupang_products, 'ali': aliExpress_products, 'amazon': amazon_products}



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