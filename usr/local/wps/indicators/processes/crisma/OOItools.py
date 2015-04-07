#!/usr/bin/env python
#
# Peter.Kutschera@ait.ac.at, 2014-03-14
# Time-stamp: "2015-02-19 13:57:26 peter"
#
# Tools to access OOI

######################
#  Configuration
defaultBaseUrl = 'http://crisma-ooi.ait.ac.at/api'
#####################


# some constants, see OOI-WSR docu
patientTypeId = 10         #is this sufficient or might there be subclasses?
patientExposedPropertyId = 476        # if false this pationt is not part of the game, ignore him/her
patientLifePropertyId = 42            # 0..100 
patientTreatmentStatePropertyId = 474 # Treatment-State	Supported values: None, Pre-Triaged, Triaged, On-Site-Treatment, Evacuating, Evacuated
vehicleCapacityPropertyId = 19        # Ambulance-Capacity
vehicleResourceCommandId = 1000       # Command to the resource
vehicleAvailabilityPropertyId = 312   # -1: Vehicle is not part of the game
vehicleDisplayStatePropertyId = 327   # "", Idle, Treat, Rescue, Evacuate, Refill, Dispatch, Build-Area
indicatorEntityId = 101


import json
import requests
import re
import time
import math
import logging

class OOIAccess:
    def __init__ (self, url):
        """crunch OOI-WSR URL into endpoint, resource, id

        url: 'http://crisma-ooi.ait.ac.at/api/worldstates/1

        result:
         endpoint=http://crisma-ooi.ait.ac.at/api
         resource=worldstates
         id=1
        """
        self.url = url
        self.endpoint = None
        self.resource = None
        self.id = None
        if (url is not None):
            match = re.search ("(https?://.*)/([^/?]+)/([0-9]+)(\?.*)?$", url)
            if (match):
                self.endpoint = match.group(1)
                self.resource = match.group(2)
                self.id = int (match.group(3))

    def __repr__ (self):
        return "endpoint={0}, resource={1}, id={2}".format (self.endpoint, self.resource, self.id)

def getJson (url, params=None, headers={'content-type': 'application/json'}):
    entityProperties = requests.get(url, params=params, headers=headers) 
    if entityProperties.status_code != 200:
        raise Exception ("Error accessing OOI-WSR at {0}: {1}".format (urllib.quote (entityProperties.url), entityProperties.status_code))
    if entityProperties.text is None:
        raise Exception ("Error accessing OOI-WSR at {0}: {1}".format (urllib.quote (entityProperties.url), "No such entityProperties"))
    if entityProperties.text == "":
        raise Exception ("Error accessing OOI-WSR at {0}: {1}".format (urllib.quote (entityProperties.url), "No such entityProperties"))
    jsonData = entityProperties.json() if callable (entityProperties.json) else entityProperties.json
    return jsonData


def getIndicatorRef (wsid, indicatorPropertyId, baseUrl=defaultBaseUrl):
    """get reference (URL) to an indicator within OOI

    wsid: OOI-specific WorldState id
    indicatorPropertyId: OOI and indicator specific property id

    returns indicatorURL or None
    """
    indicatorURL = None
    params = {
        'wsid' :  wsid,
        'etpid' : indicatorPropertyId
        }
    headers = {'content-type': 'application/json'}
    jsonData = getJson ("{0}/EntityProperty".format (baseUrl), params=params, headers=headers) 
    # count already existing results
    existingResults = 0;
    for ep in jsonData:
        existingResults +=1
    if existingResults > 1:
        raise Exception ("There are already {0} results! This should not be the case!".format (existingResults))
        # Just an idea, does not work as is
        #result = requests.delete("{0}/EntityProperty".format (baseUrl), params=params, headers=headers)         
        #logging.info (result)
        #exisitingResults = 0;
    if existingResults == 1:
        existingResultId = jsonData[0]['entityPropertyId']
        indicatorURL = "{0}/EntityProperty/{1}".format (baseUrl, existingResultId)
    return indicatorURL

def storeIndicatorValue (wsid, indicatorPropertyId, indicatorValue, indicatorURL=None, baseurl=defaultBaseUrl):
    """store an indicator value

    wsid: OOI-specific WorldState id
    indicatorPropertyId: OOI and indicator specific property id
    indicatorValue: JSON-String
    indicatorURL: URL of already existing stored value; None otherwise

    returns indicatorURL
    """
    # write result to OOI-WSR
    indicatorValue = json.dumps (indicatorValue)
    # create OOI data structure
    indicatorProperty = {
        "entityId" : indicatorEntityId,
        "entityTypePropertyId": indicatorPropertyId,
        "entityPropertyValue": indicatorValue,
        "worldStateId": wsid,
        }
    if (indicatorURL is None):
        result = requests.post ("{0}/{1}".format (baseurl, "EntityProperty"), data=json.dumps (indicatorProperty), headers={'content-type': 'application/json'})
        if result.status_code != 201:
            raise Exception ("Unable to POST result at {0}/{1}: {2}".format (baseurl, "EntityProperty", result.status_code))
        resultData = result.json() if callable (result.json) else result.json
        newResult = resultData[u'entityPropertyId']
        indicatorURL = "{0}/{1}/{2}".format (baseurl, "EntityProperty", newResult)
    else:
        existingResultId = OOIAccess (indicatorURL).id
        indicatorProperty["entityPropertyId"] = existingResultId
        result = requests.put (indicatorURL, data=json.dumps (indicatorProperty), headers={'content-type': 'application/json'})
        if result.status_code != 200:
            raise Exception ("Unable to PUT result to {0}: {1}".format (indicatorURL, result.status_code))
    return indicatorURL

