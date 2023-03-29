import ast
from nis import cat
import geocoder
from datetime import datetime
import json
from math import asin, cos, pi, sqrt
import os
from flask import Flask, jsonify, url_for, redirect, request, Blueprint
import pymongo
from bson.json_util import dumps
from bson import ObjectId
from flask_caching import Cache
from dataGenerator.barcodelookup import getBarcodeInfo
from dataGenerator.closestSupplierInfo import getSupplierInfo
from dataGenerator.distanceEmission import Emission
from dataGenerator.geoRun import calcTotalDistance
from predictor.predict import predictCategory
import redis
from flask_cors import CORS
from google_images_search import GoogleImagesSearch
import requests
from google.cloud import vision
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

client = vision.ImageAnnotatorClient()


API_KEY = config.get('gcp','apiKey')
CX = config.get('gcp','CX')
gis = GoogleImagesSearch(API_KEY, CX)


config = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_HOST": "localhost",
    "CACHE_REDIS_PORT": "6379",
    "CACHE_REDIS_URL": 'redis://localhost:6379'
}

mongoClinet = pymongo.MongoClient(config.get('mongo','url'))
redisclient  = redis.StrictRedis("localhost",port=6379,db=0,charset="utf-8", decode_responses=True)

db = mongoClinet['new']

app = Flask(__name__)
CORS(app)

cache = Cache(app, config = config)

def getImage(name):
    
    res = requests.get("https://www.googleapis.com/customsearch/v1", params={"key" : API_KEY, "cx" : CX, "q" : name})


    for x in json.loads(res.content)["items"]:

        if "pagemap" in x and "cse_thumbnail" in x["pagemap"] and len(x["pagemap"]["cse_thumbnail"]) > 0 and int(x["pagemap"]["cse_thumbnail"][0]["width"]) < 420:
            return x["pagemap"]["cse_thumbnail"][0]["src"]



    return "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/1024px-No_image_available.svg.png"

@app.route('/')
def home_page():
    return 'Welcome to Ecotag!'


@app.route('/getProduct')
def get_product():
    """
    GET request | Returns product details
    Query Params : barcode
    Returns : json containing all the details
    """
    details = request.args
    barcode = details["barcode"]
    
    mongoCollection = db['products']

    return dumps(mongoCollection.find_one({'_id' : barcode}))

@app.route('/getProductsByCategory')
def get_product_by_category():
    """
    GET request | Returns product details
    Query Params : categories
    Returns : json containing all the details
    """
    details = request.args
    cats = []
    for x in details["categories"].split(','):
        cats.append(x.strip())
    
    mongoCollection = db['products']

    return dumps(list(mongoCollection.find({"category" : {"$in" : cats}})))

# Generate a key for product name caching
def productNameKey():
    data = request.args

    return str(data["searchTerm"]).lower()

@app.route('/getProductByName')
@cache.cached(timeout=100, key_prefix=productNameKey)
def get_product_by_name():
    """
    GET request | Returns list of product details
    Query Params : searchTerm
    Returns : json containing all the details
    """
    details = request.args
    searchTerm = details["searchTerm"]
    
    mongoCollection = db['products']

    res = mongoCollection.find(
        { '$text': { '$search': searchTerm } },
        { 'score': { '$meta': "textScore" } }
    ).sort([('score', {'$meta': 'textScore'})])

    return dumps(list(res))

@app.route('/getProductFromManufacturer')
def get_product_from_manufacturer():
    """
    GET request | Returns list of product details
    Query Params : mid
    Returns : json containing all the details
    """
    details = request.args
    mid = details["mid"]
    
    mongoCollection = db['products']

    return dumps(list(mongoCollection.find({"manufacturer" : {"$in" : [mid]}})))
# Generate a key for supplier caching
def supplierKey():
    data = request.args

    return str(data["searchTerm"]).lower()


@app.route('/getSuppliers')
@cache.cached(timeout=50, key_prefix=supplierKey)
def get_supplier():
    """
    GET request | Returns supplier details
    Query Params : searchTerm, latitude, longitude
    Returns : json containing all the details
    """

    details = request.args

    term = details["searchTerm"]
    lat = float(details["latitude"])
    long = float(details["longitude"])
    
    res = getSupplierInfo(term,lat,long)

    return json.dumps(res)

# Generate a key for barcode caching
def barcodeKey():
    data = request.args

    return str(data["barcode"]).lower()

@app.route('/getProductNameByBarcode')
@cache.cached(timeout=0, key_prefix=barcodeKey)
def get_product_name_by_barcode():
    """
    GET request | Returns barcode product
    Query Params : barcode
    Returns : json containing all the details
    """

    details = request.args

    barcode = details["barcode"]

    return getBarcodeInfo(barcode)

