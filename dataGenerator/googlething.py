from requests import get
import json,re
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

blacklist = ["smartconsumer.org.in"]
KEY = config.get('gcp','apiKey')
CX = config.get('gcp','CX')
url = "https://www.googleapis.com/customsearch/v1?key=" + KEY +  "&cx=" + CX + "&q=8901324061239"



def scrapergoogle(code):
    
    url = f"https://www.googleapis.com/customsearch/v1?key={KEY}&cx={CX}&q=" + code
    x = get(url)
    print(url)
    js = json.loads(x.text)
    if "items" in js and js["items"]:
        for item in js["items"]:
            blackflag = False
            for black in blacklist:
                if black in item['link']:
                    blackflag = True
                    break
            if blackflag:continue
            tit = item["title"].lower()
            tit = re.split(" online",tit)[0]
            tit = re.split(" in",tit)[0]
            tit = re.split(" from",tit)[0]
            tit = re.sub("buy ","",tit)        
            tit = re.sub("\.\.\.","",tit)
            return (tit.title(),item["link"])
    return ("NOT FOUND","NA")
    # print(d)

