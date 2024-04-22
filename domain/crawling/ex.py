import threading
import time
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

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
    # options.add_argument("--headless")
    # service = Service(GeckoDriverManager().install()) # github api 한도초과남
    # return webdriver.Chrome(service=service, options=options)


    return webdriver.Firefox(options=options)


def crawl_site(driver, url, find_all_args, name_args, price_args):
    driver.get(url)
    time.sleep(5) 
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    products = []
    for item in soup.find_all(*find_all_args):
        name = item.find(*name_args)
        price = item.find(*price_args)
        if name and price:
            products.append({'title': name.text.strip(), 'price': price.text.strip()})
    return products

# def crawl_site(driver, url, find_all_args, name_args, price_container_args, price_parts_args):
#     driver.get(url)
#     time.sleep(5)  # 페이지 로드 대기
#     soup = BeautifulSoup(driver.page_source, 'html.parser')
#     products = []
#     for item in soup.find_all(*find_all_args):
#         name = item.find(*name_args).text.strip() if item.find(*name_args) else "No name found"
#         price_container = item.find(*price_container_args)
#         if price_container:
#             price_parts = price_container.find_all(*price_parts_args)
#             price = ''.join(part.text.strip() for part in price_parts)
#         else:
#             price = "No price found"
#         products.append({'title': name, 'price': price})
#     return products

def run_selenium(keyword):
    driver = setup_driver()
    try:
        coupang_url = f"https://www.coupang.com/np/search?component=&q={keyword}"        
        aliExpress_url = f"https://ko.aliexpress.com/w/wholesale-{keyword}.html?spm=a2g0o.productlist.search.0"
        temu_url = f"https://www.temu.com/search_result.html?search_key={keyword}&search_method=user&refer_page_el_sn=200010&srch_enter_source=top_search_entrance_10005&_x_sessn_id=gb14fi35xs&refer_page_name=home&refer_page_id=10005_1713717575011_mqlwi0ykgm&refer_page_sn=10005"
        # amazon_url = f"https://www.amazon.com/s?k={keyword}&crid=27U3YQOWZ2RCZ&sprefix=us%2Caps%2C275&ref=nb_sb_noss_2"
        # never_url = f""

        coupang_products = crawl_site(driver, coupang_url, ['div', {'class': 'descriptions-inner'}], ['div', {'class': 'name'}], ['strong', {'class': 'price-value'}])
        aliExpress_products = crawl_site(driver, aliExpress_url, ['div', {'class': 'multi--content--11nFIBL'}], ['div', {'class': 'multi--title--G7dOCj3'}], ['div', {'class': 'multi--price-sale--U-S0jtj'}])        
        # temu_products = crawl_site(driver,temu_url, ['div', {'class': '_6q6qVUF5 _1QhQr8pq _1ak1dai3 _3AbcHYoU'}], ['h2', {'class': '_2BvQbnbN'}], ['div', {'class': 'LiwdOzUs'}])

        # amazon_products = crawl_site(driver, amazon_url, ['div', {'data-component-type': 's-search-result'}], ['h2'], ['span', 'a-price'])
        # never_product = 

    finally:
        driver.quit()
    return {'coupang':coupang_products, 'ali':aliExpress_products}

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
