"""
Peter Kutschera, 2013-09-11
Update to create KPI also, 2014-11-27
Time-stamp: "2015-04-15 10:48:10 peter"

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


kpi;LastPreTriage;Last Pre-Triage;Time until all patients got pre-triage;number
kpi;LastInHospital;Last Patient in Hospital;Time until all patients are in a hospital;number
kpi;FirstRedTreated;First red Patient treated;Minutes until first red Patient treated;number
kpi;LastRedTreated;Last red Patient treated;Time until all red patients are treated;number
kpi;LastRedEvacuated;Last red Patient evacuated;Time until all red patients are evacuated;number
kpi;LastRedInHospital;Last red Patient in Hospital;Time until all red patients are in a hospital;number

kpi;SecoundResourceRequest;Secound Resource Request;Time until Secound Resource Request;number

kpi;LoadingAreaBuild;Loading-Area build;Time until first loading area is build;number
kpi;StagingAreaBuild;Staging-Area build;Time until first staging area is build;number
kpi;TreatmentAreaBuild;Treatment-Area build;Time until first treatment area is build;number

kpi;UsedTacticalAreas;Used Tactical Areas;Number of tactical areas used;number


indicator;SecoundResourceRequest;Secound Resource Request;Time until Secound Resource Request;timeintervals
indicator;LoadingAreaBuild;Loading-Area build;Time until first loading area is build;timeintervals
indicator;StagingAreaBuild;Staging-Area build;Time until first staging area is build;timeintervals
indicator;TreatmentAreaBuild;Treatment-Area build;Time until first treatment area is build;timeintervals
indicator;UsedTacticalAreas;Used Tactical Areas;Number of tactical areas used;histogram

indicator;First_Color_State;First injury-type Patient in state;From start to first Patient of injury type in treatment state;timeintervals
indicator;Last_Color_State;Last injury-type Patient in state;From start till last Patient of injury type in treatment state;timeintervals
indicator;In_Color_State;First to last injury-type Patient in state;From first Patient to last Patient of injury type in treatment state;timeintervals


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
        if (len(ts) == 19):
            ts = ts + "Z"
        t = dateutil.parser.parse (ts)
        # logging.info (" getTimeFromICMMws: '{0}' -> {1}".format (ts, t))
        return t

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
                        },
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
        #tFirstRedTreated = None # 1st red patient treated
        #tLastRedTreated = None # last red patient treated
        #tLastRedEvacuated = None # last red patient evacuated
        #tLastRedInHospital = None # last red patient in hospital
        tLoadingAreaBuild = None 
        tStagingAreaBuild = None
        tTreatmentAreaBuild = None
        #tLastInHospital = None # last patient in hospital
        usedTacticalAreas = -1

        # count patients - needed to answer questions like "When got the LAST patient ....?"
        # Answer: When ...  was true for each patient in at least one previous WS
        # This is only done once as it never changes (No one is born or dies)
        #  [id, id,...]
        patientsIdList = None 
        #  {'RED': [id, id,..],..
        coloredPatientsIdList = None
        #  {id: 'RED', id: 'GREEN, ...
        patientsIdColorList = None 
        # the following lists are accumulated starting from the baseline !
        # list of patient that where already ....
        #  {'Evacuated': [id, id,..]
        statedPatientIdList = None
        #  {'RED': {'Evacuated': [id, id,...],..},..}
        coloredStatedPatientsIdList = None
        # times
        #  {'Evacuated': time, ..}
        tFirstState = None
        #  {'RED': {'Evacuated': time, ..},..}
        tFirstColorState = None
        #  {'Evacuated': time, ..}
        tLastState = None
        #  {'RED': {'Evacuated': time, ..},..}
        tLastColorState = None
        # Area lists
        areaIdLists = None
        # Vehicle command times
        vehicleCommandTimes = []

        # Loop over all parent worldstates
        for i in range (0, len (parents)):
            wsid = parents[i]
            # Time of this worldstate
            tWsid = self.getTimeFromICMMws (wsid)
            logging.info ("get ws {0}: {1}".format (wsid, tWsid.isoformat()))
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

            # This in only done once, so for the base worldstate
            if patientsIdList == None:
                logging.info ("looking for exposed patients")
                patientsIdList = []
                patientsIdColorList = {}
                for ep in jsonData:
                    if (476 != ep["entityTypePropertyId"]):       # patient-is-exposed
                        continue
                    exposed = ep["entityPropertyValue"]
                    if exposed:
                        patientsIdList.append (ep["entityId"])
                logging.info (" found {0} exposed patients: {1}".format (len (patientsIdList), patientsIdList))
                logging.info (" looking for injury types of exposed patients")
                statedPatientIdList = {}
                coloredPatientsIdList = {}
                coloredStatedPatientsIdList = {}
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
                    # logging.info ("  injuryTypeTriageLevel[{0}] = {1}".format (ep['entityId'], ep["entityPropertyValue"]))
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
                    color = injuryTypeTriageLevel[epv]
                    patientsIdColorList[ep["entityId"]] = color
                    if (color not in coloredPatientsIdList):
                        coloredPatientsIdList[color] = []
                    coloredPatientsIdList[color].append (ep["entityId"])
                for color in coloredPatientsIdList:
                    logging.info (" found {0} {2} exposed patients: {1}".format (len (coloredPatientsIdList[color]), coloredPatientsIdList[color], color))
                for id in patientsIdList:
                    if id not in patientsIdColorList:
                        logging.error ("Input data error: Injury type of patient {0} not defined, removing".format (id))
                        patientsIdList.remove (id)

                # Now I know all the colors
                tFirstState = {}
                tLastState = {}
                tFirstColorState = {}
                tLastColorState = {}
                for color in coloredPatientsIdList:
                    tFirstColorState[color] = {}
                    tLastColorState[color] = {}
        

            # create area lists - only once
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
               

            # the rest is done for each worldstate from baseworldstate down to actual worldstate
            # 2nd Vehicle request
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


            # collect treatment state of patients
            logging.info ("collecting patient Treatment-State")
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
                state = ep["entityPropertyValue"]
                if state not in statedPatientIdList:
                    statedPatientIdList[state] = []
                if ep["entityId"] not in statedPatientIdList[state]:
                    statedPatientIdList[state].append (ep["entityId"])
                color = patientsIdColorList[ep["entityId"]]
                if color not in coloredStatedPatientsIdList:
                    coloredStatedPatientsIdList[color] = {}
                if state not in coloredStatedPatientsIdList[color]:
                    coloredStatedPatientsIdList[color][state] = []
                if ep["entityId"] not in coloredStatedPatientsIdList[color][state]:
                    coloredStatedPatientsIdList[color][state].append (ep["entityId"])
            logging.info ("coloredStatedPatientsIdList: {0}".format (coloredStatedPatientsIdList))


            # Collect patient-related times
            # First something
            for state in statedPatientIdList:
                if state not in tFirstState:
                    tFirstState[state] = tWsid
            for color in coloredStatedPatientsIdList:
                for state in coloredStatedPatientsIdList[color]:
                    if state not in tFirstColorState[color]:
                        tFirstColorState[color][state] = tWsid
            # Last something
            # Last: All id's are already in this state
            for state in statedPatientIdList:
                if state not in tLastState:
                    if len (statedPatientIdList[state]) == len (patientsIdList):
                        tLastState[state] = tWsid
            for color in coloredStatedPatientsIdList:
                for state in coloredStatedPatientsIdList[color]:
                    if state not in tLastColorState[color]:
                        if len (coloredStatedPatientsIdList[color][state]) == len (coloredPatientsIdList[color]):
                            tLastColorState[color][state] = tWsid
                        

            # Area-related times
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
                        tLoadingAreaBuild = tWsid
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
                      tStagingAreaBuild = tWsid
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
                      tTreatmentAreaBuild = tWsid
                logging.info (" found functional treatment area")


        # END of loop over all parent worldstates
        logging.info ("tFirstState: {0}".format (tFirstState))
        logging.info ("tLastState:  {0}".format (tLastState))
        logging.info ("tFirstColorState: {0}".format (tFirstColorState))
        logging.info ("tLastColorState:  {0}".format (tLastColorState))

        # set KPI data
        # KPI 8
        if 'PreTriage' in tLastState:
            self.result['kpi']['Accomplishment']['LastPreTriage']['value'] = (tLastState['PreTriage'] - t0).total_seconds() / 60
        # KPI 17
        if 'Evacuated' in tLastState:
            self.result['kpi']['Accomplishment']['LastInHospital']['value'] = (tLastState['Evacuated'] - t0).total_seconds() / 60
        # KPI 9
        if ('RED' in tFirstColorState) and ('Treated' in tFirstColorState['RED']):
            self.result['kpi']['Accomplishment']['FirstRedTreated']['value'] = (tFirstColorState['RED']['Treated'] - t0).total_seconds() / 60
        # KPI 10
        if ('RED' in tLastColorState) and ('Treated' in tLastColorState['RED']):
            self.result['kpi']['Accomplishment']['LastRedTreated']['value'] = (tLastColorState['RED']['Treated'] - t0).total_seconds() / 60
        # KPI 11
        # Evacuated from scene: Evacuating            
        if ('RED' in tLastColorState) and ('Evacuating' in tLastColorState['RED']):
            self.result['kpi']['Accomplishment']['LastRedEvacuated']['value'] = (tLastColorState['RED']['Evacuating'] - t0).total_seconds() / 60
        # KPI 12
        # in hospital: Evacuated
        if ('RED' in tLastColorState) and ('Evacuated' in tLastColorState['RED']):
            self.result['kpi']['Accomplishment']['LastRedInHospital']['value'] = (tLastColorState['RED']['Evacuated'] - t0).total_seconds() / 60
        # KPI 7
        if minutesSecondVehicle != None:
            self.result['kpi']['Tactics']['SecoundResourceRequest']['value'] = minutesSecondVehicle
        # KPI 15
        if tLoadingAreaBuild != None:
            self.result['kpi']['Accomplishment']['LoadingAreaBuild']['value'] = (tLoadingAreaBuild - t0).total_seconds() / 60
        # KPI 16
        if tStagingAreaBuild != None:
            self.result['kpi']['Accomplishment']['StagingAreaBuild']['value'] = (tStagingAreaBuild - t0).total_seconds() / 60
        # KPI 14
        if tTreatmentAreaBuild != None:
            self.result['kpi']['Accomplishment']['TreatmentAreaBuild']['value'] = (tTreatmentAreaBuild - t0).total_seconds() / 60
        # KPI 5
        if usedTacticalAreas > -1:
            self.result['kpi']['Tactics']['UsedTacticalAreas']['value'] = usedTacticalAreas



        # create indicator value structure
        if minutesSecondVehicle != None:
            self.result['indicator'].append ({
                    'id': 'SecoundResourceRequest',
                    'name': "Secound Resource Request",
                    'description': "Time until Secound Resource Request",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates": parents,
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


        if tLoadingAreaBuild != None:
            self.result['indicator'].append ({
                    'id': 'LoadingAreaBuild',
                    'name': "Loading Area Build",
                    'description': "Time until first loading area is build",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates": parents,
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



        if tStagingAreaBuild != None:
            self.result['indicator'].append ({
                    'id': 'StaggingAreaBuild',
                    'name': "Staging Area Build",
                    'description': "Time until first staging area is build",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates": parents,
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



        if tTreatmentAreaBuild != None:
            self.result['indicator'].append ({
                    'id': 'TreatmentAreaBuild',
                    'name': "Treatment Area Build",
                    'description': "Time until first treatment area is build",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates": parents,
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
                    "worldstates": parents,
                    'type': "histogram",
                    'data': data
                    })


        for color in coloredPatientsIdList:
            for state in tFirstState:
                if (state == '') or (state == 'None'):
                    continue
                # t0..first
                if (color in tFirstColorState) and (state in tFirstColorState[color]):
                    self.result['indicator'].append ({
                            'id': 'First_{0}_{1}'.format (color, state),
                            'name': "First {0} patient {1}".format (color, state),
                            'description': "Time until first {0} patients is {1}".format (color, state),
                            "worldstateDescription": self.worldstateDescription,
                            "worldstates": parents,
                            'type': "timeintervals",
                            'data': {
                                "intervals": [
                                    {
                                        "startTime": t0.isoformat(),
                                        "endTime": tFirstColorState[color][state].isoformat()
                                        }
                                    ],
                                "color": "#00cc00",
                                "linewidth": 2
                        }
                    })
                # t0..last
                if (color in tLastColorState) and (state in tLastColorState[color]):
                    self.result['indicator'].append ({
                            'id': 'Last_{0}_{1}'.format (color, state),
                            'name': "Last {0} patient {1}".format (color, state),
                            'description': "Time until last {0} patients is {1}".format (color, state),
                            "worldstateDescription": self.worldstateDescription,
                            "worldstates": parents,
                            'type': "timeintervals",
                            'data': {
                                "intervals": [
                                    {
                                        "startTime": t0.isoformat(),
                                        "endTime": tLastColorState[color][state].isoformat()
                                        }
                                    ],
                                "color": "#00cc00",
                                "linewidth": 2
                        }
                    })
                # first..last
                if (color in tFirstColorState) and (state in tFirstColorState[color]) and (color in tLastColorState) and (state in tLastColorState[color]):
                    self.result['indicator'].append ({
                            'id': 'In_{0}_{1}'.format (color, state),
                            'name': "{0} patient {1}".format (color, state),
                            'description': "Time from first to last {0} patient {1}".format (color, state),
                            "worldstateDescription": self.worldstateDescription,
                            "worldstates": parents,
                            'type': "timeintervals",
                            'data': {
                                "intervals": [
                                    {
                                        "startTime": tFirstColorState[color][state].isoformat(),
                                        "endTime": tLastColorState[color][state].isoformat()
                                        }
                                    ],
                                "color": "#00cc00",
                                "linewidth": 2
                        }
                    })


       
        # return indicator value structure
        return 
