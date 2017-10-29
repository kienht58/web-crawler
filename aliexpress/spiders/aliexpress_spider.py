# -*- coding: utf-8 -*-
import scrapy
import json
import re
import xlsxwriter
from aliexpress.items import AliexpressItem
from scrapy.http import Request

protocol_prefix = 'https:'
feedback_url = 'https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId='


class AliExpressSpider(scrapy.Spider):
    name = 'aliexpress'
    start_urls = ['https://www.aliexpress.com/wholesale?SearchText=shirt&g=y&page=40']
    counter = 0
    percent = 50
    products = []


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
        if next_page and self.counter < 2:
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

        if index == (len(self.products) - 1):
            self.export_to_excel()


    def export_to_excel(self):
        try:
            os.remove('test.xlsx')
        except OSError:
            pass
        workbook = xlsxwriter.Workbook("test.xlsx")
        worksheet = workbook.add_worksheet()
        worksheet.write(0, 0, "Ten")
        worksheet.write(0, 1, "Link")
        worksheet.write(0, 2, "Tong so orders")
        worksheet.write(0, 3, 'US')
        row = 1

        for product in self.products:
            if product['orders'] >= 10:
                if((product['us']/product['orders']) * 100 >= self.percent):
                    worksheet.write(row, 0, product['product_name'])
                    worksheet.write_string(row, 1, product['product_url'])
                    worksheet.write(row, 2, product['orders'])
                    worksheet.write(row, 3, product['us'])
                    row += 1

        workbook.close()
