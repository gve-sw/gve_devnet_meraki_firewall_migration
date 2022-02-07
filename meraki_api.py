""" Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. 
"""

#How to retrieve an Meraki api key: https://developer.cisco.com/meraki/api-v1/#!getting-started/find-your-organization-id 
#Meraki Dashboard API call documentation: https://developer.cisco.com/meraki/api-v1/#!overview/api-key

# Import Section
import requests
import json
import os
from dotenv import load_dotenv
from pprint import pprint

from requests.models import HTTPError


load_dotenv()

#Global Variables
BASE_URL = "https://api.meraki.com/api/v1"
API_KEY = os.environ['MERAKI_API_TOKEN']
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Cisco-Meraki-API-KEY": API_KEY
}

#Organization endpoints
def get_organizations():
    try:
        url = BASE_URL+f'/organizations'

        response = requests.get(url, headers=HEADERS)
        
        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

        return response.json()

    except Exception as err:
        raise Exception(err)


#Network endpoints
def get_networks(organizationId):
    try:
        url = BASE_URL+f'/organizations/{organizationId}/networks'

        response = requests.get(url, headers=HEADERS)
        
        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

        return response.json()

    except Exception as err:
        raise Exception(err)


# Policy Objects and Groups endpoints
def get_policy_objects_groups(organizationId):
    try:
        url = BASE_URL+f'/organizations/{organizationId}/policyObjects/groups'

        response = requests.get(url, headers=HEADERS)
        
        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

        return response.json()

    except Exception as err:
        raise Exception(err)


def get_all_policy_objects(organizationId):
    try:
        url = BASE_URL+f"/organizations/{organizationId}/policyObjects"
        
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

        return response.json()

    except Exception as err:
        raise Exception(err)


def delete_policy_object(organizationId, policyObjectId):
    try: 
        url = BASE_URL+f"/organizations/{organizationId}/policyObjects/{policyObjectId}"

        response = requests.delete(url, headers=HEADERS)
        
        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

        return response, response.text

    except Exception as err:
        raise Exception(err)


def delete_policy_objects_group(organizationId, policyObjectGroupId):
    try:
        url = BASE_URL+f'/organizations/{organizationId}/policyObjects/groups/{policyObjectGroupId}'

        response = requests.delete(url, headers=HEADERS)
        
        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

        return response, response.text

    except Exception as err:
        raise Exception(err)


def list_network_obj(org_id):
    try:
        url = BASE_URL+f'/organizations/{org_id}/policyObjects/'

        response = requests.get(url, headers=HEADERS)
        print(f'List Network Object response code: {response.status_code}')  

        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

        return response.json()

    except Exception as err:
        raise Exception(err)


def list_group_obj(org_id):
    try:
        url = BASE_URL+f'/organizations/{org_id}/policyObjects/groups'

        response = requests.get(url, headers=HEADERS)
        print(f'List Group response code: {response.status_code}') 
        
        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

        return response.json()

    except Exception as err:
        raise Exception(err)



# Action Batches endpoints
def post_organization_action_batches(organizationId, action_batch_payload):
    try:
        url = BASE_URL+f'/organizations/{organizationId}/actionBatches'
        payload = action_batch_payload

        response = requests.post(url, headers=HEADERS, data=json.dumps(payload))
        print(f'POST Action Batch response status : {response.reason} (Code: {response.status_code})')

        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')
        
        return response.json()

    except Exception as err:
        raise Exception(err)


def get_organization_action_batches(organizationId, status=''):
    try:
        if status == '':
            url = BASE_URL+f'/organizations/{organizationId}/actionBatches'
        else: 
            url = BASE_URL+f'/organizations/{organizationId}/actionBatches?status={status}'    

        response = requests.get(url, headers=HEADERS)
        print(f'GET Action Batches response status : {response.reason} (Code: {response.status_code})')
        
        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

        return response.json()

    except Exception as err:
        raise Exception(err)


def get_organization_action_batch(organizationId, batchId):
    try:
        url = BASE_URL+f'/organizations/{organizationId}/actionBatches/{batchId}'

        response = requests.get(url, headers=HEADERS)
        print(f'GET Action Batch response status : {response.reason} (Code: {response.status_code})')
        
        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

        return response.json()

    except Exception as err:
        raise Exception(err)


def delete_action_batch(organizationId, batchId):
    try:
        url = BASE_URL+f'/organizations/{organizationId}/actionBatches/{batchId}'

        response = requests.delete(url, headers=HEADERS)
        print(f'DELETE Action Batch response status : {response.reason} (Code: {response.status_code})')
        
        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

        return response.json()

    except Exception as err:
        raise Exception(err)


# L3 Firewall rules endpoints
def create_l3_fw_rules(net_id, fw_rule_payload):
    try:
        url = BASE_URL+f'/networks/{net_id}/appliance/firewall/l3FirewallRules'
        payload = fw_rule_payload

        response = requests.put(url, headers=HEADERS, data=payload)
        print(f'Update L3 Firewall Rules response status : {response.reason} (Code: {response.status_code})')

        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

    except Exception as err:
        raise Exception(err)


# Create Site to Site VPN firewall rules endpoint
def create_s2s_vpn_fw_rules(org_id, fw_rule_payload):
    try:
        url = BASE_URL+f'/organizations/{org_id}/appliance/vpn/vpnFirewallRules'
        payload = fw_rule_payload

        response = requests.put(url, headers=HEADERS, data=payload)
        print(f'Update S2S VPN Firewall Rules response status : {response.reason} (Code: {response.status_code})')

        if response.status_code >= 400:
            raise Exception(f'HTTP error code: {response.status_code} - {response.reason}')

    except Exception as err:
        raise Exception(err)



