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
    buffer_url = "https://www.aliexpress.com/"
    start_url = "https://www.aliexpress.com/category/200004720/office-electronics.html?spm=2114.20011208.2.1.AkTOEP&site=glo"
    products = {}

    def __init__(self):
        InitSpider.__init__(self)
        self.products['iteration'] = 0
        self.driver = webdriver.Chrome()

    def __del__(self):
        self.driver.close()
        CrawlSpider.__del__(self)

    def init_request(self):
        #create login request
        return Request(url=self.login_page, callback=self.login)

    def login(self, response):
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
        if "login" in response.url:
            self.driver.get(response.url)
            validation_box = self.driver.find_element_by_id('alibaba-login-box')
            self.driver.switch_to.frame(validation_box)
            self.driver.find_element_by_id('has-login-submit').click()

            self.driver.get(self.start_url)
            products = self.driver.find_elements_by_class_name("list-item")
            for product in products:
                product_url = product.find_element_by_class_name("product").get_attribute("href")
                product_name = product.find_element_by_class_name("product").text
                product_id = product_url.split("/")[5].split("?")[0].replace(".html", "")
                product_orders = int(product.find_element_by_css_selector("a.order-num-a em").text[8:].replace(")", ""))
                self.products['iteration'] = self.products['iteration'] + 1
                self.products[product_id] = {'name': product_name, 'url': product_url, 'orders': product_orders, 'us_orders': 0}
                for index in range((product_orders // 8) if (product_orders % 8 == 0) else (product_orders // 8 + 1)):
                    yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId=" + product_id + "&type=default&page=" + str(index + 1), callback=self.get_us_order, meta={'product_id': product_id})

            # product_urls = response.css("a.product::attr(href)").extract()
            #
            # for product_url in product_urls:
            #     product_url = product_url[2:]
            #     product_id = product_url.split("/")[3].split("?")[0].replace(".html", "")
            #     actual_url = "https://" + product_url
            #     yield Request(url=actual_url, callback=self.get_product_details, meta={'product_id': product_id, 'actual_url': actual_url})

    # def get_product_details(self, response):
    #     if "login" in response.url:
    #         self.driver.get(response.url)
    #         validation_box = self.driver.find_element_by_id('alibaba-login-box')
    #         self.driver.switch_to.frame(validation_box)
    #         self.driver.find_element_by_id('has-login-submit').click()
    #         actual_url = response.meta['actual_url']
    #         yield Request(url=actual_url, callback=self.get_product_details, meta={'product_id': response.meta['product_id'], 'actual_url': actual_url}, dont_filter=True)
    #     else:
    #         product_id = response.meta['product_id']
    #         self.products[product_id] = {}
    #         self.products['iteration'] = self.products['iteration'] + 1
    #         self.products[product_id]['name'] = response.css("h1.product-name::text").extract_first()
    #         self.products[product_id]['url'] = response.url
    #         self.products[product_id]['orders'] = int(response.css("span.order-num::text").extract_first().replace('orders', '').strip())
    #         orders = int(self.products[product_id]['orders'])
    #         self.products[product_id]['us_orders'] = 0
    #         for index in range((orders // 8) if (orders % 8 == 0) else (orders // 8 + 1)):
    #             yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId=" + product_id + "&type=default&page=" + str(index + 1), callback=self.get_us_order, meta={'product_id': product_id})
    #
    def get_us_order(self, response):
        product_id = response.meta['product_id']
        data = json.loads(response.body_as_unicode()) if json.loads(response.body_as_unicode()) else ""
        if(data != ""):
            for item in data['records']:
                if(item['countryCode'] == 'us'):
                    self.products[product_id]['us_orders'] = self.products[product_id]['us_orders'] + 1
        if self.products['iteration'] > 45:
            self.log(self.products)
