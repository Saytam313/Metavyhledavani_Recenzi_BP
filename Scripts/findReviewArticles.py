#hlavni skript, vyhleda clanky mezi dvema daty obsahujici recenze zadaneho produktu.
#Author: Simon Matyas (xmatya11)
from urllib.request import urlopen as uReq
import urllib
from bs4 import BeautifulSoup as soup 
from difflib import SequenceMatcher
import os
import sys
import brandFinder
import productFinder
import SentimentAnalyzerAspect
from datetime import datetime
from ast import literal_eval
import multiprocessing
from functools import partial
import tqdm
import time

reviewProduct=sys.argv[1]
brands=brandFinder.findBrands(reviewProduct) #vyhledani vyrobcu zadaneho produktu
product=brandFinder.findProductNames(reviewProduct) #vyhledani alternativnich nazvu produktu
product=[x.lower() for x in product] #prevod nazvu produktu do lowercase
resultDict=dict()
reviewUrls=list()
specialProductFlag=False

dirname = os.path.dirname(os.path.realpath(__file__))
f=open(dirname+"/./config.txt","r")
config=literal_eval(f.read())
specialProductList=list(config["specialProduct"].keys()) #specialni pripady pro knihy,filmy a videohry
for x in specialProductList:
	if(x in product):
		specialProduct=x
		specialProductFlag=True
		for y in config['specialProduct'][x]:
			reviewUrls.append(y['portal']) 

#Vyhledani jestli nektery prvek ze seznamu neobsahuje hledany string
#param:
#	word - hledane slovo
#	list - zadany seznam
def SubstrInList(word,list):
	if(len(word)>1):
		if(word[0].islower() and len(word)<4):#specialni priklad po porovnavani znacek, nektery znacky jsou kratky treba BMW
			return False
	else:
		return False

	for x in list:
		
		if(word in x):
			return True
		elif(x in word):
			return True
	return False

