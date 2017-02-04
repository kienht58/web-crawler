from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

import xlsxwriter

def process_page(driver, request, products, userInput):
	urlParts = request.split('/')

	if(urlParts[3] == 'store'):
		filter_store_products(driver, urlParts, products, userInput)
	else:
		filter_product_in_search_page(driver, request, products, userInput)

def filter_store_products(driver, urlParts, products, userInput):
	storeId = urlParts[4].split("?")[0]
	driver.get("https://www.aliexpress.com/store/" + storeId + "/search/1.html")
	try:
		storeTotalProducts = int(driver.find_element_by_css_selector("div#result-info strong").text.replace(",",""))
	except NoSuchElementException:
		print "Vui long xu ly dang nhap, sau do nhap \"c\" de tiep tuc"
		raw_input()
		storeTotalProducts = int(driver.find_element_by_css_selector("div#result-info strong").text.replace(",",""))
	storeName = driver.find_element_by_css_selector("span.shop-name a").text
	storeTotalPages = (storeTotalProducts // 36) if (storeTotalProducts % 36 == 0) else (storeTotalProducts // 36 + 1)
	userInput['index'] = storeName
	products[userInput['index']] = []

	for storePage in range(2, storeTotalPages + 1):
		try:
			perPageProducts = driver.find_elements_by_css_selector("ul.items-list.util-clearfix li.item div.detail")
		except NoSuchElementException:
			print "Vui long xu ly dang nhap, sau do nhap \"c\" de tiep tuc"
			raw_input()
			perPageProducts = driver.find_elements_by_css_selector("ul.items-list.util-clearfix li.item div.detail")
			
		for product in perPageProducts:
			productUrl = product.find_element_by_tag_name("a").get_attribute("href")
			productName = product.find_element_by_tag_name("a").text
			productId = productUrl.split("/")[6].replace(".html", "").split("_")[1]
			try:
				productOrders = product.find_element_by_css_selector("div.recent-order").text
				if "s" in productOrders:
					productOrders = int(productOrders[7:].replace(")", ''))
				else:
					productOrders = int(productOrders[6:].replace(")", ''))
			except NoSuchElementException:
				productOrders = 0 

			print productOrders
			products[userInput['index']].append({
													'id': productId,
													'name': productName,
													'url': productUrl,
													'orders': productOrders,
												})
		driver.get("https://www.aliexpress.com/store/" + storeId + "/search/" + str(storePage) + ".html?")

	product = call_scrapy_wrapper(products, userInput)

def filter_product_in_search_page(driver, request, products, userInput):
	userInput['index'] = "search"
	products[userInput['index']] = []
	for index in range(userInput['pageRange'][0], userInput['pageRange'][1] + 1):
		driver.get(request + "&page=" + str(index) + "&g=n")
		perPageProducts = driver.find_elements_by_class_name("list-item")
		for product in perPageProducts:
			productUrl = product.find_element_by_class_name("product").get_attribute("href")
			productName = product.find_element_by_class_name("product").text
			productId = productUrl.split("/")[5].split("?")[0].replace(".html", "")
			try:
				productOrders = product.find_element_by_css_selector("a.order-num-a em").text
				if "s" in productOrders:
					productOrders = int(productOrders[8:].replace(")", ''))
				else:
					productOrders = int(productOrders[7:].replace(")", ''))
			except NoSuchElementException:
				productOrders = 0

			products[userInput['index']].append({
													'id': productId,
													'name': productName,
													'url': productUrl,
													'orders': productOrders,
											   })

	products = call_scrapy_wrapper(products, userInput)

def call_scrapy_wrapper(products, userInput):
	process = CrawlerProcess(get_project_settings())

	process.crawl('feedback', products = products, userInput = userInput)
	process.start()

if __name__ == "__main__":
	process_page()