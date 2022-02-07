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

'''
Imports
'''
from flask import Flask, render_template, request, url_for, redirect, Response
from pprint import pprint
import time
import os

from context_helper import Context
#from policy import Policy

import meraki_api
import policy_helper
import firewall_helper


'''
Global variables
'''
step = 0
hide_loader = False
context_helper = Context()

app = Flask(__name__)


#Routes
'''
Migration Settings Page
'''
@app.route('/', methods=['GET', 'POST'])
def migration():
    try:

        global step
        global hide_loader
        global context_helper

        if request.method == 'POST':

            step = 0
            hide_loader = False
            
            #Retieve information from form
            organization_id = request.form.get("organizations_select")
            network_id = request.form.get("network")
            policy_document_file = request.files['policy_objects']
            firewall_document_file = request.files['firewall_rules'] 
            fw_rule_type = request.form['type'] # l3 or s2s

            #Update context
            context_helper.update_user_selection(organization_id, network_id, fw_rule_type, policy_document_file, firewall_document_file)

            return render_template('migration_workflow.html', hiddenLinks=False, dropdown_content = context_helper.dropdown_list, selected_elements = context_helper.dropdown_list)

        elif request.method == 'GET':
            
            #Create list with all organization and networks used for the dropdown selection
            dropdown_list = meraki_api.get_organizations()
    
            for organization in dropdown_list:
                organization_id = organization['id']
                organization.update([("networks", meraki_api.get_networks(organization_id))])

            #Create Context object
            context_helper = Context(dropdown_list=dropdown_list)

        return render_template('migration_settings.html', hiddenLinks=True, dropdown_content = context_helper.dropdown_list, selected_elements = context_helper.dropdown_list)
    
    except Exception as e: 
        print(f'EXCEPTION!! {e}')
        return render_template('migration_settings.html', error=True, errormessage=e, dropdown_content = context_helper.dropdown_list, selected_elements = context_helper.dropdown_list)


'''
Migration process
'''
@app.route('/steps')
def steps():
    try:

        global step
        global hide_loader
        global context_helper

        policy_dashboard_url = ''
        firewall_dashboard_url = ''

        step += 1
        organization_id = context_helper.selected_context['organization_id']
        organization_name = context_helper.selected_context['organization_name']
        network_id = context_helper.selected_context['network_id']
        network_name = context_helper.selected_context['network_name']

        print(f'---------------------Step: {step} ---------------------')


        if(step == 1):
            
            #Process policy excel files
            context_helper.policy_object_groups_lst, context_helper.policy_object_names_lst, context_helper.policy_object_dict_lst, context_helper.policy_linking_dict = policy_helper.read_csv(context_helper.policy_document_filename, organization_id)

        elif(step == 2):

            # Call function: to determine if group object exists or needs created
            context_helper.added_groups_count = policy_helper.check_group_obj(context_helper.policy_object_groups_lst, organization_id)
        
        elif(step == 3):

            # Call function: to determine if network object exists or needs created
            context_helper.added_objects_count = policy_helper.check_net_obj(context_helper.policy_object_names_lst, context_helper.policy_object_dict_lst, organization_id)
                      
        elif(step == 4): 
             
            # Call function: to link network objects to group objects
            context_helper.added_links = policy_helper.link_objects_to_groups(organization_id, context_helper.policy_linking_dict)
                    
        elif(step == 5):
            
            #Get policy objects and groups      
            context_helper.firewall_group_obj_lst = []
            context_helper.firewall_network_obj_lst = []
            context_helper.firewall_group_obj_lst = meraki_api.list_group_obj(organization_id)
            context_helper.firewall_network_obj_lst = meraki_api.list_network_obj(organization_id)
            
            #Read firewall rules file and create firewall rule payload  
            context_helper.firewall_rule_payload, context_helper.firewall_rules_count = firewall_helper.read_csv(network_id, context_helper.firewall_document_filename, context_helper.firewall_group_obj_lst, context_helper.firewall_network_obj_lst)

        elif(step == 6):

            # Call function to create firewall rules
            firewall_helper.execute(network_id, organization_id, context_helper.firewall_rule_payload, context_helper.fw_rule_type)
        
        elif(step == 7):

            #Build Dashboard URLs
            print('Generate Meraki Dashboard URLs')
            policy_dashboard_url = context_helper.selected_organization_dashboard_url.split('/organization/overview')[0] + '/network_objects/objects' 
            if context_helper.fw_rule_type == "l3":
                firewall_dashboard_url = context_helper.selected_network_dashboard_url.split('/usage/list')[0] + '/configure/firewall'
            elif context_helper.fw_rule_type == "s2s":
                firewall_dashboard_url = context_helper.selected_network_dashboard_url.split('/usage/list')[0] + '/configure/vpn_settings'

            hide_loader = True
            
        time.sleep(1)

        return render_template('migration_steps.html', error=False, step=step, hideloader = hide_loader, policy_dashboard_url = policy_dashboard_url, firewall_dashboard_url = firewall_dashboard_url, networkName = network_name, orgaName = organization_name, documented_groups = len(context_helper.policy_object_groups_lst), added_groups=context_helper.added_groups_count, documented_objects=len(context_helper.policy_object_names_lst), added_objects=context_helper.added_objects_count, documented_firewall_rules=context_helper.firewall_rules_count, added_links = context_helper.added_links)
    except Exception as e: 
        print(f'EXCEPTION!! {e}')  
        return render_template('migration_steps.html', error=True, errormessage=e, step=step, hideloader = hide_loader)


'''
Deletion procress - deletes all firewall rules, policy objects and groups
'''
@app.route('/delete', methods=['GET', 'POST'])
def delete():

    global context_helper

    try:

        if request.method == 'POST':
            
            success_message = 'Successfully removed all firewall rules, policy groups and objects.'
            organization_id = request.form.get("organizations_select")
            network_id = request.form.get("network")

            #Delete firewall rules
            firewall_helper.delete_firewall_rules(network_id, organization_id)

            #Delete policy groups and objects
            policy_helper.delete_everything_batch(organization_id)
            
            return render_template('delete_settings.html', hiddenLinks=False, dropdown_content = context_helper.dropdown_list, selected_elements = context_helper.dropdown_list, success = True, successmessage=success_message)

        elif request.method == 'GET':
            
            #Create list with all organization and networks used for the dropdown selection
            dropdown_list = meraki_api.get_organizations()
    
            for organization in dropdown_list:
                organization_id = organization['id']
                organization.update([("networks", meraki_api.get_networks(organization_id))])

            #Create Context object
            context_helper = Context(dropdown_list=dropdown_list)

        return render_template('delete_settings.html', hiddenLinks=False, dropdown_content = context_helper.dropdown_list, selected_elements = context_helper.dropdown_list, success = False)
    
    except Exception as e: 
        print(f'EXCEPTION!! {e}')  
        return render_template('delete_settings.html', error=True, errormessage=e, dropdown_content = context_helper.dropdown_list, selected_elements = context_helper.dropdown_list, success = False)


'''
Download functionality - support the download of csv templates used for this migration tool
Call via: /downloadTemplate?file=<filename>.csv
'''
@app.route('/downloadTemplate', methods=['GET'])
def downloadTemplate():

    file_name = request.args.get('file') 
    file_path = 'CSVTEMPLATES/' + file_name
    
    with open(file_path, 'rb') as f:
        data = f.readlines()

    return Response(data, headers={
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=%s;' % file_name
    })


if __name__ == "__main__":

    app.run(host='0.0.0.0', port=5001, debug=True)
