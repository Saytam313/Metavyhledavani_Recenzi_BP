#ve wikidatech vyhleda alternativni nazvy pro zadany produkt a vyrobce zadaneho produktu.
#Author: Simon Matyas (xmatya11)
from SPARQLWrapper import SPARQLWrapper, JSON
from unidecode import unidecode
import pandas as pd
import requests

#vyhleda firmy ktere maji zadany produkt ve svych vyrobcich
#param:
# product - hledany produkt
def findBrands(product):
    API_ENDPOINT = "https://www.wikidata.org/w/api.php"

    query = product
    #vyhledani id zadaneho produktu
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'language': 'cs',
        'search': query
    }

    r = requests.get(API_ENDPOINT, params = params)
    WikidataID=r.json()['search'][0]['id']

    sparql = SPARQLWrapper("https://query.wikidata.org/sparql",agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
    #vyhledani kde je produkt zminen v sekci 'Products and Materials' na wikidatech
    sparql.setQuery("""
    SELECT ?item ?itemLabel (GROUP_CONCAT(DISTINCT(?altLabel); separator = ", ") AS ?altLabel_list)
    WHERE {
      ?item wdt:P1056 wd:"""+WikidataID+""" .
      OPTIONAL { ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en") }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" .}
    }
    GROUP BY ?item ?itemLabel
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    brandList=list() 

    AltFoundFlag=False
    for x in results["results"]["bindings"]:
        if(len(x["itemLabel"]["value"].split(' '))>1):
            for y in x["altLabel_list"]["value"].split(','):
                if(len(y.split(' '))==1):
                    if(len(y)<2):
                        continue
                    brandList.append(y)
                    AltFoundFlag=True
                    break
            if(not AltFoundFlag):
                brandList.append(x["itemLabel"]["value"])
            AltFoundFlag=False
        else:
            brandList.append(x["itemLabel"]["value"])   
    
    return brandList

#overi ktere ze zadaneho seznamu slov jsou nazvy firem
#param:
#  brandList -  seznam nazvu firem
def filterBrands(brandList):
    CorrectBrands=list()
    for x in brandList:
        API_ENDPOINT = "https://www.wikidata.org/w/api.php"

        query = x
        #vyhledani id zadaneho produktu
        params = {
            'action': 'wbsearchentities',
            'format': 'json',
            'language': 'en',
            'search': query
        }

        r = requests.get(API_ENDPOINT, params = params, headers={'User-Agent': 'Mozilla/5.0'})
        SearchResultCounter=1
        GoodResult=False
        for SearchResult in r.json()['search']: #kontrola prvnich 2 vysledku hledani podle nazvu jestli se nejedna o firmu
            if(SearchResultCounter >=2):
                break
            else:
                SearchResultCounter+=1
            WikidataID=SearchResult['id']
            params = {
                'action': 'wbgetentities',
                'format': 'json',
                'ids': WikidataID
            }
            r = requests.get(API_ENDPOINT, params = params)
            CompanyWordIDs=['Q4830453','Q6881511','Q786820','Q42855995','Q15081030']
            #Q4830453 - business
            #Q6881511 - enterprise
            #Q786820 - automobile manufacturer
            #Q42855995 - motorcycle manufacturer
            #Q15081030 - manufacturing company

            if('P1056' in r.json()['entities'][WikidataID]['claims'].keys()):
                print("Good: ",query)
                CorrectBrands.append(query)
                GoodResult=True
                break
            else:
                print("Bad: ",query)

            if(GoodResult):
                GoodResult=False
                break

    return(CorrectBrands)

#Vyhleda alternativni nazvy produktu
#parametry:
# product - hledany produkt
def findProductNames(product):

    API_ENDPOINT = "https://www.wikidata.org/w/api.php"

    query = product
    #vyhledani id zadaneho produktu
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'language': 'cs',
        'search': query
    }

    r = requests.get(API_ENDPOINT, params = params, headers={'User-Agent': 'Mozilla/5.0'})
    #vyhledani alternativni nazvy produktu podle id
    WikidataID=r.json()['search'][0]['id']
    params = {
        'action': 'wbgetentities',
        'format': 'json',
        'ids': WikidataID
    }
    r = requests.get(API_ENDPOINT, params = params)

    result=list()
    result.append(r.json()['entities'][WikidataID]['labels']['cs']['value'])
    #pridani alternativnich nazvu v cestine a anglictine
    try:
        for x in r.json()['entities'][WikidataID]['aliases']['cs']:
            result.append(x['value'])
    except:
        False

    try:
        result.append(r.json()['entities'][WikidataID]['labels']['en']['value'])
        for x in r.json()['entities'][WikidataID]['aliases']['en']:
            result.append(x['value'])
    except:
        False
    #pridani slov obsahujicich diakritiku znovu bez diakritiki pro vyhledavani v url adresách
    for x in result:
        NewProduct=unidecode(u'{0}'.format(x))
        if(len(x)<4):
            result.remove(x)
        if(NewProduct != x):
            result.append(NewProduct)

    return result



