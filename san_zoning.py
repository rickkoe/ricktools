from collections import defaultdict
from statistics import mode
import sys
import pandas as pd
import warnings
import os
import shutil
from openpyxl import load_workbook, Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import importlib
# Import custom functions
from my_mods.general import iterate_dict, iterate_list, clear
from my_mods.san import wwpn_colonizer
from my_mods.san_cheatsheet import brocade_cheatsheet, cisco_cheatsheet
import config
yes_answers = ['y','yes']

def make_workbook(wb_name):
    workbook_path = os.path.join(customer_path, config.san_input, wb_name)
    wb = Workbook()
    wb.remove(wb.active)
    all_sheets = [
        'fabrics',
        'aliases',
        'zones',
        'config',
        'alias_lookup',
        'zone_lookup',
        'scratchpad'
    ]
    for sheet_name in all_sheets:
        wb.create_sheet(sheet_name)
    wb.save(workbook_path)

def make_customer(customer_path):
    os.makedirs(os.path.join(customer_path,config.ds_input),exist_ok=True)
    os.makedirs(os.path.join(customer_path,config.ds_output),exist_ok=True)
    os.makedirs(os.path.join(customer_path,config.fs_input),exist_ok=True)
    os.makedirs(os.path.join(customer_path,config.fs_output),exist_ok=True)
    os.makedirs(os.path.join(customer_path,config.san_input),exist_ok=True)
    os.makedirs(os.path.join(customer_path,config.san_output),exist_ok=True)
    # make_workbook(config.zoning_workbook)


# Global Variables
clear()
if len(sys.argv) == 2:
    # If an argument exists, the first argument is customer name
    customer_name = sys.argv[1]
else:
    customer_name = input('Enter customer name: ')
customer_path = os.path.join(config.customer_path, customer_name)
make_customer(customer_path)
warnings.simplefilter(action='ignore', category=UserWarning)
workbook = os.path.join(customer_path, config.san_input, f'{customer_name}_{config.zoning_workbook}')
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
df_zone_lookup = pd.read_excel(workbook, sheet_name='zone_lookup')
df_config = table_to_df('config')
df_config.set_index("parameter", inplace = True)  # allows the column "parameter" to be index

# Set config parameters
san_vendor = df_config.loc['san_vendor', 'setting']
zone_ratio = df_config.loc['zone_ratio', 'setting']
filename = df_config.loc['filename', 'setting']
cisco_zoning_mode = df_config.loc['cisco_zoning_mode', 'setting']
if san_vendor == 'Brocade':
    zoneset_config = 'zone config'
    san_cheatsheet = brocade_cheatsheet
elif san_vendor == 'Cisco':
    zoneset_config = 'zoneset'
    san_cheatsheet = cisco_cheatsheet
    alias_type = df_config.loc['cisco_alias', 'setting']

# Set Classes
class Fabric:
    def __init__(self, name, active_zoneset_config, exists, vsan='None'):
        self.name = name
        self.active_zoneset_config = active_zoneset_config
        self.vsan = vsan
        self.exists = exists
    def __str__(self):
        return self.name


class Port:
    def __init__(self, alias, wwpn, tag, fabric, exists):
        self.alias = alias
        self.wwpn = wwpn
        self.tag = tag
        self.fabric = fabric
        self.exists = exists
    def __str__(self):
        return self.alias


class Zone:
    def __init__(self, name, fabric, zone_type, member_list, exists=False):
        self.name = name
        self.fabric = fabric
        self.zone_type = zone_type
        self.member_list = member_list
        self.exists = exists
    def __str__(self):
        return self.name


class Host:
    def __init__(self, name, wwpns, storage):
        self.name = name
        self.wwpns = wwpns
        self.storage = storage
    def __str__(self):
        return self.name


def main():
    fabric_dict = create_fabric_dict()
    port_dict = create_port_dict(fabric_dict)
    host_list = create_host_list(fabric_dict)
    zone_dict = create_zone_dict(fabric_dict, port_dict)
    alias_command_dict = create_alias_command_dict(port_dict)
    zone_command_dict = create_zone_command_dict(zone_dict)
    zoneset_command_dict = create_zoneset_command_dict(zone_dict)
    mkhost_command_dict = create_mkhost_command_dict(host_list)
    write_to_file(alias_command_dict, zone_command_dict, zoneset_command_dict, mkhost_command_dict)
    # add_to_zones()
    df_hosts = table_to_df('hosts')
    for index, row in df_hosts.iterrows():
        host_qty = row['host_qty']
        volume_qty = row['volume_qty']
        host_name = row['host_name']
        volume_name = row['volume_name']
        for i in range(host_qty):
            print(fs_map(i, host_name, volume_name, volume_qty, host_qty))


