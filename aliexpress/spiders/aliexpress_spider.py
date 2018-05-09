# -*- coding: utf-8 -*-
import scrapy
import os
import json
import re
import logging
import xlsxwriter
from datetime import datetime, timedelta
from aliexpress.items import AliexpressItem
from scrapy.http import Request

protocol_prefix = 'https:'
feedback_url = 'https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId='


class AliExpressSpider(scrapy.Spider):
    """ Crawl info from aliexpress search page.

    """
    name = 'aliexpress'
    start_urls = []
    products = []
    from_page = 0
    limit = 0
    counter = 1
    percent = 10
    filename='',
    buf=0


    def __init__(self):
        print "Link: ",
        search_link = raw_input()
        print "From page: ",
        self.from_page = raw_input()
        print "To page: ",
        self.limit = int(raw_input())
        search_link += '&page=' + self.from_page
        search_link = search_link if 'g=y' in search_link else search_link + '&g=y'
        self.start_urls.append(search_link)
        print "Percentage: ",
        self.percent = int(raw_input()) #type: int, from 0 to 100
        print "File name: ",
        self.filename = raw_input() + '.xlsx'


    def parse(self, response):
        for product in response.css('.list-item'):
            item = AliexpressItem()
            if product.css('.info h3 a::text').extract_first():
                item['product_name'] = product.css('.info h3 a::text').extract_first()
                item['product_url'] = protocol_prefix + product.css('.info h3 a::attr(href)').extract_first()
                try:
                    item['product_id'] = item['product_url'].split('/')[5].split('.')[0]
                except:
                    print item['product_url']
                    print product.css('.order-num a em::text').extract_first()
                try:    
                    item['orders'] = int(re.search('\((.+?)\)', product.css('.order-num a em::text').extract_first()).group(1))
                except:
                    item['orders'] = 0
                item['pages'] = (item['orders'] // 8) if (item['orders'] % 8 == 0) else (item['orders'] // 8 + 1) # 1 feedback page has only 8 orders
                self.buf = self.buf + item['pages']
                item['us'] = 0
                item['bak_orders'] = 0
                self.products.append(item)

        next_page = response.css('.ui-pagination-next::attr(href)').extract_first()
        if next_page and self.counter < self.limit:
            self.counter = self.counter + 1
            url = protocol_prefix + next_page
            yield scrapy.Request(url, self.parse)
        else:
            for idx, product in enumerate(self.products):
                for page in range(product['pages']):
                    yield Request(
                        url=feedback_url + product['product_id'] + "&type=default&page=" + str(page + 1),
                        callback=self.process_orders,
                        meta={
                            'product_idx': idx,
                            'page': page + 1
                            },
                        dont_filter=True
                    )


    def process_orders(self, response):
        self.buf = self.buf - 1
        index = response.meta['product_idx']
        page = response.meta['page']
        product = self.products[index]
        data = json.loads(response.body_as_unicode()) if json.loads(response.body_as_unicode()) else ""
        if data:
            if len(data['records']):
                product['bak_orders'] = product['bak_orders'] + len(data['records'])
                for item in data['records']:
                    if item:
                        order_date = datetime.strptime(item['date'], '%d %b %Y %H:%M').date()
                        if item['countryCode'] == 'us':
                            if datetime.now().date() - order_date <= timedelta(days=5):
                                product['us'] = product['us'] + 1
                if page == product['pages']:
                    self.buf = self.buf + 1
                    yield Request(
                        url=feedback_url + product['product_id'] + "&type=default&page=" + str(page + 1),
                        callback=self.process_additional_orders,
                        meta={
                            'product_idx': index,
                            'page': page + 1,
                            'prev_data': data
                        },
                        dont_filter=True
                    )

        if self.buf == 0:
            logging.info("READY TO EXPORT")
            self.export_to_excel()


    def process_additional_orders(self, response):
        self.buf = self.buf - 1
        index = response.meta['product_idx']
        page = response.meta['page']
        prev_data = response.meta['prev_data']
        product = self.products[index]
        data = json.loads(response.body_as_unicode()) if json.loads(response.body_as_unicode()) else ""
        if data and data != prev_data:
            if len(data['records']):
                product['bak_orders'] = product['bak_orders'] + len(data['records'])
                for item in data['records']:
                    if item:
                        order_date = datetime.strptime(item['date'], '%d %b %Y %H:%M').date()
                        if item['countryCode'] == 'us':
                            if datetime.now().date() - order_date <= timedelta(days=5):
                                product['us'] = product['us'] + 1
                self.buf = self.buf + 1
                yield Request(
                    url=feedback_url + product['product_id'] + "&type=default&page=" + str(page + 1),
                    callback=self.process_additional_orders,
                    meta={
                        'product_idx': index,
                        'page': page + 1,
                        'prev_data': data
                    },
                    dont_filter=True
                )
        if self.buf == 0:
            logging.info("READY TO EXPORT")
            self.export_to_excel()

    def export_to_excel(self):
        try:
            os.remove(self.filename)
        except OSError:
            pass
        workbook = xlsxwriter.Workbook(self.filename)
        worksheet = workbook.add_worksheet()
        worksheet.write(0, 0, "Ten")
        worksheet.write(0, 1, "Link")
        worksheet.write(0, 2, "Tong so orders")
        worksheet.write(0, 3, 'US')
        row = 1

        for product in self.products:
            if product['bak_orders'] > 0:
                if ((float(product['us'])/product['bak_orders']) * 100) > self.percent:
                    worksheet.write(row, 0, product['product_name'])
                    worksheet.write_string(row, 1, product['product_url'])
                    worksheet.write(row, 2, product['bak_orders'])
                    worksheet.write(row, 3, product['us'])
                    row += 1

        workbook.close()
