#!/usr/bin/env python3
"""
Copyright (c) 2022 Cisco and/or its affiliates.

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

import os, sys
import meraki
import pandas as pd
from dotenv import load_dotenv
from pprint import pprint
from collections import defaultdict
from datetime import datetime
from meraki_functions import get_org_id, get_network_id, get_network, get_switch_ports, get_port_statuses, get_device_clients, get_network_devices, get_switch_profile


def main(argv):
    # retrieve environment variable
    load_dotenv()
    api_key = os.getenv("API_KEY")
    org_name = os.getenv("ORG_NAME")
    # the network name retrieve from the argument variables
    if len(argv) < 2:
        print("Provide the name of the network after 'python3 report.py'")

        return

    net_name = argv[1]

    # created dashboard object with Meraki SDK to connect to your Meraki account
    dashboard = meraki.DashboardAPI(api_key, suppress_logging=True)

    # get organization id from organization name
    org_id = get_org_id(org_name, dashboard)
    if org_id is None:
        print("There was an issue finding an organization with the name {}".format(org_name))

        return

    # get network id from network name
    net_id = get_network_id(org_id, net_name, dashboard)
    if net_id is None:
        print("There was an issue finding a network with the name {}".format(net_name))

        return

    profile_dict = {} # this variable will map the switch profile ids to the profile names
    # retrieve network information for the network provided
    network = get_network(net_id, dashboard)
    # if network is bound to a config template, retrieve the configuration template id and all the switch profiles associated with that configuration template
    if network["isBoundToConfigTemplate"]:
        template_id = network["configTemplateId"]
        switch_profiles = get_switch_profile(org_id, template_id, dashboard)
        for profile in switch_profiles:
            profile_id = profile["switchProfileId"]
            profile_name = profile["name"]
            # map profile id to profile name with profile_dict
            profile_dict[profile_id] = profile_name

    # retrieve all the devices as a part of the network provided
    network_devices = get_network_devices(net_id, dashboard)

    # save a list of all the switches that are a part of the network
    switches = []
    for device in network_devices:
        if "MS" in device["model"]:
            switches.append(device)

    # iterate through the switches and save which switch profile is applied to each switch, then add it to the list of switch_templates
    switch_templates = []
    for switch in switches:
        serial = switch["serial"]
        switch_name = switch["name"]
        if "switchProfileId" in switch.keys():
            switch_profile_id = switch["switchProfileId"]
            profile_name = profile_dict[switch_profile_id]
            switch_template_info = {
                "switchSerial": serial,
                "switchName": switch_name,
                "profileId": switch_profile_id,
                "profileName": profile_name
            }
        else:
            switch_template_info = {
                "switchSerial": serial,
                "switchName": switch_name,
                "profileId": "None",
                "profileName": "None"
            }
        switch_templates.append(switch_template_info)

    # iterate through the switches and retrieve the port information, the clients of each switch, and the port statuses
    switch_ports = {}
    switch_clients = {}
    switch_port_statuses = {}
    for switch in switches:
        serial = switch["serial"]

        ports = get_switch_ports(serial, dashboard)
        switch_ports[serial] = ports

        clients = get_device_clients(serial, dashboard)
        switch_clients[serial] = clients

        port_statuses = get_port_statuses(serial, dashboard)
        switch_port_statuses[serial] = port_statuses

    # for each client of the switch, track the mac addresses and ip addresses
    switch_port_client_macs = {}
    switch_port_client_ips = {}
    for switch in switch_clients:
        switch_port_client_macs[switch] = defaultdict(list)
        switch_port_client_ips[switch] = defaultdict(list)
        for client in switch_clients[switch]:
            client_port_no = client["switchport"]
            switch_port_client_macs[switch][client_port_no].append(client["mac"])
            switch_port_client_ips[switch][client_port_no].append(client["ip"])

    # add the client mac addresses and ip addresses to the dictionary saving information about the port
    for switch in switch_ports:
        for port in switch_ports[switch]:
            port_id = port["portId"]
            if switch_port_client_macs[switch][port_id]:
                port["client_macs"] = switch_port_client_macs[switch][port_id]
            if switch_port_client_ips[switch][port_id]:
                port["client_ips"] = switch_port_client_ips[switch][port_id]


    # create a dictionary that will hold the information that will go into the spreadsheet
    switch_port_report = {}
    for switch in switch_port_statuses:
        switch_port_report[switch] = []
        for index, status in enumerate(switch_port_statuses[switch]):
            port_id = switch_ports[switch][index]["portId"]
            enabled = switch_ports[switch][index]["enabled"]
            port_type = switch_ports[switch][index]["type"]
            vlan = switch_ports[switch][index]["vlan"]
            allowed_vlan = switch_ports[switch][index]["allowedVlans"]
            if "client_macs" in switch_ports[switch][index].keys():
                client_macs = switch_ports[switch][index]["client_macs"]
            else:
                client_macs = []
            if "client_ips" in switch_ports[switch][index].keys():
                client_ips = switch_ports[switch][index]["client_ips"]
            else:
                client_ips = []
            port_report_info = {
                "portId": port_id,
                "enabled": enabled,
                "type": port_type,
                "vlan": vlan,
                "allowedVlans": allowed_vlan,
                "status": status["status"],
                "clientMacAddresses": client_macs,
                "clientIpAddresses": client_ips
            }
            switch_port_report[switch].append(port_report_info)

    pprint(switch_port_report)

    # create the spreadsheet
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d") # save the current date as a string
    wb = net_name + "_" + date_str + "_Report.xlsx" # name the workbook after the network name and the current date
    with pd.ExcelWriter(wb) as writer:
        # for each switch create a worksheet from the information in the switch_port_report dictionary
        for switch in switches:
            switch_name = switch["name"].split('-')
            ws = switch_name[-1]
            serial = switch["serial"]

            df = pd.DataFrame.from_dict(switch_port_report[serial])
            df.to_excel(writer, sheet_name=ws)

        # create a worksheet for the switch templates
        ws = "Switch_Templates"
        df = pd.DataFrame.from_dict(switch_templates)
        df.to_excel(writer, sheet_name=ws)

    return


if __name__ == "__main__":
    sys.exit(main(sys.argv))
