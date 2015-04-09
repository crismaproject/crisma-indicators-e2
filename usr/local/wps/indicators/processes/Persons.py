"""
Peter Kutschera, 2013-09-11
Update to create KPI also, 2014-11-27
Time-stamp: "2015-04-08 17:47:24 peter"

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
            identifier="Persons", #the same as the file name
            version = "1.0",
            title="Person related",
            abstract="""Count patients and responders.

indicator;Patients;Patients;Number of patients;number
kpi;Patients;Patients;Number of patients;number
indicator;PatientsThatWalk;Walking patients;Number of patients that can walk;number
kpi;PatientsThatWalk;Walking patients;Number of patients that can walk;number
indicator;Responders;Responders;Number of responders;number
kpi;Responders;Responders;Number of responders;number
indicator;RespondersPerPatient; Responders per Patient: Responder / Patient ratio;number
kpi;RespondersPerPatient; Responders per Patient: Responder / Patient ratio;number
""")


    def calculateIndicator(self):
        # Define values to be used if indicator can not be calculated (e.g. missing input data)
        self.result = {
            'kpi': {
                "Situation": {
                    "displayName": "Situation",
                    "iconResource": "flower_16.png",
                    "Patients": {
                        "displayName": "Patients",
                        "iconResource": "flower_dead_16.png",
                        "value": 0,
                        "unit": "Persons"
                        },
                    "PatientsThatWalk": {
                        "displayName": "Walking patients",
                        "iconResource": "flower_dead_16.png",
                        "value": 0,
                        "unit": "Persons"
                        }
                    },
                "Tactics": {
                    "displayName": "Tactics",
                    "iconResource": "flower_16.png",
                    "Responders": {
                        "displayName": "Responders",
                        "iconResource": "flower_dead_16.png",
                        "value": 0,
                        "unit": "Persons"
                        },
                    "ResponderPerPatient": {
                        "displayName": "Responders per Patient",
                        "iconResource": "flower_dead_16.png",
                        "value": 0,
                        "unit": ""
                        }
                    }
                }
            }

        # calculate indicator value

        # number of patients
        self.status.set("Start collecting input data for numberOfPatients", 20)

        patientsIdList = []

        params = {
            'wsid' : self.OOIworldstate.id, 
            'etpid' : 476       # patient-is-exposed
            }
        jsonData = OOI.getJson ("{0}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 

        self.status.set("Got input data", 21)

        for ep in jsonData:
            exposed = ep["entityPropertyValue"]
            if exposed:
                patientsIdList.append (ep["entityId"])
        
        numberOfPatients = len (patientsIdList)

        self.status.set("Calculated number of patients: {0}".format (numberOfPatients), 29)


        # number of patients that can walk
        self.status.set("Start collecting input data for numberOfPatientsThatWalk", 30)

        numberOfPatientsThatWalk = 0;

        params = {
            'wsid' : self.OOIworldstate.id, 
            #'etpid' : 473       # Injury-Type-Identifyer
            'etpid' : 205        # Can-Walk: Yes / No / Dynamic
            }
        jsonData = OOI.getJson ("{0}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 

        self.status.set("Got input data", 31)

        for ep in jsonData:
            if ep["entityId"] in patientsIdList:
                canWalk = ep["entityPropertyValue"]
                if 'Yes' == canWalk:
                    numberOfPatientsThatWalk += 1;
                elif 'No' == canWalk:
                    pass # fine
                else:
                    #BAD!!
                    logging.error ("Found patient {0} with Can-Walk property '{1}'".format (ep["entityId"], canWalk))
        
        self.status.set("Calculated number of patients that walk: {0}".format (numberOfPatientsThatWalk), 49)


        # number of patients that can walk
        self.status.set("Start collecting input data for numberOfResonders", 40)

        # over all wordstates up to now:
        #   find vehicles involved (DisplayState != 'Idle')
        # for all involved vehicles:
        #   sum up vehicle-num-of-responders

        numberOfResponders = 0
        vehiclesIds = {}

        icmmWorldstates = ICMM.getParentWorldstates (self.ICMMworldstate.id, baseCategory="Baseline", baseUrl=self.ICMMworldstate.endpoint)
        for icmmWs in icmmWorldstates:
            ooiWsURL = ICMM.getOOIRef (icmmWs, 'OOI-worldstate-ref', baseUrl=self.ICMMworldstate.endpoint)
            ooiWs = OOI.OOIAccess(ooiWsURL)
            params = {
                'wsid' : ooiWs.id, 
                'etpid' : 327 # Display-State
            }
            jsonData = OOI.getJson ("{0}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 
            for ep in jsonData:
                displayState = ep["entityPropertyValue"]
                if 'Idle' != displayState:
                    vehiclesIds[ep["entityId"]] = 1

        self.status.set("Got vehicle input data: {0} used vehicles".format (len (vehiclesIds)), 41)
         

        params = {
            'wsid' : self.OOIworldstate.id, 
            'etpid' : 600  # Vehicle-Num-of-responders
            }
        jsonData = OOI.getJson ("{0}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 

        self.status.set("Got vehicle-num-of-responders data", 42)

        for ep in jsonData:
            logging.info (ep)
            if ep["entityId"] in vehiclesIds:
                numResponders = float (ep["entityPropertyValue"].replace (",", "."))
                logging.info ("numResponders = {0}".format (numResponders))
                numberOfResponders += numResponders
        
        self.status.set("Calculated number of responders: {0} in {1} vehicles".format (numberOfResponders, len (vehiclesIds)), 49)

        respondersPerPatient = (numberOfResponders / numberOfPatients) if numberOfPatients > 0 else 0

        self.status.set("Calculated number of responders per patient: {0}".format (respondersPerPatient), 59)

        
        # create indicator value structure
        self.result = {
            'indicator': [
                {
                    'id': 'Patients',
                    'name': "Patients",
                    'description': "Number of patients",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "number",
                    'data': numberOfPatients
                    },
                {
                    'id': 'PatientsThatWalk',
                    'name': "Walking patients",
                    'description': "Number of patients that can walk",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "number",
                    'data': numberOfPatientsThatWalk
                    },
                {
                    'id': 'Responders',
                    'name': "Responders",
                    'description': "Number of Responders",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[icmmWorldstates],
                    'type': "number",
                    'data': numberOfResponders
                    },
                {
                    'id': 'RespondersPerPatient',
                    'name': "Responder per Patient",
                    'description': "Responder / Patient ratio",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[icmmWorldstates],
                    'type': "number",
                    'data': respondersPerPatient
                    }
                ],
            'kpi': {
                "Situation": {
                    "displayName": "Situation",
                    "iconResource": "flower_16.png",
                    "Patients": {
                        "displayName": "Patients",
                        "iconResource": "flower_dead_16.png",
                        "value": numberOfPatients,
                        "unit": "Persons"
                        },
                    "PatientsThatWalk": {
                        "displayName": "Walking patients",
                        "iconResource": "flower_dead_16.png",
                        "value": numberOfPatientsThatWalk,
                        "unit": "Persons"
                        }
                    },
                "Tactics": {
                    "displayName": "Tactics",
                    "iconResource": "flower_16.png",
                    "Responders": {
                        "displayName": "Responders",
                        "iconResource": "flower_dead_16.png",
                        "value": numberOfResponders,
                        "unit": "Persons"
                        },
                    "ResponderPerPatient": {
                        "displayName": "Responders per Patient",
                        "iconResource": "flower_dead_16.png",
                        "value": respondersPerPatient,
                        "unit": ""
                        }
                    }
                }
            }
        return 
