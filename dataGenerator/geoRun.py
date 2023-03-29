from datetime import datetime
from functools import partial
from threading import Thread
import geocoder
import requests
import pandas as pd
import numpy as np
from math import asin, cos, pi, sqrt
from dataGenerator.NewThread import ThreadWithReturnValue
from dataGenerator.closestLocation import ClosestLocation
from dataGenerator.distanceEmission import Emission
import json

def distance(lat1, lon1, lat2, lon2):
    p = pi/180
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
    return 12742 * asin(sqrt(a))

def getDistance(address):

    res = geocoder.osm(address)

    return res.latlng


def calcTotalDistance(adr1,adr2):

    modes = ["air", "water", "rail", "road"]

    modeDict = {modes[i] : i for i in range(len(modes))}

    closestFuncs = [partial(ClosestLocation.nearestAirport),partial(ClosestLocation.nearestPort), partial(ClosestLocation.nearestRailway), partial(ClosestLocation.nearestRoad)]

    costFuncs = [partial(Emission.airEmission),partial(Emission.waterEmission),partial(Emission.railEmission),partial(Emission.roadEmission)]
    
    t1 = ThreadWithReturnValue(target=getDistance, args=(adr1,))

    t1.start()

    t2 = ThreadWithReturnValue(target=getDistance, args=(adr2,))

    t2.start()

    a = t1.join()

    b = t2.join()

    threads = []

    for k in range(len(closestFuncs)):

        threads.append(ThreadWithReturnValue(target = closestFuncs[k], args = (a,)))

        threads[-1].start()

        threads.append(ThreadWithReturnValue(target = closestFuncs[k], args = (b,)))

        threads[-1].start()

    
    result = []


    for i in range(0,len(threads),2):
        # print("=================")
        # print("Mode is " + modes[i // 2])

        d = {}

        d['mode'] = modes[i//2]

        loc1 = threads[i].join()
        loc2 = threads[i + 1].join()

        d['from'] = loc1["Name"]
        d['to'] = loc2["Name"]


        # print("From " + loc1["Name"])
        # print("To " + loc2["Name"])
        # print("Total Emission is: ")

        l1 = (loc1["Latitude"], loc1["Longitude"])
        l2 = (loc2["Latitude"], loc2["Longitude"])

        d1, d2, d3 = distance(l1[0], l1[1],a[0], a[1]), distance(l1[0], l1[1],l2[0], l2[1]), distance(l2[0], l2[1],b[0], b[1])

        road1 = costFuncs[modeDict["road"]](d1)

        modeCalc = costFuncs[i // 2](d2)

        road2 = costFuncs[modeDict["road"]](d3)

        total = road1 + modeCalc + road2
        
        d['initalToPort1_distance'] = d1
        d['initalToPort1_emission'] = road1

        d['port1ToPort2_distance'] = d2
        d['port1ToPort2_emission'] = modeCalc

        d['port2ToFinal_distance'] = d3
        d['port2ToFinal_emission'] = road2


        d['emission'] = total
        # returndict[modes[i // 2]] = d

        result.append(d)

        # print(total)

    return json.dumps({ "source" : adr1, "destination" : adr2,'result' : result})

    


# calcTotalDistance("Kanyakumari", "Shrinagar")
