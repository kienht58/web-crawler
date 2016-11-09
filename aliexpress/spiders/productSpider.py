from scrapy.spiders.init import InitSpider
from scrapy.http import Request, FormRequest
from scrapy.spiders import CrawlSpider, Rule

from scrapy.spiders import BaseSpider
from scrapy.selector import HtmlXPathSelector

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime, timedelta
import json
import xlsxwriter

class ProductSpider(InitSpider):
    name = 'product'
    start_url = ""
    products = {}
    country_code = ""
    filename = ""
    threshold = 0
    selection = 0

    def __init__(self):
        InitSpider.__init__(self)
        print "***********************************************"
        print "*                    MENU                     *"
        print "***********************************************"
        print "*1. Quet theo country code                    *"
        print "*2. Quet theo ngay                            *"
        print "***********************************************"
        print "Nhap lua chon cua ban:",
        self.selection = input()
        print "Nhap url: ",
        self.start_url = raw_input()
        if self.selection == 1:
            print "Nhap ma country code: ",
            self.country_code = raw_input()
            self.filename = self.filename + ".xlsx"
            print "Nhap gioi han: ",
            self.threshold = float(raw_input())
        else:
            print "Nhap gioi han ngay: ",
            self.threshold = int(raw_input())
        print "Nhap ten file output: ",
        self.filename = raw_input() + ".xlsx"
        self.driver = webdriver.Chrome()

    def __del__(self):
        self.driver.close()
        CrawlSpider.__del__(self)

    def start_requests(self):
        url_parts = self.start_url.split("/")

        if(url_parts[3] == 'store'):
            store_id = url_parts[4].split("?")[0]
            self.driver.get("https://www.aliexpress.com/store/" + store_id + "/search/1.html")
            total_products = int(self.driver.find_element_by_css_selector("div#result-info strong").text.replace(",",""))
            total_pages = (total_products // 36) if (total_products % 36 == 0) else (total_products // 36 + 1)
            for page in range(2, total_pages + 1):
                self.products[page - 1] = {}
                products = self.driver.find_elements_by_class_name("detail")
                product_count_in_page = len(products)
                for product_index, product in enumerate(products):
                    product_url = product.find_element_by_tag_name("a").get_attribute("href")
                    product_name = product.find_element_by_tag_name("a").text
                    product_id = product_url.split("/")[6].replace(".html", "").split("_")[1]
                    try:
                        product_orders = product.find_element_by_css_selector("div.recent-order").text
                        if "s" in product_orders:
                            product_orders = int(product_orders[7:].replace(")", ''))
                        else:
                            product_orders = int(product_orders[6:].replace(")", ''))
                    except NoSuchElementException:
                        product_orders = 0

                    if self.selection == 1:
                        self.products[page - 1][product_index + 1] = {'name': product_name, 'url': product_url, 'orders': product_orders, self.country_code: 0}
                    else:
                        self.products[page - 1][product_index + 1] = {'name': product_name, 'url': product_url, 'orders': product_orders, 'orders in the last' + str(self.threshold) + 'days': 0}

                    feedback_pages = (product_orders // 8) if (product_orders % 8 == 0) else (product_orders // 8 + 1)
                    if feedback_pages == 0:
                        yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm",
                                      callback=self.process_orders,
                                      meta={'product_index': product_index,
                                            'feedback_pages_left': 0,
                                            'page': page, 'is_last_page': True if page == total_pages else False,
                                            'product_left_in_page': product_count_in_page - product_index - 1},
                                      dont_filter=True)
                    for idx in range(feedback_pages):
                        yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId=" + product_id + "&type=default&page=" + str(idx + 1),
                                      callback=self.process_orders,
                                      meta={'product_index': product_index,
                                            'feedback_pages_left': feedback_pages - idx - 1,
                                            'page': page, 'is_last_page': True if page == total_pages else False,
                                            'product_left_in_page': product_count_in_page - product_index - 1})

                self.driver.get("https://www.aliexpress.com/store/" + store_id + "/search/" + str(page) + ".html")

        else:
            self.driver.get(self.start_url)
            products = self.driver.find_elements_by_class_name("list-item")
            self.products[1] = {}
            total = len(products)
            for index, product in enumerate(products):
                product_url = product.find_element_by_class_name("product").get_attribute("href")
                product_name = product.find_element_by_class_name("product").text
                product_id = product_url.split("/")[5].split("?")[0].replace(".html", "")
                product_orders = product.find_element_by_css_selector("a.order-num-a em").text
                if "s" in product_orders:
                    product_orders = int(product_orders[8:].replace(")", ''))
                else:
                    product_orders = int(product_orders[7:].replace(")", ''))

                if self.selection == 1:
                    self.products[1][index + 1] = {'name': product_name, 'url': product_url, 'orders': product_orders, self.country_code: 0}
                else:
                    self.products[1][index + 1] = {'name': product_name, 'url': product_url, 'orders': product_orders, 'orders in the last' + str(self.threshold) + 'days': 0}

                feedback_pages = (product_orders // 8) if (product_orders % 8 == 0) else (product_orders // 8 + 1)
                if feedback_pages == 0:
                    yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm",
                                  callback=self.process_orders,
                                  meta={'product_index': index,
                                        'feedback_pages_left': 0,
                                        'page': 2, 'is_last_page': True,
                                        'product_left_in_page': total - index - 1},
                                  dont_filter=True)
                for idx in range(feedback_pages):
                    yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId=" + product_id + "&type=default&page=" + str(idx + 1),
                                  callback=self.process_orders,
                                  meta={'product_index': index,
                                        'feedback_pages_left': feedback_pages - idx - 1,
                                        'page': 2, 'is_last_page': True,
                                        'product_left_in_page': total - index - 1})


    def process_orders(self, response):
        product_index = response.meta['product_index']
        page = response.meta['page']
        data = json.loads(response.body_as_unicode()) if json.loads(response.body_as_unicode()) else ""
        if(data != ""):
            for item in data['records']:
                if self.selection == 1:
                    if(item['countryCode'] == self.country_code):
                        self.products[page - 1][product_index + 1][self.country_code] = self.products[page - 1][product_index + 1][self.country_code] + 1
                else:
                    order_date = datetime.strptime(item['date'], '%d %b %Y %H:%M').date()
                    if datetime.now().date() - order_date > timedelta(days=self.threshold):
                        self.products[page - 1][product_index + 1]['orders in the last' + str(self.threshold) + 'days'] = self.products[page - 1][product_index + 1]['orders in the last' + str(self.threshold) + 'days'] + 1
        if response.meta['is_last_page'] and response.meta['product_left_in_page'] <= 1 and response.meta['feedback_pages_left'] == 0:
            self.write_to_excel(self.products)


    def write_to_excel(self, products):
        workbook = xlsxwriter.Workbook(self.filename)
        worksheet = workbook.add_worksheet()
        worksheet.write(0, 0, "Ten")
        worksheet.write(0, 1, "Link")
        worksheet.write(0, 2, "Tong so orders")
        if self.selection == 1:
            worksheet.write(0, 3, self.country_code)
        else:
            worksheet.write(0, 3, 'So orders trong ' + str(self.threshold) + ' ngay gan day')

        row = 1
        for (page_index, page_details) in products.items():
            for (product_index, product) in page_details.items():
                if product['orders'] > 0:
                    if self.selection == 1:
                        if (float(product[self.country_code])/product['orders']) * 100 >= self.threshold:
                            worksheet.write(row, 1, product['name'])
                            worksheet.write_string(row, 2, product['url'])
                            worksheet.write(row, 3, product['orders'])
                            worksheet.write(row, 4, product[self.country_code])
                            row += 1
                    else:
                        if product['orders in the last' + str(self.threshold) + 'days'] > 0:
                            worksheet.write(row, 1, product['name'])
                            worksheet.write_string(row, 2, product['url'])
                            worksheet.write(row, 3, product['orders'])
                            worksheet.write(row, 4, product['orders in the last' + str(self.threshold) + 'days'])
                            row += 1
        workbook.close()
