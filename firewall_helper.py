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

import meraki_api

'''
Function to read csv file
'''
def read_csv(net_id, csv_file, group_obj_lst, network_obj_lst):
    
    src_cidr_lst = []
    src_port_lst = []
    dest_cidr_lst = []
    dest_port_lst = []
    row_values = []
    fw_rule_payload = {}
    dest_cidr_group_id_lst = []
    dest_cidr_network_id_lst = []
    src_cidr_group_id_lst = []
    src_cidr_network_id_lst = []
    fw_rule_dict = {}
    fw_rule_lst = []

    try:

        print('Reading firewall file.')
        with open(csv_file, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            # The data from four columns in the file will be used
            # The columns are name, category, type, cidr and Group Name
            # Read in data from the relevant columns in the row
            # and assign it to a variable
            rule = 0
            # Read in row
            print("Processing data. This may take a minute or two. Please be patient....")
            for row in reader:
                row_values = list(row.values())
                # Check if row is empty
                result = all(element == row_values[0] for element in row_values)  # Will be True if all values are the same "empty" or blank
                if not result:  # Row is not empty
                    rule_number = row['Rule Number']
                    policy = row['Policy']
                    comment = row['Comment']
                    protocol = row['Protocol']
                    src_cidr = row['Source CIDR']
                    src_port = row['Source Port']
                    dest_cidr = row['Destination CIDR']
                    dest_port = row['Destination Port']
                    syslog = row['Syslog Enabled']
                    if rule_number:  # Rule number field not empty
                        if rule_number == 'END':
                            break
                        elif int(rule_number) > rule:
                            rule_policy = policy.strip()  # Strip away white spaces
                            rule_comment = comment
                            rule_protocol = protocol.strip()
                            rule_syslog = syslog

                            if src_cidr:
                                src_cidr_lst.append(src_cidr.strip())
                            if src_port:
                                src_port_lst.append(src_port.strip())
                            if dest_cidr:
                                dest_cidr_lst.append(dest_cidr.strip())
                            if dest_port:
                                dest_port_lst.append(dest_port.strip())
                            rule = int(rule_number)

                    else:   # Rule number field is empty - same rule more info
                        if src_cidr:
                            src_cidr_lst.append(src_cidr.strip())
                        if src_port:
                            src_port_lst.append(src_port.strip())
                        if dest_cidr:
                            dest_cidr_lst.append(dest_cidr.strip())
                        if dest_port:
                            dest_port_lst.append(dest_port.strip())

                else:  # Row is entirely empty
                    dest_not_empty = bool(dest_cidr_lst)  # False means empty
                    if dest_not_empty is False:
                        break
                    src_not_empty = bool(src_cidr_lst)    # False means empty
                    if src_not_empty is False:
                        break

                    # CHECK DESTINATION CIDR
                    # Determine if destination is a group or network object
                    for dest in dest_cidr_lst:
                        # Is dest any?
                        if dest == 'Any':
                            dest_cidr_group_id_lst.append(dest)
                            break
                        # Is dest a group?
                        for grp_object in group_obj_lst:
                            if dest in grp_object.values():
                                #name = grp_object['name']
                                id = grp_object['id']
                                dest_group_object = f'GRP({id})'
                                if dest_group_object not in dest_cidr_group_id_lst:
                                    dest_cidr_group_id_lst.append(f'GRP({id})')  # Contains group policy name and id
                                    break
                            # Check if the dest ends in /32 if so, remove the /32
                            if dest.endswith('/32'):  # dest is an IP address
                                dest = dest.replace('/32', '')
                                for net_object in network_obj_lst:
                                    if dest in net_object.values():
                                        id = net_object['id']
                                        dest_obj_32 = f'OBJ({id})'
                                        if dest_obj_32 not in dest_cidr_network_id_lst:
                                            dest_cidr_network_id_lst.append(f'OBJ({id})')  # Contains group policy name and id
                                            break
                            else:   # dest is a policy object name or doesn't exist
                                for net_object in network_obj_lst:
                                    if dest in net_object.values():
                                        id = net_object['id']
                                        dest_obj = f'OBJ({id})'
                                        if dest_obj not in dest_cidr_network_id_lst:
                                            dest_cidr_network_id_lst.append(f'OBJ({id})')  # Contains group policy name and id
                                            break

                    # Determine if destination was a group by checking length of list
                    list_len = len(dest_cidr_group_id_lst)
                    if list_len > 0:
                        dest_exist_as_group_object = True
                    else:
                        dest_exist_as_group_object = False

                    # Determine if destination was a network object by checking length of list
                    list_len = len(dest_cidr_network_id_lst)
                    if list_len > 0:
                        dest_exist_as_network_object = True
                    else:
                        dest_exist_as_network_object = False

                    # Check to see if the destination was found as a group or object 
                    # If not a group or network object alert and EXIT !
                    if dest_exist_as_group_object is False:
                        if dest_exist_as_network_object is False:
                            print(f"\nCould not find destination CIDR: {dest} \n")
                            print("Please check spelling as well as the Group and Network objects to fix issue.\n")
                            print("Exiting script...")
                            quit()

                    # CHECK SOURCE CIDR
                    # Determine if source is a group or network object
                    for src in src_cidr_lst:
                        # Is source any?
                        if src == 'Any':
                            src_cidr_group_id_lst.append(src)
                            break
                        # Is source a group?
                        for grp_object in group_obj_lst:
                            if src in grp_object.values():
                                id = grp_object['id']
                                src_group_object = f'GRP({id})'
                                if src_group_object not in src_cidr_group_id_lst:
                                    src_cidr_group_id_lst.append(f'GRP({id})')  # Contains group policy name and id
                                    break
                            # Check if the the source ends in /32 remove the /32
                            if src.endswith('/32'):  # src is an IP address
                                src = src.replace('/32', '')
                                for net_object in network_obj_lst:
                                    if src in net_object.values():
                                        id = net_object['id']
                                        # If not in list - append
                                        src_obj_32 = f'OBJ({id})'
                                        if src_obj_32 not in src_cidr_network_id_lst:
                                            src_cidr_network_id_lst.append(f'OBJ({id})')  # Contains group policy name and id
                                            break
                            else:  # src is a policy object name or doesn't exist
                                for net_object in network_obj_lst:
                                    if src in net_object.values():
                                        id = net_object['id']
                                        # If not in list - append
                                        src_obj = f'OBJ({id})'
                                        if src_obj not in src_cidr_network_id_lst:
                                            src_cidr_network_id_lst.append(f'OBJ({id})')  # Contains group policy name and id
                                            break

                    # Determine if source was a group by checking length of list
                    list_len = len(src_cidr_group_id_lst)
                    if list_len > 0:
                        src_exist_as_group_object = True
                    else:
                        src_exist_as_group_object = False

                    # Determine if source was a network object by checking length of list
                    list_len = len(src_cidr_network_id_lst)
                    if list_len > 0:
                        src_exist_as_network_object = True
                    else:
                        src_exist_as_network_object = False

                    # Check to see if the source was found as a group or object
                    # If not a group or network object alert and EXIT !
                    if src_exist_as_group_object is False:
                        if src_exist_as_network_object is False:
                            print(f"\nCould not find source CIDR: {src} \n")
                            print("Please check spelling as well as the Group and Network objects to fix issue.\n")
                            print("Exiting script...")
                            quit()

                    # Start putting togther the pieces to build FW rule

                    # Change dest port from list to sting
                    dest_ports = ','.join(dest_port_lst)
                    # Change source port from list to string
                    src_ports = ','.join(src_port_lst)

                    # Create source and destination values
                    # To be use in the FW rule payload
                    # This could be a combination of Group objects
                    # As well as Network objects
                    dest_group_cidr_string = ''
                    dest_network_cidr_string = ''
                    dest_cidr_string = ''
                    src_group_cidr_string = ''
                    src_network_cidr_string = ''
                    src_cidr_string = ''

                    # Join all the ids in the destination group id list and network id list
                    if len(dest_cidr_group_id_lst) > 0:
                        dest_group_cidr_string = ','.join(dest_cidr_group_id_lst)
                    if len(dest_cidr_network_id_lst) > 0:
                        dest_network_cidr_string = ','.join(dest_cidr_network_id_lst)

                    if len(dest_group_cidr_string) > 0 and len(dest_network_cidr_string) > 0:
                        dest_cidr_string = f'{dest_group_cidr_string},{dest_network_cidr_string}'
                    elif len(dest_group_cidr_string) > 0:
                        dest_cidr_string = dest_group_cidr_string
                    else:
                        dest_cidr_string = dest_network_cidr_string

                    # Join all the ids in the source group id list and network id list
                    if len(src_cidr_group_id_lst) > 0:
                        src_group_cidr_string = ','.join(src_cidr_group_id_lst)
                    if len(src_cidr_network_id_lst) > 0:
                        src_network_cidr_string = ','.join(src_cidr_network_id_lst)

                    if len(src_group_cidr_string) > 0 and len(src_network_cidr_string) > 0:
                        src_cidr_string = f'{src_group_cidr_string},{src_network_cidr_string}'
                    elif len(src_group_cidr_string) > 0:
                        src_cidr_string = src_group_cidr_string
                    else:
                        src_cidr_string = src_network_cidr_string

                    # Fill in parameters for firewall rule
                    fw_rule_dict = {
                        "comment": rule_comment,
                        "policy": rule_policy,
                        "protocol": rule_protocol,
                        "destPort": dest_ports,
                        "destCidr": dest_cidr_string,
                        "srcPort": src_ports,
                        "srcCidr": src_cidr_string,
                        "syslogEnabled": rule_syslog
                    }

                    # Create a list of firewall rules
                    fw_rule_dict_copy = copy.deepcopy(fw_rule_dict)
                    fw_rule_lst.append(fw_rule_dict_copy)

                    # Clear variables and lists for next loop
                    rule_policy = ''
                    rule_comment = ''
                    rule_protocol = ''
                    rule_syslog = ''

                    src_cidr_lst.clear()
                    src_port_lst.clear()
                    dest_cidr_lst.clear()
                    dest_port_lst.clear()
                    dest_cidr_group_id_lst.clear()
                    dest_cidr_network_id_lst.clear()
                    src_cidr_group_id_lst.clear()
                    src_cidr_network_id_lst.clear()

            # Generate payload
            for d in fw_rule_lst:
                fw_rule_payload = json.dumps({
                    "rules":
                        fw_rule_lst
                })

            print(f'Firewall Rules to add: {len(fw_rule_lst)}')

            return fw_rule_payload, len(fw_rule_lst)

    except Exception as err: 
        raise Exception(err)

'''
Funtion to execute firewall update
'''
def execute(network_id, org_id, payload, fw_rule_type):

    try:
        print('Creating firewall rules.')
        
        if fw_rule_type == 'l3':
            meraki_api.create_l3_fw_rules(network_id, payload)
        elif fw_rule_type == 's2s':
            meraki_api.create_s2s_vpn_fw_rules(org_id, payload)

    except Exception as err: 
        raise Exception(err)


'''
Function to remove all firewalls
'''
def delete_firewall_rules(net_id, org_id):

    try:

        print('Deleting firewall rules.')

        fw_rule_payload = json.dumps({
                            "rules":[]
                        })

        meraki_api.create_l3_fw_rules(net_id, fw_rule_payload)
        meraki_api.create_s2s_vpn_fw_rules(org_id, fw_rule_payload)
    
    except Exception as err: 
        raise Exception(err)


