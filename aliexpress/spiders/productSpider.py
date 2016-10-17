from scrapy.spiders.init import InitSpider
from scrapy.http import Request, FormRequest
from scrapy.spiders import CrawlSpider, Rule

from scrapy.spiders import BaseSpider
from scrapy.selector import HtmlXPathSelector

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json

class ProductSpider(InitSpider):
    name = 'product'
    login_page = "https://login.aliexpress.com"
    start_url = "https://www.aliexpress.com/category/200004720/office-electronics.html?spm=2114.20011208.2.1.AkTOEP&site=glo"
    products = {}

    def __init__(self):
        InitSpider.__init__(self)
        self.driver = webdriver.Chrome()

    def __del__(self):
        self.driver.close()
        print self.verificationErrors
        CrawlSpider.__del__(self)

    def init_request(self):
        #create login request
        self.log('[LOG]: Start crawling login page!')
        return Request(url=self.login_page, callback=self.login)

    def login(self, response):
        self.log('[LOG]: Get iframe and fill in login form.')
        self.driver.get(response.url)
        #return login page as response
        frame = self.driver.find_element_by_id('alibaba-login-box')
        self.driver.switch_to.frame(frame)
        #get email and password
        email = self.driver.find_element_by_name("loginId")
        password = self.driver.find_element_by_name("password")

        #fill in data
        email.send_keys("kien.isp15@gmail.com")
        password.send_keys("kienhoang95")

        #submit
        self.driver.find_element_by_name("submit-btn").click()

        return Request(url=self.start_url, callback=self.get_list_products)

    def get_list_products(self, response):
        if "Sign Out" in response.body:
            #approved
            self.log("[LOG]: Successfully logged in. Start crawling!")
            product_urls = response.css("a.product::attr(href)").extract()
            for product_url in product_urls:
                product_url = product_url[2:]
                product_id = product_url.split("/")[3].split("?")[0].replace(".html", "")
                self.log(product_id)
                products[product_id] = Request(url=product_url, callback=self.parse)
        else:
            self.log("[LOG]: Failed!")

    def parse(self, response):
        product = {}
        product['name'] = response.css("h1.product-name::text").extract_first()
        product['orders'] = response.css("span.order-num::text").extract_first().replace('orders', '').strip()
        us_orders = 0
        for index in range((orders // 8) if (orders % 8 == 0) else (orders // 8 + 1)):
            us_orders_per_page =  Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId=" + product_id + "&type=default&page=" + str(index + 1), callback=self.get_us_order)
            us_orders = us_orders + us_orders_per_page
        product['us_orders'] = us_orders
        return product

    def get_us_order(self, response):
        us_orders = 0
        data = json.loads(response.body_as_unicode()) if json.loads(response.body_as_unicode()) else ""
        if(data != ""):
            for item in data['records']:
                if(item['countryCode'] == 'us'):
                    us_orders = self.us_orders + 1
        return us_orders
