# vaibhavthakurcste@outlook.com
# OyjeWQ!t!&Y4lw#5

# henull.com

import pandas as pd
import csv
import yaml
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from asyncio import run, sleep
import json
from datetime import datetime
import time
from requests import Session
import logging


with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

login = config['helium_login']
logging.basicConfig(
    level=logging.INFO,
    format='Amazon_Adva_Search_%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt = "%Y-%m-%d_%H:%M:%S",
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(f'amazon_adva_search_{datetime.now().strftime("%Y-%m-%d")}.log',mode='a')
    ],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_cookies(cookies):
    dic = {}
    for cookie in cookies:
        dic[cookie['name']] = cookie['value']
    return dic



def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto('https://www.henull.com/auth/login')
        page.type('//input[@type="email"]',login['username'],timeout=30000)
        page.type('//input[@type="password"]',login['password'],timeout=30000)
        page.click('//button[@type="submit"]',timeout=30000)
        time.sleep(20)
        page.click('//a[@href="/tools"]',timeout=30000)
        page.click("text=Browser", timeout=30000)
        page.wait_for_load_state('networkidle')
        time.sleep(20)
        cookies = page.context.cookies()
        page.close()
        context.close()
        browser.close()
        return cookies


def main():
    logger.info(f"Automation Started at {datetime.now()}")
    logger.info(f"Playwright Started at {datetime.now()}")
    cookies = run()
    logger.info(f"Playwright ended at {datetime.now()} and Cookies Saved.")
    session = Session()
    cook = get_cookies(cookies)
    session.headers.update({
        'authority': 'ljrhjhnk.realnull.com',
        'accept': 'application/json',
        'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': 'Bearer 53616c7465645f5f6f1d0a6c25ee206f6d44c51185811ad7d2771996a02ebedcc5ee60a7b9dab0a42ad432051c3626ba62009a3deecd65899cfc516de3ae43ecb0a0e1010829f4e2b075f7228cc8852c6a97fb211b3463a0f26f06471a88b1d87fc9bb06453776cedc427daad376b82f6a65e6a88bb023c4d9e12c2ba6b0dfc7a897d22f90c98b3df6cc3969bcef75a3',
        'content-type': 'application/json',
        'origin': 'https://ljrhjhng.realnull.com',
        'referer': 'https://ljrhjhng.realnull.com/',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    })
    session.cookies.update(cook)
    logger.info(f"Cookies Uploaded to Session")
    for each in lst:
        params = {
            'accountId': '1545764501',
        }
        logger.info(f"Getting Data for Cat: {each.get('category')}")
        json_data = {
            'filters': {
                'titleIncludeKeyword': each.get('titleIncludeKeyword'),
                'category': [
                    each.get('category'),
                ],
                'salesRankFrom': each.get('salesRankFrom'),
                'salesRankTo': each.get('salesRankTo'),
                'priceFrom': each.get('priceFrom'),
                'priceTo': each.get('priceTo'),
                'monthlySalesFrom': each.get('monthlySalesFrom'),
                'monthlySalesTo': each.get('monthlySalesTo'),
                'numberOfSellersFrom': each.get('numberOfSellersFrom'),
                'reviewsRatingFrom': each.get('reviewsRatingFrom'),
                'reviewsRatingTo': each.get('reviewsRatingTo'),
                'monthlyRevenueFrom': each.get('monthlyRevenueFrom'),
                'monthlyRevenueTo': each.get('monthlyRevenueTo'),
                'ageFrom': each.get('ageFrom'),
                'ageTo': each.get('ageTo'),
                'reviewsRatingFrom': each.get('reviewsRatingFrom'),
                'reviewsRatingTo': each.get('reviewsRatingTo'),
                'numberOfSellersFrom': each.get('numberOfSellersFrom'),
                'numberOfSellersTo': each.get('numberOfSellersTo'),
            },
            'marketplaceId': 9,
            'filtersType': 'advanced',
        }
        response = session.post(
            'https://ljrhjhnk.realnull.com/api/blackbox/v1/search/products',
            params=params,
            json=json_data,
        )
        id = json.loads(response.text).get('data').get('id')
        params = {
            'accountId': '1546047433',
            'sort': '-monthlySales',
        }
        final_response = session.get(
            f'https://ljrhjhnk.realnull.com/api/blackbox/v1/search/products/{id}/export',
            params=params,
        ) 
        if final_response.status_code==200:
            final_data = json.loads(final_response.text).get('data')
            df =pd.DataFrame(final_data)
            df.to_csv(f'{datetime.now().strftime("%Y-%m-%d")}_report_{each.get("category")}.csv')
            logger.info("Data Saved and Stored in Csv File")
        else:
            logger.info("Sheet Not Available.")
    logger.info(f"Automation Ended at {datetime.now()}")

if __name__=="__main__":
    with open('analysis.csv','r') as file:
        lst = list(csv.DictReader(file))
    main()