def fs_map(group, host_name, volume_name, volume_qty, host_qty ):
    group += 1
    volumes_per_group = volume_qty/host_qty
    range_list = []
    starting_volume = 0
    for i in range(host_qty):
        starting_volume = i * volumes_per_group
        ending_volume = starting_volume + volumes_per_group - 1
        range_list.append((int(starting_volume), int(ending_volume)))
    start = range_list[group-1][0]
    end = range_list[group-1][1]
    return f'for ((i={start};i<={end};i++)); do svctask mkvdiskhostmap -force -host {host_name}_{group:02d} {volume_name}_$i; done'



def fs_mkhost(host_obj):
    """
    Pass in a host object.  Returns a FlashSystem
    CLI command to make the host definition
    """
    wwpn_list = []
    for wwpn in host_obj.wwpns:
        wwpn_list.append(wwpn_colonizer(wwpn,''))
    wwpns = ':'.join(wwpn_list)
    host_command = f'svctask mkhost -fcwwpn {wwpns} -force -name {host_obj.name} -protocol scsi -type generic'
    return host_command


def create_mkhost_command_dict(host_list):
    mkhost_command_dict = defaultdict(list)
    for host in host_list:
        host_command = fs_mkhost(host)
        mkhost_command_dict[host.storage].append(host_command)
    return mkhost_command_dict
    

def make_customer():
    if os.path.exists(customer_path):
        print('Existing customer found')
    else:
        print('Customer folder not found.  Creating folders now.')
        os.makedirs(customer_path)


def create_fabric_dict():
    fabric_dict = {}
    for index, row in df_fabrics.iterrows():
        active_zoneset_config = row['active zoneset/config']
        name = row['name']
        vsan = str(row['vsan'])
        if row['exists_new'] == 'exists':
            exists = True
        else:
            exists = False
        
        fabric_dict[name] = Fabric(name, active_zoneset_config, exists, vsan)
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
        if row['exists_new'] == 'exists':
            exists = True
        else:
            exists = False
        this_port = Port(name, wwpn, tag, fabric, exists)
        port_list.append(this_port)
    for port in port_list:
        port_dict[port.fabric].append(port)
    return dict(port_dict)


def create_host_list(fabric_dict):
    host_list = []
    for index, row in df_aliases.iterrows():
        wwpn_list =[]
        if row['fs_host_name']:
            name = row['fs_host_name']
            if row['fs_name']:
                fs = row['fs_name']
            else:
                fs = 'fs_not_defined'
            if row['wwpn1']:
                wwpn_list.append(row['wwpn1'])
            if row['wwpn2']:
                wwpn_list.append(row['wwpn2'])


            if any(host.name == name for host in host_list):
                for idx, host in enumerate(host_list):
                    if host.name == name:
                        host.wwpns.extend(wwpn_list)
            else:
                host_list.append(Host(name, wwpn_list, fs))
    return host_list

def add_to_zones():
    test_file = os.path.join(customer_path, config.san_input, f'test_file.xlsx')
    wb_test = load_workbook(test_file)
    ws_test = wb_test.active
    for index, row in df_aliases.iterrows():
        if row['add_to_zone']:
            # Check to see if the zone already contains the member
            if not df_zones[row['add_to_zone']].eq(row['name']).any():
    
                # df_zones.append({row['add_to_zone']:row['name']}, ignore_index=True)
                zone_row = df_zones[row['add_to_zone']].last_valid_index() + 1
                df_zones.loc[zone_row, row['add_to_zone']] = row['name']
    rows =dataframe_to_rows(df_zones, index=False)
    for r_idx, row in enumerate(rows, 1):
        for c_idx, value in enumerate(row, 1):
            ws_test.cell(row=r_idx, column=c_idx, value=value)
  

    wb_test.save(test_file)


def create_zone_dict(fabric_dict, port_dict):
    zone_list = []
    zone_dict = defaultdict(list)
    member_columns = [col for col in df_zone_lookup.columns if 'member' in col]
    for index, row in df_zone_lookup.iterrows():
        member_list = []
        zone_type = row['zone_type']
        name = row['name']
        fabric_name = row['fabric']
        if row['exists_new'] == 'exists':
            exists = True
        else:
            exists = False
        if row['create_zone']:
            fabric = fabric_dict[fabric_name]
            for port in port_dict[fabric]:
                for col in member_columns:
                    if port.alias == row[col]:
                        if zone_type == 'smart_peer' and port.tag == None:
                            print(f'WARNING:  Alias {port.alias} is missing a tag for Smart/Peer Zoning')
                        member_list.append(port)
            member_list.sort(key=lambda x: x.tag, reverse=True)
            # Create non-smart zones
            if zone_type == 'standard':
                if zone_ratio == "one-to-one":
                    for member in member_list:
                        if member.tag == 'target':
                            target_member = member.alias
                            for sub_member in member_list:
                                if sub_member.tag == 'init':
                                    name = f'{sub_member.alias}_{target_member}'
                                    this_zone = Zone(name, fabric, zone_type, [sub_member,target_member], exists)
                                    zone_list.append(this_zone)
                if zone_ratio == "one-to-many":
                    target_list = []
                    init_list = []
                    for member in member_list:
                        if member.tag == 'target':
                            target_list.append(member)
                        if member.tag == 'init':
                            init_list.append(member)
                    for init in init_list:
                        zone_name = f'{init.alias}_{name}'
                        zone_member_list = target_list
                        print(f'{zone_name}')
                        # zone_member_list.append(init)
                        this_zone = Zone(zone_name, fabric, zone_type, zone_member_list, exists)
                        zone_list.append(this_zone)
                    
            else:
                this_zone = Zone(name, fabric, zone_type, member_list, exists)
                zone_list.append(this_zone)
    for zone in zone_list:
        zone_dict[zone.fabric].append(zone)
    return dict(zone_dict)


