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
from my_mods.general import iterate_dict, iterate_list, clear, hex2dec, dec2hex, dec2hex2x, is_even
from my_mods.san import wwpn_colonizer
from my_mods.san_cheatsheet import brocade_cheatsheet, cisco_cheatsheet
import config
yes_answers = ['y','yes']

# Global Variables
clear()
if len(sys.argv) == 2:
    # If an argument exists, the first argument is customer name
    customer_name = sys.argv[1]
else:
    customer_name = input('Enter customer name: ')
customer_path = os.path.join(config.customer_path, customer_name)
warnings.simplefilter(action='ignore', category=UserWarning)
workbook = os.path.join(customer_path, config.fs_input, f'wni_migration.xlsx')
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
df_migrate = table_to_df('migrate')


def main():
    targetvol_list = []
    changevol_list = []
    drvol_list = []
    flashvol_list = []
    fcconsistgrp_list = []
    fcmap_list = []
    mkrcrelationship_list = []
    masterchange_list = []
    auxchange_list = []
    rcconsistgrp_list = []
    for index,row in df_migrate.iterrows():
        host = row['host']
        capacity = row['capacity']
        start = row['start']
        qty = row['qty']
        cg_group = row['cg_group']
        cv_prefix = row['cv_prefix']
        flash_prefix = row['flash_prefix']
        node = row['starting_node']
        thin = row['thin']
        print_row = row['print']
        end = start + qty - 1
        aux_cluster_id = '00000204A00047FC'
        if print_row:
            targetvol_list.append(mkvdisk(host, start ,end, capacity, thin))
            flashvol_list.append(mkvdisk(host, start ,end, capacity, False, flash_prefix))
            drvol_list.append(mkvdisk(host, start, end, capacity, True, flash_prefix))
            changevol_list.append(mkvdisk(host, start ,end, capacity, True, cv_prefix))
            fcconsistgrp_list.append(mkfcconsistgrp(host))
            fcmap_list.append(mkfcmap(host,start,end,flash_prefix))
            fcmap_list.append(f'startfcconsistgrp -prep {host}_mig')
            mkrcrelationship_list.append(mkrcrelationship(host,start,end,aux_cluster_id,flash_prefix))
            masterchange_list.append(masterchange(host,start,end,cv_prefix))
            auxchange_list.append(auxchange(host,start,end,cv_prefix))
            rcconsistgrp_list.extend(rcconsistgrp(start, end, host, aux_cluster_id))

    print('### CHASKA-P10-FS5200')
    iterate_list(targetvol_list)
    iterate_list(changevol_list)
    print(f'\n\n### WNI-COLO-iSeries-v5000')
    iterate_list(flashvol_list)
    iterate_list(fcconsistgrp_list)
    iterate_list(fcmap_list)
    iterate_list(mkrcrelationship_list)
    iterate_list(masterchange_list)
    iterate_list(auxchange_list)
    iterate_list(rcconsistgrp_list)
    print(f'\n\b### WNI-Boulder-iSeries-v5000')
    iterate_list(drvol_list)


def mkvdisk(host, start, end, capacity, thin, prefix='', suffix=''):
    if thin:
        command = f'for ((i={start};i<={end};i++)); do svctask mkvdisk -autoexpand -grainsize 256 -rsize 2% -warning 100% -mdiskgrp 0 -name {prefix}{host}_$i{suffix} -size {capacity} -unit gb; done'
    else:
        command = f'for ((i={start};i<={end};i++)); do svctask mkvdisk -mdiskgrp 0 -name {prefix}{host}_$i{suffix} -size {capacity} -unit gb; done'
    return command

def mkfcconsistgrp(host):
    return f'svctask mkfcconsistgrp -name {host}_mig'


def mkfcmap(host, start, end, prefix='', suffix=''):
    return f'for ((i={start};i<={end};i++)); do svctask mkfcmap -cleanrate 130 -consistgrp {host}_mig -copyrate 130 -incremental -source {host}_$i -target {prefix}{host}_$i; done'


def mkrcrelationship(host, start, end, aux_cluster_id, prefix):
    return f'for ((i={start};i<={end};i++)); do svctask mkrcrelationship -aux {host}_$i -cluster {aux_cluster_id} -global -master {prefix}{host}_$i -name {host}$i; done'


def masterchange(host, start, end, prefix):
    return f'for ((i={start};i<={end};i++)); do svctask chrcrelationship -masterchange {prefix}{host}_$i {host}$i; done'

def auxchange(host, start, end, prefix):
    return f'for ((i={start};i<={end};i++)); do svctask chrcrelationship -auxchange {prefix}{host}_$i {host}$i; done'

def rcconsistgrp(start,end, host,aux_cluster_id):
    consistency_group = f'MIG_{host}'
    command_list = []
    command_list.append(f'mkrcconsistgrp -cluster {aux_cluster_id} -name {consistency_group}')
    command_list.append(f'for ((i={start};i<={end};i++)); do svctask chrcrelationship -consistgrp {consistency_group} {host}$i; done')
    command_list.append(f'chrcconsistgrp -cyclingmode multi -global {consistency_group}')
    command_list.append(f'chrcconsistgrp -cycleperiodseconds 300 {consistency_group}')
    command_list.append(f'startrcconsistgrp {consistency_group}')
    return command_list

if __name__ == '__main__':
    main()