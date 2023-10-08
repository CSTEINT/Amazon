from lxml import html
from emails import *
from playwright.sync_api import Playwright, sync_playwright, expect,TimeoutError
from datetime import datetime
import time
from undetected_playwright import stealth_sync
import schedule
from pyotp import *
import logging
from nanoid import generate
from emails import get_sheet_and_timings, send_mail
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


log_file = f'Amazon_AdClicker_{datetime.now().strftime("%Y-%m-%d")}.log'
with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

login = config['login']['amazon']
logging.basicConfig(
    level=logging.INFO,
    format='Amazon_Ad_Clicker_%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt = "%Y-%m-%d_%H:%M:%S",
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(log_file,mode='a')
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
	all_prod_pages = tree.xpath('//a[@class="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"]/@href')
	spon_lst = tree.xpath("//h2[@class='a-size-mini s-line-clamp-1']/span/text()")
	final_pair = []
	for i  in range(len(spon_lst)):
		final_pair.append({'owner':spon_lst[i],'url':''.join(['https://www.amazon.in',all_prod_pages[i]])})
	for each in final_pair:
		if ('spc=' in each['url']) and ('fusked' not in each['owner'].lower()) and ('caaju' not in each['owner'].lower()):
			temp_tar_spon.append(each)
		else: 
			if ('fusked' in each['owner'].lower()) or ('caaju' in each['owner'].lower()):
				temp_our_pro.append(each)
			else:
				temp_tar_pro.append(each)
	return temp_tar_spon,temp_tar_pro,temp_our_pro



def run(playwright: Playwright,phrase):
	tar_spon = []
	tar_pro = []
	our_pro = []
	browser = playwright.chromium.launch(channel="chrome", headless=False, proxy= {
		'server': login['p_server'],
		'username': login['p_username'],
		'password': login['p_password'],
	})
	context = browser.new_context()
	stealth_sync(context)
	page = context.new_page()
	try:
		page.goto(login['proxy_url'],timeout=10000)
	except TimeoutError:
		page.close()
		browser.close()
		return run(playwright,phrase)
	time.sleep(5)
	page.goto('https://www.amazon.in')
	if 'Enter the characters you see below' in page.content(): 
		time.sleep(20)
		page.close()
		browser.close()
		return run(playwright,phrase)
	page.get_by_placeholder("Search Amazon.in").fill(phrase)
	page.get_by_placeholder("Search Amazon.in").press("Enter")
	time.sleep(10)
	tree = html.fromstring(page.content())
	for idx in range(5):
		page.get_by_text("Next", exact=True).click()
		page.wait_for_selector('.s-pagination-strip')
		time.sleep(3)
		data = page.content()
		s1,p1,o1 = loop(data)
		tar_spon += s1
		tar_pro += p1 
		our_pro += o1
	for each in tar_spon:
		page.goto(each['url'],timeout=60000)
		logger.info(f"Clicked to Ad Sponsored by {each['owner']} at timestamp {datetime.now()}")
	for each in our_pro:
		page.goto(each['url'],timeout=60000)
		logger.info(f"Clicked to our products at timestamp {datetime.now()}")
	for each in tar_pro[:3]:
		page.goto(each['url'],timeout=60000)
		logger.info(f"Clicked to competetors products at timestamp {datetime.now()}")
	page.close()
	browser.close()
	return True


if __name__=="__main__":
	while(True):
		get_sheet_and_timings()
		logger.info(f"Automation Started at {datetime.now()}")
		df = pd.read_csv('ad_clicker.csv')
		lst = [x for x in df['phrases']]
		for phrase in lst:
			with sync_playwright() as playwright:
				run(playwright,phrase)
		send_mail(log_file)
		logger.info(f"Automation ended at {datetime.now()}")
		logger.info(f"Automation Will Restart after 5 minutes.")
		time.sleep(300)