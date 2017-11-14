# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AliexpressItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    product_name = scrapy.Field()
    product_url = scrapy.Field()
    product_id = scrapy.Field()
    orders = scrapy.Field()
    pages = scrapy.Field()
    us = scrapy.Field()
    bak_orders = scrapy.Field()
