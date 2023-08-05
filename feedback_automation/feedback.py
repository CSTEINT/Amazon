from playwright.sync_api import Playwright, sync_playwright, expect
from datetime import datetime
import time
from pyotp import *
import logging
import logging.config
import json
import requests
import yaml
import csv
import pandas as pd

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

login = config['login']
log_config = config['logging']
logging.config.dictConfig(log_config)
logger = logging.getLogger(__name__)

totp = TOTP(login['secret'])


def get_cookies(cookies, cat):

    session = requests.Session()
    dic = {}
    for cookie in cookies:
        dic[cookie['name']] = cookie['value']
    url = 'https://sellercentral.amazon.in/orders-api/search'
    params = {
        'limit': '10000',
        'offset': '0',
        'sort': 'ship_by_desc',
        'date-range': 'last-7',
        'fulfillmentType': 'mfn',
        'orderStatus': 'shipped',
        'program': 'easyship',
        'subtab': 'handover-done',
        'shippingStatus': 'delivered_to_buyer',
        'forceOrdersTableRefreshTrigger': 'false'
    }
    response = session.get(
        'https://sellercentral.amazon.in/orders-api/search', params=params, cookies=dic)
    with open('response.html', 'wb') as file:
        file.write(response.content)
    data = json.loads(response.text).get('orders')
    feedbacks = []
    reviews = []
    for item in range(len(data)):
        temp = {}
        temp['id'] = data[item]['amazonOrderId']
        temp['url'] = 'https://sellercentral.amazon.in/messaging/contact?orderID={}&marketplaceID={}'.format(
            data[item]['amazonOrderId'], data[item]['homeMarketplaceId'])
        reviews.append('https://sellercentral.amazon.in/messaging/reviews?orderId={}&marketplaceID={}'.format(
            data[item]['amazonOrderId'], data[item]['homeMarketplaceId']))
        temp['asins'] = []
        for orderid in data[item]['orderItems']:
            temp['asins'].append(orderid['asin'])
        feedbacks.append(temp)
    if cat == 'feed':
        return feedbacks
    return reviews


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(channel="chrome", headless=False)
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
        "link", name="Manage Orders Add page to favourites bar").click()
    page.locator("[data-test-id=\"button-close\"]").click()
    page.locator(
        "#myo-spa-tabs-container div").filter(has_text="Sent").nth(1).click()
    time.sleep(2)
    page.locator("[data-test-id=\"tab-\\/mfn\\/shipped\"]").click()
    time.sleep(2)
    page.locator(
        "[data-test-id=\"subtab-\\/mfn\\/shipped\\/easyship\\/handover-done\"]").click()
    time.sleep(2)
    page.get_by_label("Delivered to Buyer").check()
    time.sleep(2)
    page.locator("#a-autoid-2-announce").click()
    page.get_by_role(
        "option", name="Ship-by date (descending)").get_by_text("Ship-by date (descending)").click()
    cookies = page.context.cookies()
    feedbacks = get_cookies(cookies, 'feed')
    reviews = get_cookies(cookies, 'review')
    for feedback in feedbacks:
        if feedback['id'] in feedback_lst:
            print("feedback already requested")
            continue
        page = context.new_page()
        page.goto(feedback['url'])
        page.locator("#katal-id-27 slot").filter(
            has_text="Ask your customer for clarification for a topic not covered by another contact r").locator("span").click()
        other_button = page.locator("//input[@aria-label='Other']")
        if not other_button.is_checked():
            logger.info(f"feedback already provided for order_id {feedback['id']}")
            page.close()
            continue
        page.get_by_role(
            "textbox", name="4000 character limit. Only links related to order completion are allowed, no HTML or email addresses.").click()
        text = '\n'.join([f'https://www.amazon.in/review/create-review?asin={x}' for x in feedback['asins']])
        template = f'''Dear Buyer

                    Thank you for Shopping with us. I hope you have received your order and everything is OK.

                    Do not hesitate to communicate with us for any concern you might have regarding our products. 

                    If you are satisfied with your order, we would be delighted if you could take a few seconds and leave feedback for your purchase - as a brand owner, this helps us tremendously to improve the customer experience. 

                    Below are links for both product and seller feedback. Please leave a product review if you have a moment:
                    {text}
                    https://www.amazon.in/feedback?ref_=cs_seller_bsm_feedback 

                    Thanks & Regards, 
                    CSTE International '''
        page.get_by_role(
            "textbox", name="4000 character limit. Only links related to order completion are allowed, no HTML or email addresses.").fill(template)
        page.get_by_role('button', name='Send').click()
        time.sleep(2)
        page.screenshot(path=f"feedback_{feedback['id']}.png")
        logger.info(f"Successffuly feed requested for order_id {feedback['id']}")
        page.close()
        feedback_lst.append(feedback['id'])
    # for review in reviews[:2]:
    #     if review in reviews_lst:
    #         print("review already requested.")
    #         continue
    #     page = context.new_page()
    #     page.goto(review)
    #     if 'not eligible at this time' in str(page.content()).lower():
    #         page.close()
    #     time.sleep(5)
    #     page.pause()
    #     # page.get_by_role("button", name="Yes", exact=True).click()
    #     time.sleep(3)
    #     # page.screenshot(path=f"reviews_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png")
    #     page.close()
    #     reviews_lst.append(review)

    time.sleep(5)

    # ---------------------
    context.close()
    browser.close()


if __name__ == "__main__":
    logger.info(f"Task started at {datetime.now()}")
    df_feeds = pd.read_csv('feed_master.csv')
    df_reviews = pd.read_csv('review_master.csv')
    feedback_lst = [x.strip() for x in df_feeds['IDS']]
    reviews_lst = [x.strip() for x in df_reviews['urls']]
    with sync_playwright() as playwright:
        run(playwright)
    feed_temp = pd.DataFrame({'IDS': feedback_lst})
    review_temp = pd.DataFrame({'urls': reviews_lst})
    feed_temp.to_csv('feed_master.csv')
    review_temp.to_csv('review_master.csv')
    logger.info(f"Task completed at {datetime.now()}")
