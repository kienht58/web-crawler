# -*- coding: utf-8 -*-
import scrapy
import os
import json
import re
import xlsxwriter
from datetime import datetime, timedelta
from aliexpress.items import AliexpressItem
from scrapy.http import Request
from scrapy.exceptions import CloseSpider

protocol_prefix = 'https:'
feedback_url = 'https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId='
MAXIMUM_FEEDBACK_PAGES = 10
FEEDBACK_PER_PAGE = 20
DEFAULT_DATE_LIMIT = 5
DROPSHIP_THRESHOLD = 10


class AliExpressSpider(scrapy.Spider):
    """ Crawl info from aliexpress search page.

    """
    name = 'aliexpress'
    start_urls = []
    products = []
    start = 0
    limit = 0
    minimum_orders = 0
    crawled = 1
    remaining_pages = 0
    filename = ''

    def __init__(self):
        print "Link: ",
        search_link = raw_input()

        print "Trang bắt đầu quét: ",
        self.start = int(raw_input())

        print "Trang kết thúc: ",
        self.limit = int(raw_input())

        print "Số orders trong 5 ngày: ",
        self.minimum_orders = int(raw_input())

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
                    product['orders'] = int(
                        re.search(
                            '\((.+?)\)',
                            item.css('.order-num a em::text').extract_first()
                        ).group(1)
                    )  # extract order from string with format (x)

                    pages = (product['orders'] // FEEDBACK_PER_PAGE) if \
                        (product['orders'] % FEEDBACK_PER_PAGE == 0) else \
                        (product['orders'] // FEEDBACK_PER_PAGE + 1)
                    product['pages'] = pages if pages < MAXIMUM_FEEDBACK_PAGES else MAXIMUM_FEEDBACK_PAGES
                    self.remaining_pages = self.remaining_pages + product['pages']

                    # initiate other properties
                    product['orders_crawled'] = 0
                    product['orders_5_days'] = 0
                    product['sellers'] = {}

                    self.products.append(product)
                except RuntimeError:
                    self.logger.info('Error while processing product %s', item)

            next_page = response.css('.ui-pagination-next::attr(href)').extract_first()
            if next_page is not None and self.start < self.limit:
                # continue scraping through product pages
                self.start = self.start + 1
                self.crawled = self.crawled + 1
                url = protocol_prefix + next_page

                yield scrapy.Request(url, self.parse)
            else:
                # crawl feedback from products
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
        except RuntimeError:
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
        except SystemError:
            data = None

        if data is not None:
            if data['records']:
                for item in data['records']:
                    product['orders_crawled'] = product['orders_crawled'] + 1 if product['orders_crawled'] else 1

                    order_date = datetime.strptime(item['date'], '%d %b %Y %H:%M').date()
                    if datetime.now().date() - order_date <= timedelta(days=5):
                        product['orders_5_days'] = product['orders_5_days'] + 1 if product['orders_5_days'] else 1

                    seller_name = str(item['name'])
                    if seller_name in product['sellers']:
                        product['sellers'][seller_name]['orders'] = product['sellers'][seller_name]['orders'] + 1
                    else:
                        product['sellers'][seller_name] = {
                            'name': seller_name,
                            'level': item['buyerAccountPointLeval'],
                            'orders': 1
                        }

        if self.remaining_pages == 0:
            self.export_to_excel()

    def export_to_excel(self):
        try:
            os.remove(self.filename)
        except OSError:
            pass

        workbook = xlsxwriter.Workbook(self.filename)
        worksheet = workbook.add_worksheet()
        worksheet.write(0, 0, "Tong so trang quet duoc")
        worksheet.write(0, 1, self.crawled)
        worksheet.write(2, 0, "Ten")
        worksheet.write(2, 1, "Link")
        worksheet.write(2, 2, "Tong so order")
        worksheet.write(2, 3, "So order toi da quet dc")
        worksheet.write(2, 4, "Tong so order trong 5 ngay")
        worksheet.write(2, 5, "Dropshippers")
        row = 3

        for product in self.products:
            if product['orders'] > 0:
                if product['orders_5_days'] > self.minimum_orders:
                    dropshipper = has_dropship(product['sellers'])
                    if dropshipper:
                        worksheet.write(row, 0, product['name'])
                        worksheet.write_string(row, 1, product['url'])
                        worksheet.write(row, 2, product['orders'])
                        worksheet.write(row, 3, product['orders_crawled'])
                        worksheet.write(row, 4, product['orders_5_days'])
                        worksheet.write(row, 5, group_dropship(dropshipper))

                    row += 1

        workbook.close()


def has_dropship(sellers):
    """
    Check if product is being dropshipped
    :param sellers:
    :return:
    """
    dropshipper = ''
    for name, seller in sellers.iteritems():
        if seller['orders'] >= DROPSHIP_THRESHOLD:
            if dropshipper:
                if seller['orders'] > dropshipper['orders']:
                    dropshipper = seller
            else:
                dropshipper = seller

    return dropshipper


def group_dropship(seller):
    """

    :param seller:
    :return:
    """
    return 'Name: ' + seller['name'] + ', level: ' + seller['level'] + ', orders: ' + str(seller['orders'])