@app.route('/getProductDetailsByBarcode')
def get_product_details_by_barcode():
    """
    GET request | Returns barcode product
    Query Params : barcode
    Returns : json containing all the details
    """

    details = request.args

    barcode = details["barcode"]

    mongoCollection = db['products']

    res = mongoCollection.find_one({'_id' : barcode})

    if res:
        return dumps(res)

    redisRes = redisclient.get("flask_cache_" + barcode)

    if redisRes:
        name = json.loads(redisRes)["productName"]
    else:
        name = getBarcodeInfo(barcode)["productName"]

        redisclient.set("flask_cache_" + barcode, json.dumps({"productName":name,"status":"Passed"}))

    predisRed = redisclient.get("flask_cache_cat" + name.lower())

    imgUrl = getImage(name)
    
    # t1 = ThreadWithReturnValue(target = getImage, args = (name,))

    # t1.start()

    if predisRed:
        cats = json.loads(predisRed)
    else:
        cats = predictCategory(name)[:10]

        redisclient.set("flask_cache_cat" + name.lower(), json.dumps(cats))

    

    catId = '+'.join(cats[:5])

    res = db['categoryEmission'].find_one({'_id' : catId})

    emission = 150

    rating = 2.5

    if res:
        emission = res['totalEmission'] / res['totalManufacturers']
    
    # imgUrl = t1.join()

    return dumps({"_id" : "NA", "weight" : -1, "price" : -1,  "category" : cats, "categoryID" : catId,"image_url" : imgUrl, "manufacturer" : [], "name" : name, "rating" : 2.5, "emission" : emission, "totalManufacturers" : 0, 'rawMaterials' : [], 'components' : []})

@app.route('/getAllRoutes')
def get_all_routes():
    """
    GET request | Returns all routes from A to B and its emission
    Query Params : fromAddress, toAddress
    Returns : json containing all the details
    """

    details = request.args

    return calcTotalDistance(details["fromAddress"], details["toAddress"])


@app.route('/getManufacturers')
def get_manufacturers():
    """
    Depreciated
    GET request | Returns all Manufacturers
    Query Params : searchTerm
    Returns : json containing all the details
    """

    details = request.args

    searchTerm = details["searchTerm"]

    mongoCollection = db['manufacturers']

    res = mongoCollection.find(
        { '$text': { '$search': searchTerm } },
        { 'score': { '$meta': "textScore" } }
    ).sort([('score', {'$meta': 'textScore'})])

    return dumps(list(res))

@app.route('/getManufacturer')
def get_manufacturer():
    """
    GET request | Returns the Manufacturer details
    Query Params : mid
    Returns : json containing all the details
    """

    details = request.args

    mid = details["mid"]

    mongoCollection = db['manufacturers']

    res = mongoCollection.find_one({"_id" : mid})

    return dumps(res)

# Generate a key for category caching
def categoryKey():
    data = request.args

    return str("cat" + data["searchTerm"]).lower()

@app.route('/getCategories')
@cache.cached(timeout=0,key_prefix=categoryKey)
def get_categories():
    """
    GET request | Returns category through name
    Query Params : searchTerm
    Returns : json array having top 10 categories
    """

    details = request.args

    searchTerm = details["searchTerm"]

    res = predictCategory(searchTerm)

    return dumps(res[:10])


@app.route('/addManufacturer',methods=['POST'])
def add_manufacturer():
    """
    POST request | Adds a Manufacturer
    Json params : [_id,companyName,lat,long,address,phone]
    """

    details = request.json

    mongoCollection = db['manufacturers']

    res = mongoCollection.insert_one(details)

    return jsonify({'_id' : str(res.inserted_id)}) if res.acknowledged else 'Failed'


