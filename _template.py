from statistics import mode
import pandas as pd
import os
from openpyxl import load_workbook
import importlib
# Import custom functions
from my_mods.general import iterate_dict, iterate_list, clear
from my_mods.san import wwpn_colonizer
# Global Variables
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
df_sheet1 = table_to_df('aliases')


def main():
    command_dict = {}
    port_dict = {}
    for index, row in df_sheet1.iterrows():
        print(row)
                   

if __name__ == '__main__':
    main()