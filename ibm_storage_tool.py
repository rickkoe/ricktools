from collections import defaultdict
from statistics import mode
import sys
import pandas as pd
import warnings
import os
import math
import shutil
from openpyxl import load_workbook, Workbook
import importlib
# Import custom functions
from my_mods.general import iterate_dict, iterate_list, clear, hex2dec, dec2hex
from my_mods.san import wwpn_colonizer
from my_mods.san_cheatsheet import brocade_cheatsheet, cisco_cheatsheet
import json

with open('config.json') as f:
  config = json.load(f)

# Global Variables
clear()
if len(sys.argv) == 2:
    # If an argument exists, the first argument is customer name
    customer_name = sys.argv[1]
else:
    customer_name = input('Enter customer name: ')
try:
    customer_path = config[customer_name]['path']
    customer_workbook = config[customer_name]['workbook']
except KeyError:
    print("Customer has not been setup correctly in config.json\nQuitting...")
    exit()

warnings.simplefilter(action='ignore', category=UserWarning)
site = input("Enter Site (Chaska,Lexington):  ")
if site == 'Chaska' or site == 'Lexington':
    print('Configuring ' + site + ' Storage...')
else:
    print('Invalid site')
    exit()

wb = load_workbook(os.path.join(customer_path,customer_workbook), data_only=True)
# Create Objects in Global Namespace
class Volume:
    def __init__(self, name, size, thin=False):
        self.name = name
        self.size = size
        self.thin = thin

    def __str__(self):
        return self.name

class VolumeRange:
    def __init__(self, lpar, lun_qty, lun_size, storage_sys, groups=1):
        self.lpar = lpar
        self.qty = lun_qty
        self.size = lun_size
        self.storage_sys = storage_sys
        self.groups = groups

    def __str__(self):
        return self.lpar

class Storage:
    def __init__(self, name, nickname, serial, cluster_id):
        self.name = name
        self.nickname = nickname
        self.serial = serial
        self.cluster_id = cluster_id
    def __str__(self):
        return self.name

class Host:
    def __init__(self, name, wwpns):
        self.name = name
        self.wwpns = wwpns
    def __str__(self):
        return self.name

class Port:
    def __init__(self, alias, wwpn, tag, fabric, vsan, zoned_to):
        self.alias = alias
        self.wwpn = wwpn
        self.tag = tag
        self.fabric = fabric
        self.vsan = vsan
        self.zoned_to = zoned_to
    def __str__(self):
        return self.alias

