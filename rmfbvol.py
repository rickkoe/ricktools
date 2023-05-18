import csv
from collections import defaultdict # Used to init dictionary items with list
from my_mods.general import iterate_dict, iterate_list, clear, hex2dec, dec2hex, dec2hex2x, is_even
import os
# from config import storage_image, data_file
filename = 'Chaska_OldBlue_StorageVolumes.csv'
data_file = os.path.join('data','Prime','fs_input', filename)
with open(data_file, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    system_dict = defaultdict(list)
    for row in reader:
        system_name = row['Name'][:-5]
        # Remove Media Preference Names
        system_name = system_name.replace('_mp', '')
        storage_image = row['Storage System']
        if row['Volume Number'] == '':
            volume_number = 0
        else:
            volume_number = int(row['Volume Number'])
        system_dict[system_name].append((row['LSS or LCU'], volume_number))

final_dict = {}
for system, volume_range in system_dict.items():
    range_dict = defaultdict(list)
    for volume_tup in volume_range:
        range_dict[volume_tup[0]].append(volume_tup[1])
    final_dict[system]=dict(range_dict)

for system, range_dict in final_dict.items():
    # print(system)
    range_list = []
    for lss, volume_list in range_dict.items():
        counter = 0
        for volume in sorted(volume_list):
            if counter == 0:
                start = format(volume, '02X')
            else:
                end = format(volume, '02X')
            counter += 1
        range_list.append(lss.upper()+start+'-'+lss.upper()+end)
    # iterate_list(sorted(range_list))
    for vol_range in sorted(range_list):
        print(f'rmfbvol -dev {storage_image} -quiet -force {vol_range}')
