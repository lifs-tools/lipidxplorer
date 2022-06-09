from lx.spectraTools import loadSC
import pandas as pd
import logging, sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)


def find_common_elements(lx1_df, lx2_df, tolerance=0.05):

    lx1_df.sort_values(by=["precurmass_lx1"], inplace=True)
    lx2_df.sort_values(by=["precurmass_lx2"], inplace=True)
    merged = pd.merge_asof(
        lx1_df,
        lx2_df,
        left_on="precurmass_lx1",
        right_on="precurmass_lx2",
        tolerance=tolerance,
        direction="nearest",
    )
    merged2 = pd.merge_asof(
        lx2_df,
        lx1_df,
        left_on="precurmass_lx2",
        right_on="precurmass_lx1",
        tolerance=tolerance,
        direction="nearest",
    )

    return pd.concat([merged, merged2], sort=False)


def ms2_common(matching_ms1s, lx1_masterscan, lx2_masterscan):
    for row in matching_ms1s.itertuples():
        listMSMS_lx1 = lx1_masterscan.listSurveyEntry[int(row.idx_lx1)].listMSMS
        listMSMS_lx2 = lx2_masterscan.listSurveyEntry[int(row.idx_lx2)].listMSMS
        s1 = pd.Series((x.mass for x in listMSMS_lx1), name="ms2_lx1").sort_values()
        s2 = pd.Series((x.mass for x in listMSMS_lx2), name="ms2_lx2").sort_values()
        m1 = pd.merge_asof(
            s1,
            s2,
            left_on="ms2_lx1",
            right_on="ms2_lx2",
            direction="nearest",
            tolerance=0.05,
        )
        m2 = pd.merge_asof(
            s2,
            s1,
            left_on="ms2_lx2",
            right_on="ms2_lx1",
            direction="nearest",
            tolerance=0.05,
        )
        c = pd.concat([m1, m2], sort=False)
        c.drop_duplicates(inplace=True)
        c["common_idx"] = row.Index
        yield c


def ms2_uncommon(*args, **kwargs):
    for c in ms2_common(*args, **kwargs):
        yield (c[c.isna().any(axis=1)])


def compare_masterscan(lx1_masterscan_path, lx2_masterscan_path, xls_output_path=None):
    """
    Compare a master scan with a list of scans.
    """
    # Load the master scan
    if xls_output_path is None:
        xls_output_path = "output.xlsx"

    lx1_masterscan = loadSC(lx1_masterscan_path)
    lx2_masterscan = loadSC(lx2_masterscan_path)

    log.info("Getting MS1")
    lx1_ms1 = (
        (idx, se.precurmass) for idx, se in enumerate(lx1_masterscan.listSurveyEntry)
    )
    lx2_ms1 = (
        (idx, se.precurmass) for idx, se in enumerate(lx2_masterscan.listSurveyEntry)
    )

    log.info("Making dataframe")
    lx1_df = pd.DataFrame(lx1_ms1, columns=["idx_lx1", "precurmass_lx1"])
    lx2_df = pd.DataFrame(lx2_ms1, columns=["idx_lx2", "precurmass_lx2"])

    log.info("find_common_elements")
    common = find_common_elements(lx1_df, lx2_df)
    in_both = common[~common.isna().any(axis=1)]
    not_in_lx2 = common[common.idx_lx2.isna()]
    not_in_lx1 = common[common.idx_lx1.isna()]

    log.info("ExcelWriter( output.xlsx )")
    with pd.ExcelWriter("output.xlsx") as writer:
        in_both.to_excel(writer, sheet_name="in_both")
        not_in_lx2.to_excel(writer, sheet_name="not_in_lx2")
        not_in_lx1.to_excel(writer, sheet_name="not_in_lx1")

    # compare the ms2s
    log.info("compare the ms2s")
    matching_ms1s = common.dropna().drop_duplicates(
        subset=["precurmass_lx1", "precurmass_lx2"]
    )
    ms2_mismatch = pd.concat(
        ms2_uncommon(matching_ms1s, lx1_masterscan, lx2_masterscan)
    )

    log.info("output ms2_mismatch")
    with pd.ExcelWriter("output.xlsx") as writer:
        ms2_mismatch.to_excel(writer, sheet_name="ms2_mismatch")
        ms2_mismatch.common_idx.value_counts().to_excel(
            writer, sheet_name="ms2_mismatch_counts"
        )
        common.loc[ms2_mismatch.common_idx.value_counts().index].to_excel(
            writer, sheet_name="ms2_mismatch_precursors"
        )
    
    log.info("done")

    # TODO  handrolled find nearest closest, but with tolerance instead of merge_asof
    # https://stackoverflow.com/questions/57361453/matching-two-lists-containing-slightly-differing-float-values-by-allowing-a-tole?


if __name__ == "__main__":
    lx1_masterscan_path = r"c:\Users\mirandaa\Downloads\stitched\stitched\stitched.sc"
    lx2_masterscan_path = (
        r"c:\Users\mirandaa\Downloads\stitched\stitched\stitched-lx2.sc"
    )
    xls_output_path = None
    compare_masterscan(lx1_masterscan_path, lx2_masterscan_path, xls_output_path)
