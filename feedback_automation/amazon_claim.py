#
# Amazon Claim Automation
#
# Execution : python amazon_claim.py
#
#

from playwright.sync_api import Playwright, sync_playwright, expect
from datetime import datetime
from drive import *
import time
from pyotp import *
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

login = config['login']['amazon']
log_config = config['claim']['logging']['amazon']
logging.config.dictConfig(log_config)
logger = logging.getLogger(__name__)

totp = TOTP(login['secret'])


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(channel="chrome", headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto(login['url'])
    page.get_by_role("link", name="Log in").click()
    page.get_by_label("Email or mobile phone number").click(
        modifiers=["Control"])
    page.get_by_label("Email or mobile phone number").fill(login['username'])
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
    page.get_by_role(
        "link", name="Manage SAFE-T Claims Add page to favourites bar").click()
    for idx in range(len(order_ids)):
        if order_ids[idx] in claimed_lst:
            logger.info(f"claim already applied for the order_id : {order_ids[idx]}")
            continue
        page = context.new_page()
        # acknowledgementCheckBox
        page.goto(f'https://sellercentral.amazon.in/safet-claims/create?orderId={order_ids[idx]}')
        page.locator("#a-autoid-1-announce").click()
        page.get_by_label(df['Claim Reason'][idx]).get_by_text(
            df['Claim Reason'][idx]).click()
        cwd_dir1 = '\\'.join([str(os.getcwd()), 'img1.jpg'])
        cwd_dir2 = '\\'.join([str(os.getcwd()), 'img2.jpg'])
        ids = ['#CONTENT_PHOTO_fileInput',
               '#PACKAGING_PHOTO_fileInput', '#SNO_PHOTO_fileInput']
        ls = ["content", "shipping", "serial"]
        for each in range(3):
            for file in os.listdir('amazon_claims'):
                if f'{ls[each]}_{order_ids[idx]}' in file:
                    page.locator(ids[each]).set_input_files(
                        '\\'.join([str(os.getcwd()), 'amazon_claims', file]))
        page.get_by_placeholder("Issue Description").click()
        page.get_by_placeholder("Issue Description").fill(
            df['Claim Description'][idx])
        time.sleep(10)
        page.locator("(//input[@type='checkbox'])[1]").check()
        page.get_by_role('button', name='Submit SAFE-T Claim').click()
        time.sleep(3)
        logger.info(f"Successffuly Claimed for the order_id : {order_ids[idx]}")
        claimed_lst.append(order_ids[idx])
        page.close()
    page.close()
    context.close()
    browser.close()


if __name__ == "__main__":
    logger.info(f"script started at {datetime.now()}")
    if not os.path.exists("amazon_claims"):
        os.makedirs("amazon_claims")
    dowloaded = os.listdir('amazon_claims')
    opt = [login['drive_link']]
    main(opt, dowloaded)
    df = pd.read_csv('amazon_claims//return_claims_amazon.csv')
    order_ids = [x for x in df['Order Id']]
    df1 = pd.read_csv('claimed_list_amazon.csv')
    claimed_lst = [x for x in df1['Order_Id']]
    with sync_playwright() as playwright:
        run(playwright)
    df1 = pd.DataFrame({'Order_Id': claimed_lst})
    df1.to_csv('claimed_list_amazon.csv')
    logger.info(f"csv sheet succefully updated")
    logger.info(f"script ended at {datetime.now()}")
