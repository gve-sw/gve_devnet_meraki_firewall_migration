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

import time
import json
import os
from enum import Enum, auto
from pprint import pprint
from dotenv import load_dotenv

import meraki_api

load_dotenv()

class BatchHelper: 

    def __init__(self,
                organizationId: str,
                new_actions: list,
                confirmed_new_batches: bool = True,
                actions_per_new_batch: int = int(os.environ['MAX_ACTIONS_ASYNC']),
                interval_factor: float = float(os.environ['MINIMUM_INTERVAL_FACTOR']),
                maximum_active_batches: int = int(os.environ['MAXIMUM_ACTIVE_ACTION_BATCHES'])):


        # self assignments
        self.organizationId = organizationId
        self.new_actions = new_actions
        self.confirmed_new_batches = confirmed_new_batches
        self.actions_per_new_batch = actions_per_new_batch
        self.interval_factor = interval_factor
        self.maximum_active_batches = maximum_active_batches

        # defaults prior to preparation
        self.new_batches = list()
        self.new_batches_responses = list()
        self.submitted_new_batches_ids = list()


    #Prepare
    ''' Groups actions into lists of appropriate size and returns a list generator. '''
    def group_actions(self):
        total_actions = len(self.new_actions)
        for i in range(0, total_actions, self.actions_per_new_batch):
            yield self.new_actions[i:i + self.actions_per_new_batch]

    '''Groups actions into batches of the appropriate size. '''
    def prepare(self):
        grouped_actions_list = list(self.group_actions())
        created_batches = list()

        # Add each new batch to the new_batches list
        for action_list in grouped_actions_list:
            batch = {
                "actions": action_list,
                "synchronous": False,
                "confirmed": True
            }
            created_batches.append(batch)

        self.new_batches = created_batches

    #Preview
    ''' Generates a JSON preview of the new batches. '''
    def generate_preview(self):
        self.prepare()

        preview_json = json.dumps(self.new_batches, indent=2)
        with open('batch_helper_preview.json', 'w+', encoding='utf-8', newline='') as preview_file:
            preview_file.write(preview_json)

    #Execute
    ''' Submit the next batch and remove it from the list of remaining batches. '''
    def submit_action_batches(self):
        try:            
            new_batch_response = meraki_api.post_organization_action_batches(self.organizationId, self.new_batches.pop(0))
            time.sleep(1)
        except Exception as err: 
            raise Exception(err)

        self.new_batches_responses.append(new_batch_response)
        self.submitted_new_batches_ids.append(new_batch_response['id'])

        print(f'Creating the next action batch. {len(self.new_batches)} action batches remain.')

    
    ''' Returns the organization's batch queue: pending, active, and whether full. '''
    def check_batch_queue(self):
        try:
            pending_action_batches = meraki_api.get_organization_action_batches(self.organizationId, 'pending')
            
            active_action_batches = [batch for batch in pending_action_batches if batch['confirmed']]

            # Dashboard API supports up to MAXIMUM_ACTIVE_ACTION_BATCHES.
            batch_queue_is_full = True if len(active_action_batches) >= self.maximum_active_batches else False

            print(f'Checking batch queue...')
            return pending_action_batches, active_action_batches, batch_queue_is_full
        except Exception as err: 
            raise Exception(err)

    ''' Finds capacity on the batch queue. '''
    def find_batch_queue_capacity(self):
        pending_action_batches, active_action_batches, batch_queue_is_full = self.check_batch_queue()
        number_of_active_batches = len(active_action_batches)
        print(f'There are {number_of_active_batches} active action batches.')

        if len(active_action_batches):
            # If there are any active action batches, then flatten the list of actions; we want to know how many total
            # actions are pending, so we can calculate a reasonable wait time. Waiting too long is no fun, but
            # checking too frequently is inefficient, and might impact other API applications.
            print(f'Finding batch queue capacity...')

            # Gather all the action lists for the existing action batches
            active_batch_action_lists = [batch['actions'] for batch in active_action_batches]

            # Flatten the list of action lists into a single list of actions
            active_batch_actions = [action for action_list in active_batch_action_lists for action in action_list]

            # Calculate the mean number of actions per batch
            mean_actions_per_batch = len(active_batch_actions) / number_of_active_batches

            # Set an interval based on the interval_factor and the mean actions per batch
            interval = self.interval_factor * mean_actions_per_batch

            while batch_queue_is_full:
                # Wait for space in the queue until there's an open slot.
                print(f'There are already {number_of_active_batches} active action batches. Waiting {interval} '
                        f'seconds before trying again.')
                time.sleep(interval)

                active_action_batches, active_action_batches, batch_queue_is_full = self.check_batch_queue()
        return True

    ''' Submits new batches. '''
    def execute(self):
        while len(self.new_batches):
            
            # Loop as long as there are batches left to process
            print(f'Confirming readiness for batch submission...')

            ready_for_new_batch = False
            while not ready_for_new_batch:
                ready_for_new_batch = self.find_batch_queue_capacity()

            print(f'Submitting new batch.')
            # submit new batch(es)
            self.submit_action_batches()

        return True
    
    #Report
    '''Check if action batches finished successful'''
    def report(self):

        try:

            failed_batches_lst = list()

            #Check that all action batches in queue finished
            self.wait_for_finished_batch_queue()

            print(f'{len(self.submitted_new_batches_ids)} action batches were submitted. Action batch ids: {self.submitted_new_batches_ids}')

            # Check for all submitted and finished action batches that the finished successful. 
            # If not output error in console and add action batch to a seperate list
            for submitted_batch_id in self.submitted_new_batches_ids:
            
                submitted_batch_info = meraki_api.get_organization_action_batch(self.organizationId, submitted_batch_id)

                if submitted_batch_info["status"]['failed']:
                    failed_batch_id = submitted_batch_info['id'] 
                    failed_batch_error = submitted_batch_info["status"]["errors"]
                    
                    print(f'Batch ID: {failed_batch_id}')
                    print(f'Failure Reason: {failed_batch_error}')

                    failed_batches_lst.append()

                time.sleep(1)

            failed_batches_count = len(failed_batches_lst)

            #If 1 or more action batches failed throw an exception
            if(failed_batches_count > 0):
                raise Exception(f'{failed_batches_count} action batches failed. Failed action batch ids: {failed_batches_lst} .Check your console for details.')
            else:
                print('All actions batches executed successfully.')

        except Exception as err: 
            raise Exception(err)

    '''Function to wait for the queue to finish'''
    def wait_for_finished_batch_queue(self):

        queue_finished = False

        while(not queue_finished):
            queue_finished = self.queue_finished()
            time.sleep(1)

        print('No pending action batches in the queue.')

        return queue_finished

    '''Function to check if queue finished'''
    def queue_finished(self):
        try:
            pending_action_batches = meraki_api.get_organization_action_batches(self.organizationId, 'pending')
            
            active_action_batches = [batch for batch in pending_action_batches if batch['confirmed']]
            
            print('Current batch queue: ' + str(len(active_action_batches)))
            
            if(len(active_action_batches) == 0):
                return True
            else:
                return False

        except Exception as err: 
            raise Exception(err)










