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
from scrapy.exceptions import CloseSpider

protocol_prefix = 'https:'
feedback_url = 'https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId='
MAXIMUM_FEEDBACK_PAGES = 10


class AliExpressSpider(scrapy.Spider):
    """ Crawl info from aliexpress search page.

    """
    name = 'aliexpress'
    start_urls = []
    products = []
    start = 0
    limit = 0
    percent = 0
    crawled = 0
    remaining_pages = 0
    filename = ''

    def __init__(self):
        print "Link: ",
        search_link = raw_input()

        print "From page: ",
        self.start = int(raw_input())

        print "To page: ",
        self.limit = int(raw_input())

        print "Percentage: ",
        self.percent = int(raw_input())

        print "Export file name: ",
        self.filename = raw_input() + '.xlsx'

        search_link += '&page=' + str(self.start)
        search_link = search_link if 'g=y' in search_link else search_link + '&g=y'
        self.start_urls.append(search_link)


    def parse(self, response):
        try:
            list_item = response.css('.list-item')
            for item in list_item:
                product = AliexpressItem()
                try:
                    product['name'] = item.css('.info h3 a::attr(title)').extract_first()
                    product['url'] = protocol_prefix + item.css('.info h3 a::attr(href)').extract_first()
                    product['id'] = product['url'].split('/')[5].split('.')[0]
                    product['orders'] = int(re.search('\((.+?)\)', item.css('.order-num a em::text').extract_first()).group(1))

                    pages = (product['orders'] // 8) if (product['orders'] % 8 == 0) else (product['orders'] // 8 + 1)
                    product['pages'] = pages if pages < MAXIMUM_FEEDBACK_PAGES else MAXIMUM_FEEDBACK_PAGES
                    self.remaining_pages = self.remaining_pages + product['pages']

                    # initiate other properties
                    product['orders_crawled'] = 0
                    product['us_crawled'] = 0
                    product['orders_in_5_days'] = 0
                    product['us_in_5_days'] = 0

                    self.products.append(product)
                except:
                    self.logger.info('Error while processing product %s', item)


            next_page = response.css('.ui-pagination-next::attr(href)').extract_first()
            if next_page is not None and self.start < self.limit:
                self.start = self.start + 1
                self.crawled = self.crawled + 1
                url = protocol_prefix + next_page

                yield scrapy.Request(url, self.parse)
            else:
                for index, product in enumerate(self.products):
                    for page in range(product['pages']):
                        yield Request(
                            url=feedback_url + product['id'] + "&type=default&page=" + str(page + 1),
                            callback=self.process_order,
                            meta={
                                'index': index,
                                'page': page + 1,

                            },
                            dont_filter=True
                        )
        except:
            print response.css('.list-item')
            if len(self.products):
                self.export_to_excel()
            raise CloseSpider('terminated')


    def process_order(self, response):
        self.remaining_pages = self.remaining_pages - 1
        index = response.meta['index']
        page = response.meta['page']
        product = self.products[index]

        try:
            data = json.loads(response.body_as_unicode())
        except:
            data = None

        if data is not None:
            if data['records']:
                for item in data['records']:
                    product['orders_crawled'] = product['orders_crawled'] + 1 if product['orders_crawled'] else 1

                    if item['countryCode'] == 'us':
                        product['us_crawled'] = product['us_crawled'] + 1 if product['us_crawled'] else 1

                    order_date = datetime.strptime(item['date'], '%d %b %Y %H:%M').date()
                    if datetime.now().date() - order_date <= timedelta(days=5):
                        product['orders_in_5_days'] = product['orders_in_5_days'] + 1 if product['orders_in_5_days'] else 1

                    if item['countryCode'] == 'us' and datetime.now().date() - order_date <= timedelta(days=5):
                        product['us_in_5_days'] = product['us_in_5_days'] + 1 if product['us_in_5_days'] else 1

        if self.remaining_pages == 0:
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
        worksheet.write(0, 2, "Tong so order")
        worksheet.write(0, 3, "So order toi da quet dc")
        worksheet.write(0, 4, "So order US toi da quet duoc")
        worksheet.write(0, 4, "Tong so order trong 5 ngay")
        worksheet.write(0, 5, "So order US trong 5 ngay")
        row = 1

        for product in self.products:
            if product['orders'] > 0:
                if ((float(product['us_crawled'])/product['orders']) * 100) > self.percent and product['orders_in_5_days'] > 0:
                    worksheet.write(row, 0, product['name'])
                    worksheet.write_string(row, 1, product['url'])
                    worksheet.write(row, 2, product['orders'])
                    worksheet.write(row, 3, product['orders_crawled'])
                    worksheet.write(row, 4, product['us_crawled'])
                    worksheet.write(row, 5, product['orders_in_5_days'])
                    worksheet.write(row, 5, product['us_in_5_days'])
                    row += 1

        workbook.close()
