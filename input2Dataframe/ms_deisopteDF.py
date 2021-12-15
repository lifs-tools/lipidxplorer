from ms_deisotope import MSFileLoader
import pandas as pd
import logging
from pathlib import Path
from pymzml import pymzml


def pymzml_path2df(path, time_start=0, time_end=float("inf")):
    dfs = []
    with pymzml.run.Reader(str(path)) as r:
        for b in r:
            if time_start / 60 > b.scan_time_in_minutes() > time_end / 60:
                continue
            df = {}
            df["mz"] = b.mz
            df["inty"] = b.i
            df["scan_id"] = b.ID
            df["filter_string"] = b.get("MS:1000512")
            if b.ms_level == 2:
                df["precursor_id"] = b.selected_precursors[0].get("precursor id")
            else:
                df["precursor_id"] = None
            dfs.append(df)
    # df = pd.concat(dfs)
    # df["path_stem"] = path.stem
    # df.set_index(
    #     ["path_stem", "scan_id", "filter_string", "precursor_id"],
    #     append=True,
    #     inplace=True,
    # )
    # df.attrs = {"path": path}
    logging.debug(f"from {path} made dataframe...")
    logging.debug(f"{df}")

    return df


def path2df(path, time_start=0, time_end=float("inf")):
    dfs = []
    with MSFileLoader(str(path)) as r:
        r.get_scan_by_time(time_start / 60)
        r.start_from_scan(r.get_scan_by_time(time_start / 60).id)
        for b in r:
            if time_start / 60 > b.precursor.scan_time > time_end / 60:
                break
            a = b.precursor.arrays
            df = pd.DataFrame({"mz": a.mz, "inty": a.intensity})
            df["scan_id"] = b.precursor.scan_id
            df["filter_string"] = b.precursor.annotations["filter string"]
            df["precursor_id"] = None
            dfs.append(df)
            for p in b.products:
                if time_start > p.scan_time > time_end:
                    continue
                a = p.arrays
                df = pd.DataFrame({"mz": a.mz, "inty": a.intensity})
                df["scan_id"] = p.scan_id  # TODO  make them categoriacal?
                df["filter_string"] = p.annotations["filter string"]
                df["precursor_id"] = b.precursor.scan_id
                df.set_index(["scan_id", "filter_string"], append=True, inplace=True)
                dfs.append(df)
    df = pd.concat(dfs)
    df.set_index(
        {
            "path_stem": path.stem,
            "scan_id": b.precursor.scan_id,
            "filter_string": b.precursor.annotations["filter string"],
            "precursor_id": None,
        },
        append=True,
        inplace=True,
    )
    df.attrs = {"path": path}
    logging.debug(f"from {path} made dataframe...")
    logging.debug(f"{df}")

    return df


def main():
    p = Path(r"D:\fork\isas_lipidxplorer\test_resources\small_test")
    files = p.glob("*.mzml")
    dfs = [path2df(path) for path in files]


if __name__ == "__main__":
    main()

