from collections import defaultdict
from statistics import mode
import pandas as pd
import os
from openpyxl import load_workbook
import importlib
# Import custom functions
from my_mods.general import iterate_dict, iterate_list, clear
from my_mods.san import wwpn_colonizer
from my_mods.san_cheatsheet import brocade_cheatsheet, cisco_cheatsheet
# Global Variables
clear()
customer_name = input('Enter customer name: ').lower()
config = importlib.import_module(f'data.{customer_name}.config')
customer_path = os.path.join(config.customer_path, customer_name)
workbook = os.path.join(customer_path, config.san_input, config.zoning_workbook)
wb = load_workbook(workbook, data_only=True)


# Function required to build Data Frames
def table_to_df(sheet_name, table_name='default'):
    '''
    Pass in a worksheet from openpyxl and the name of the table
    function will return the contents of the table as a pandas df with the table 
    headers as the header of the dataframe
    '''
    table_dict = {}
    for table, data_boundary in wb[sheet_name].tables.items():
        #parse the data within the ref boundary
        data = wb[sheet_name][data_boundary]
        #extract the data 
        #the inner list comprehension gets the values for each cell in the table
        content = [[cell.value for cell in ent] 
                for ent in data
            ]
        header = content[0]
        #the contents ... excluding the header
        table_contents = content[1:]
        
        #create dataframe with the column names
        #and pair table name with dataframe
        df = pd.DataFrame(table_contents, columns = header)
        table_dict[table] = df
    if table_name == 'default':
        return table_dict[table]
    else:
        return table_dict[table_name]

# Build Data Frames from Workbook Tables
df_fabrics = table_to_df('fabrics')
df_aliases = table_to_df('aliases')
df_zones = table_to_df('zones')
df_config = table_to_df('config')
df_config.set_index("parameter", inplace = True)  # allows the column "parameter" to be index

# Set config parameters
san_vendor = df_config.loc['san_vendor', 'setting']
if san_vendor == 'Brocade':
    zoneset_config = 'zone config'
    san_cheatsheet = brocade_cheatsheet
elif san_vendor == 'Cisco':
    zoneset_config = 'zoneset'
    san_cheatsheet = cisco_cheatsheet
    alias_type = df_config.loc['cisco_alias', 'setting']

# Set Classes
class Fabric:
    def __init__(self, name, active_zoneset_config, vsan='None'):
        self.name = name
        self.active_zoneset_config = active_zoneset_config
        self.vsan = vsan
    def __str__(self):
        return self.name


class Port:
    def __init__(self, alias, wwpn, tag, fabric):
        self.alias = alias
        self.wwpn = wwpn
        self.tag = tag
        self.fabric = fabric
    def __str__(self):
        return self.alias


class Zone:
    def __init__(self, name, fabric, zone_type, member_list):
        self.name = name
        self.fabric = fabric
        self.zone_type = zone_type
        self.member_list = member_list
    def __str__(self):
        return self.name


def main():
    fabric_dict = create_fabric_dict()
    port_dict = create_port_dict(fabric_dict)
    zone_dict = create_zone_dict(fabric_dict, port_dict)
    alias_command_dict = create_alias_command_dict(port_dict)
    zone_command_dict = create_zone_command_dict(zone_dict)
    zoneset_command_dict = create_zoneset_command_dict(zone_dict)
    write_to_file(alias_command_dict, zone_command_dict, zoneset_command_dict)



def create_fabric_dict():
    fabric_dict = {}
    for index, row in df_fabrics.iterrows():
        active_zoneset_config = row['active zoneset/config']
        name = row['name']
        vsan = row['vsan']
        fabric_dict[name] = Fabric(name, active_zoneset_config, vsan)
    return fabric_dict


def create_port_dict(fabric_dict):
    port_list = []
    port_dict = defaultdict(list)
    for index, row in df_aliases.iterrows():
        fabric_name = row['fabric']
        fabric = fabric_dict[fabric_name]
        name = row['name']
        wwpn = row['wwpn1']
        tag = row['tag']
        this_port = Port(name, wwpn, tag, fabric)
        port_list.append(this_port)
    for port in port_list:
        port_dict[port.fabric].append(port)
    return dict(port_dict)


def create_zone_dict(fabric_dict, port_dict):
    zone_list = []
    zone_dict = defaultdict(list)
    for index, row in df_zones.iterrows():
        member_list = []
        name = row['name']
        fabric_name = row['fabric']
        zone_type = row['zone type']
        fabric = fabric_dict[fabric_name]
        for port in port_dict[fabric]:
            if port.alias == row['member1']:
                member_list.append(port)
            if port.alias == row['member2']:
                member_list.append(port)
            if port.alias == row['member3']:
                member_list.append(port)
            if port.alias == row['member4']:
                member_list.append(port)
            if port.alias == row['member5']:
                member_list.append(port)       
            if port.alias == row['member6']:
                member_list.append(port)
            if port.alias == row['member7']:
                member_list.append(port)
            if port.alias == row['member8']:
                member_list.append(port)
        this_zone = Zone(name, fabric, zone_type, member_list)
        zone_list.append(this_zone)
    for zone in zone_list:
        zone_dict[zone.fabric].append(zone)
    return dict(zone_dict)


