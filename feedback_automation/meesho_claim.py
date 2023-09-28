from playwright.sync_api import Playwright, sync_playwright, expect
from datetime import datetime
from drive import *
import time
import logging
import logging.config
import json
import requests
import os
import yaml
import csv
import pandas as pd

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

login = config['login']['meesho']
log_config = config['claim']['logging']['meesho']
logging.config.dictConfig(log_config)
logger = logging.getLogger(__name__)


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(channel="chrome", headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(login['url'])
    page.get_by_label("Email Id or mobile number").fill(login['username'])
    page.get_by_label("Password").fill(login['password'])
    page.get_by_role("button", name="Log in").click()
    page.wait_for_load_state('networkidle')
    ids= ['#product_image_link_6','#product_reverse_way_bill_link_7','#product_openingvideo_link_8']
    ls = ["product","reverse_bill",'openingvideo']
    time.sleep(5)
    for idx in range(len(order_ids)):
        if order_ids[idx] not in claimed_lst:
            page.goto("https://supplier.meesho.com/panel/v3/new/payouts/wbixy/support/1/3/create")
            for each in range(3):
                for file in os.listdir('meesho_claims'):
                    if f'{ls[each]}_{order_ids[idx]}' in file:
                        page.locator(ids[each]).set_input_files('\\'.join([str(os.getcwd()),'meesho_claims',file]))
            page.wait_for_selector('#mui-6')
            page.click('//*[@id="mainWrapper"]/div/div/div/form/div[1]/div[3]/div/div')
            page.click('text=Intact')
            page.locator("//textarea[@placeholder='']").fill(df['Comments'][idx])
            time.sleep(3)
            page.get_by_placeholder("Packet ID").click()
            page.get_by_placeholder("Packet ID").fill(str(df['Packet_ID'][idx]))
            time.sleep(3)
            page.get_by_placeholder("Sub Order Number").click()
            page.get_by_placeholder("Sub Order Number").fill(str(order_ids[idx]))
            page.click('//*[@id="mainWrapper"]/div/div/div/form/div[3]/div/button[1]/span')
            time.sleep(10)
            claimed_lst.append(order_ids[idx])
            logger.info(f"Successffuly Claimed for the order_id : {order_ids[idx]}")
    # ---------------------
    page.close()
    context.close()
    browser.close()


if __name__=="__main__":
    logger.info(f"script started at {datetime.now()}")
    if not os.path.exists("meesho_claims"):
        os.makedirs("meesho_claims")
    dowloaded = os.listdir('meesho_claims')
    opt = [login['drive_link']]
    main(opt, dowloaded)
    df = pd.read_csv('meesho_claims//return_claims_meesho.csv')
    order_ids = [x for x in df['Order_Id']]
    df1 = pd.read_csv('claimed_list_meesho.csv')
    claimed_lst = [x for x in df1['Order_Id']]
    with sync_playwright() as playwright:
        run(playwright)
    df1 = pd.DataFrame({'Order_Id': claimed_lst})
    df1.to_csv('claimed_list_meesho.csv')
    logger.info(f"csv sheet succefully updated")
    logger.info(f"script ended at {datetime.now()}")