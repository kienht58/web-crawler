# -*- coding: utf-8 -*-
import scrapy
import os
import json
import re
import logging
import xlsxwriter
from aliexpress.items import AliexpressItem
from scrapy.http import Request

protocol_prefix = 'https:'
feedback_url = 'https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId='


class AliExpressSpider(scrapy.Spider):
    name = 'aliexpress'
    start_urls = []
    products = []
    from_page = 0
    limit = 0
    counter = 0
    filename=''


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
        print "File name: ",
        self.filename = raw_input() + '.xlsx'


    def parse(self, response):
        for product in response.css('.list-item'):
            item = AliexpressItem()
            if product.css('.info h3 a::text').extract_first():
                item['product_name'] = product.css('.info h3 a::text').extract_first()
                item['product_url'] = protocol_prefix + product.css('.info h3 a::attr(href)').extract_first()
                item['product_id'] = item['product_url'].split('/')[5].split('.')[0]
                item['orders'] = int(re.search('\((.+?)\)', product.css('.order-num a em::text').extract_first()).group(1))
                item['pages'] = (item['orders'] // 8) if (item['orders'] % 8 == 0) else (item['orders'] // 8 + 1)
                item['us'] = 0
                self.products.append(item)

        next_page = response.css('.ui-pagination-next::attr(href)').extract_first()
        if next_page and self.counter < self.limit:
            self.counter = self.counter + 1
            url = protocol_prefix + next_page
            yield scrapy.Request(url, self.parse)
        else:
            for idx, product in enumerate(self.products):
                for page in range(product['pages']):
                    yield Request(url=feedback_url + product['product_id'] + "&type=default&page=" + str(page + 1),
                      callback=self.process_orders,
                      meta={
                        'product_idx': idx,
                        'pages': product['pages'] - page - 1
                      },
                      dont_filter=True
                    )


    def process_orders(self, response):
        index = response.meta['product_idx']
        pages = response.meta['pages']
        data = json.loads(response.body_as_unicode()) if json.loads(response.body_as_unicode()) else ""
        if data:
            for item in data['records']:
                if item['countryCode'] == 'us':
                    self.products[index]['us'] = self.products[index]['us'] + 1 if self.products[index]['us'] else 1

        logging.info("product index: %s, pages left: %s", str(index), str(pages))

        if index == 0:
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
            if product['orders'] >= 10:
                if((product['us']/product['orders']) * 100 >= 0):
                    worksheet.write(row, 0, product['product_name'])
                    worksheet.write_string(row, 1, product['product_url'])
                    worksheet.write(row, 2, product['orders'])
                    worksheet.write(row, 3, product['us'])
                    row += 1

        workbook.close()
