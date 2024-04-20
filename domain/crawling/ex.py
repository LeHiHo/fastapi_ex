import threading
import time
from bs4 import BeautifulSoup

from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator

from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager



router = APIRouter(
    prefix="/api/products",
)

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

def run_selenium(keyword):
    options = Options()
    # options.headless = True
    options.add_argument("window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36")    
    options.add_argument("--disable-gpu")  
    options.add_argument("--headless")
    options.add_argument("--start-maximized")

    # service = Service(ChromeDriverManager().install())
    # driver = webdriver.Chrome(service=service, options=options)

    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)


    

    try:
        driver.get(f"https://www.coupang.com/np/search?component=&q={keyword}&channel=user")
        time.sleep(5)
        source = driver.page_source
        soup = BeautifulSoup(source, 'html.parser')
        products = []
        for item in soup.find_all('div', class_='descriptions-inner'):
            name = item.find('div', class_='name')
            price = item.find('strong', class_='price-value')
            if name and price:
                products.append({'title': name.text.strip(), 'price': price.text.strip()})
        return products
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        driver.quit()

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