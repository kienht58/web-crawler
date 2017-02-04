import scrapy
from scrapy.http import Request, FormRequest
from scrapy.spiders import CrawlSpider, Rule

from scrapy.spiders import BaseSpider
from scrapy.selector import HtmlXPathSelector

from datetime import datetime, timedelta
import json

class MySpider(scrapy.Spider):
	name = "feedback"
	products = {}
	userInput = {}
	def __init__(self, *args, **kwargs):
		print "LOGLOGLOGLOGLOG"
		print kwargs
		self.products = kwargs.get('products')
		self.userInput = kwargs.get('userInput')

	def start_requests(self):
		return 0


	# 	if productFeedbackPages == 0:
	# 		yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm",
	# 					  callback=self.process_orders,
	# 					  dont_filter=True)
	# 	else:
	# 		for index in range(productFeedbackPages):
	# 			yield Request(url="https://feedback.aliexpress.com/display/evaluationProductDetailAjaxService.htm?productId=" + productId + "&type=default&page=" + str(index + 1),
	# 						  callback=self.process_orders,
	# 						  meta={'products': self.products})

	# def process_orders(self, response):
	# 	data = json.loads(response.body_as_unicode()) if json.loads(response.body_as_unicode()) else ""
	# 	if(data != ""):
	# 		self.products = response.meta['products']
	# 		for item in data['records']:
	# 			if userInput['userSelection'] == 1:
	# 				if(item['countryCode'] == userInput['countryCode']):
	# 					self.products[userInput['index']][productId][userInput['countryCode']] += 1
				
	# 			elif userInput['userSelection'] == 2:
	# 				productOrderDate = datetime.strptime(item['date'], '%d %b %Y %H:%M').date()
	# 				if datetime.now().date() - productOrderDate <= timedelta(days=userInput['dateThreshold']):
	# 					self.products[userInput['index']][productId]['orders in the last' + str(userInput['dateThreshold']) + 'days'] += 1
				
	# 			else:
	# 				if(item['countryCode'] == userInput['countryCode']):
	# 					self.products[userInput['index']][productId][userInput['countryCode']] += 1
	# 				productOrderDate = datetime.strptime(item['date'], '%d %b %Y %H:%M').date()
	# 				if datetime.now().date() - productOrderDate <= timedelta(days=userInput['dateThreshold']):
	# 					self.products[userInput['index']][productId]['orders in the last' + str(userInput['dateThreshold']) + 'days'] += 1

	def get_result(self):
		return self.products