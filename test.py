import threading
import os
from selenium import webdriver
from pageProcessing import process_page
import xlsxwriter

userInput = {}
requestList = []
userInput['userSelection'] = 0
userInput['countryCode'] = ""
userInput['outputFilename'] = ""
userInput['percentThreshold'] = 0.0
userInput['dateThreshold'] = 0
userInput['pageRange'] = ()

def initiate():
	print "***********************************************"
	print "*                    MENU                     *"
	print "***********************************************"
	print "*1. Quet theo shop                            *"
	print "*2. Quet theo ket qua tim kiem                *"
	print "***********************************************"
	print "Nhap lua chon cua ban:",
	choice = int(raw_input())
	if choice == 1:
		print "Nhap duong dan toi file du lieu: ",
		filePath = raw_input()
		with open(filePath) as f:
			for line in f:
				requestList.append(line.strip())
	else:
		print "Nhap url:",
		requestList.append(raw_input())
		print "Nhap gioi han quet:"
		userInput['pageRange'] = (int(raw_input()), int(raw_input()))

	clear = lambda: os.system('cls')
	clear()

	print "***********************************************"
	print "*                    MENU                     *"
	print "***********************************************"
	print "*1. Quet theo country code                    *"
	print "*2. Quet theo ngay                            *"
	print "*3. Quet tong hop                             *"
	print "***********************************************"
	print "Nhap lua chon cua ban:",
	userInput['userSelection'] = input()

	if userInput['userSelection'] == 1:
		print "Nhap ma country code: ",
		userInput['countryCode'] = raw_input()
		print "Nhap gioi han: ",
		userInput['percentThreshold'] = float(raw_input())

	elif userInput['userSelection'] == 2:
		print "Nhap gioi han ngay: ",
		userInput['dateThreshold'] = int(raw_input())

	else:
		print "Nhap ma country code: ",
		userInput['countryCode'] = raw_input()
		print "Nhap gioi han %: ",
		userInput['percentThreshold'] = float(raw_input())
		print "Nhap gioi han ngay: ",
		userInput['dateThreshold'] = int(raw_input())

	print "Ten file output(excel): ",
	userInput['outputFilename'] = raw_input()

if __name__ == "__main__":
	initiate()
	driver = webdriver.Chrome()
	process_page(driver, requestList, userInput)
