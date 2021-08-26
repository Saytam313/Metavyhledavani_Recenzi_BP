#skript obsahuje funkce pro potvrzeni, pro kontrolu jestli se jedna o platny nazev produktu
#Author: Simon Matyas (xmatya11)
from urllib.request import urlopen as uReq
import urllib
from bs4 import BeautifulSoup as soup    
import os, sys, time
from difflib import SequenceMatcher
#porovnani podobnosti dvou stringu
#param:
# a - string 1
# b - string 2
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()
#vyhledani na webu heureka.cz jestli zadany produkt existuje
#param:
# product - hledany produkt
def WebScrape_product(product):

	search_word=product
	search_word=search_word.replace(' ','+')
	try:
		uClient = uReq('https://www.heureka.cz/?h%5Bfraze%5D='+search_word)
	except:
		return

	time.sleep(2)
	page_html = uClient.read()
	uClient.close()

	#vyhledani hledanych dat v html
	page_soup = soup(page_html, "html.parser")
	count=0
	product_list=page_soup.findAll('a',{"class":"c-product__link"})
	for x in product_list:
		count+=1
		if(similar(product.lower(),x.text.lower())>=0.3):
			return True
		if(count>2):
			break
	return False

#vyhledani na webu auto-mania.cz jestli zadany produkt existuje
#param:
# product - hledany produkt
def WebScrape_productAuto(product):

	search_word=product.strip()
	search_word=search_word.replace(' ','+')
	try:
		uClient = uReq('https://auto-mania.cz/?s='+search_word,timeout=10)
	except:
		return False
	try:
		page_html = uClient.read()
	except:
		return False
	#print(page_html)
	uClient.close()
	#vyhledani hledanych dat v html
	page_soup = soup(page_html, "html.parser")

	count=0
	
	for x in page_soup.findAll("h3",{"class":"entry-title td-module-title"}):

		count+=1
		if(similar(product,x.a.text.lower())>=0.3):
			return True
		if(count>3):
			break
	return False
