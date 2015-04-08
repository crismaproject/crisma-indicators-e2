"""
Peter Kutschera, 2013-09-11
Update to create KPI also, 2014-11-27
Time-stamp: "2015-04-08 08:56:15 peter"

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
import datetime
import dateutil.parser

from crisma.Indicator import Indicator
import crisma.ICMMtools as ICMM
import crisma.OOItools as OOI

class Process(Indicator):
    def __init__(self):
        # init process
        Indicator.__init__(
            self,
            identifier="Times", #the same as the file name
            version = "1.0",
            title="Time related",
            abstract="""Calculate some time intervals.

indicator;SecoundResourceRequest;Secound Resource Request;Time until Secound Resource Request;timeintervals
kpi;SecoundResourceRequest;Secound Resource Request;Time until Secound Resource Request;number

indicator;LastPreTriage;Last Pre-Triage;Time until all patients got pre-triage;timeintervals
kpi;LastPreTriage;Last Pre-Triage;Time until all patients got pre-triage;number

indicator;FirstReadTreated;First red Patient treated;Time until first red Patient treated;timeintervals
kpi;FirstReadTreated;First red Patient treated;Minutes until first red Patient treated;number

indicator;LastRedTreated;Last red Patient treated;Time until all red patients are treated;timeintervals
kpi;LastRedTreated;Last red Patient treated;Time until all red patients are treated;number

indicator;LastRedEvacuated;Last red Patient evacuated;Time until all red patients are evacuated;timeintervals
kpi;LastRedEvacuated;Last red Patient evacuated;Time until all red patients are evacuated;number

indicator;LastRedInHospital;Last red Patient in Hospital;Time until all red patients are in a hospital;timeintervals
kpi;LastRedInHospital;Last red Patient in Hospital;Time until all red patients are in a hospital;number

indicator;LastInHospital;Last Patient in Hospital;Time until all patients are in a hospital;timeintervals
kpi;LastInHospital;Last Patient in Hospital;Time until all patients are in a hospital;number

indicator;LoadingAreaBuild;Loading-Area build;Time until first loading area is build;timeintervals
kpi;LoadingAreaBuild;Loading-Area build;Time until first loading area is build;number

indicator;StagingAreaBuild;Staging-Area build;Time until first staging area is build;timeintervals
kpi;StagingAreaBuild;Staging-Area build;Time until first staging area is build;number

indicator;TreatmentAreaBuild;Treatment-Area build;Time until first treatment area is build;timeintervals
kpi;TreatmentAreaBuild;Treatment-Area build;Time until first treatment area is build;number

indicator;UsedTacticalAreas;Used Tactical Areas;Number of tactical areas used;histogram
kpi;UsedTacticalAreas;Used Tactical Areas;Number of tactical areas used;number

