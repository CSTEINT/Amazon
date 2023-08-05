import requests
from requests import exceptions
from lxml import html
from playwright.sync_api import sync_playwright
import yaml


with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

log_config = config['product']['logging']
logging.config.dictConfig(log_config)
logger = logging.getLogger(__name__)


def main(url, asin):
    try:
        val = True
        response = requests.get(url)
        tree = html.fromstring(response.text)
        while(val):
            response = requests.get(url)
            tree = html.fromstring(response.text)
            available = tree.xpath("//div[@id='availability']")
            if available:
                val = False
        images = ['.'.join([y.strip('.') for y in x.split('_')[0::2]]) for x in
                  tree.xpath("//div[@id='imageBlock']//li//img/@src")
                  if x.count('_') == 2 and x.endswith('.jpg')]
        title = tree.xpath("//span[@id='productTitle']//text()")[0].strip()
        price_tag = tree.xpath("//span[contains(@class,'priceToPay')]//text()")
        price = price_tag[0] if price_tag else ''
        tech = tree.xpath('//table[@id="productDetails_techSpec_section_1"]')
        tech_keys = [x.strip() for x in tech[0].xpath(
            './/tr//th//text()')] if tech else []
        tech_values = [x.strip().strip('\u200e')
                       for x in tech[0].xpath('.//tr//td//text()')] if tech else []
        prod = tree.xpath(
            '//table[@id="productDetails_detailBullets_sections1"]')
        prod_keys = [x.strip() for x in prod[0].xpath(
            './/tr//th//text()')] if prod else []
        prod_values = [x.strip().strip('\u200e')
                       for x in prod[0].xpath('.//tr//td//text()')] if prod else []
        prod_details = dict(zip(prod_keys, prod_values))
        tech_details = dict(zip(tech_keys, tech_values))
        descrip = tree.xpath(
            "//div[@id='productDescription']//p/text()")[0].strip()
        brand = tree.xpath("(//tr[contains(@class,'po-brand')]//td)[2]")[0]
        rating = tree.xpath(
            "//i[contains(@class,'cm-cr-review-stars-spacin')]//text()")[0].strip()
        Data = {
            'asin': asin,
            'title': title,
            'brand': brand,
            'image': images,
            'rating': rating,
            '# of reviewers': no_of_ratingss,
            'bestsellers rank': bsrs
            'product_details': prod_details,
            'technical': tech_details
            'prod_desc': descrip
        }
        df = pd.DataFrame.from_dict(Data)
        logger.info(df.head())
        '''
        if ratings_box != []:
             nv_stars = ratings_box[0].get_attribute('aria-label')
             nv_ratings = ratings_box[1].get_attribute('aria-label')
          else:
             nv_stars, nv_ratings = 0, 0
        '''
        logger.info(title, brand, image, ratings, no_of_ratings, bsr)
        return(df)
    except exceptions.ConnectionError:
        logger.info("Faced ConnectionError and Handled properly.")
        main(url)


def populate_list(df):
    df3 = pd.DataFrame()
    df2 = pd.DataFrame()
    df3 = df
    logger.info('loading links')
    i = 1
    if (i-1) <= len(df):
        for asin in df:
            logger.info("length=", len(df), "i=", i)
            logger.info("scraping #", i, "asin...")
            link = "http://www.amazon.in/dp/"+asin
            try:
                df = main(link, asin)
            except NoSuchElementException:
                pass
            df2 = df2.append(df, ignore_index=True)
            i = i+1
    savefile(df2)


def savefile(d):
    logger.info("saving file...")
    filename = "output_amazon_search"+timename+".csv"
    filepath = Path(
        '/Users/vaibhavthakur/Desktop/python dev/output/amazon-product/'+filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(filepath)


def get_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto('https://www.amazon.in/dp/B093Q3M8M9')
        cookies = page.context.cookies()
        page.close()
        context.close()
        browser.close()
    dic = {}
    for cookie in cookies:
        dic[cookie['name']] = cookie['value']
    return dic


def get_asins():
    logger.info("asins fetched..")
    df = pd.DataFrame
    FPath = Path(
        '/Users/vaibhavthakur/Desktop/python dev/output/amazon-product/asins_all_amz.csv')
    df = pd.read_csv(FPath)
    logger.info(len(df))
    return df['asin']


if __name__ == "__main__":
    session = requests.Session()
    session.cookies.update(get_cookies())
    df = get_asins()
    populate_list(df)
