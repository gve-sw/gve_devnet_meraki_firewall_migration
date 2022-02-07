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

import requests
from requests.models import HTTPError
import getpass
import csv
import json
import copy
import time
from pprint import pprint
from batches_helper import BatchHelper


import meraki_api

'''
Function to read csv file
'''
def read_csv(csv_file, org_id):

    object_names_lst = []
    object_groups_lst = []
    object_dict_lst = []
    linking_dict = {}
    try:
        print('Reading policy objects and groups file.')

        with open(csv_file, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            # The data from four columns in the file will be used
            # The columns are name, category, type, cidr and groupName
            # Read in data from the relevant columns in the row and assign it to a variable
            for row in reader:
                name = row['name']
                category = row['category']
                type = row['type']
                cidr = row['cidr']
                fqdn = row['fqdn']
                group_name = row['groupName']

                # Create a 'linking' dictionary
                # This contains the policy object name and policy object group that it belongs too
                if group_name:  # If group name is not empty
                    # If there is no key with the Object Group Name create one
                    if group_name not in linking_dict:
                        linking_dict[group_name] = list()
                        linking_dict[group_name].append(name)
                    else:
                        # Key exists check if object is in the list of networks
                        if name in linking_dict[group_name]:
                            print(f'Policy Object {name} already exists in Group {group_name}')
                        else:
                            # Key exists add object not in list of networks - add it
                            linking_dict[group_name].append(name)

                # Create a list of unique Policy Group Names
                # If the group is not in the list, append it to the list
                if group_name:  # If group name is not empty
                    if group_name not in object_groups_lst:
                        # Append to list
                        object_groups_lst.append(group_name)

                # Create a list of unique Network Object Names
                # If object is not in the list then add it
                if name not in object_names_lst:
                    # append to list
                    object_names_lst.append(name)

                # Create a dictionary with the following keys
                # name, category, type, cidr, groupIds
                # Assign each key a value
                # Append the dictionary to obj_dict_lst list
                # This will be the Body of the API call
                    if cidr != "":
                        # This will be the Body of the API call for CIDR objects
                        policy_object = {
                            'name': name,
                            'category': category,
                            'type': type,
                            'cidr': cidr,
                            'groupIds': []
                        }
                    else:
                        # This will be the Body of the API call for FQDN objects
                        policy_object = {
                            'name': name,
                            'category': category,
                            'type': type,
                            'fqdn': fqdn,
                            'groupIds': []
                        }
                    object_dict_lst.append(policy_object)  # This will be a list of dictionaries

            print(f'UNIQUE OBJECT GROUPS: {len(object_groups_lst)}')
            print(f'UNIQUE OBJECT NAMES: {len(object_names_lst)}')

            return object_groups_lst, object_names_lst, object_dict_lst, linking_dict

    except Exception as err: 
        raise Exception(err)



'''
Function to check and add group policy objects to Dashboard
'''
def check_group_obj(obj_group_lst, org_id):
    try:

        print('Check policy objects and add if not present')

        existing_group_obj_name_lst = []
        # Check if the group object already exists using List Group function
        existing_group_obj = meraki_api.list_group_obj(org_id)  # This will return a list of dictionaries

        # Create list of existing object names from the list of dictionaries
        if existing_group_obj:   # List is not empty - some group objects found in Dashboard
            for item in existing_group_obj:   # Create a list of existing group object names
                name = item['name']
                # Append to list
                existing_group_obj_name_lst.append(name)

        # Search list of dictionaries to see if group object name exists
        # Create Object Group for each item in obj_group_lst

        actions_group_lst = list()

        for group in obj_group_lst:  # This is the list of policy group objects we want to create
            if existing_group_obj:   # Tist is not empty - some group objects found in Dashboard
                # Create Object Group for each item in obj_group_lst
                if group in existing_group_obj_name_lst:   # This is the list of policy group object names in Dashboard
                    print(f'Group {group} is already configured in Dashboard.')
                else:
                    print(f'Need to create group object {group}')

                    action_payload = {
                        'resource': f'/organizations/{org_id}/policyObjects/groups',
                        'operation': 'create',
                        'body': {
                            'name': group
                        }
                    }
                    actions_group_lst.append(action_payload)

            else:   # List is empty - no network objects found in Dashboard
                action_payload = {
                    'resource': f'/organizations/{org_id}/policyObjects/groups',
                    'operation': 'create',
                    'body': {
                        'name': group
                    }
                }
                actions_group_lst.append(action_payload)
        
        all_actions_count = len(actions_group_lst)
        print(f'Policy groups to add: {all_actions_count}')

        if(all_actions_count > 0):

            policy_group_helper = BatchHelper(org_id, actions_group_lst)

            policy_group_helper.prepare()
            #policy_group_helper.generate_preview()
            policy_group_helper.execute()
            policy_group_helper.report()
        else:
            print('No policy groups to create.')

        return all_actions_count

    except Exception as err: 
        raise Exception(err)



'''
Function to check and add policy objects to Dashboard
'''
def check_net_obj(obj_names_lst, obj_dict_lst, org_id):
    try:
        print('Check policy groups and add if not present')

        existing_net_obj_lst = []

        # Check if the group object already exists using List Network Object function
        existing_net_obj = meraki_api.list_network_obj(org_id)  # this will return a list of dictionaries

        # Create list of existing object names from the list of dictionaries
        for i in existing_net_obj:
            name = i['name']
            # if name not in existing_net_obj
            # append to list
            existing_net_obj_lst.append(name)

        # Search list of dictionaries to see if network object name exists
        # Create Network Object for each item in obj_net_lst
        actions_lst = list()

        for network in obj_names_lst:  # This is the list of policy objects we want to create
            if existing_net_obj:   # List is not empty - network objects found in Dashboard
                print('Existing Network Object list NOT empty')

                if network in existing_net_obj_lst:  # This is the list of policy objects in Dashboard
                    print(f'Network {network} is already configured in Dashboard.')
                else:
                    print(f'Need to create network object {network}')
                    # Call Function to make API Call if network in obj_dict_list
                    for d in obj_dict_lst:   # choose item in obj_dict_lst
                        if network == d['name']:
                            nme = d['name']
                            print(f'Network {network} Name : {nme}')
                            # Check if object is CIDR
                            if 'cidr' in d.keys():  # if cidr key exists create payload
                                action_payload = {
                                    'resource': f'/organizations/{org_id}/policyObjects',
                                    'operation': 'create',
                                    'body': {
                                        'name': d['name'],
                                        'category': d['category'],
                                        'type': d['type'],
                                        'cidr': d['cidr']
                                    }
                                }
                            else:  # create payload with fqdn
                                action_payload = {
                                    'resource': f'/organizations/{org_id}/policyObjects',
                                    'operation': 'create',
                                    'body': {
                                        'name': d['name'],
                                        'category': d['category'],
                                        'type': d['type'],
                                        'fqdn': d['fqdn']
                                    }
                                }
                            actions_lst.append(action_payload)
            else:   # List is empty - no network objects found in Dashboard
                for d in obj_dict_lst:
                    if network == d['name']:
                        # Check if object is CIDR
                        if 'cidr' in d.keys():  # if cidr key exists create payload
                            action_payload = {
                                'resource': f'/organizations/{org_id}/policyObjects',
                                'operation': 'create',
                                'body': {
                                    'name': d['name'],
                                    'category': d['category'],
                                    'type': d['type'],
                                    'cidr': d['cidr']
                                }
                            }
                        else:  # create payload with fqdn
                            action_payload = {
                                'resource': f'/organizations/{org_id}/policyObjects',
                                'operation': 'create',
                                'body': {
                                    'name': d['name'],
                                    'category': d['category'],
                                    'type': d['type'],
                                    'fqdn': d['fqdn']
                                    }
                                }
                        actions_lst.append(action_payload)

        all_actions_count = len(actions_lst)
        print('Policy objects to add: ' + str(all_actions_count))

        if(all_actions_count > 0):

            policy_object_helper = BatchHelper(org_id, actions_lst)

            policy_object_helper.prepare()
            #policy_object_helper.generate_preview()
            policy_object_helper.execute()
            policy_object_helper.report()

        else:
            print('No policy objects to create.')

        return all_actions_count

    except Exception as err: 
        raise Exception(err)


'''
Function to link policy objects to group objects in Dashboard
'''
def link_objects_to_groups(org_id, linking_dict):
    try:

        print('Create link between policy objects and groups')

        network_obj_lst = []
        group_policy_obj_lst = []
        policy_obj_group_id = ''

        network_objects = meraki_api.list_network_obj(org_id)  # This will return a list

        # Create list of existing object names from the list of dictionaries
        for net_object in network_objects:
            name = net_object['name']
            id = net_object['id']
            policy_object = {
                'name': name,
                'id': id
            }
            network_obj_lst.append(policy_object)

        group_policy_objects = meraki_api.list_group_obj(org_id)

        # Create list of existing object names from the list of dictionaries
        for grp_object in group_policy_objects:
            name = grp_object['name']
            id = grp_object['id']
            group_policy_object = {
                'name': name,
                'id': id
            }
            group_policy_obj_lst.append(group_policy_object)  # Contains group policy name and id

        actions_lst = list()
        obj_id_list = list()

        for group_object_name, networks in linking_dict.items():  # For group(key), networks(value) in linking dict
            obj_id_list.clear()  # Clear out list for next set
            val_count = len(networks)
            # Loop over networks list
            if val_count > 150:
                print(f'Number of policy objects for group {group_object_name} exceeds 150 Value Count is {val_count}')
                print(f'Please create additional group(s) for {group_object_name} for policies that exceed the 150 count limit.')
            else:

                for group_object in group_policy_obj_lst:
                    group_name = group_object['name']
                    group_id = group_object['id']
                    if group_object_name == group_name:
                        policy_obj_group_id = group_id

                for net_name in networks:  # for net_name in networks
                    for network_object in network_obj_lst:
                        name = network_object['name']
                        id = network_object['id']
                        if net_name == name:
                            obj_id_list.append(id)

                action_payload = {
                    'resource': f'/organizations/{org_id}/policyObjects/groups/{policy_obj_group_id}',
                    'operation': 'update',
                    'body': {
                        'name': group_object_name,
                        'objectIds': obj_id_list
                        }
                    }
                # A deep copy creates a *new object* and adds *copies* of nested objects in the original
                action_payload_copy = copy.deepcopy(action_payload)
                actions_lst.append(action_payload_copy)

        all_actions_count = len(actions_lst)
        print('Links between objects and groups to add: ' + str(all_actions_count))

        if(all_actions_count > 0):
            link_helper = BatchHelper(org_id, actions_lst)

            link_helper.prepare()
            #link_helper.generate_preview()
            link_helper.execute()
            link_helper.report()

        else:
            print('No links to create.')
        
        return all_actions_count

    except Exception as err: 
        raise Exception(err)



'''
Deletes all policy objects AND policy object groups
'''           
def delete_everything_batch(organizationId):
    try: 

        print('Delete all policy objects and groups.')

        actions_group_lst = list()
        actions_object_lst = list()
        all_actions = list()

        actions_group_lst = create_policy_groups_action_list(organizationId)
        actions_object_lst = create_policy_objects_action_list(organizationId)

        all_actions.extend(actions_group_lst)
        print('Policy groups to remove: ' + str(len(actions_group_lst)))
        all_actions.extend(actions_object_lst)
        print('Policy objects to remove: ' + str(len(actions_object_lst)))
    
        all_actions_count = len(all_actions)

        if(all_actions_count > 0):
            delete_helper = BatchHelper(organizationId, all_actions)

            delete_helper.prepare()
            #delete_helper.generate_preview()
            delete_helper.execute()
            delete_helper.report()

        else:
            print('Nothing to delete.')

    except Exception as err: 
        raise Exception(err)


'''
Create action list that includes all policy objects
'''
def create_policy_objects_action_list(organizationId):

    actions_object_lst = list()

    all_objects = meraki_api.get_all_policy_objects(organizationId)
    for policy_object in all_objects:
        
            policy_obj_id = policy_object['id']
            url = f"/organizations/{organizationId}/policyObjects/{policy_obj_id}"
            action_payload = {
                        'resource': url,
                        'operation': 'destroy',
                        'body': {}
                    }
            actions_object_lst.append(action_payload)

    return actions_object_lst


'''
Create actions list that includes all policy groups.
'''
def create_policy_groups_action_list(organizationId):
    
    actions_group_lst = list()

    all_objects = meraki_api.get_policy_objects_groups(organizationId)
    for policy_object_group in all_objects:

        policy_obj_group_id = policy_object_group['id']
        url = f"/organizations/{organizationId}/policyObjects/groups/{policy_obj_group_id}"
        action_payload = {
                    'resource': url,
                    'operation': 'destroy',
                    'body': {}
                }
        actions_group_lst.append(action_payload)

    return actions_group_lst







