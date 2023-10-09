# Amazon Listing Script flow:
# Send mail with Subject as 'mapping start_time-end_time
# example  subject: 'mapping 21:00-04:00'
# add attachment in mail 



from emails import *
from playwright.sync_api import Playwright, sync_playwright, expect,TimeoutError
from datetime import datetime
import time
import schedule
from pyotp import *
import logging
from nanoid import generate
import re
import logging.config
import json
from requests import Session
import os
import yaml
from bs4 import BeautifulSoup
import csv
import pandas as pd
from sys import argv


with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

login = config['login']['amazon']
logging.basicConfig(
    level=logging.INFO,
    format='Amazon_Listing_%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt = "%Y-%m-%d_%H:%M:%S",
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(f'Amazon_Listing_{datetime.now().strftime("%Y-%m-%d")}.log',mode='a')
    ],
    )
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



totp = TOTP(login['secret'])

def get_cookies(cookies):
    dic = {}
    for cookie in cookies:
        dic[cookie['name']] = cookie['value']
    return dic

def list_orders(cookies):
    df = pd.read_csv('amazon_listing.csv')
    asins = [x for x in df['ASIN']]
    session = Session()
    session.cookies.update(cookies)
    skus = []
    for idx in range(len(asins)):
        payload = {
            'limit': '15',
            'offset': '0',
            'sort': 'ship_by_desc',
            'date-range': 'last-7',
            'q': f' {asins[idx]}',
            'qt': 'asin',
            'forceOrdersTableRefreshTrigger': 'false'
        }
        response = session.get('https://sellercentral.amazon.in/orders-api/search',params=payload)
        data = json.loads(response.text).get('orders')
        skus.append(df['SKUS'][idx]-len(data))
    return skus


