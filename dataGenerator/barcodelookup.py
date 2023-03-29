# import redis
import requests as req
from bs4 import BeautifulSoup
import json
from dataGenerator.googlething import scrapergoogle
 
# methodology : 

"""
# no other way is there. barcodes are not stored in any centralized way so each shop contains its own repo of information pertaining to each barcode
first search on  https://barcode-list.com/barcode/EN/Search.htm?barcode={barcode} if there is something, then send taht
else  : use https://world.openfoodfacts.org/product/{barcode}
else : https://www.barcodelookup.com/{barcode}
else:  Nothing found.  
"""

def scrape1(barcode):
    url = "https://barcode-list.com/barcode/EN/Search.htm?barcode={}".format(barcode)
    print(url)
    soup = BeautifulSoup(req.get(url).content,features="html.parser")
    # print(soup)
    x = soup.find("h1",attrs={"class":"pageTitle"}).text
    if x:
        if "Search For" not in x:
            return {"productName":x.split("-")[0],"status":"Passed"}

def scrape2(barcode):
    # openfoodfacts.com
    url = "https://world.openfoodfacts.org/product/{}".format(barcode)
    print(url)
    soup = BeautifulSoup(req.get(url).content,features="html.parser")
    # print(soup)
    x = soup.find("title").text
    if x != "Error":
        return {"productName":x,"status":"Passed"}

def scrape3(barcode):
    url = "https://barcodereport.com/{}".format(barcode)
    # print(url)
    soup = BeautifulSoup(req.get(url).content,features="html.parser")
    # print(soup)
    x = soup.find("h1",attrs={"class":"mb-3"})
    if x:
        return {"productName":x.text,"status":"Passed"}

def scrape4(barcode):
    res = scrapergoogle(barcode)

    if res[1] != "NA":
        return {'productName': res[0],"status":"Passed"}

   

def getBarcodeInfo(barcode):
    functions = [scrape4,scrape1,scrape2,scrape3]
    ret = None
    for f in functions:
        ret = f(barcode)
        if ret:
            return ret
    return {"status":"Failed","barcode":barcode}
# print(getBarcodeInfo('8901425074008'))
# r = ["8904132918467","9780099590392","8901138511470","4987176018779","6001065034126"]
     
    # redisclient.set(searchparam, json.dumps(data))
   
    # print(req.get(url).content)
    # print(url)
# print(getSupplierInfo("Mix fruit jam",12.930000569995991, 77.61684039833547))
# print(getBarcodeInfo("8903754000062"))