""")



    def getTimeFromICMMws (self, wsid):
        params = {
            'level' :  1,
            'fields' : "simulatedTime",
            'omitNullValues' : 'true',
            'deduplicate' : 'true'
            }
        headers = {'content-type': 'application/json'}
        response = requests.get("{0}/{1}.{2}/{3}".format (self.ICMMworldstate.endpoint, self.ICMMworldstate.domain, "worldstates", wsid), params=params, headers=headers) 
        if response.status_code != 200:
            raise Exception ( "Error accessing ICMM at {0}: {1}".format (response.url, response.status_code))
        # Depending on the requests-version json might be an field instead of on method
        jsonData = response.json() if callable (response.json) else response.json

        ts = jsonData['simulatedTime']
        if (len(ts) == 16):
            ts = ts + ":00.0Z"
        return dateutil.parser.parse (ts)

    def calculateIndicator(self):
        # Define values to be used if indicator can not be calculated (e.g. missing input data)
        self.result = {
            'indicator': [],
            'kpi': {
                "Tactics": {
                    "displayName": "Tactics",
                    "iconResource": "flower_16.png",

                    "SecoundResourceRequest": {
                        "displayName": "Secound Resource Request",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": "minutes"
                        }
                    "UsedTacticalAreas": {
                        "displayName": "Used Tactical Areas",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": ""
                        }
                    },

                "Accomplishment": {
                    "displayName": "Accomplishment",
                    "iconResource": "flower_16.png",


                    "LastPreTriage": {
                        "displayName": "All patients got pre-triage",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": "minutes"
                        },
                    'FirstRedTreated': {
                        "displayName": "First red Patient treated",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": "minutes"
                        },
                    'LastRedTreated': {
                        "displayName": "Last red Patient treated",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": "minutes"
                        },
                    'LastRedEvacuated': {
                        "displayName": "Last red Patient evacuated",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": "minutes"
                        },
                    'LastRedInHospital': {
                        "displayName": "Last red Patient in Hospital",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": "minutes"
                        },
                    'LoadingAreaBuild': {
                        "displayName": "Loading Area build",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": "minutes"
                        },
                    'StagingAreaBuild': {
                        "displayName": "Staging Area build",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": "minutes"
                        },
                    'TreatmentAreaBuild': {
                        "displayName": "Treatment Area build",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": "minutes"
                        },
                    'LastInHospital': {
                        "displayName": "Last Patient in Hospital",
                        "iconResource": "flower_dead_16.png",
                        "value": -1,
                        "unit": "minutes"
                        }
                    }
                }
            }
            
        self.status.set("Start collecting input data", 20)

        # calculate indicator value
        # find base WorldState from ICMM
        parents = ICMM.getParentWorldstates (self.ICMMworldstate.id, baseCategory="Baseline", baseUrl=self.ICMMworldstate.endpoint)
        if (parents is None):
            raise Exception ("Base ICMM WorldState not found for actual ICMM WorldState = {0}".format (self.ICMMworldstate))

        basewsid = parents[0]

        logging.info ("get start time from ws {0}".format (basewsid))
        t0 = self.getTimeFromICMMws (basewsid)  # incident time
        # tNow = self.getTimeFromICMMws (self.ICMMworldstate.id) # this WorldState
        minutesSecondVehicle = None  # 2nd vehicle request
        tLastPreTriage = None  # Last patient has been pre-triaged
        tFirstRedTreated = None # 1st red patient treated
        tLastRedTreated = None # last red patient treated
        tLastRedEvacuated = None # last red patient evacuated
        tLastRedInHospital = None # last red patient in hospital
        tLoadingAreaBuild = None 
        tStagingAreaBuild = None
        tTreatmentAreaBuild = None
        tLastInHospital = None # last patient in hospital
        usedTacticalAreas = -1

        # count patients - needed to answer questions like "When got the LAST patient ....?"
        # Answer: When ...  was true for each patient in at least one previous WS
        # This is only done once as it never changes (No one is born or dies)
        patientsIdList = None 
        redPatientsIdList = None 
        # list of patient that where already ....
        preTriageList = {}
        redTreatedList = {}
        redEvacuatedList = {}
        redInHospitalList = {}
        inHospitalList = {}
        # Area lists
        areaIdLists = None
        # Vehicle command times
        vehicleCommandTimes = []

        for i in range (0, len (parents)):
            wsid = parents[i]
            logging.info ("get ws {0}".format (wsid))
            ooiWorldstateURL = ICMM.getOOIRef (wsid, 'OOI-worldstate-ref', baseUrl=self.ICMMworldstate.endpoint)
            logging.info ("  ooiWorldstateURL = {0}".format (ooiWorldstateURL))
            if (ooiWorldstateURL is None):
                return "invalid OOI URL: {0}".format (ooiWorldstateURL)
            # OOI-URL -> Endpoint, id, ...
            ooiWorldstate = OOI.OOIAccess(ooiWorldstateURL)
            # logging.info ("ooiWorldState = {0}".format (ooiWorldstate))
            if (ooiWorldstate.endpoint is None):
                return "invalid OOI ref: {0}".format (ooiWorldstate)
        

            logging.info("Request input data for OOI WorldState = {0}".format (ooiWorldstate.id))
            params = {
                'wsid' :  ooiWorldstate.id 
                }
            jsonData = OOI.getJson ("{0}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 

            # this now contaions ALL EntityPropertyIds !
            
            if patientsIdList == None:
                logging.info ("looking for exposed patients")
                patientsIdList = []
                for ep in jsonData:
                    if (476 != ep["entityTypePropertyId"]):       # patient-is-exposed
                        continue
                    exposed = ep["entityPropertyValue"]
                    if exposed:
                        patientsIdList.append (ep["entityId"])
                logging.info (" found {0} exposed patients: {1}".format (len (patientsIdList), patientsIdList))
                logging.info (" looking for RED exposed patients")
                redPatientsIdList = []
                # 2 steps: 
                # 1.: injuryType -> Default_Triage-Level (201)
                injuryTypeTriageLevel = {}
                for ep in jsonData:
                    if (201 != ep["entityTypePropertyId"]):      # Injury-type
                        # skip properties I am not interested in
                        continue
                    # Needs to be a string. If not this is an error. Just silently skip to get an result anyway!
                    if ep["entityTypeProperty"]['entityTypePropertyType'] != 2: 
                        logging.error (" Property default_Traige-Lavel (201) is not of type 2 (String)!")
                        continue 
                    logging.info ("  injuryTypeTriageLevel[{0}] = {1}".format (ep['entityId'], ep["entityPropertyValue"]))
                    injuryTypeTriageLevel[ep['entityId']] = ep["entityPropertyValue"]
                # 2. filter patients: parientId -> InjuryType (473); 
                for ep in jsonData:
                    if ep["entityId"] not in patientsIdList:
                        # skip patients not involved
                        continue
                    if (473 != ep["entityTypePropertyId"]):      # Injury-type
                        # skip properties I am not interested in
                        continue
                    # But within the dataset: is of type 1 (number), but contains a string !!
                    epv = int (float (ep["entityPropertyValue"]))
                    if epv not in injuryTypeTriageLevel:
                        logging.error ("  injuryType {1} of patient {0} not found!".format (ep["entityId"], ep["entityPropertyValue"]))
                        continue 
                    if (injuryTypeTriageLevel[epv] == 'RED'):
                        redPatientsIdList.append (ep["entityId"])
                logging.info (" found {0} RED exposed patients: {1}".format (len (redPatientsIdList), redPatientsIdList))

            # create area lists
            if areaIdLists == None:
                logging.info ("looking for areas")
                areaIdListsAll = {}
                for ep in jsonData:
                    if (54 != ep["entityTypePropertyId"]):       # Area
                        continue
                    areaType = ep["entityPropertyValue"]
                    areaIdListsAll[ep["entityId"]] = areaType
                logging.info (" looking for active areas within {0} existing areas".format (len (areaIdListsAll)))
                areaIdLists = {}
                tacticalAreas = ['Danger-Zone', 'Advanced-Medical-Post', 'Treatment', 'Loading', 'Staging']
                usedTacticalAreas = 0
                for ep in jsonData:
                    if (547!= ep["entityTypePropertyId"]):       # Area IsEnabled
                        continue
                    enabled = ep["entityPropertyValue"]
                    if enabled:
                        areaType = areaIdListsAll[ep["entityId"]]
                        if areaType in tacticalAreas:
                            usedTacticalAreas += 1
                        if areaType not in areaIdLists:
                            areaIdLists[areaType] = []
                        areaIdLists[areaType].append (ep["entityId"])
                

                for areaType in areaIdLists:
                    logging.info (" found {0} {1} areas".format (len (areaIdLists[areaType]), areaType))
                logging.info (" Number of used tactical areas: {0}".format (usedTacticalAreas))
               


            if minutesSecondVehicle == None:
                logging.info ("Looking for vehicle commands") 
                for ep in jsonData:
                    if (2 != ep["entityTypePropertyId"]):  # Vehicle Request-Time
                        # skip properties I am not interested in
                        continue
                    try:
                        minutes = float (ep["entityPropertyValue"].replace (",", "."))
                        vehicleCommandTimes.append (minutes)
                    except:
                        logging.error (" etpid=2: entityPropertyValue is not a number: {0}!".format (ep["entityPropertyValue"]))
                        # ignore problem !?!?
                        pass

                if len (vehicleCommandTimes) > 1:
                    vehicleCommandTimes = sorted (set (vehicleCommandTimes))
                    if len (vehicleCommandTimes) > 1:
                        minutesSecondVehicle = vehicleCommandTimes[1]
                        logging.info ( " 2nd order for vehicles after {0} minutes".format (minutesSecondVehicle))




            if tLastPreTriage == None:
                logging.info ("looking for patient with Treatment-State == 'Pre-Triaged'")
                for ep in jsonData:
                    if ep["entityId"] not in patientsIdList:
                        # skip patients not involved
                        continue
                    if (OOI.patientTreatmentStatePropertyId != ep["entityTypePropertyId"]):
                        # skip properties I am not interested in
                        continue
                    # Needs to be a string. If not this is an error. Just silently skip to get an result anyway!
                    if ep["entityTypeProperty"]['entityTypePropertyType'] != 2: 
                        logging.error (" Property Treatment-State is not of type 2 (String)!")
                        continue 
                    if (ep["entityPropertyValue"] == 'Pre-Triaged'):
                        preTriageList[ep["entityId"]] = 1

                logging.info (" {0} out of {1} patients where already pre-triaged".format (len (preTriageList), len (patientsIdList)))

                if len (preTriageList) == len (patientsIdList):
                    tLastPreTriage = self.getTimeFromICMMws (wsid)

            

            if tFirstRedTreated == None:
                logging.info ("looking for 1st RED patient with Treatment-State == 'On-Site-Treatment'")
                for ep in jsonData:
                    if ep["entityId"] not in redPatientsIdList:
                        # skip patients not involved
                        continue
                    if (OOI.patientTreatmentStatePropertyId != ep["entityTypePropertyId"]):
                        # skip properties I am not interested in
                        continue
                    # Needs to be a string. If not this is an error. Just silently skip to get an result anyway!
                    if ep["entityTypeProperty"]['entityTypePropertyType'] != 2: 
                        logging.error (" Property Treatment-State is not of type 2 (String)!")
                        continue 
                    if (ep["entityPropertyValue"] == 'On-Site-Treatment'):
                        tFirstRedTreated = self.getTimeFromICMMws (wsid)
                        logging.info (" found red patient with Treatment-State == 'On-Site-Treatment'")
                        break;



            if tLastRedTreated == None:
                logging.info ("looking for RED patient with Treatment-State == 'Treated'")
                for ep in jsonData:
                    if ep["entityId"] not in redPatientsIdList:
                        # skip patients not involved
                        continue
                    if (OOI.patientTreatmentStatePropertyId != ep["entityTypePropertyId"]):
                        # skip properties I am not interested in
                        continue
                    # Needs to be a string. If not this is an error. Just silently skip to get an result anyway!
                    if ep["entityTypeProperty"]['entityTypePropertyType'] != 2: 
                        logging.error (" Property Treatment-State is not of type 2 (String)!")
                        continue 
                    if (ep["entityPropertyValue"] == 'Treated'):
                        redTreatedList[ep["entityId"]] = 1

                logging.info (" {0} out of {1} RED patients where already treated".format (len (redTreatedList), len (redPatientsIdList)))

                if len (redTreatedList) == len (redPatientsIdList):
                    tLastRedTreated = self.getTimeFromICMMws (wsid)
                





            if tLastRedEvacuated == None:
                logging.info ("looking for RED patient with Treatment-State == 'Evacuating'")
                for ep in jsonData:
                    if ep["entityId"] not in redPatientsIdList:
                        # skip patients not involved
                        continue
                    if (OOI.patientTreatmentStatePropertyId != ep["entityTypePropertyId"]):
                        # skip properties I am not interested in
                        continue
                    # Needs to be a string. If not this is an error. Just silently skip to get an result anyway!
                    if ep["entityTypeProperty"]['entityTypePropertyType'] != 2: 
                        logging.error (" Property Treatment-State is not of type 2 (String)!")
                        continue 
                    if (ep["entityPropertyValue"] == 'Evacuating'):
                        redEvacuatedList[ep["entityId"]] = 1

                logging.info (" {0} out of {1} RED patients where already evacuated".format (len (redEvacuatedList), len (redPatientsIdList)))

                if len (redEvacuatedList) == len (redPatientsIdList):
                    tLastRedEvacuated = self.getTimeFromICMMws (wsid)



            if tLastRedInHospital == None:
                logging.info ("looking for RED patient with Treatment-State == 'Evacuated'")
                for ep in jsonData:
                    if ep["entityId"] not in redPatientsIdList:
                        # skip patients not involved
                        continue
                    if (OOI.patientTreatmentStatePropertyId != ep["entityTypePropertyId"]):
                        # skip properties I am not interested in
                        continue
                    # Needs to be a string. If not this is an error. Just silently skip to get an result anyway!
                    if ep["entityTypeProperty"]['entityTypePropertyType'] != 2: 
                        logging.error (" Property Treatment-State is not of type 2 (String)!")
                        continue 
                    if (ep["entityPropertyValue"] == 'Evacuated'):
                        redInHospitalList[ep["entityId"]] = 1

                logging.info (" {0} out of {1} RED patients where already in hospital".format (len (redInHospitalList), len (redPatientsIdList)))

                if len (redInHospitalList) == len (redPatientsIdList):
                    tLastRedInHospital = self.getTimeFromICMMws (wsid)
                    # logging.info (" setting 'tLastRedInHospital' to {0}".format (tLastRedInHospital.isoformat()))


            if (tLoadingAreaBuild == None) and ('Loading' in areaIdLists):
                logging.info ("looking for functional loading area")
                for ep in jsonData:
                    if ep["entityId"] not in areaIdLists['Loading']:
                        # skip other areas
                        continue
                    if (546 != ep["entityTypePropertyId"]):
                        # skip properties I am not interested in
                        continue
                    if ep["entityPropertyValue"]:
                        tLoadingAreaBuild = self.getTimeFromICMMws (wsid)
                logging.info (" found functional loading area")
                        
            if (tStagingAreaBuild == None) and ('Staging' in areaIdLists):
                logging.info ("looking for functional staging area")
                for ep in jsonData:
                    if ep["entityId"] not in areaIdLists['Staging']:
                        # skip other areas
                        continue
                    if (546 != ep["entityTypePropertyId"]):
                        # skip properties I am not interested in
                        continue
                    if ep["entityPropertyValue"]:
                      tStagingAreaBuild = self.getTimeFromICMMws (wsid)
                logging.info (" found functional staging area")

            if (tTreatmentAreaBuild == None) and ('Treatment' in areaIdLists):
                logging.info ("looking for functional treatment area")
                for ep in jsonData:
                    if ep["entityId"] not in areaIdLists['Treatment']:
                        # skip other areas
                        continue
                    if (546 != ep["entityTypePropertyId"]):
                        # skip properties I am not interested in
                        continue
                    if ep["entityPropertyValue"]:
                      tTreatmentAreaBuild = self.getTimeFromICMMws (wsid)
                logging.info (" found functional treatment area")



            if tLastInHospital == None:
                logging.info ("looking for patient with Treatment-State == 'Evacuated'")
                for ep in jsonData:
                    if ep["entityId"] not in patientsIdList:
                        # skip patients not involved
                        continue
                    if (OOI.patientTreatmentStatePropertyId != ep["entityTypePropertyId"]):
                        # skip properties I am not interested in
                        continue
                    # Needs to be a string. If not this is an error. Just silently skip to get an result anyway!
                    if ep["entityTypeProperty"]['entityTypePropertyType'] != 2: 
                        logging.error (" Property Treatment-State is not of type 2 (String)!")
                        continue 
                    if (ep["entityPropertyValue"] == 'Evacuated'):
                        inHospitalList[ep["entityId"]] = 1

                logging.info (" {0} out of {1} patients where already in hospital".format (len (inHospitalList), len (patientsIdList)))

                if len (inHospitalList) == len (patientsIdList):
                    tLastInHospital = self.getTimeFromICMMws (wsid)




        # create indicator value structure
        if minutesSecondVehicle != None:
            self.result['indicator'].append ({
                    'id': 'SecoundResourceRequest',
                    'name': "Secound Resource Request",
                    'description': "Time until Secound Resource Request",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "timeintervals",
                    'data': {
                        "intervals": [
                            {
                                "startTime": t0.isoformat(),
                                "endTime": (t0 + datetime.timedelta(minutes=minutesSecondVehicle)).isoformat()
                                }
                            ],
                        "color": "#00cc00",
                        "linewidth": 2
                        }
                    })
            self.result['kpi']['Tactics']['SecoundResourceRequest']['value'] = minutesSecondVehicle

        if tLastPreTriage != None:
            self.result['indicator'].append ({
                    'id': 'LastPreTriage',
                    'name': "Last patient pre-triaged",
                    'description': "All patients got pre-triage",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "timeintervals",
                    'data': {
                        "intervals": [
                            {
                                "startTime": t0.isoformat(),
                                "endTime": tLastPreTriage.isoformat()
                                }
                            ],
                        "color": "#00cc00",
                        "linewidth": 2
                        }
                    })
            self.result['kpi']['Accomplishment']['LastPreTriage']['value'] = (tLastPreTriage - t0).total_seconds() / 60


        if tFirstRedTreated != None:
            self.result['indicator'].append ({
                    'id': 'FirstRedTreated',
                    'name': "First Red Treated",
                    'description': "Time until first red patient is treated",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "timeintervals",
                    'data': {
                        "intervals": [
                            {
                                "startTime": t0.isoformat(),
                                "endTime": tFirstRedTreated.isoformat()
                                }
                            ],
                        "color": "#00cc00",
                        "linewidth": 2
                        }
                    })
            self.result['kpi']['Accomplishment']['FirstRedTreated']['value'] = (tFirstRedTreated - t0).total_seconds() / 60


        if tLastRedTreated != None:
            self.result['indicator'].append ({
                    'id': 'LastRedTreated',
                    'name': "Last Red Treated",
                    'description': "Time until all red patients are treated",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "timeintervals",
                    'data': {
                        "intervals": [
                            {
                                "startTime": t0.isoformat(),
                                "endTime": tLastRedTreated.isoformat()
                                }
                            ],
                        "color": "#00cc00",
                        "linewidth": 2
                        }
                    })
            self.result['kpi']['Accomplishment']['LastRedTreated']['value'] = (tLastRedTreated - t0).total_seconds() / 60


        if tLastRedEvacuated != None:
            self.result['indicator'].append ({
                    'id': 'LastRedEvacuated',
                    'name': "Last Red Evacuated",
                    'description': "Time until all red patients are evacuated",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "timeintervals",
                    'data': {
                        "intervals": [
                            {
                                "startTime": t0.isoformat(),
                                "endTime": tLastRedEvacuated.isoformat()
                                }
                            ],
                        "color": "#00cc00",
                        "linewidth": 2
                        }
                    })
            self.result['kpi']['Accomplishment']['LastRedEvacuated']['value'] = (tLastRedEvacuated - t0).total_seconds() / 60

        if tLastRedInHospital != None:
            self.result['indicator'].append ({
                    'id': 'LastRedInHospital',
                    'name': "Last Red in Hospital",
                    'description': "Time until all red patients are in a Hospital",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "timeintervals",
                    'data': {
                        "intervals": [
                            {
                                "startTime": t0.isoformat(),
                                "endTime": tLastRedInHospital.isoformat()
                                }
                            ],
                        "color": "#00cc00",
                        "linewidth": 2
                        }
                    })
            self.result['kpi']['Accomplishment']['LastRedInHospital']['value'] = (tLastRedInHospital - t0).total_seconds() / 60


        if tLoadingAreaBuild != None:
            self.result['indicator'].append ({
                    'id': 'LoadingAreaBuild',
                    'name': "Loading Area Build",
                    'description': "Time until first loading area is build",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "timeintervals",
                    'data': {
                        "intervals": [
                            {
                                "startTime": t0.isoformat(),
                                "endTime": tLoadingAreaBuild.isoformat()
                                }
                            ],
                        "color": "#00cc00",
                        "linewidth": 2
                        }
                    })
            self.result['kpi']['Accomplishment']['LoadingAreaBuild']['value'] = (tLoadingAreaBuild - t0).total_seconds() / 60


        if tStagingAreaBuild != None:
            self.result['indicator'].append ({
                    'id': 'StaggingAreaBuild',
                    'name': "Staging Area Build",
                    'description': "Time until first staging area is build",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "timeintervals",
                    'data': {
                        "intervals": [
                            {
                                "startTime": t0.isoformat(),
                                "endTime": tStagingAreaBuild.isoformat()
                                }
                            ],
                        "color": "#00cc00",
                        "linewidth": 2
                        }
                    })
            self.result['kpi']['Accomplishment']['StagingAreaBuild']['value'] = (tStagingAreaBuild - t0).total_seconds() / 60


        if tTreatmentAreaBuild != None:
            self.result['indicator'].append ({
                    'id': 'TreatmentAreaBuild',
                    'name': "Treatment Area Build",
                    'description': "Time until first treatment area is build",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "timeintervals",
                    'data': {
                        "intervals": [
                            {
                                "startTime": t0.isoformat(),
                                "endTime": tTreatmentAreaBuild.isoformat()
                                }
                            ],
                        "color": "#00cc00",
                        "linewidth": 2
                        }
                    })
            self.result['kpi']['Accomplishment']['TreatmentAreaBuild']['value'] = (tTreatmentAreaBuild - t0).total_seconds() / 60


        if tLastInHospital != None:
            self.result['indicator'].append ({
                    'id': 'LastInHospital',
                    'name': "Last in Hospital",
                    'description': "Time until all patients are in a Hospital",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "timeintervals",
                    'data': {
                        "intervals": [
                            {
                                "startTime": t0.isoformat(),
                                "endTime": tLastInHospital.isoformat()
                                }
                            ],
                        "color": "#00cc00",
                        "linewidth": 2
                        }
                    })
            self.result['kpi']['Accomplishment']['LastInHospital']['value'] = (tLastInHospital - t0).total_seconds() / 60

        if usedTacticalAreas > -1:
            data = []
            for areaType in tacticalAreas:
                if areaType in areaIdLists:
                    data.append ({
                            "key": areaType,
                            "value": len (areaIdLists[areaType]),
                            "desc" : "Number of {0} areas".format (areaType),
                            "cssClass": "tacticalArea-{0}".format (areaType)
                            })

            self.result['indicator'].append ({
                    'id': 'UsedTacticalAreas',
                    'name': "Used Tactical Areas",
                    'description': "Number of tactical areas used",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "histogram",
                    'data': data
                    })
            self.result['kpi']['Tactics']['UsedTacticalAreas']['value'] = usedTacticalAreas
            

       
        # return indicator value structure
        return 
