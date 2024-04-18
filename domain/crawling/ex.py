from pydantic import BaseModel
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup

from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/crawl",
)

def run_selenium():
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://www.coupang.com/np/search?component=&q=과일&channel=user")
        time.sleep(5)
        source = driver.page_source
        soup = BeautifulSoup(source, 'html.parser')
        products = []
        for item in soup.find_all('div', class_='descriptions-inner'):
            title = item.find('div', class_='name').text.strip()
            price = item.find('strong', class_='price-value').text.strip()
            products.append({'title': title, 'price': price})
        return products
    finally:
        driver.quit()

@router.get("/fruits")
async def crawl_fruits():
    product_data = run_in_thread(run_selenium)
    return product_data

def run_in_thread(func):
    result_holder = []

    def run():
        result_holder.append(func())

    thread = threading.Thread(target=run)
    thread.start()
    thread.join()
    return result_holder[0]

