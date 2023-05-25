"""
Created on 16.02.2018

@author: mirandaa
"""
import sys
import logging
import os
import time
import numpy as np
import pandas as pd

log = logging.getLogger(os.path.basename(__file__))
import MSFileReader


def ThermoRawfile2DataFrames(file_path, head=None):
    log.info("file: %s", file_path)
    rawfile = MSFileReader.ThermoRawfile(file_path)

    start = rawfile.FirstSpectrumNumber
    end = rawfile.GetLastSpectrumNumber() if head == None else head

    MSrawscansDF = pd.DataFrame(
        index=np.arange(start, end + 1),
        columns=["scanNum", "filterLine", "retTime", "chargeState", "isolationMass"],
    )
    peak_datasDF_list = []
    startTime = time.time()
    for scanNum in np.arange(start, end + 1):
        filterLine = rawfile.GetFilterForScanNum(scanNum)
        peak_datas = rawfile.GetLabelData(scanNum)[0]
        if not peak_datas.mass:  # there was no data
            peak_datas = (
                rawfile.GetMassListFromScanNum(scanNum)[0][0],
                rawfile.GetMassListFromScanNum(scanNum)[0][1],
            )

        retTime = rawfile.RTFromScanNum(scanNum) * 60
        chargeState = rawfile.GetTrailerExtraForScanNum(scanNum)["Charge State"]
        isolationMass = (
            rawfile.GetFullMSOrderPrecursorDataFromScanNum(scanNum,0).precursorMass
            if rawfile.GetFullMSOrderPrecursorDataFromScanNum(scanNum,0) is not None
            else 0.0
        )  # or monoIsoMass
        row = [scanNum, filterLine, retTime, chargeState, isolationMass]
        MSrawscansDF.loc[scanNum] = row
        # peak_datasT = list(zip(*peak_datas))
        if len(peak_datas) > 2:
            peak_datasDF = pd.DataFrame(peak_datas).T
            peak_datasDF.columns = [
                "mass",
                "intensity",
                "resolution",
                "baseline",
                "noise",
                "charge",
            ]
            peak_datasDF["scanNum"] = scanNum
            peak_datasDF.set_index("scanNum", inplace=True)
        else:
            peak_datasDF = pd.DataFrame(peak_datas).T
            peak_datasDF.columns = ["mass", "intensity"]
            peak_datasDF["scanNum"] = scanNum
            peak_datasDF.set_index("scanNum", inplace=True)
        peak_datasDF_list.append(peak_datasDF)
    MSPeakDatasDF = pd.concat(peak_datasDF_list)  # concat is expensive so just once
    log.info("File Read time %f s", time.time() - startTime)
    log.info("Scan Count is %d", len(MSrawscansDF))

    return MSrawscansDF, MSPeakDatasDF


def main(filename):
    log.info("convert raw file {} to dataframe".format(filename))
    MSrawscansDF, MSPeakDatasDF = ThermoRawfile2DataFrames(filename)
    name = filename  # os.path.split(filename)[-1]
    MSrawscansDF.to_pickle(name[:-4] + "_Scans.pkl")
    MSPeakDatasDF.to_pickle(name[:-4] + "_Peaks.pkl")


if __name__ == "__main__":
    filename = " ".join(sys.argv[1:])
    main(filename)