#vyhledni clanku obsahujici recenze hledaneho produktu
#param:
#	link - odkaz na soubor obsahujici texty stazenych clanku
def readReviews(link):
	reviewWordsListPart = ['recenze','hodnoceni','test']
	datafile=open(link,"r",encoding="utf8",errors='replace')


	dataContent=datafile.read()
	dataContentList=dataContent.split('<doc') #rozdeleni celeho textu na seznam clanku
	

	BrandWeight=0.5
	ProductWeight=10
	ReviewWeight=0

	for x in dataContentList:

		firstLine=True
		WordResult=0
		UrlResult=0
		
		IsReview=0
		IsProduct=0
		IsBrand=0


		url=''
		LinkInPar=False
		ParagraphLines=list()
		paragraph=''
		ArticleProduct=''
		ArticleHead=''
		ParagraphTagsS=0
		ParHeading=False
		ArticleHeadFlag=False
		for line in x.splitlines(): 


			if(firstLine==True): #specialni pripad pro prvni radek clanku

				firstLine=False
				url=line.split('url="')[-1].split('"')[0] # ziskani url clanku
				if('comment' in url.split('#')[-1] or '.sk' in url or 'tipcars' in url): #odstraneni slovenskych webu a odkazu na komentare
					break
				try:
					urlName=url.split('.')[1]
				except:
					break
				if('www' in url.split('.')[0] ):
					urlName=url.split('.')[1]
				else:
					urlName=url.split('.')[0].split('/')[-1]
				
				if(urlName not in reviewUrls and len(reviewUrls)!=0):
					break

				IsReview=0
				IsProduct=0
				IsBrand=0
			
			ParagraphLines.append(line)
			if(line.startswith('<head')):
				ArticleHeadFlag=True
			if(line.startswith('<link')):
				LinkInPar=True
			if(line.startswith('<s>')):
				ParagraphTagsS+=1
			if(line.startswith('<h')):
				ParHeading=True
			if(line.startswith('</p')):
				if(ParagraphTagsS>2 or ArticleHeadFlag or ParHeading):
					
					if(ArticleHeadFlag):

						BrandWeight=10
						ProductWeight=20
						ReviewWeight=30
				
					else:

						BrandWeight=0.5
						ProductWeight=10
						ReviewWeight=0
					

					for ParagraphLine in ParagraphLines:
						if(not ParagraphLine.startswith('<')):
							lineList=ParagraphLine.split('\t')							
							#paragraph.append(lineList[1])
							if('title' not in ParagraphLine):
								if(ArticleHeadFlag):
									ArticleHead+=lineList[0]+' '
								else:
									paragraph+=lineList[0]+' '
							if('NN' in lineList[2]): #potvrzeni ze se jedna o podstatne jmeno
								ParagraphLine=lineList[1]

								#vyhledani v seznamu slov urcujicich ze se jedna o recenzi
								if(ParagraphLine.lower() in reviewWordsListPart):
									WordResult+=ReviewWeight
									IsReview+=1
								#vyhledani v seznamu slov urcujicich ze se jedna o vyrobce
								if(ParagraphLine in brands):
									WordResult+=BrandWeight
									IsBrand+=1


								#vyhledani v seznamu slov urcujicich ze se jedna o hledany produkt
								if(ParagraphLine.lower() in product):
									WordResult+=ProductWeight
									IsProduct+=1

				LinkInPar=False
				ParagraphLines=list()
				ParagraphTagsS=0
				ParHeading=False
				ArticleHeadFlag=False

		#pokud clanek obsahuje jedno slovo ze seznamu recenzi a alespon jeden vyskyt produktu je oznacen za recenzi produktu
		if(WordResult>=30 and IsProduct>0 and IsReview>0):
			urlName=url.split('.')[1]
			if('www' in url.split('.')[0] ):
				urlName=url.split('.')[1]
			else:
				urlName=url.split('.')[0].split('/')[-1]

			if(not specialProductFlag):
				for headPart in ArticleHead.split(' '):
					if(len(headPart)>0):
						if(headPart[0].isupper() or headPart.isdigit()):
							if(headPart.lower() in url and headPart.lower() not in reviewWordsListPart):#vyhledani nazvu produktu v hlavicce clanku
								if(headPart.lower() not in urlName):
									ArticleProduct+=headPart+' '
				
				if('auto' in product): #potvrzeni ze vyhledany nazev produktu existuje
					if(not productFinder.WebScrape_productAuto(ArticleProduct)):				
						continue
				else:
					#if(False):
					if(not productFinder.WebScrape_product(ArticleProduct)):
						continue

			else:#pripad pro specialni produkty jako jsou knihy, filmy a videohry
				try:
					uClient = uReq(url)
					page_html = uClient.read()
					uClient.close()
				except:
					continue	
				page_soup = soup(page_html, "html.parser")
				specialProductportalID=0
				for x in config['specialProduct'][specialProduct]:
					if(x['portal']==urlName):
						break
					else:
						specialProductportalID+=1

				try:
					execOutput={}
					exec(config['specialProduct'][specialProduct][specialProductportalID]['productName'].replace('\t','').strip(),{'page_soup':page_soup},execOutput)
					ArticleProduct=execOutput['ArticleProduct']
				except:
					continue


			#pridani clanku do slovniku recenzi s ohodnocenim pravdepodobnosti vyskytu recenze
			resultDict[url]=[WordResult , IsBrand, IsProduct, IsReview,ArticleProduct.strip(),urlName]
	return resultDict

if __name__ == '__main__':
	date1=sys.argv[2]
	date2=sys.argv[3]
	num_threads = int(sys.argv[4])
	
	CorrectDateFilesList=list()
	for x in os.listdir(config['dataSource']):#vyhledani souboru ve kterych budou vyhledany recenze
			y=x.split('.')[0].split('_')[0]

			date_time_obj = datetime.strptime(y, '%Y-%m-%d')#vybrani souboru na zaklade dat zadanych ve vstupnich parametrech
			if(date_time_obj>=datetime.strptime(date1, '%Y-%m-%d') and  date_time_obj<=datetime.strptime(date2,'%Y-%m-%d')):
				
				CorrectDateFilesList.append(config['dataSource']+x)	

	pool=multiprocessing.Pool(processes=num_threads)

	resList=list()#paralelni zpracovani souboru a vyhledni recenzi
	for x in tqdm.tqdm(pool.imap_unordered(readReviews, CorrectDateFilesList), total=len(CorrectDateFilesList)):
		resList.append(x)
	time.sleep(1)
	for y in resList:#prevod seznamu vysledku na slovnik pro dalsi zpracovani
		if(y is not None):
			resultDict.update(y)


	sortedDictlist=sorted(resultDict.items(), key=lambda j: j[1])
	for x in sortedDictlist:
		print(x[-1][-2], end = ' - ')
		print(SentimentAnalyzerAspect.Sentiment_from_url(x[0]), end=' - ')#ohodnoceni clanku podle url
		print(x[0])

