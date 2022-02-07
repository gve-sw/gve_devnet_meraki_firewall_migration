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

''' This class includes all context variables and classes'''

import meraki_api

import pandas as pd
import os
from pathlib import Path
import json
from pprint import pprint
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage

load_dotenv()


class Context:

    '''
    Variable shared by all
    '''
    UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__)) + '/UPLOADS'

    '''
    Variables shared per object
    '''
    def __init__(self, dropdown_list = list()):
        self.api_key = os.environ['MERAKI_API_TOKEN']
        self.dropdown_list = dropdown_list
        self.selected_context = {'organization_id': None, 'organization_name': None, 'network_id': None, 'network_name': None}
        self.selected_organization_dashboard_url = ''
        self.selected_network_dashboard_url = ''
        self.fw_rule_type = ''
        self.policy_document_filename = ''
        self.firewall_document_filename = ''
        self.policy_object_groups_lst = list()
        self.added_groups_count = 0
        self.added_objects_count = 0
        self.policy_object_names_lst = list()  
        self.policy_object_dict_lst = list()
        self.policy_linking_dict = list()
        self.added_links = 0
        self.firewall_rules_count = 0
        self.firewall_rule_payload = list()
        self.firewall_network_obj_lst = list()
        self.firewall_group_obj_lst = list()

    '''
    Map organization and network ids to names and save all as selected_context 
    '''
    def update_user_selection(self, organization_id, network_id, fw_rule_type, policy_document_file, firewall_document_file):
        
        #Reset values
        self.selected_context = {'organization_id': None, 'organization_name': None, 'network_id': None, 'network_name': None}
        self.clear_folder(self.UPLOAD_FOLDER)        
        self.policy_document_filename = ''
        self.firewall_document_filename = ''
        self.fw_rule_type = ''

        #Populate selected_context and selected_dashboard_url
        for organization in self.dropdown_list:

            if organization_id == organization['id']:
                self.selected_context['organization_id'] = organization_id
                self.selected_context['organization_name'] = organization['name']
                self.selected_organization_dashboard_url = organization['url']

                for network in organization['networks']:
                    if network_id == network['id']:
                        self.selected_context['network_id'] = network_id
                        self.selected_context['network_name'] = network['name']
                        self.selected_network_dashboard_url = network['url']

        #Save files and populate filename variables
        self.policy_document_filename = self.save_file(policy_document_file)
        self.firewall_document_filename = self.save_file(firewall_document_file)
        self.fw_rule_type = fw_rule_type


    '''
    Remove all files in folder
    '''
    def clear_folder(self, path):
        
        for f in os.listdir(path):
            os.remove(os.path.join(path, f))

    '''
    Save files in UPLOAD_FOLDER
    '''
    def save_file(self, uploaded_file):   
        if uploaded_file:

            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(self.UPLOAD_FOLDER, filename)

            uploaded_file.save(file_path)

            return file_path

    '''
    Save excel as converted json file in UPLOAD_FOLDER
    '''
    def save_json_file(self, uploaded_excel_filename): 

        file_path =  os.path.join(self.UPLOAD_FOLDER, uploaded_excel_filename)

        uploaded_file_json = self.excelToJson(file_path, False)
        self.write_json_file(file_path, uploaded_excel_filename)

    '''
    Convert excel xlsx, xls or csv to json 
    '''
    def excelToJson(file, print_bool):

        file_extension = Path(file).suffix.lower()[1:]

        if file_extension == 'xlsx':
            excel_df = pd.read_excel(file, engine='openpyxl')
        elif file_extension == 'xls':
            excel_df = pd.read_excel(file)
        elif file_extension == 'csv':
            excel_df = pd.read_csv(file)

        excel_json = json.loads(excel_df.to_json(orient="records"))
        
        if(print_bool):   
            print(json.dumps(excel_json, indent=4, sort_keys=True, ensure_ascii=False))
        
        return excel_json

    '''
    Write json data to json file
    '''
    def write_json_file(filepath, data):
        
        filepath = filepath.split('.')[0] + '.json'
        
        with open(filepath, "w") as f:
            json.dump(data, f)
        
        f.close()
        

