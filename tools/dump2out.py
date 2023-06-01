dump = r"c:\Users\mirandaa\Downloads\LX1 Dump-Out\LX1 Dump-Out\Trim-dump- 5 ppm.csv"
import pandas as pd
import numpy as np


def to_lister(lines):
    for line in lines:
        yield line.strip().split(',')

# Read the file content
with open(dump, "r") as file:
    lines = file.readlines()

header_data = {}

second_section = []
# Process the lines
for line in lines:
    # Skip empty lines
    if not line.strip():
        continue

    # Split the line based on ',' into parts
    parts = line.strip().split(',')

    # Check if the first part has ':'
    if ":" in parts[0].strip():
        parts = line.strip().split(":")
        k = parts[0].strip()
        v = parts[1].strip().strip(",").strip()
        header_data[k] = v

    else:
        second_section.append(line)


# Process the lines
second_section_data = []
for line in second_section:
    # Skip empty lines
    if not line.strip():
        continue

    # Split the line based on '\t' into cells
    cells = line.strip().split(',')

    # Add the cells to the second_section_data list
    second_section_data.append(cells)

# Convert the second_section_data into a DataFrame
df = pd.DataFrame(second_section_data[1:])

headers = second_section_data[0]
new_column_names = []
for idx,name in enumerate(headers):
    if name.strip():
        new_column_names.append(name)
    else:
        new_column_names.append(idx)

# fixed columns
new_column_names[0]='dash'
new_column_names[1]='empty'
new_column_names[2]='mass'
new_column_names[3]='mol'


df.rename(columns=dict(zip(df.columns, new_column_names)), inplace=True)

for column in df.columns:
    try:
        pd.to_numeric(df[column])
        df[column] = pd.to_numeric(df[column])
    except ValueError:
        pass


flag_columns = df.columns[len(headers):]
dirty_flag_df = df[flag_columns]
flag_df = pd.melt(dirty_flag_df.reset_index(), id_vars='index', value_name='flag')
flag_df['flag'].replace('', np.nan, inplace=True)
flag_df = flag_df[flag_df['flag'].notna()] # column 'variable' is the unmelted column name

molecules_df = df.iloc[:,:4]
molecules_df = molecules_df.reset_index()
molecules_df.loc[molecules_df.mass == ' ','index'] = None
molecules_df['index'].fillna(method='ffill', inplace=True)
molecules_df.set_index('index', inplace=True)

print("First Section:")
# print(header_data)
# Print the DataFrame
print("Second Section DataFrame:")
print(df)


