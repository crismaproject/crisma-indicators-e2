"""
Peter Kutschera, 2013-09-11
Update to create KPI also, 2014-11-27
Time-stamp: "2015-04-08 08:49:47 peter"

The server gets an ICMM worldstate URL and calculates an indicator and an KPI from OOI-data

Creation of a new indicator:
1. Copy this file
2. Update identifier - need to match file name
3. Update title
4. Update abstract
5. Replace the code inside of calculateIndicator()
6. Copy the file into the processes directory
7. Update __init__.py in the processes directory


This programm needs an recent requests library:
pip install requests --upgrade
"""

"""
    Copyright (C) 2014  AIT / Austrian Institute of Technology
    http://www.ait.ac.at
 
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as
    published by the Free Software Foundation, either version 2 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
 
    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see http://www.gnu.org/licenses/gpl-2.0.html
"""


from pywps.Process import WPSProcess                                
from sys import stderr
import json
import requests
import urllib
from xml.sax.saxutils import escape
import time
import logging

from crisma.Indicator import Indicator
import crisma.ICMMtools as ICMM
import crisma.OOItools as OOI

class Process(Indicator):
    def __init__(self):
        # init process
        Indicator.__init__(
            self,
            identifier="Weather", #the same as the file name
            version = "1.0",
            title="Weather conditions",
            abstract="""Weather conditions.

indicator;Weather;Weather;Weather conditions;number
kpi;Weather;Weather;Weather conditions;number
""")


    def calculateIndicator(self):
        # Define values to be used if indicator can not be calculated (e.g. missing input data)
        self.result = {
            'kpi': {
                "Situation": {
                    "displayName": "Situation",
                    "iconResource": "flower_16.png",
                    "Weather": {
                        "displayName": "Weather",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": "enum"
                        }
                    }
                }
            }
        
        # calculate indicator value

        weather = -1

        params = {
            'wsid' : self.OOIworldstate.id, 
            'etpid' : 135      # Environment-WinterSummer	Values 1-5 (1 hot summer, 5-heavy winter)
            }
        jsonData = OOI.getJson ("{0}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 

        self.status.set("Got input data", 21)

        for ep in jsonData:
            weather = ep["entityPropertyValue"]
        
        self.status.set("Calculated weather-conditions: {0}".format (weather), 29)

        
        # create indicator value structure
        self.result['indicator'] = {
                    'id': 'Weather',
                    'name': "Weather",
                    'description': "Weather conditions",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "number",
                    'data': weather
                    }

        self.result['kpi']['Situation']['Weather']['value'] = weather

        return 
