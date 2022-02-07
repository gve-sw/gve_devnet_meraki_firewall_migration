# Meraki Policy Objects
The purpose of this sample code is to ease the migration of L3 and Site-to-Site VPN firewall rules including network policy objects and groups to a Meraki MX security appliance. Via a simple user interface, all relevant migration information can be uploaded as .csv files to then trigger the automatic migration process. The sample code uses RESTful API endpoints to:

* Create Policy Objects
* Create Policy Object Groups
* Add Policy Objects to the appropriate Policy Object Groups
* Leverage the Policy Objects and Policy Object Groups to create Layer 3 or Site-to-Site VPN firewall rules

Furthermore, the scripts offers the functionality to delete all network policy objects, groups and firewall rules for a specific network.

  > Please be aware: at the time of this writing Meraki Network Objects is an Open Beta feature. Details can be found here on how to enable the Open Beta Network Objects: [Network Objects Configuration Guide](https://documentation.meraki.com/MX/Firewall_and_Traffic_Shaping/Network_Objects_Configuration_Guide)


## Contacts
* Clint Mann
* Ramona Renner

## Solution Components
* Meraki Dashboard with a Meraki MX Security Appliance
* Dashboard API Key (Instructions shared in this document later)

## Workflow
![/IMAGES/migration_workflow.png](/IMAGES/migration_workflow.png)

## High-Level Architecture
![/IMAGES/migration_workflow.png](/IMAGES/migration_high_level.png)

## Preparation of the .csv Files

### Creation of the Policy Objects and Groups .csv File 

Use the **sample-object-import.csv** as a template.  

The first row of the .csv must contain the following column headers:  

**name | category | type | cidr | fqdn | groupName**

These column headers correlate to the parameters used for our API request body.

* The **name** of a policy objects and policy object groups must be alphanumeric. They can contain spaces, dashes, or underscore characters and must be unique within the organization. A period (.) or foward slash (/) in the name will not be accepted. Take this into account when naming your subnets.  

* The **category** field will always be **network** in our use case.

* The **type** field will either be **cidr** or **fqdn**

* If the policy object is not part of a policy object group. Leave the **groupName** field empty.

* If the policy object is in multiple policy object groups: enter the object **name**, **category**, **type**, **cidr** or **fqnd** in a new row with the second **groupName**.

* Policy object groups can only contain 150 objects. Therefore, you may have to break up some of your groups in order to adhere to the 150 object limit.

### Creation of the Layer 3 or Site-to-Site VPN Firewall Rules .csv File  

Use the **sample-l3-fw-rules.csv** or **sample-vpn-fw-rules.csv** as a template.  

The first row of the .csv must contain the following column headers:

**Rule Number | Policy | Comment | Protocol | Source CIDR | Source Port | Destination CIDR | Destination Port | Syslog Enabled**

* There must be an empty row between each firewall rule. The last firwall rule will be followed by a row with the word **END** in each field as shown in the firewall sample templates.

* Firewall rules can have one **port** range defined (5000-7500) or a group of individual ports (80,443,558) but not both. They also can’t have 2 ranges (5000-7500, 10000-11000). If multiple port ranges are required. Each range must be in a new row.

* Meraki rules can be created for the following **protocols**: **TCP**, **UDP**, **ICMP** or **ANY**. Unless you use ANY, you can’t define TCP and UDP in the same rule. If you require both TCP and UDP, you can create two separate rules. One for TCP and one for UDP.


## Installation

1. Make sure you have [Python 3.8.0](https://www.python.org/downloads/) and [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed

2.	(Optional) Create and activate a virtual environment 
    ```
    python3 -m venv [add name of virtual environment here] 
    source [add name of virtual environment here]/bin/activate
    ```
  * Access the created virtual environment folder
    ```
    cd [add name of virtual environment here] 
    ```

3. Clone this Github repository into the local folder:  
  ```git clone [add github link here]```
  * For Github link: 
      In Github, click on the **Clone or download** button in the upper part of the page > click the **copy icon**  
      ![/IMAGES/giturl.png](/IMAGES/giturl.png)
  * Or simply download the repository as zip file using 'Download ZIP' button and extract it

4. Access the downloaded folder:  
    ```cd gve_devnet_meraki_firewall_migration```

5. Install all dependencies:  
  ```pip install -r requirements.txt```

6. Fill in your MERAKI_API_TOKEN in the **.env** file. All other values in this file need no configuration.     
      
  ```  
    MERAKI_API_TOKEN="[Fill in the Meraki API Token]"
  ```
  > Note: Follow the instruction under https://developer.cisco.com/meraki/api/#!authorization/obtaining-your-meraki-api-key to obtain the **Meraki API Token**.

  > Note: Mac OS hides the .env file in the finder by default. View the demo folder for example with your preferred IDE to make the file visible.

7. Run the application   
  ```python app.py```


At this point, everything is set up and the application is running.   
Open a browser and access the URL localhost:5001 via the browser.

The policy objects and groups file will append anything new without touching the existing objects/groups. After the first import, you can use smaller files with just a few new items to add new objects/groups or to adjust the group membership of an existing object.

The Firewall rules file will always overwrite the existing rules with whatever is in the import file. This is a function of how the API call works. If you want to add a rule, you should add it to the .csv file and re-run the migration process.


## Screenshots

![/IMAGES/screenshot_1.png](/IMAGES/screenshot_1.png)
![/IMAGES/screenshot_2.png](/IMAGES/screenshot_2.png)
![/IMAGES/screenshot_3.png](/IMAGES/screenshot_3.png)
![/IMAGES/screenshot_4.png](/IMAGES/screenshot_4.png)


## More Useful Resources
 - [Cisco Meraki Dashboard API Documentation](https://developer.cisco.com/meraki/api-v1/)
 - This script uses code of the [Action Batch Helper Project](https://github.com/TKIPisalegacycipher/Action-Batch-Helper)


### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> 
This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.

  

  

