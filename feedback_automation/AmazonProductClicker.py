from lxml import html
from playwright.sync_api import Playwright, sync_playwright, expect, TimeoutError
from datetime import datetime
import time
from undetected_playwright import stealth_sync
import schedule
from pyotp import *
import logging
from multiprocessing import Pool
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
import gspread
import socket
import pytz
from zoneinfo import ZoneInfo
import requests
import json

def getIP():
    endpoint = 'https://ipinfo.io/json'
    response = requests.get(endpoint, verify = True)

    if response.status_code != 200:
        return 'Status:', response.status_code, 'Problem with the request. Exiting.'
        exit()

    data = response.json()

    return data['ip']


def get_local_ip():
    """Get the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


#Google Sheet
sa=gspread.service_account(filename="GoogleTest.json")
WorkBook=sa.open_by_url("")
LogSheet=WorkBook.get_worksheet(0)
KeywordSheet=WorkBook.get_worksheet(1)
RawLogSheet=WorkBook.get_worksheet(2)

log_file = f'Amazon_AdClicker.log'
with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

login = config['login']['amazon']
logging.basicConfig(
    level=logging.INFO,
    format='Amazon_Ad_Clicker_%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt="%Y-%m-%d_%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, mode='a')
    ],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def loop(data):
    temp_tar_spon = []
    temp_our_pro = []
    temp_tar_pro = []
    tree = html.fromstring(data)
    spon_lst = []
    prod_lst = []
    all_prod_pages = tree.xpath(
        '//a[@class="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"]/@href')
    spon_lst = tree.xpath(
        '//a[@class="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"]/span/text()')
    final_pair = []
    for i in range(len(spon_lst)):
        final_pair.append({'owner': spon_lst[i], 'url': ''.join(
            ['https://www.amazon.in', all_prod_pages[i]])})
    for each in final_pair:
        if ('spc=' in each['url']):
            if ('fusked' in each['owner'].lower()) or ('caaju' in each['owner'].lower()):
                logger.info(f"Our Product Listed as Sponsored Product: {each['owner']}")
            else:
                temp_tar_spon.append(each)
        else:
            if ('fusked' in each['owner'].lower()) or ('caaju' in each['owner'].lower()):
                temp_our_pro.append(each)
            else:
                temp_tar_pro.append(each)
    return temp_tar_spon, temp_tar_pro, temp_our_pro


def run(playwright: Playwright, lst):
    browser = playwright.chromium.launch(channel="chrome", headless=True, proxy={
        'server': login['p_server'],
        'username': login['p_username'],
        'password': login['p_password'],
    })
    context = browser.new_context()
    stealth_sync(context)
    page = context.new_page()
    try:
        page.goto(login['proxy_url'], timeout=10000)
    except TimeoutError:
        page.close()
        browser.close()
        return run(playwright, lst)
    time.sleep(5)
    # page.goto("https://www.iplocation.net")
    # IPAddress=page.locator("/html/body/div/div[1]/div[2]/div/div[1]/div[4]/div[2]/div/div/div[2]/div[1]/div[1]/p/strong/span").textContent()
    # print(IPAddress)
    page.goto('https://www.amazon.in')
    if 'Enter the characters you see below' in page.content():
        time.sleep(20)
        page.close()
        browser.close()
        return run(playwright, lst)
    for phrase in lst:
        tar_spon = []
        tar_pro = []
        our_pro = []
        page.get_by_placeholder("Search Amazon.in").fill(phrase)
        page.get_by_placeholder("Search Amazon.in").press(
            "Enter", timeout=60000)
        page.wait_for_selector('.s-pagination-strip', timeout=6000)
        time.sleep(10)
        tree = html.fromstring(page.content())
        data = page.content()
        s1, p1, o1 = loop(data)
        tar_spon += s1
        tar_pro += p1
        our_pro += o1
        for idx in range(2):
            page.get_by_text("Next", exact=True).click()
            page.wait_for_selector('.s-pagination-strip')
            time.sleep(3)
            data = page.content()
            s1, p1, o1 = loop(data)
            tar_spon += s1
            tar_pro += p1
            our_pro += o1
        GoogleSheetTemporaryLog=[]
        GoogleSheetPermanentLog=[]
        logger.info(f"We have obtained {len(tar_spon)} sponsored items.")
        for each in tar_spon:
            page.goto(each['url'], timeout=600000)
            TimeStamp=datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime(r"%Y/%m/%d %H:%M:%S")
            logger.info(f"Clicked to Ad Sponsored by {each['owner']} at timestamp {TimeStamp}")
            GoogleSheetTemporaryLog.append([f"Clicked to Ad Sponsored by {each['owner']} at timestamp {TimeStamp}"])
            GoogleSheetPermanentLog.append([TimeStamp,each["owner"],each["url"],phrase,"Sponsored"])   
        RawLogSheet.append_rows(GoogleSheetTemporaryLog)
        LogSheet.append_rows(GoogleSheetPermanentLog)
        GoogleSheetTemporaryLog=[]
        GoogleSheetPermanentLog=[]
        try:
            for each in random.choices(our_pro,k=2):
                page.goto(each['url'], timeout=60000)
                TimeStamp=datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime("%Y/%m/%d %H:%M:%S")
                logger.info(f"Clicked to our products at timestamp {TimeStamp}")
                GoogleSheetTemporaryLog.append([f"Clicked to our products at timestamp {TimeStamp}"])
                GoogleSheetPermanentLog.append([TimeStamp,each["owner"],each["url"],phrase,"Self"])
        except IndexError:
            continue
        RawLogSheet.append_rows(GoogleSheetTemporaryLog)
        LogSheet.append_rows(GoogleSheetPermanentLog)
        GoogleSheetTemporaryLog=[]
        GoogleSheetPermanentLog=[]
        for each in tar_pro[:random.randint(1,3)]:
            page.goto(each['url'], timeout=60000)
            TimeStamp=datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime("%Y/%m/%d %H:%M:%S")
            logger.info(f"Clicked to competitors products at timestamp {TimeStamp}")
            GoogleSheetTemporaryLog.append([f"Clicked to competitors products at timestamp {TimeStamp}"])
            GoogleSheetPermanentLog.append([TimeStamp,each["owner"],each["url"],phrase,"Random"])
        RawLogSheet.append_rows(GoogleSheetTemporaryLog)
        LogSheet.append_rows(GoogleSheetPermanentLog)
    page.close()
    browser.close()
    return True


def re_main(val):
    while(True):
        try:
            logger.info(f"Automation Started at {datetime.now(tz=ZoneInfo('Asia/Kolkata'))}")
            df = pd.DataFrame(KeywordSheet.get_all_records())
            lst = [x for x in df['phrases']]
            print(lst)
            with sync_playwright() as playwright:
                run(playwright, lst)
            logger.info(f"Automation ended at {datetime.now(tz=ZoneInfo('Asia/Kolkata'))}")
            time.sleep(random.randint(60,120))
        except KeyboardInterrupt:
            break
        except:
            pass


if __name__ == "__main__":
    with Pool(2) as p:
        p.map(re_main, range(2))