@app.route('/addProduct',methods=['POST'])
def add_product():
    """
    POST request | Adds a Product
    Json params : [name, weight, price, category, emission, manufacturer, barcode, rawMaterials, components]
    """

    details = request.json
    mongoCollection = db['products']

    # Details init
    name = details["name"]
    cats = details["category"]
    emission = details["emission"]
    mid = details["manufacturer"]
    barcode = details["barcode"]
    rawMaterials = details['rawMaterials']
    weight = details["weight"]
    price = details["price"]
    components = details["components"]

    imgUrl = getImage(name)

    # Create a category ID
    catId = str(hash("+".join(cats).replace(" ", "")))

    # Increment for that category using upsert
    db['categoryEmission'].update_one({'_id' : catId}, {'$inc' : {'totalEmission' : emission, 'totalManufacturers' : 1, }}, upsert=True)

    # Get total value
    query = db['categoryEmission'].find_one({'_id' : catId})

    tot = query['totalEmission']
    ct = query["totalManufacturers"]

    # Get rating by using a stat formula
    rating = 5 * (tot) / (tot + (emission * (ct - 1)))

    res2 = db['manpro'].insert_one({'category' : cats,'categoryID': catId, 'barcode' : barcode, 'name' : name, 'emission' : emission , 'manufacturer' : mid, 'rawMaterials' : rawMaterials, 'components' : components})

    # Push the product details
    f = mongoCollection.find_one({'_id' : barcode})

    if f is None:
        mongoCollection.insert_one({'_id' : barcode, 'category' : cats, 'name' : name, 'categoryID': catId,'image_url' : imgUrl, 'weight' : weight, "price" : price, 'rating' : rating})

        for m in rawMaterials:

            mongoCollection.update_one({'_id' : barcode}, {'$push': {'rawMaterials': m}})


        for m in components:

            mongoCollection.update_one({'_id' : barcode}, {'$push': {'components': m}})


    res = mongoCollection.update_one({'_id' : barcode},
    {
        '$set' : {'rating' : rating},
        '$push' : {'manufacturer' : mid}, 
        '$inc' : {'totalManufacturers' : 1, 'totalEmission' : emission},
        
    }, upsert= True)

    # Insert into a collection that has mid and pid present linking each person with their product
    res2 = db['manpro'].insert_one({'category' : cats,'categoryID': catId, 'barcode' : barcode, 'name' : name, 'emission' : emission , 'manufacturer' : mid, 'rawMaterials' : rawMaterials, 'components' : components})

    # Update each product in the category to maintain dynamic scoring 
    for row in mongoCollection.find({'categoryID' : catId}):

        bc = row['_id']

        avgEmission = row['totalEmission'] / row['totalManufacturers'] 

        rowRating = 5 * (tot) / (tot + (avgEmission * (ct - 1)))


        mongoCollection.update_one({'_id' : bc}, {'$set' : {'rating' : rowRating}})

    # Append product into the manufacturer thingy
    db["manufacturers"].update_one({'_id' : mid}, {'$push' : {'products' : barcode}})

    details = db["manufacturers"].find_one({'_id' : mid})

    return jsonify({'status' : str(res.acknowledged and res2.acknowledged)})



# returns the shipment statuses to the manufacturer
@app.route('/getShipments')
def get_shipments():
    """
    GET request | Returns shipment details for a manufacturer
    Query Params : manufacturer
    Returns : json containing all the details
    """

    details = request.args

    manufacturer = details["manufacturer"]

    mongoCollection = db['shipments']

    res = mongoCollection.find({'manufacturer' : manufacturer})

    return dumps(list(res))



@app.route('/addShipment',methods=['POST'])
def add_shipment():
    """
    POST request | Adds a shipment
    Json params : [manufacturer, startLocation, pid, totalWeight, currentLat, currentLong]
    dlang and dlong are destination lat and long
    currentLat and currentLong are the lat and long of where the product is added
    jounrey shall be ["Bangalore", "Delhi", "Kolkata"] basically the location names where all it reaches
    """

    details = request.json

    manufacturer = details['manufacturer']

    details["status"] = "PROCESSING"
    details["timestamp"] = datetime.now()
    details["journey"] = [details["startLocation"]]
    details["transportMode"] = "-"
    details["enroute_to"] = "-"
    details["emission"] = 0 # just the carbon so far used. in update we will update this

    mongoCollection = db['shipments']
    res = mongoCollection.insert_one(details)

    db['manufacturers'].update_one({'_id':  manufacturer}, {"$push":{"currentShipments": res.inserted_id} },upsert=True)

    return dumps({'id' : res.inserted_id})

def distance(lat1, lon1, lat2, lon2):

    p = pi/180
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon2-lon1)*p))/2

    return 12742 * asin(sqrt(a))

