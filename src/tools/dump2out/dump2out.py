import numpy as np
import pandas as pd
from pathlib import Path
import argparse


def to_lister(lines):
    for line in lines:
        yield line.strip().split(",")


def suggest_result_file(out_file):
    out_path = Path(out_file)
    result_file = str(
        out_path.with_name(out_path.stem + "_v2" + out_path.suffix)
    )
    return result_file


def parse_dump_file(dump):
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
        parts = line.strip().split(",")

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
        cells = line.strip().split(",")

        # Add the cells to the second_section_data list
        second_section_data.append(cells)

    # Convert the second_section_data into a DataFrame
    df = pd.DataFrame(second_section_data[1:])

    headers = second_section_data[0]
    new_column_names = []
    for idx, name in enumerate(headers):
        if name.strip():
            new_column_names.append(name)
        else:
            new_column_names.append(idx)

    # fixed columns
    new_column_names[0] = "dash"
    new_column_names[1] = "empty"
    new_column_names[2] = "mass"
    new_column_names[3] = "mol"

    df.rename(columns=dict(zip(df.columns, new_column_names)), inplace=True)

    for column in df.columns:
        try:
            pd.to_numeric(df[column])
            df[column] = pd.to_numeric(df[column])
        except ValueError:
            pass

    header_data["headers"] = headers
    return header_data, df


def get_id_info(header_data, df):
    headers = header_data["headers"]

    flag_columns = df.columns[len(headers) :]
    dirty_flag_df = df[flag_columns]
    flag_df = pd.melt(
        dirty_flag_df.reset_index(), id_vars="index", value_name="flag"
    )
    flag_df["flag"].replace("", np.nan, inplace=True)
    flag_df = flag_df[
        flag_df["flag"].notna()
    ]  # column 'variable' is the unmelted column name
    flag_df[["var", "nominal", "mode", "molecule"]] = flag_df.flag.str.split(
        ":", expand=True
    )
    flag_df.set_index("index", inplace=True)
    # flag_df = flag_df.drop_duplicates()
    # flag_df = flag_df.sort_values(['var','nominal'])

    molecules_df = df.iloc[:, :4]
    molecules_df = molecules_df.reset_index()
    molecules_df.loc[molecules_df.mass == " ", "index"] = np.nan

    molecules_df["index"].fillna(method="ffill", inplace=True)
    molecules_df.set_index("index", inplace=True)
    molecules_df = molecules_df[molecules_df["mol"] != "%"]
    molecules_df[["molecule", "error"]] = molecules_df["mol"].str.extract(
        r"\((.*?) ; (.*?)\)"
    )
    molecules_df["error"] = pd.to_numeric(molecules_df["error"])
    molecules_df["abs_err"] = molecules_df["error"].abs()
    molecules_df["min_err"] = molecules_df.groupby("molecule")[
        "abs_err"
    ].transform("min")
    molecules_df["selected"] = (
        molecules_df["min_err"] == molecules_df["abs_err"]
    )

    result_df = pd.merge(
        molecules_df, flag_df, how="left", left_index=True, right_index=True
    )
    result_df = result_df.drop_duplicates()

    return result_df


def parse_out_file(out):
    # Read the file content
    with open(out, "r") as file:
        lines = file.readlines()

    df = pd.DataFrame((line.split(",") for line in lines))
    df["row_no"] = df.index

    col_names = []
    for idx, e in enumerate(df.iloc[0].to_list()):
        if e:
            col_names.append(e.strip())
        else:
            col_names.append(idx)

    df.columns = col_names

    df = df.drop(0)
    df["section"] = df["EC"].where(df["PRM"] == "###")
    df["section"] = df["section"].str.strip()
    df["section"] = df["section"].ffill()

    df = df[df["CLASS"].notna()]

    return df


def replace_results_with_min_abs_error(out, dump, result_file):
    """
    replace the results from the out file with values from the dump file,
    where the eabsolute error is smaller,

    out: out csv from
    dunp: dum.csv file that contains the results from the out file
    result_file: path to the updated outfile, if falsy no file is created
    """
    outs_mass_row = 0
    outs_elemental_comp_row = 1
    outs_error_row = 9
    out_title_prefix = "QS:"

    header_data, df = parse_dump_file(dump)
    result_df = get_id_info(header_data, df)
    result_df = result_df[result_df.selected]

    with open(out, "r") as file:
        lines = file.readlines()

    lines_out = []
    header = lines[0].split(",")

    lines_out.append(lines[0])

    for line in lines[1:]:
        if not line.strip():  # nothing there
            lines_out.append(line)
            continue
        if line.startswith("###"):  # nothing to do
            lines_out.append(line)
            continue

        row = line.split(",")
        Elemental_comp = row[outs_elemental_comp_row]
        Elemental_comp = Elemental_comp.strip()
        error = float(row[outs_error_row])
        error = round(error, 2)

        result = (
            result_df[result_df.molecule_x == Elemental_comp]
            .reset_index()
            .iloc[0]
        )
        e_1 = round(float(result.error), 2)

        if error == e_1:  # same error no replacement
            lines_out.append(line)
            continue

        replacement = df.iloc[int(result["index"])]

        for idx, title in enumerate(header):
            if title.strip(out_title_prefix) in replacement.index:
                row[idx] = str(replacement[title.strip(out_title_prefix)])

        row[outs_mass_row] = replacement.mass
        row[outs_error_row] = str(result.error)

        lines_out.append(",".join(row))

    if result_file:
        with open(result_file, "w") as file:
            file.writelines("".join(lines_out))

    return lines_out


def parse_args():
    # Create the argument parser
    parser = argparse.ArgumentParser(
        description="replaces the out values with updated values from the dump file, and generates a new results file."
    )

    # Add the input file argument
    parser.add_argument(
        "out_file", type=argparse.FileType("r"), help="path to the output file"
    )

    # Add the dump file argument
    parser.add_argument(
        "dump_file", type=argparse.FileType("r"), help="path to the dump file"
    )

    # Add an optional result file argument
    parser.add_argument(
        "-r",
        "--result_file",
        type=argparse.FileType("w"),
        help='path to the result file (default: next to the out file with "_v2" suffix)',
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # Get the paths from the arguments
    out_file = args.out_file.name
    dump_file = args.dump_file.name
    result_file = args.result_file.name if args.result_file else None

    if not result_file:
        result_file = suggest_result_file(out_file)

    # Print the file paths
    print(f"Output file: {out_file}")
    print(f"Dump file: {dump_file}")
    print(f"Result file: {result_file}")

    return out_file, dump_file, result_file


def main():
    args = parse_args()
    replace_results_with_min_abs_error(*args)


if __name__ == "__main__":
    main()
