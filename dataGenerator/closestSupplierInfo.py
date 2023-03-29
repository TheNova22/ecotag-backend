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
        url = "https://www.tradeindia.com/search.html?loggedin_sellers=0&loggedin_profiles_list=0&keyword={}&search_form_id=18&list_type=search&paginate=1&page_no={}&_=1659683889285".format(searchparam,page)
        soup = BeautifulSoup(req.get(url).content,features="html.parser")
        x = soup.findAll("li",attrs={"class":"bx--row product-box fullContainerBg relative"})
        data = []
        for i in x:
            d = {}
            pricetemp = i.find("span",attrs={"class":"fs-16 font-w-500 priceColor"})
            d["price"] = "" if not pricetemp else pricetemp.text.strip()

            if d["price"] == "":
                continue
            # image url first
            imgtemp = i.find('img')['src'] 
            d['image_url'] = imgtemp if imgtemp else ""

            
            # print(pricetemp.text)

            # name of product 2nd 
            headertemp = i.find('h3').text
            d['product_title'] = headertemp if headertemp else " ".join(searchtext)
            # manufacturer name
            nametemp = i.find('div',attrs={"class":"text-6 companyNameMobile"}).text
            d['manufacturer_name'] = nametemp if nametemp else " ".join(searchtext)
            # manufacture address
            addresstemp = i.find('div',attrs={"class":"feature-list"}).text.split('\n')[0]
            addresstemp = addresstemp.replace('Online','')
            # print(addresstemp)
            d['manufacturer_address'] = addresstemp if addresstemp else "call to get address"
            # get direct link to the product
            urltemp = i.find('a')['href']
            d['product_link'] = "https://www.tradeindia.com/" + (urltemp if urltemp else "")
            g = geocoder.osm(addresstemp)
            # print(addresstemp)
            d['osm'] = {'lat' : g.json['lat'],'lng':g.json['lng']}
            data.append(d)
        # redisclient.set(searchparam, json.dumps(data))
        for d in data:
            d['distance'] = distance(l1,l2,d['osm']['lat'],d['osm']['lng'])
        # with open("./hekki.json",'w') as f:
        #     json.dump({"products":data},f,indent=4)
    return data
        
        # print(req.get(url).content)
        # print(url)
# print(getSupplierInfo("Mix fruit jam",12.930000569995991, 77.61684039833547))