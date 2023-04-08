from my_mods.general import iterate_dict, iterate_list, hex2dec, dec2hex, is_even
import pandas as pd
import os
from openpyxl import load_workbook

file_name = 'ABB Primary DS8950 Disk Config.Final'
file = file_name + '.xlsx'
serial_number = '75LRR50'
# DR serial_number = '75LPM40'
capacity_dict = {
    'M1': '1113',
    'M3': '3339',
    'M9': '10017',
    'M27': '32760',
    'M54': '65520',
    'M223': '262668'
    }


def storage_image(serial_number):
    return f'IBM.2107-{serial_number[:-1]}1'


storage_image_id = storage_image(serial_number)

def main():
    mklcu_list = [f'### CREATE CKD LCUS ON {storage_image_id}']
    mkckdvol_list = [f'### CREATE CKD VOLUMES ON {storage_image_id}']
    mkaliasvol_list = [f'### CREATE PAVS ON {storage_image_id}']
    df = pd.read_excel(file, keep_default_na=False)
    for ind in df.index:
        lcu = df['LCU'][ind]
        ssid = df['SSID'][ind]
        complete_range = df['CKDVOL  Complete Range'][ind]
        qty_base = int(df['VOLS'][ind]) + int(df['VOLS.1'][ind]) + int(df['VOLS.2'][ind]) + int(df['VOLS.3'][ind])
        qty_alias = int(df['ALIAS VOL'][ind])
        alias_tup = alias_per_base(qty_base, qty_alias)

        mklcu_list.append(mklcu(lcu, ssid))
        try:
            mkckdvol_list.append(mkckdvol(find_pool(lcu),capacity_dict[df['MOD TYPE'][ind]],'ckdvol_#h', df['ADDRESS RANGE'][ind]))
        except KeyError as ke:
            pass
        try:
            mkckdvol_list.append(mkckdvol(find_pool(lcu),capacity_dict[df['MOD TYPE.1'][ind]],'ckdvol_#h', df['ADDRESS RANGE.1'][ind]))
        except KeyError as ke:
            pass
        try:
            mkckdvol_list.append(mkckdvol(find_pool(lcu),capacity_dict[df['MOD TYPE.2'][ind]],'ckdvol_#h', df['ADDRESS RANGE.2'][ind]))
        except KeyError as ke:
            pass
        try:
            mkckdvol_list.append(mkckdvol(find_pool(lcu),capacity_dict[df['MOD TYPE.3'][ind]],'ckdvol_#h', df['ADDRESS RANGE.3'][ind]))
        except KeyError as ke:
            pass
        base_start = complete_range.split('-')[0]
        mkaliasvol_list.append(mkaliasvol(base_start, 'decrement', lcu + 'FF', qty_alias))

    file_dict = {
        'mklcu': mklcu_list, 
        'mkckdvol': mkckdvol_list,
        'mkaliasvol': mkaliasvol_list
        }

    for k, v in file_dict.items():
        with open((serial_number + '-' + k + '.txt'), mode='wt', encoding='utf-8') as script_file:
            list_to_file(v, script_file)
    
    
    with open((file_name + '.txt'), mode='wt', encoding='utf-8') as script_file:
        for this_list in ([mklcu_list, mkckdvol_list, mkaliasvol_list]):
            list_to_file(this_list, script_file)



def find_pool(lcu):
    if is_even(hex2dec(lcu)):
        return 'P0'
    else:
        return 'P1'


def alias_per_base (qty_base, qty_alias):
    if qty_base == qty_alias:
        return (1, 0)
    elif qty_base > qty_alias:
        return (0, qty_alias)
    elif qty_base < qty_alias:
        all_base_aliases = qty_alias//qty_base
        some_base_aliases = qty_alias - (qty_base * all_base_aliases)
        return (all_base_aliases, some_base_aliases)


def list_to_file(this_list, this_file):
    for line in this_list:
        this_file.write(line + '\n')



def mklcu(lcu, ssid):
    return f'mklcu -dev {storage_image_id} -qty 1 -id {lcu} -ss {ssid}'


def mkckdvol(pool, capacity, vol_name_prefix, vol_range, sam='ese', eam='rotateexts'):
    return f'mkckdvol -dev {storage_image_id} -extpool {pool} -sam {sam} -eam {eam} -cap {capacity} -name {vol_name_prefix} {vol_range}'


def mkaliasvol(base_vol_range, order, start_vol, qty=1):
    return f'mkaliasvol -dev {storage_image_id} -base {base_vol_range} -order {order} -qty {qty} {start_vol}'


if __name__ ==  "__main__":
    main()
