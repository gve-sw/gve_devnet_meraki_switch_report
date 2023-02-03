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
import meraki


def get_org_id(org_name, dashboard):
    organizations = dashboard.organizations.getOrganizations()
    for org in organizations:
        if org["name"] == org_name:
            return org["id"]

    return None


def get_network_id(org_id, net_name, dashboard):
    networks = dashboard.organizations.getOrganizationNetworks(org_id,
                                                               total_pages="all")
    for net in networks:
        if net["name"] == net_name:
            return net["id"]

    return None


def get_network(net_id, dashboard):
    network = dashboard.networks.getNetwork(net_id)

    return network


def get_organization_switches(org_id, dashboard):
    switches = dashboard.organizations.getOrganizationDevices(org_id,
                                                              total_pages="all",
                                                              productTypes=["switch"])

    return switches


def get_network_devices(network_id, dashboard):
    devices = dashboard.networks.getNetworkDevices(network_id)

    return devices


def get_switch_ports(serial, dashboard):
    ports = dashboard.switch.getDeviceSwitchPorts(serial)

    return ports


def get_port_statuses(serial, dashboard):
    port_statuses = dashboard.switch.getDeviceSwitchPortsStatuses(serial)

    return port_statuses


def get_device_clients(serial, dashboard):
    clients = dashboard.devices.getDeviceClients(serial, total_pages="all")

    return clients


def get_network_client(net_id, client_id, dashboard):
    client = dashboard.networks.getNetworkClient(net_id, client_id)

    return client


def get_network_clients(net_id, dashboard):
    client = dashboard.networks.getNetworkClients(net_id)

    return client


def get_switch_profile(org_id, profile_id, dashboard):
    switch_profile = dashboard.switch.getOrganizationConfigTemplateSwitchProfiles(org_id, profile_id)

    return switch_profile
