import logging
import sys
import warnings
from collections import OrderedDict
from pathlib import Path

from lx.spectraContainer import MasterScan, MSMSEntry, SurveyEntry

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(Path(__file__).stem)


#### build masterscan
def df2listSurveyEntry(df, polarity, samples):

    listSurveyEntry = [
        se_factory(msmass, dictIntensity, samples, polarity, massWindow)
        for msmass, dictIntensity, polarity, massWindow in mass_inty_generator_ms1_agg(
            df, polarity
        )
    ]

    # TODO: need to optimised (most time spent)
    return sorted(listSurveyEntry, key=lambda x: x.precurmass)

def mass_inty_generator_ms1_agg(df, polarity):
    for mass, gdf in df.groupby("_group"):
        # dictIntensity = gdf.set_index("stem")["lx1_bad_inty"].to_dict()
        dictIntensity = gdf.set_index("stem")["inty"].to_dict()
        # dictIntensity.update({f"{k}_lx2": v for k, v in dictIntensity_lx2.items()})
        dictIntensity = OrderedDict(sorted(dictIntensity.items()))
        massWindow = float(gdf['masswindow'].mean())
        mass = float(gdf.mz.mean())
        yield (mass, dictIntensity, polarity, massWindow)


def se_factory(msmass, dictIntensity, samples, polarity, massWindow=0):
    holder = {s: 0 for s in samples}
    holder.update(dictIntensity)
    se = SurveyEntry(
        msmass=msmass,
        smpl=holder,
        peaks=[],
        charge=None,
        polarity=polarity,
        dictScans={
            s: 1 for s in samples
        },  # needed for the intensity threshold (thrshl / sqrt(nb. of scans))
        msms=None,
        dictBasePeakIntensity={s: 1 for s in samples},
    )
    se.massWindow = (
        massWindow  # used for isotopic c orrection when no resolution is given
    )
    return se

def mass_inty_generator_ms1(ms1_df, occupancy=1):
    add_group_no_ms1_df(ms1_df, occupancy=occupancy)
    for _, df in ms1_df.groupby(ms1_df.group_no):
        msmass = float(df.mz_mean.mean())
        dictIntensity = df.set_index("stem_first")["inty_mean"].to_dict()
        polarity = df.polarity_first.to_list()[0]
        yield msmass, dictIntensity, polarity

def build_masterscan(options, listSurveyEntry, stems):
    listSurveyEntry = list(sorted(listSurveyEntry, key=lambda x: x.precurmass))
    scan = MasterScan(options)
    scan.listSurveyEntry = listSurveyEntry
    scan.sampleOccThr["MS"] = [
        (0.0, [])
    ]  # to avoid bug at def checkOccupation
    scan.sampleOccThr["MSMS"] = [(0.0, [])]

    # for printing we need
    scan.listSamples = stems
    return scan
