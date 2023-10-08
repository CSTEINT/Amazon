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


def loop(page):
	tree = html.fromstring(page.content())
	spon_lst = []
	prod_lst = []
	all_prod_pages = tree.xpath('//a[@class="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"]/@href')
	spon_lst = tree.xpath("//h2[@class='a-size-mini s-line-clamp-1']/span/text()")
	final_pair = []
	for i  in range(len(spon_lst)):
		final_pair.append({'owner':spon_lst[i],'url':''.join(['https://www.amazon.in',all_prod_pages[i]])})
	for each in final_pair:
		if ('spc=' in each['url']) and ('Fusked' not in each['owner']) and ('Caaju' not in each['owner']):
			tar_spon.append(each)
		else: 
			if ('Fusked' in each['owner']) or ('Caaju' in each['owner']):
				our_pro.append(each)
			else:
				tar_pro.append(each)


def run(playwright: Playwright,phrase):
	browser = playwright.chromium.launch(channel="chrome", headless=False, proxy= {
		'server': login['p_server'],
		'username': login['p_username'],
		'password': login['p_password'],
	})
	context = browser.new_context()
	stealth_sync(context)
	page = context.new_page()
	try:
		page.goto(login['proxy_url'])
	except TimeoutError:
		pass
	try:
		page.goto('https://www.amazon.in')
	except TimeoutError:
		page.close()
		browser.close()
		return run(playwright,phrase)
	time.sleep(5)
	if 'Enter the characters you see below' in page.content(): 
		time.sleep(20)
		page.close()
		browser.close()
		return run(playwright,phrase)
	page.get_by_placeholder("Search Amazon.in").fill(phrase)
	page.get_by_placeholder("Search Amazon.in").press("Enter")
	time.sleep(10)
	tree = html.fromstring(page.content())
	pages = tree.xpath("//div[@class='a-section a-text-center s-pagination-container']//a//text()")
	l_pages =[x for x in pages if x not in ['Next','Previous']]
	loop(page)
	for idx in range(len(l_pages)):
		page.get_by_text("Next", exact=True).click()
		time.sleep(10)
		loop(page)
	for each in tar_spon:
		page.goto(each['url'],timeout=60000)
		logger.info(f"Clicked to Ad Sponsored by {each['owner']} at timestamp {datetime.now()}")
	for each in our_pro:
		logger.info(f"Clicked to our products at timestamp {datetime.now()}")
		page.goto(each['url'],timeout=60000)
	for each in tar_pro[:3]:
		logger.info(f"Clicked to competetors products at timestamp {datetime.now()}")
		page.goto(each['url'],timeout=60000)
	page.close()
	browser.close()
	return True


if __name__=="__main__":
	get_sheet_and_timings()
	df = pd.read_csv('ad_clicker.csv')
	logger.info(f"Automation Started at {datetime.now()}")
	lst = [x for x in df['phrases']]
	tar_spon = []
	tar_pro = []
	our_pro = []
	for phrase in lst:
		with sync_playwright() as playwright:
			run(playwright,phrase)
	send_mail(log_file)
	logger.info(f"Automation ended at {datetime.now()}")