def create_alias_command_dict(port_dict):
    alias_command_dict = defaultdict(list)
    for fabric, port_list in port_dict.items():
        for port in port_list:
            if san_vendor == 'Brocade':
                alias_command_dict[port.fabric].append(f'alicreate "{port.alias}", "{wwpn_colonizer(port.wwpn)}"')
            elif san_vendor == 'Cisco':
                if alias_type == 'device-alias': 
                    alias_command_dict[port.fabric].append(f'device-alias name {port.alias} pwwn {wwpn_colonizer(port.wwpn)}')
                elif alias_type == 'fcalias':
                    alias_command_dict[port.fabric].append(f'fcalias name {port.alias} vsan {port.fabric.vsan}')
                    alias_command_dict[port.fabric].append(f'member pwwn {wwpn_colonizer(port.wwpn)}')
    return dict(alias_command_dict)


def create_zone_command_dict(zone_dict):
    zone_command_dict = defaultdict(list)
    for fabric, zone_list in zone_dict.items():
       for zone in zone_list:
            if san_vendor == 'Brocade':
                principal_member_list = []
                peer_member_list = []
                for member in zone.member_list:
                    if member.tag == 'target':
                        principal_member_list.append(member)
                    elif member.tag == 'init':
                        peer_member_list.append(member)
                members = ";".join(str(member) for member in zone.member_list)
                principal_members = ";".join(str(member) for member in principal_member_list)
                peer_members = ";".join(str(member) for member in peer_member_list)
                if zone.zone_type == 'smart_peer':
                    zone_command_dict[fabric].append(f'zonecreate --peerzone "{zone.name}", -principal "{principal_members}" -members "{peer_members}"')
                else:
                    zone_command_dict[fabric].append(f'zonecreate "{zone.name}", "{members}"')
            elif san_vendor == 'Cisco':
                zone_command_dict[fabric].append(f'zone name {zone.name} vsan {zone.fabric.vsan}')
                for member in zone.member_list:
                    if zone.zone_type == 'smart_peer':
                        zone_command_dict[fabric].append(f'member {alias_type} {member} {member.tag}')
                    else:
                        zone_command_dict[fabric].append(f'member {alias_type} {member}')
    return dict(zone_command_dict)


def create_zoneset_command_dict(zone_dict):
    zoneset_command_dict = defaultdict(list)
    for fabric, zone_list in zone_dict.items():
        if san_vendor == 'Brocade':
            members = ";".join(str(member) for member in zone_list)
            zoneset_command = f'cfgadd "{fabric.active_zoneset_config}", "{members}"'
            zoneset_command_dict[fabric].append(zoneset_command)
            zoneset_command_dict[fabric].append('cfgsave')
            zoneset_command_dict[fabric].append(f'cfgenable "{fabric.name}"')
        elif san_vendor == 'Cisco':
            zoneset_command_dict[fabric].append(f'zoneset name {fabric.active_zoneset_config} vsan {fabric.vsan}')
            for zone in zone_list:
                zoneset_command_dict[fabric].append(f'member {zone}')
    return zoneset_command_dict


def write_to_file(alias_command_dict, zone_command_dict, zoneset_command_dict):
    for fabric, alias_commands in alias_command_dict.items():
        print(f'Writing alias commands for {customer_name} {fabric}')
        with open(os.path.join(customer_path,config.san_output, f'{customer_name}_{fabric.name.lower()}_zoning_commands.txt'), mode='wt', encoding='utf-8') as script_file:
            script_file.write(f'### ALIAS COMMANDS FOR {fabric.name.upper()}')
            for command in alias_commands:
                script_file.write('\n' + command)
    for fabric, zone_commands in zone_command_dict.items():
        print(f'Writing zone commands for {customer_name} {fabric}')
        with open(os.path.join(customer_path,config.san_output, f'{customer_name}_{fabric.name.lower()}_zoning_commands.txt'), mode='a', encoding='utf-8') as script_file:
            script_file.write(f'\n\n### ZONE COMMANDS FOR {fabric.name.upper()}')
            for command in zone_commands:
                script_file.write('\n' + command)
    for fabric, zoneset_commands in zoneset_command_dict.items():
        print(f'Writing {zoneset_config} commands for {customer_name} {fabric}')
        with open(os.path.join(customer_path,config.san_output, f'{customer_name}_{fabric.name.lower()}_zoning_commands.txt'), mode='a', encoding='utf-8') as script_file:
            script_file.write(f'\n\n### {zoneset_config.upper()} COMMANDS FOR {fabric.name.upper()}')
            for command in zoneset_commands:
                script_file.write('\n' + command)
            for command in san_cheatsheet:
                script_file.write('\n' + command)


if __name__ == '__main__':
    main()