def main():
    if site == 'Lexington':
        source_storage_image = '75KBM71'
        target_storage_image = '75MGF61'
    elif site == 'Chaska':
        source_storage_image = '75KHY01'
        target_storage_image = '75MFK41'
    df_volumes = table_to_df(f'{source_storage_image}-StorageVolumes')
    df_hosts = table_to_df(f'{source_storage_image}-Hosts')

    lss_dict = defaultdict(dict)
    for index, row in df_volumes.iterrows():
        volume_number = row['ID']
        lss = row['ID'][:2]
        size = row['Capacity (GiB)']
        name = row['Name'].strip(f'_{row["ID"]}')

        if size == 65.72:
            ibmi_size = 'A04'
        elif size == 131.44:
            ibmi_size = 'A06'
        else:
            ibmi_size = size
        if lss in lss_dict.keys():
            lss_dict[lss]['qty'] += 1
            if ibmi_size != lss_dict[lss]['size']:
                lss_dict[lss]['sizesmatch'] = False
            if hex2dec(volume_number) < hex2dec(lss_dict[lss]['start']):
                lss_dict[lss]['start'] = volume_number
            elif hex2dec(volume_number) > hex2dec(lss_dict[lss]['end']):
                lss_dict[lss]['end'] = volume_number
            if hex2dec(lss_dict[lss]['end']) - hex2dec(lss_dict[lss]['start']) + 1 == lss_dict[lss]['qty']:
                lss_dict[lss]['isconsecutive'] = True
            else:
                lss_dict[lss]['isconsecutive'] = False
            lss_dict[lss]['total_size'] += size
            
        else:
            lss_dict[lss]['qty'] = 1
            lss_dict[lss]['size'] = ibmi_size
            lss_dict[lss]['sizesmatch'] = True
            lss_dict[lss]['name'] = name
            lss_dict[lss]['start'] = volume_number
            lss_dict[lss]['end'] = volume_number
            lss_dict[lss]['isconsecutive'] = False
            lss_dict[lss]['total_size'] = size
    host_list = []
    for index, row in df_hosts.iterrows():
        this_host = Host(row['Name'],row['WWPNs'].split(', '))
        host_list.append(this_host)


    # lss_dict = defaultdict(dict)
    # for k, v in lss_count.items():
    #     lss_dict[k]['qty'] = len(v)
        # print(f'{k}: {len(v)}')

    # for k, v in lss_dict.items():
    #     if 'MGT' in v['name']:
    #         print(mkfbvol(target_storage_image,k,v))

    size_dict = {}
    for k,v in lss_dict.items():
        # print(f"{k},{v['name']},{math.ceil(v['total_size'])},{v['start']}-{v['end']},{v['sizesmatch']}")
        if v['name'] in size_dict.keys():
            size_dict[v['name']] += v['total_size']
        else:
            size_dict[v['name']] = v['total_size']

    # for k,v in size_dict.items():
    #     print(f"{k},{math.ceil(v)}")
    fs_vol_size = 200
    fs_name = 'Lexington Orange FS9500'
    exclude_list = ['PRD02','MGT']
    for lpar, total_size in size_dict.items():
        total_size = total_size * 1.07374
        qty = round_up_to_even(total_size/fs_vol_size)
        this_volrange = VolumeRange(lpar,qty,fs_vol_size,fs_name)
        print(fs_mkvdisk(this_volrange))

    # for host in host_list:
    #     if "MGT" in host.name:
    #         print(ds_mkhost(target_storage_image, host))
    



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

def round_up_to_even(f):
    return math.ceil(f / 2.) * 2

def iseven(num):
    if (int(num) % 2) == 0:
        return True
    else:
        return False

def mkfbvol(storage_image,lss,volume_range):
    if iseven(hex2dec(lss)):
        pool = 'P0'
    else:
        pool = 'P1'
    sam = 'standard'
    size = volume_range['size']
    volrange = volume_range['start'] + '-' + volume_range['end']
    name = volume_range['name']
    return f'mkfbvol -dev IBM.2107-{storage_image} -extpool {pool} -os400 {size} -sam {sam} -eam rotateexts -name {name} {volrange}'

def fs_mkvdisk(volume_range, thin=False, prefix=''):
    name = volume_range.lpar
    new_line = '\n'
    if thin:
        return f'for ((i=0;i<={volume_range.qty - 1};i++)); do svctask mkvdisk -autoexpand -grainsize 256 -rsize 2% -warning 80% -mdiskgrp 0 -name {name}_$i -size {volume_range.size} -unit gb; done'
    else:
        return f'for ((i=0;i<={volume_range.qty - 1};i++)); do svctask mkvdisk -mdiskgrp 0 -name {name}_$i -size {volume_range.size} -unit gb; done'

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

def ds_mkhost(storage_image, host_obj):
    """
    Pass in a host object.  Returns a DS8000
    DCLI command to make the host definition
    """
    wwpn_list = []
    for wwpn in host_obj.wwpns:
        wwpn_list.append(wwpn_colonizer(wwpn,''))
    wwpns = ','.join(wwpn_list)
    host_command = f'mkhost -dev IBM.2107-{storage_image} -type "IBM I AS/400" -hostport {wwpns} {host_obj.name}'
    return host_command




if __name__ == '__main__':
    main()