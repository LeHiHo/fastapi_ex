from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator
import requests
from bs4 import BeautifulSoup

router = APIRouter(prefix="/api/bs")


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


def fetch_html(url):
    response = requests.get(url)
    return response.text


def parse_html(html, find_all_args, name_args, price_args, img_args):
    soup = BeautifulSoup(html, 'html.parser')
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


@router.get("/")
async def search(query: ProductQuery = Depends()):
    keyword = query.keyword
    coupang_url = f"https://www.coupang.com/np/search?component=&q={keyword}"
    aliExpress_url = f"https://ko.aliexpress.com/w/wholesale-{keyword}.html"

    coupang_html = fetch_html(coupang_url)
    aliExpress_html = fetch_html(aliExpress_url)

    coupang_products = parse_html(coupang_html, ['li', {'class': 'search-product'}], ['div', {'class': 'name'}],
                                  ['strong', {'class': 'price-value'}], ['img', {'class': 'search-product-wrap-img'}])
    aliExpress_products = parse_html(aliExpress_html, ['div', {'class': 'list-item'}], ['span', {'class': 'title'}],
                                     ['span', {'class': 'price'}], ['img'])

    return {'coupang': coupang_products, 'aliExpress': aliExpress_products}
