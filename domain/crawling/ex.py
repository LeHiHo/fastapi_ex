from pydantic import BaseModel
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup


from fastapi import APIRouter, Query

router = APIRouter(
    prefix="/api",
)

def run_selenium(keyword):
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(f"https://www.coupang.com/np/search?component=&q={keyword}&channel=user")
        time.sleep(5)
        source = driver.page_source
        soup = BeautifulSoup(source, 'html.parser')
        products = []
        for item in soup.find_all('div', class_='descriptions-inner'):
            name = item.find('div', class_='name')
            price = item.find('strong', class_='price-value')
            if name and price:  # 제품명과 가격 정보가 있을 경우에만 추가
                products.append({'title': name.text.strip(), 'price': price.text.strip()})
        return products
    except Exception as e:
        print(f"An error occurred: {e}")  # 오류 출력
        return []  # 예외 발생 시 빈 리스트 반환
    finally:
        driver.quit()

@router.get("/fruits")
async def crawl_fruits(keyword: str = Query(..., description="Search keyword for fruits")):
    product_data = run_in_thread(run_selenium, keyword)
    return product_data

def run_in_thread(func, *args):
    result_holder = []

    def run():
        result = func(*args)  # 함수에 인수 전달
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
        return "No results available"  # 결과가 없을 경우의 처리