@app.route('/updateShipment',methods=['POST'])
def update_shipment():
    """
    POST request | Update a shipment
    Json params : [shipmentID, location, transportMode, currentLat, currentLong, enroute_to, status]
    """

    details = request.json

    status = details["status"]

    shipmentID = ObjectId(details["shipmentID"])

    res = db['shipments'].find_one({'_id' : shipmentID})

    prevMode = res["transportMode"]

    emission = 0

    if res["status"] == "TRAVEL":

        prevLat, prevLong = res["currentLat"], res["currentLong"]
        curLat, curLong = details["currentLat"], details["currentLong"]

        if prevMode == "AIR": emission += Emission.airEmission(distance(curLat, curLong,prevLat, prevLong))

        elif prevMode == "WATER" : emission += Emission.waterEmission(distance(curLat, curLong,prevLat, prevLong))

        elif prevMode == "RAIL" : emission += Emission.railEmission(distance(curLat, curLong,prevLat, prevLong))

        elif prevMode == "ROAD" : emission += Emission.roadEmission(distance(curLat, curLong,prevLat, prevLong))



        db['shipments'].update_one(
            {'_id' : shipmentID},
            {
                "$set" : {
                    "transportMode" : details["transportMode"],
                    "status" : status,
                    "currentLat" : details["currentLat"],
                    "currentLong" : details["currentLong"],
                    "enroute_to" : details["enroute_to"]
                },
                '$push' : {'journey' : details["location"]}, 
                '$inc' : {'emission' : emission },
            }
        )

    else:

        db['shipments'].update_one(
            {'_id' : shipmentID},
            {
                "$set" : {
                    "transportMode" : details["transportMode"],
                    "status" : status,
                    "currentLat" : details["currentLat"],
                    "currentLong" : details["currentLong"],
                    "enroute_to" : details["enroute_to"]
                },
                '$inc' : {'emission' : emission },
            }
        )

        if (status == "DELIVERED"):

            state = geocoder.osm([details["currentLat"], details["currentLong"]], method='reverse').state

            ship = db["shipments"].find_one({"_id":ObjectId(details["shipmentID"])})

            prod = db["products"].find_one({"_id" : ship["pid"]})

            db["categoryEmission"].update_one({"_id" : prod["categoryID"]}, {"$inc" : {"states." + state.lower() : 1}}, upsert = True)


    return jsonify({'status' : True})



@app.route('/detectImage',methods=['POST'])
def detect_image():
    direc = os.getcwd()
    path = os.path.join(direc,'test.jpg') 

    if 'Picture' not in request.files:
        return "someting went wrong 1"
    
    user_file = request.files['Picture']


    user_file.save(path)
    with open(path, 'rb') as image_file:
        content = image_file.read()
        image = vision.Image(content=content)
        objects = client.object_localization(image=image).localized_object_annotations
    
        return jsonify({"object" : objects[0].name})


@app.route('/addInspectionForm',methods=['POST'])
def add_inspection_form():
    """
    POST request | Add an inspection form
    Json params : ["manufacturer", "inputFields", "inputTypes", "formName", "makerName"]
    """

    details = request.json

    mname = details["manufacturer"]

    mid = db["manufacturers"].find(
        { '$text': { '$search': mname } },
        { 'score': { '$meta': "textScore" } }
    ).sort([('score', {'$meta': 'textScore'})])[0]["_id"]

    formName = details["formName"]

    makerName = details["makerName"]

    inputFields = details["inputFields"]

    inputTypes = details["inputTypes"]

    cats = set()

    pids = set(db["manufacturers"].find_one({"_id" : mid})["products"])

    for i in pids:

        pcats = db["products"].find_one({"_id" : i})
        if pcats:
            for c in pcats["category"]:

                cats.add(c)


    res = db["forms"].insert_one({"manufacturer" : mid, "inputFields" : inputFields, "inputTypes" : inputTypes, "formName" : formName, "makerName" : makerName, "targetCategories" : list(cats)})
    
    return json.dumps({"status" : res.acknowledged })



@app.route('/getInspectionForms')
def get_inspection_forms():

    return dumps(list(db["forms"].find()))


@app.route('/getStates')
def get_states():

    details = request.args

    return dumps(db["categoryEmission"].find_one({"_id" : details["categoryID"]}))


@app.route('/reverseLoc')
def reverse_loc():

    details = request.args

    return dumps({"state" : geocoder.osm([details["lat"], details["long"]], method='reverse').state})

@app.route('/enterFormValues',methods=['POST'])
def enter_form_value():

    """
    POST request | Add an inspection form
    Json params : ["manufacturer", "inputFields", "inputTypes", "formName", "makerName"]
    """

    details = request.json
    formid = details["id"]
    formValues = details["formValues"]

    res = db["formEntries"].insert_one({"formid" : formid, "values" : formValues})

    return json.dumps({"status" : res.acknowledged })

if __name__ == "__main__":
    app.run('0.0.0.0',443,ssl_context=('/etc/letsencrypt/live/back.ecotag.dev/fullchain.pem', '/etc/letsencrypt/live/back.ecotag.dev/privkey.pem'))