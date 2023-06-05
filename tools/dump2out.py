

import numpy as np
import pandas as pd


def to_lister(lines):
    for line in lines:
        yield line.strip().split(',')

def  parse_dump_file(dump):
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
    
    header_data['headers'] = headers
    return header_data, df

def get_id_info(header_data, df):
    headers = header_data['headers']

    flag_columns = df.columns[len(headers):]
    dirty_flag_df = df[flag_columns]
    flag_df = pd.melt(dirty_flag_df.reset_index(), id_vars='index', value_name='flag')
    flag_df['flag'].replace('', np.nan, inplace=True)
    flag_df = flag_df[flag_df['flag'].notna()] # column 'variable' is the unmelted column name
    flag_df[['var','nominal','mode','molecule']] = flag_df.flag.str.split(":", expand = True)
    flag_df.set_index('index', inplace=True)
    # flag_df = flag_df.drop_duplicates()
    # flag_df = flag_df.sort_values(['var','nominal'])

    molecules_df = df.iloc[:,:4]
    molecules_df = molecules_df.reset_index()
    molecules_df.loc[molecules_df.mass == ' ','index'] = np.nan

    molecules_df['index'].fillna(method='ffill', inplace=True)
    molecules_df.set_index('index', inplace=True)
    molecules_df = molecules_df[molecules_df['mol'] != '%']
    molecules_df[['molecule','error']] = molecules_df['mol'].str.extract(r'\((.*?) ; (.*?)\)')
    molecules_df['error'] = pd.to_numeric(molecules_df['error'])
    molecules_df['abs_err'] = molecules_df['error'].abs()
    molecules_df['min_err'] = molecules_df.groupby('molecule')['abs_err'].transform('min')
    molecules_df['selected'] = molecules_df['min_err'] == molecules_df['abs_err']

    result_df = pd.merge(molecules_df, flag_df, how='left', left_index=True, right_index=True)
    result_df = result_df.drop_duplicates()

    return result_df



def main():
    import pprint
    dump = r"c:\Users\mirandaa\Downloads\LX1 Dump-Out\LX1 Dump-Out\Trim-dump- 5 ppm.csv"
    out = r'c:\Users\mirandaa\Downloads\LX1 Dump-Out\LX1 Dump-Out\Trim-out-5 ppm.csv'
    header_data, df = parse_dump_file(dump)
    result_df = get_id_info(header_data, df)
    print("First Section:")
    pprint.pprint(header_data)
    # Print the DataFrame
    print("Second Section DataFrame:")
    print(df)


if __name__ == '__main__':
    main()

