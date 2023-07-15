import os
import csv
import pandas as pd

# Function to convert file name to sheet name
def convert_to_sheet_name(filename):
    base_name = os.path.basename(filename)
    sheet_name = base_name.split("_")[-1].split(".")[0]
    return sheet_name

# Folder path to search for CSV files
folder_path = "/Users/rickk/Library/CloudStorage/OneDrive-SharedLibraries-evolvingsolutions/UNFI - Documents/General/SAN Health/Mark_Beelman_230626_1001_Boise_SAN_26_June_2023/Mark_Beelman_230626_1001_Boise_SAN_26_June_2023_CSVReports"

# Create a new Excel workbook
excel_file = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')

# Get all CSV files in the folder
csv_files = [file for file in os.listdir(folder_path) if file.endswith(".csv")]

# Import each CSV file into a separate sheet in the Excel workbook
for csv_file in csv_files:
    csv_path = os.path.join(folder_path, csv_file)
    sheet_name = convert_to_sheet_name(csv_file)
    
    # Read CSV file as a DataFrame
    df = pd.read_csv(csv_path)
    
    # Write the DataFrame to a new sheet in the Excel workbook
    df.to_excel(excel_file, sheet_name=sheet_name, index=False)

# Save and close the Excel workbook
excel_file.close()