def create_alias_command_dict(port_dict):
    alias_command_dict = defaultdict(list)
    for fabric, port_list in port_dict.items():
        for port in port_list:
            if port.exists == False:
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
                if principal_member_list:
                    principal_members = ";".join(str(member) for member in principal_member_list)
                    principal_members_command = f'-principal "{principal_members}" '
                else:
                    principal_members_command = ''
                if peer_member_list:
                    peer_members = ";".join(str(member) for member in peer_member_list)
                    peer_members_command = f'-members "{peer_members}"'
                else:
                    peer_members_command = ''
                if zone.zone_type == 'smart_peer':
                    if zone.exists:
                        zone_command_dict[fabric].append(f'zoneadd --peerzone {zone.name} {principal_members_command}{peer_members_command}')
                    else:
                        zone_command_dict[fabric].append(f'zonecreate --peerzone {zone.name} {principal_members_command}{peer_members_command}')

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
            if fabric.exists:
                zoneset_command = f'cfgadd "{fabric.active_zoneset_config}", "{members}"'
            else:
                zoneset_command = f'cfgcreate "{fabric.active_zoneset_config}", "{members}"'
            zoneset_command_dict[fabric].append(zoneset_command)
            zoneset_command_dict[fabric].append(f'cfgenable "{fabric.active_zoneset_config}"')
        elif san_vendor == 'Cisco':
            firstpass = True
            for zone in zone_list:
                if zone.exists == False:
                    if firstpass == True:
                        zoneset_command_dict[fabric].append(f'zoneset name {fabric.active_zoneset_config} vsan {fabric.vsan}')
                        firstpass = False
                    zoneset_command_dict[fabric].append(f'member {zone}')
            zoneset_command_dict[fabric].append(f'zoneset activate name {fabric.active_zoneset_config} vsan {fabric.vsan}')
            if cisco_zoning_mode == 'enhanced':
                zoneset_command_dict[fabric].append(f'zone commit vsan {fabric.vsan}')
            zoneset_command_dict[fabric].append(f'copy run start')
    return zoneset_command_dict


def write_to_file(alias_command_dict, zone_command_dict, zoneset_command_dict, mkhost_command_dict):
    file_open = False
    for fabric, alias_commands in alias_command_dict.items():
        print(f'Writing alias commands for {customer_name} {fabric}')
        with open(os.path.join(customer_path,config.san_output, f'{customer_name}_{fabric.name}_{filename}.txt'), mode='wt', encoding='utf-8') as script_file:
            script_file.write(f'### ALIAS COMMANDS FOR {fabric.name.upper()}')
            if san_vendor == 'Cisco':
                script_file.write('\nconfig\ndevice-alias database')
            for command in alias_commands:
                script_file.write('\n' + command)
            if san_vendor == 'Cisco':
                script_file.write('\ndevice-alias commit')
            file_open = True
    for fabric, zone_commands in zone_command_dict.items():
        print(f'Writing zone commands for {customer_name} {fabric}')
        if file_open:
            mode = 'a'
        else:
            mode = 'wt'
        with open(os.path.join(customer_path,config.san_output, f'{customer_name}_{fabric.name}_{filename}.txt'), mode=mode, encoding='utf-8') as script_file:
            script_file.write(f'\n\n### ZONE COMMANDS FOR {fabric.name.upper()}')
            for command in zone_commands:
                script_file.write('\n' + command)
    for fabric, zoneset_commands in zoneset_command_dict.items():
        print(f'Writing {zoneset_config} commands for {customer_name} {fabric}')
        with open(os.path.join(customer_path,config.san_output, f'{customer_name}_{fabric.name}_{filename}.txt'), mode='a', encoding='utf-8') as script_file:
            script_file.write(f'\n\n### {zoneset_config.upper()} COMMANDS FOR {fabric.name.upper()}')
            for command in zoneset_commands:
                script_file.write('\n' + command)
            for command in san_cheatsheet:
                script_file.write('\n' + command)
    for fs, host_commands in mkhost_command_dict.items():
        print(f'Writing FlashSystem host commands for {customer_name} {fs}')
        with open(os.path.join(customer_path,config.san_output, f'{customer_name}_STORAGE_{fs}_mkhost_commands.txt'), mode='a', encoding='utf-8') as script_file:
            script_file.write(f'### MKHOST COMMANDS FOR {fs.upper()}')
            for command in host_commands:
                script_file.write('\n' + command)


if __name__ == '__main__':
    main()