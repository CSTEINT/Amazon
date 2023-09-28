from playwright.sync_api import sync_playwright
import logging
import os
from drive import *
import pandas as pd
import time
import yaml
from datetime import datetime
from requests import Session
from bs4 import BeautifulSoup
import json


with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
login = config['login']['flipkart']


logging.basicConfig(
    level=logging.INFO,
    format='flipkart_claims_ %(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt="%Y-%m-%d_%H:%M:%S",
    handlers=[
        logging.FileHandler(f"flipkart_cliams.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)    



def main_playwright():
    with sync_playwright() as page:
        browser = page.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(login['url'])
        page.get_by_role("button", name="Login").click()
        page.get_by_placeholder("Username or phone number or email").click()
        page.get_by_placeholder("Username or phone number or email").fill(login['username'])
        page.get_by_placeholder("Username or phone number or email").press("Enter")
        page.get_by_placeholder("Enter password").click()
        page.get_by_placeholder("Enter password").fill(login['password'])
        page.get_by_role("button", name="Login").first.click()
        page.get_by_text("CSTE INTERNATIONAL").click()
        page.get_by_test_id("button").click()
        time.sleep(10)
        for idx in range(len(order_ids))[::-1]:
            if order_ids[idx] in claimed_lst:
                logger.info(f"claim already applied for the order_id : {order_ids[idx]}")
                continue
            url = 'https://seller.flipkart.com/index.html\#dashboard/payments/spf'
            page.goto(url)
            time.sleep(2)
            page.locator(".joyride-spotlight").click()
            page.get_by_test_id("create-new-claim-btn").click()
            page.locator(".joyride-spotlight").click()
            page.get_by_test_id("test-input").fill(str(order_ids[idx]))
            page.get_by_test_id("search-icon").click()
            time.sleep(3)
            if str(page.content()).count(str(order_ids[idx]))<=1:
                continue
            page.get_by_test_id(f"order-card-title-{order_ids[idx]}").click()
            page.get_by_text("Select the Issue Area").click()
            page.get_by_role("button", name=df['Issue_Area'][idx]).click()
            page.get_by_text("Select the Issue Type").click()
            page.get_by_role("button", name=df['Issue_Type'][idx]).click()
            ids = ["#claim-form-shipping-label-uploader","#claim-form-photo-proof-0","#claim-form-photo-proof-1","#claim-form-photo-proof-2"]
            ls = ["label","damaged","damaged","damaged"]
            for each in range(4):
                for file in os.listdir('flipkart_claims')[each:each+1]:
                    if f'{ls[each]}_{order_ids[idx]}' in file:
                        page.locator(ids[each]).set_input_files('\\'.join([str(os.getcwd()),'flipkart_claims',file]))
                        time.sleep(2)
            page.get_by_test_id("claim-form-description").click()
            page.get_by_test_id("claim-form-description").fill(df['Claim_Description'][idx])
            time.sleep(10)
            page.get_by_test_id("claim-form-submit-claim-btn").click()
            claimed_lst.append(order_ids[idx])
            logger.info(f"Successffuly Applied for the Claim for the order_id: {order_ids[idx]}")
        page.close()
        # ---------------------
        context.close()
        browser.close()



if __name__=="__main__":
    logger.info(f"script started at {datetime.now()}")
    if not os.path.exists("flipkart_claims"):
        os.makedirs("flipkart_claims")
    dowloaded = os.listdir('flipkart_claims')
    opt = [login['drive_link']]
    main(opt, dowloaded)
    df = pd.read_csv('flipkart_claims//return_claims_flipkart.csv')
    order_ids = [x for x in df['Order_Id']]
    df1 = pd.read_csv('claimed_list_flipkart.csv')
    claimed_lst = [x for x in df1['Order_Id']]
    main_playwright()
    df1 = pd.DataFrame({'Order_Id': claimed_lst})
    df1.to_csv('claimed_list_flipkart.csv')
    logger.info(f"csv sheet succefully updated")
    logger.info(f"script ended at {datetime.now()}")