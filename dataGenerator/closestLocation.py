from datetime import datetime
import geocoder
import requests
import pandas as pd
import numpy as np
import math

class ClosestLocation:

    @staticmethod
    def nearestAirport(loc):

        airports = pd.read_csv("dataGenerator/datasets/airports.csv")

        l, lg = np.array(airports["Latitude"]), np.array(airports["Longitude"])

        airLocs = [(l[i], lg[i], i) for i in range(len(l))]

        x = min(airLocs, key = lambda k : math.dist(k[:-1],loc))

        return airports.iloc[x[2]]

    @staticmethod
    def nearestPort(loc):
        ports = pd.read_csv("dataGenerator/datasets/ports.csv")

        l, lg = np.array(ports["Latitude"]), np.array(ports["Longitude"])

        portLocs = [(l[i], lg[i], i) for i in range(len(l))]

        x = min(portLocs, key = lambda k : math.dist(k[:-1],loc))

        return ports.iloc[x[2]]

    @staticmethod
    def nearestRailway(loc):
        rail = pd.read_csv("dataGenerator/datasets/rail_terminals.csv")

        l, lg = np.array(rail["Latitude"]), np.array(rail["Longitude"])

        railLocs = [(l[i], lg[i], i) for i in range(len(l))]

        x = min(railLocs, key = lambda k : math.dist(k[:-1],loc))

        return rail.iloc[x[2]]

    @staticmethod
    def nearestRoad(loc):

        road = pd.read_csv("dataGenerator/datasets/road_terminals.csv")
        l, lg = np.array(road["Latitude"]), np.array(road["Longitude"])

        roadLocs = [(l[i], lg[i], i) for i in range(len(l))]

        x = min(roadLocs, key = lambda k : math.dist(k[:-1],loc))

        return road.iloc[x[2]]

