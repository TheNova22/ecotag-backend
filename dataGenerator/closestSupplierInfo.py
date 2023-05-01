from math import cos, asin, sqrt, pi
# import redis
import requests as req
from bs4 import BeautifulSoup
import geocoder
import json

def distance(lat1, lon1, lat2, lon2):
    p = pi/180
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
    return 12742 * asin(sqrt(a))



def getSupplierInfo(query,l1,l2):
    page = 1
    # redisclient  = redis.Redis("localhost",port=6379,db=0)
    searchtext = query.split()
    searchparam = "%20".join(searchtext)
    # data = redisclient.get(searchparam)
    data = None
    if data is not None:
        tosend = json.loads(data)
    else:
        url = "https://www.tradeindia.com/search.html?loggedin_sellers=0&loggedin_profiles_list=0&keyword={}".format(searchparam)
        body = req.get(url).content
        with open("hi.html","w") as f:
            f.write(str(body))
        soup = BeautifulSoup(body,features="html.parser")
        x = soup.find("script",attrs={"type":"application/json"})
        y = json.loads(x.text)
        y = y["props"]["pageProps"]["serverData"]["searchListingData"]["listing_data"]
        data = []
        print(len(y))
        for i in y:
            d = {}

            d['product_title'] = i.get("long_tail_prod_name"," ".join(searchtext))
            d["price"] = i.get("price","Contact to get Price")
            d['image_url'] =  i.get("product_image","")
            d['manufacturer_name'] = i.get("co_name","")
            addresstemp = i.get("address","Online")
            d['manufacturer_address'] = i.get("address","call to get address")
            urltemp = i.get("prod_url","")
            d['product_link'] = "https://www.tradeindia.com" + (urltemp if urltemp else "")
            addresstemp = i.get("state","Delhi")
            g = geocoder.osm(addresstemp)
            if g:
                d['osm'] = {'lat' : g.json['lat'],'lng':g.json['lng']}
            data.append(d)
        for d in data:
            if "osm" in d:
                d['distance'] = distance(l1,l2,d['osm']['lat'],d['osm']['lng'])
                print(d["distance"])
    return data

# print(getSupplierInfo("Mix fruit jam",12.930000569995991, 77.61684039833547))
