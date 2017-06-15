#!/usr/bin/env python3
#
# Simple Script to generate a dynamic inventory for ansible from ucsd
# The script expects to find a vm_annotation of tpye Ansible: x1,x2,x3
# It will then add the VM name to the corresponding host groups x1, x2, x3
# and add at the end a mapping from VM name to IP Address
#
#

import requests
import json
import os
import sys
import argparse

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning) #dealing with self signed certificates, we do suppress this

ansibleDict = {}
aliasDict = {}

def empty_inventory():
    return {'_meta': {'hostvars': {}}}

def addElement(element,appList):
    for app in appList.split(','):
        #printElement(element)
        if app in ansibleDict:
            ansibleDict[app].append(element['VM_Name'])
            #print(ansibleDict)
        else:
            ansibleDict[app] = []
            ansibleDict[app].append(element['VM_Name'])
            #print(ansibleDict)
    if element['VM_Name'] not in aliasDict:
        aliasDict[element['VM_Name']] = element['IP_Address']

def printElement(element):
    print("---------------------------------------------------")
    print("ID:               ",element['VM_ID'])
    print("VM_Name:          ",element['VM_Name'] )
    print("IP:               ",element['IP_Address'])
    print("Category:         ",element['Category'])
    print("Power State:      ",element['Power_State'])
    #print("Annotation:       ",element['VM_Annotation'])
    #print("Tags:             ",element['Tags'])
    print("Custom Attribute: ",element['Custom_Attributes'])
    return

def getApplicationList(element):
    if (element['Custom_Attributes'].find('Ansible:') > -1) and (element['Power_State'].find('ON') > -1):
    # Extract the Ansible: xxxxxx; part from the list of custom attributes
      start = element['Custom_Attributes'].find('Ansible:') + 8 #strip also 'Ansible:'
      end = element['Custom_Attributes'].find(';', start)
      if (end == -1):                                           # if the Ansible Annotation is the last, there is no trailing ;
          end = len(element['Custom_Attributes'])
      if (end-start) > 1:                                       #there could be no information in the annotation, skip if this is the case
        res = element['Custom_Attributes'][start:end].strip()   #This gives us the list of ansible roles
        return res
      else:
        return None                                             # Annotation is there, but empty
    else:
      return None                                               # no Annotation Ansible found

def printInventory(ucsdInventory):
  print("VM Inventory")
  for element in ucsdInventory['serviceResult']['rows']:
    printElement(element)
  return

def printAnsibleInventory(ucsdInventory):
    for element in j['serviceResult']['rows']:
        if getApplicationList(element) is not None:
            # printElement(element)
            # print(getApplicationList(element))
            addElement(element, getApplicationList(element))
    for key in aliasDict:
        ansibleDict[key] = [aliasDict[key]]
    print(json.dumps(ansibleDict, indent=4, sort_keys=True))
    return

if not ("UCSD_SERVER" in os.environ and "API_KEY" in os.environ):
    print("Please specify the UCSD_SERVER AND API_KEY environment variable")
    exit(1)

url = "https://"+os.environ['UCSD_SERVER']+"/app/api/rest"
headers = {
    'x-cloupia-request-key': os.environ['API_KEY'],
    'cache-control': "no-cache"
    }
querystring = {"opName":"userAPIGetTabularReport","opData":"{param0:\"1\",param1:\"hx-dev\",param2:\"VMS-T0\"}"}

parser = argparse.ArgumentParser()
parser.add_argument('--list', action='store_true')
parser.add_argument('--host', action='store')
parser.add_argument('--inventory', action='store_true')
args = parser.parse_args()

if args.list:
    response = requests.request("GET", url, headers=headers, params=querystring, verify=False)
    j = json.loads(response.text)
    #print(json.dumps(j,indent=4))
    printAnsibleInventory(j)
elif args.host:
    print(empty_inventory())
elif args.inventory:
    print("VM Inventory from UCS Director")
    response = requests.request("GET", url, headers=headers, params=querystring, verify=False)
    j = json.loads(response.text)
    printInventory(j)
else:
    print("Parameter not recognized")
