import sys, os
from input2Dataframe.mzML2Dataframe import mzML2DataFrames


def from_mzml(filename):
    # MSrawscansDF, MSPeakDatasDF = mzML2DataFrames(filename) #TODO scans and peaks should be seperate
    scans_df = mzML2DataFrames(filename)


def by_filetype(filename):
    extension = os.path.splitext(filename)[1]
    if extension.lower() == ".mzml":
        return from_mzml(filename)
    else:
        raise NotImplementedError("TODO")


if __name__ == "__main__":
    props = by_filetype(sys.argv[1])
