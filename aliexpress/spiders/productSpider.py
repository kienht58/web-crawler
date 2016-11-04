from scrapy.spiders.init import InitSpider
from scrapy.http import Request, FormRequest
from scrapy.spiders import CrawlSpider, Rule

from scrapy.spiders import BaseSpider
from scrapy.selector import HtmlXPathSelector

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import json
import xlsxwriter

class ProductSpider(InitSpider):
    name = 'product'
    login_page = "https://login.aliexpress.com"
    buffer_url = "https://www.aliexpress.com/"
    start_url = ""
    products = {}
    country_code = ""
    filename = ""
    threshold = 0

    def __init__(self):
        InitSpider.__init__(self)
        self.total = 0
        print "Nhap url: "
        self.start_url = raw_input()
        print "Nhap ma country code: "
        self.country_code = raw_input()
        print "Nhap ten file output: "
        self.filename = raw_input()
        self.filename = self.filename + ".xlsx"
        print "Nhap nguong loai bo: "
        self.threshold = float(raw_input())
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

        url_parts = self.start_url.split("/")
        if(url_parts[3] == 'store'):
            products = self.driver.find_elements_by_class_name("detail")
            self.total = len(products)
            for index, product in enumerate(products):
                product_url = product.find_element_by_tag_name("a").get_attribute("href")
                product_name = product.find_element_by_tag_name("a").text
                product_id = product_url.split("/")[6].replace(".html", "").split("_")[1]
                try:
                    product_orders = product.find_element_by_css_selector("span.recent-order").text
                    if "s" in product_orders:
                        product_orders = int(product_orders[7:].replace(")", ''))
                    else:
                        product_orders = int(product_orders[6:].replace(")", ''))
                except NoSuchElementException:
                    product_orders = 0
                self.products[index + 1] = {'name': product_name, 'url': product_url, 'orders': product_orders, self.country_code: 0}
                feedback_pages = (product_orders // 8) if (product_orders % 8 == 0) else (product_orders // 8 + 1)
                if feedback_pages == 0:
                    yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm", callback=self.get_us_order, meta={'index': index, 'pages_left': 0}, dont_filter=True)
                for idx in range(feedback_pages):
                    yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId=" + product_id + "&type=default&page=" + str(idx + 1), callback=self.get_us_order, meta={'index': index, 'pages_left': feedback_pages - idx - 1})

        else:
            products = self.driver.find_elements_by_class_name("list-item")
            self.total = len(products)
            self.log(self.total)
            for index, product in enumerate(products):
                product_url = product.find_element_by_class_name("product").get_attribute("href")
                product_name = product.find_element_by_class_name("product").text
                product_id = product_url.split("/")[5].split("?")[0].replace(".html", "")
                product_orders = product.find_element_by_css_selector("a.order-num-a em").text
                if "s" in product_orders:
                    product_orders = int(product_orders[8:].replace(")", ''))
                else:
                    product_orders = int(product_orders[7:].replace(")", ''))
                self.products[index + 1] = {'name': product_name, 'url': product_url, 'orders': product_orders, self.country_code: 0}
                feedback_pages = (product_orders // 8) if (product_orders % 8 == 0) else (product_orders // 8 + 1)
                if feedback_pages == 0:
                    yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm", callback=self.get_us_order, meta={'index': index, 'pages_left': 0}, dont_filter=True)
                for idx in range(feedback_pages):
                    yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId=" + product_id + "&type=default&page=" + str(idx + 1), callback=self.get_us_order, meta={'index': index, 'pages_left': feedback_pages - idx - 1})
    def get_us_order(self, response):
        index = response.meta['index']
        self.log(index)
        data = json.loads(response.body_as_unicode()) if json.loads(response.body_as_unicode()) else ""
        if(data != ""):
            for item in data['records']:
                if(item['countryCode'] == self.country_code):
                    self.products[index + 1][self.country_code] = self.products[index + 1][self.country_code] + 1
        if index >= self.total - 2 and response.meta['pages_left'] == 0:
            self.write_to_excel(self.products)

    def write_to_excel(self, products):
        workbook = xlsxwriter.Workbook(self.filename)
        worksheet = workbook.add_worksheet()
        worksheet.write(0, 0, "STT")
        worksheet.write(0, 1, "Ten")
        worksheet.write(0, 2, "Link")
        worksheet.write(0, 3, "Tong so orders")
        worksheet.write(0, 4, self.country_code)

        row = 1
        for (index, product) in products.items():
            if product['orders'] > 0:
                if (float(product[self.country_code])/product['orders']) * 100 >= self.threshold:
                    worksheet.write(row, 0, index + 1)
                    worksheet.write(row, 1, product['name'])
                    worksheet.write_string(row, 2, product['url'])
                    worksheet.write(row, 3, product['orders'])
                    worksheet.write(row, 4, product[self.country_code])
                    row += 1
        workbook.close()