def run_on(playwright: Playwright) -> None:
    logger.info(f"Mapping Automation started at {datetime.now()}")
    df = pd.read_csv('amazon_listing.csv')
    asins = [x for x in df['ASIN']]
    browser = playwright.chromium.launch(channel="chrome", headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto(login['url'])
    page.get_by_role("link", name="Log in").click()
    page.locator("#ap_email").fill(login['username'])
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill(login['password'])
    page.get_by_role("button", name="Sign in").click()
    page.get_by_label("Enter OTP:").click()
    token = totp.now()
    page.get_by_label("Enter OTP:").fill(token)
    page.get_by_role("button", name="Sign in").click()
    page.get_by_role("button", name="Select Account").click()
    page.get_by_role("button", name="Navigation menu").click()
    page.locator("#sc-navbar-container").get_by_text(
        "Orders Manage Orders Order Reports Upload Order Related Files Manage Returns Man").click()
    cookies = page.context.cookies()
    fn_cookies = get_cookies(cookies)
    page.get_by_role(
        "link", name="Manage SAFE-T Claims Add page to favourites bar").click()
    Is_Listed = []
    for idx in range(len(asins)):
        page = context.new_page()
        page.goto(f"https://sellercentral.amazon.in/abis/listing/syh/offer?asin={asins[idx]}&ref_=xx_myiadprd_cont_myimain#offer")
        time.sleep(5)
        if 'This product has other listing limitations.' in page.content():
            Is_Listed.append(False)
            logger.info(f"Listing Not Possible for ASIN : {asins[idx]}")
            page.close()
            continue
        soup = BeautifulSoup(page.content(),'lxml')
        price = soup.find('kat-link',{'class':'match-low-price'})
        if not price:
            logger.info("The product is new")
            Is_Listed.append(False)
            page.close()
            continue
        fn_price = re.search(r'\d+.\d+',price.get('label')).group()
        page.locator("a").filter(has_text="Match lowest price").click()
        if soup.find('kat-input',{'kat-aria-label':'HSN Code'}):
            page.get_by_label("HSN Code").fill(str(df['HSN'][idx]))
        page.get_by_label("Quantity").fill(str(df["SKUS"][idx]))
        page.get_by_label("Seller SKU").fill(f'MyCollection{generate(size=6)}')
        if soup.find('kat-input',{'kat-aria-label':'Maximum Retail Price'}):
            page.get_by_label("Maximum Retail Price").fill(fn_price)
        if soup.find('kat-input',{'kat-aria-label':'List Price'}):
            page.get_by_label("List Price").fill(fn_price)
        page.get_by_label("Country/Region Of Origin").fill("India")
        page.get_by_label("Seller SKU").fill(f'MyCollection{generate(size=6)}')
        # time.sleep(3)
        # page.get_by_role('button',name='Save and finish').click()
        Is_Listed.append(True)
        logger.info(f"Successfully mapped the product having ASIN {asins[idx]}")
        page.close()
    page.close()
    context.close()
    browser.close()
    df['Is_Listed'] = Is_Listed
    df.to_csv('amazon_listing.csv')
    logger.info("1st Part is Done. csv sheet updated please check.")


def run_off(playwright: Playwright) -> None:
    logger.info(f"Unmapping Automation started at {datetime.now()}")
    df = pd.read_csv('amazon_listing.csv')
    asins = [x for x in df['ASIN']]
    browser = playwright.chromium.launch(channel="chrome", headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto(login['url'])
    page.get_by_role("link", name="Log in").click()
    page.locator("#ap_email").fill(login['username'])
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill(login['password'])
    page.get_by_role("button", name="Sign in").click()
    page.get_by_label("Enter OTP:").click()
    token = totp.now()
    page.get_by_label("Enter OTP:").fill(token)
    page.get_by_role("button", name="Sign in").click()
    page.get_by_role("button", name="Select Account").click()
    page.get_by_role("button", name="Navigation menu").click()
    page.locator("#sc-navbar-container").get_by_text(
        "Orders Manage Orders Order Reports Upload Order Related Files Manage Returns Man").click()
    cookies = page.context.cookies()
    fn_cookies = get_cookies(cookies)
    page.get_by_role(
        "link", name="Manage SAFE-T Claims Add page to favourites bar").click()
    Listings = df['Is_Listed']
    for idx in range(len(Listings)):
        if Listings[idx]:
            page = context.new_page()
            page.goto(f'https://sellercentral.amazon.in/inventory/ref=xx_invmgr_dnav_xx?tbla_myitable=sort:{{"sortOrder":"DESCENDING","sortedColumnId":"date"}};search:{asins[idx]};pagination:1;')
            time.sleep(2)
            page.locator("#select").click()
            page.locator("#mt-select-all").click()
            page.locator("#a-autoid-2-announce").get_by_text("Action on 1 selected").click()
            # page.get_by_role('link',name="Delete products and listings").click()
            # time.sleep(5)
            logger.info(f"Successfully unmapped the product having ASIN {asins[idx]}")
        page.close()
    page.close()
    context.close()
    browser.close()
    logger.info("Unmapping is Done. csv sheet updation in progress.")
    df['Updated_SKUS'] = list_orders(fn_cookies)
    df.to_csv('amazon_listing.csv')
    logger.info("SKUS updation is Done")
    

def main2():
    with sync_playwright() as playwright:
        run_off(playwright)

def main1():
    with sync_playwright() as playwright:
        run_on(playwright)



def call_recursion(freq):
    cnt=0
    while(cnt<freq):
        main1()
        logger.info("Given Sleep time of 30 minutes after Mapping Task")
        time.sleep(map_time*60)
        logger.info("Given Sleep time of 30 minutes after UnMapping Task")
        main2()
        cnt+=1
        time.sleep(down_time*60)
        if abs((end_hour)-(datetime.now().hour)) in [0,1]:
            logger.info(f"Reached Peak time")
            break
    send_mail('amazon_listing.csv')
    logger.info("Updated Sheet Sent and Program Successfully Completed.")




if __name__=="__main__":
    logger.info(f"script started at {datetime.now()}")
    _, msge = get_sheet_and_timings('mapping')
    soup_ = BeautifulSoup(msge.html,'lxml')
    timings = [x.text.strip() for x in soup_.find_all('div',{'dir':None})]
    orc_time = [x.strip() for x in timings[0].split(' ') if x.strip()!=''][-1]
    map_time = [x.strip() for x in timings[1].split(' ') if x.strip()!=''][-1]
    down_time =  [x.strip() for x in timings[2].split(' ') if x.strip()!=''][-1]
    freq =  [x.strip() for x in timings[3].split(' ') if x.strip()!=''][-1] if len(timings)==4 else 20
    start_time,end_time = orc_time.split('-')
    start_hour, start_minute = [int(x) for x in start_time.split(':')]
    end_hour, end_minute =  [int(x) for x in end_time.split(':')]
    if (datetime.now().hour>=start_hour) and (datetime.now().minute>=start_minute):
        logger.info(f"Function Started")
        call_recursion(freq)
    else:
        slp_time = ((start_hour-(datetime.now().hour))*60*60) + ((start_minute-(datetime.now().minute))*60)
        logger.info(f"Given sleep time of {slp_time} seconds.")
        time.sleep(slp_time)
        call_recursion(freq)

    
