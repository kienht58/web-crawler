# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AliexpressItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()
    pages = scrapy.Field()
    id = scrapy.Field()
    orders_crawled = scrapy.Field()
    us_crawled = scrapy.Field()
    orders = scrapy.Field()
    orders_in_5_days = scrapy.Field()
    us_in_5_days = scrapy.Field()
