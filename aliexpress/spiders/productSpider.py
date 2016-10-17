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
    start_url = "https://www.aliexpress.com/item/Premium-Compact-Stainless-steel-USB-Flash-Drive-8GB-16GB-32GB-USB-Flash-Pen-Drive-Thumb-Disk/1367979622.html"
    product_name = ""
    orders = ""
    us_orders = 0
    iterate = 0

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

        return Request(url=self.start_url, callback=self.parse)

    def parse(self, response):
        if "Sign Out" in response.body:
            #approved
            self.log("[LOG]: Successfully logged in. Start crawling!")
            product_name = response.css("h1.product-name::text").extract_first()
            orders = int(response.css("span.order-num::text").extract_first().replace('orders', '').strip())
            for index in range((self.orders // 8) if (self.orders % 8 == 0) else (self.orders // 8 + 1)):
                yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId=1367979622&type=default&page=" + str(index + 1), callback=self.get_us_order)
        else:
            self.log("[LOG]: Failed!")

    def get_us_order(self, response):
        data = json.loads(response.body_as_unicode()) if json.loads(response.body_as_unicode()) else ""
        if(data != ""):
            for item in data['records']:
                self.iterate = self.iterate + 1
                if(item['countryCode'] == 'us'):
                    self.us_orders = self.us_orders + 1
                    self.log("[LOG]: US ORDER!!!!!!!!")
            self.log("[LOG]: Number of us orders: " + str(self.us_orders))
            self.log("[LOg]: Total number of records: " + str(self.iterate))
