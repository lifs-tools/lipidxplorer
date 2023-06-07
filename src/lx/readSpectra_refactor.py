from pyteomics import mzml, auxiliary
import pandas as pd
import logging
import os

log = logging.getLogger(os.path.basename(__file__))

from lx.alignment import specEntry, linearAlignment


def add_Sample(sc=None, specFile=None, specDir=None, options={}, **kwargs):

    make_a_masterscan(specFile, options)

    specName = specFile
    lpdxSample_base_peak_ms1 = None
    nb_ms_scans = 0
    nb_ms_peaks = 0
    nb_msms_scans = 0
    nb_msms_peaks = 0
    return (
        specName,
        lpdxSample_base_peak_ms1,
        nb_ms_scans,
        nb_ms_peaks,
        nb_msms_scans,
        nb_msms_peaks,
    )


def make_a_masterscan(mzml_file, options):
    scansDF, peaksDF = mzML2DataFrames(mzml_file)

    # as in readspectra, filter by mass and time
    no_result = (0, float("inf"))
    MS2massrange = options.get("MSMSmassrange", no_result)
    timerange = options.get(
        "timerange", no_result
    )  # this is in seconds we need minutes
    MS1massrange = options.get("MSmassrange", no_result)

    scans_pos = scansDF.loc[scansDF.positive_scan == True]
    scans_neg = scansDF.loc[scansDF.positive_scan == False]
    scans_ms1 = scansDF.loc[scansDF.msLevel == 1]
    scans_ms2 = scansDF.loc[scansDF.msLevel == 2]

    scans_timerange = scansDF.loc[scansDF.time.multiply(60).between(*timerange)]
    peaks_MS1massrange = peaksDF.loc[peaksDF.m.between(*MS1massrange)]
    peaks_MS2massrange = peaksDF.loc[peaksDF.m.between(*MS2massrange)]

    # as in https://stackoverflow.com/questions/11976503/how-to-keep-index-when-using-pandas-merge
    ms1_pos_scans = (
        scansDF.reset_index()
        .merge(scans_ms1)
        .merge(scans_pos)
        .merge(scans_timerange)
        .set_index("id")
    )

    spectraDF = peaks_MS1massrange.merge(
        ms1_pos_scans.max_i, left_index=True, right_index=True
    )  # left_ and right_ index to keep the index
    spectraDF["rel_i"] = spectraDF.i / spectraDF.max_i

    # make the ms1Scans as in old version, TODO avoid doing this
    ms1Scans = []
    for scan_tuple in ms1_pos_scans.itertuples():
        scan_peaks = spectraDF.loc[scan_tuple.Index]
        scan_processed = [
            (peak_tuple.m, peak_tuple.i, peak_tuple.rel_i, 0, 0, 0, 0)
            for peak_tuple in scan_peaks.itertuples()
        ]  # padding zeroes because this is the expected format
        ms1Scans.append(
            {
                "time": scan_tuple.time,
                "totIonCurrent": scan_tuple.tic,
                "polarity": "+" if scan_tuple.positive_scan else "-",
                "max_it": scan_tuple.max_i,
                "scan": scan_processed,
            }
        )

    # --------------- now for the ms2

    # as in https://stackoverflow.com/questions/11976503/how-to-keep-index-when-using-pandas-merge
    ms2_pos_scans = (
        scansDF.reset_index()
        .merge(scans_ms2)
        .merge(scans_pos)
        .merge(scans_timerange)
        .set_index("id")
    )

    spectra2DF = peaks_MS2massrange.merge(
        ms2_pos_scans.max_i, left_index=True, right_index=True
    )  # left_ and right_ index to keep the index
    spectra2DF["rel_i"] = spectra2DF.i / spectra2DF.max_i

    # make the ms2Scans as in old version, TODO avoid doing this
    ms2Scans = []  # TODO this is different then the og, not clear why
    for scan_tuple in ms2_pos_scans.loc[
        spectra2DF.index.unique()
    ].itertuples():  # some scans dont have peaks
        scan_peaks = spectra2DF.loc[scan_tuple.Index]
        if type(scan_peaks) is pd.Series:  # only One entry
            scan_processed = [
                (scan_peaks["m"], scan_peaks["i"], scan_peaks["rel_i"], 0, 0, 0, 0)
            ]
        else:
            scan_processed = [
                (peak_tuple.m, peak_tuple.i, peak_tuple.rel_i, 0, 0, 0, 0)
                for peak_tuple in scan_peaks.itertuples()
            ]  # padding zeroes because this is the expected format
        ms2Scans.append(
            {
                "time": scan_tuple.time,
                "totIonCurrent": scan_tuple.tic,
                "precursorMz": scan_tuple.target_mz,  # TODO replace this with the trigger scan
                "polarity": "+" if scan_tuple.positive_scan else "-",
                "max_it": scan_tuple.max_i,
                "scan": scan_processed,
            }
        )

    # --------------------------make dict spec entry for use for linear alignment
    dictSpecEntry = {}
    # TODO use this specEntry = namedtuple('specEntry', 'mass content')
    specDF = spectraDF.loc[
        (spectraDF.i > 0) & (spectraDF.rel_i > 0)
    ]  # not sure why this is needed
    for id, group in ms1_pos_scans.groupby("id"):  # see definition above
        scan_peaks = specDF.loc[id]
        # specEntry(mass, content={})
        dictSpecEntry[id] = [
            specEntry(
                peak.m, {"sample": id, "intensity": peak.i, "intensity_rel": peak.rel_i}
            )
            for peak in scan_peaks.itertuples()
        ]

    # -----------------------TODO refactor linearAlignment
    fadi_denominator = count
    fadi_percentage = options["MSfilter"]
    listClusters = linearAlignment(
        list(dictSpecEntry.keys()),
        dictSpecEntry,
        options["MSresolution"],
        merge=mergeSumIntensity,
        mergeTolerance=options["MSresolution"],
        mergeDeltaRes=options["MSresolutionDelta"],
        fadi_denominator=fadi_denominator,
        fadi_percentage=fadi_percentage,
    )


def mzML2DataFrames(filename):  # TODO move this to input2dataframe
    scans = []
    peaks_dfs = []

    with mzml.read(filename) as reader:
        for item in reader:
            id = item["id"]
            idx = item["index"] + 1
            fs = item["scanList"]["scan"][0]["filter string"]
            time = item["scanList"]["scan"][0][
                "scan start time"
            ]  # * 1 to make a unitfloat into a float
            msLevel = item["ms level"]
            positive_scan = True if "positive scan" in item else False
            if not positive_scan:
                item["negative scan"]  # raise exceltion if not positive or negative
            p_data = item.get("precursorList", None)  # helper
            precursor_id = p_data["precursor"][0]["spectrumRef"] if p_data else None
            max_i = item["base peak intensity"]
            tic = item["total ion current"]

            # collect the scans data
            row = (id, idx, fs, time, msLevel, positive_scan, precursor_id)
            scans.append(row)

            # collect the peaks data
            i = item["intensity array"]
            m = item["m/z array"]
            cols = {"m": m, "i": i}
            df = pd.DataFrame(cols)
            df["id"] = id
            df.set_index("id", inplace=True)
            peaks_dfs.append(df)

        scansDF = pd.DataFrame(
            scans,
            columns=[
                "id",
                "idx",
                "filter_string",
                "time",
                "msLevel",
                "positive_scan",
                "precursor_id",
                "max_i",
                "tic",
            ],
        )
        scansDF.set_index("id", inplace=True)
        peaksDF = pd.concat(peaks_dfs)

    return scansDF, peaksDF
