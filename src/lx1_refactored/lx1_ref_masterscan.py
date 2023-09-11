""" adapting dataframe and dictionaries into LX1 masterscan for backward compatibility
    start with a dataframe that contains the averaged spectra
    with columns including mass, intensity, ms level, polalrity and filename (stem)

    in general:
        dataframe into -> mass_inty_generator_ms1_agg generates -> a list of tuples
        tuple into -> se_factory generates -> surveyentry
    
    specificaly:
        df into -> df2listSurveyEntry generates-> list of SurveyEntry required by the masterscan object
        options, listSurveyEntry and filenames(stems) into -> build_masterscan generates -> a masterscan object ready to use  in LX1

    could be called something like this:
        options = get options from somewhere
        polarity = df.iloc[0].at['polarity']
        stems = df.['stems'].unique()
        
        scan = build_masterscan(options, df2listSurveyEntry(df, polarity), stems)

"""
import logging
import sys
import pickle
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
    """tuple in survey entry out

    Args:
        msmass (_type_): average mass 
        dictIntensity (_type_): one intensity value per sample (a sample is a filename / stem) 
        samples (_type_): list of filenames / stems
        polarity (_type_): -1 , +1 used in que mfql, taken from the spectra
        massWindow (int, optional): should be the difference of the maximum and the minumum of the masses that where averaged. Defaults to 0 because not needed.

    Returns:
        SurveyEntry: for compatibility with LX1
    """
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
        massWindow  # used for isotopic correction when no resolution is given
    )
    return se

def make_masterscan(
    options, aligned_spectra_df, aligned_spectra_infos, lx2=False
):
    """make the masterscan based on the optoins inftomation

    Args:
        options (_type_): as in lx1

    Returns:
        masterscan: with the averaged spectra information
    """
    df = aligned_spectra_df
    df_infos = aligned_spectra_infos
    df["masswindow"] = -1  # # NOTE use :add_massWindow instead
    polarity = df_infos[0]["polarity"]
    samples = df["stem"].unique().tolist()
    listSurveyEntry = df2listSurveyEntry(df, polarity, samples)
    scan = build_masterscan(options, listSurveyEntry, samples)

    idp = Path(options["importDir"])

    if lx2:
        filename = str(idp / Path("".join([idp.stem, "-lx2.sc"])))
    else:
        filename = str(idp / Path("".join([idp.stem, "-lx1-ref.sc"])))

    # filename = options["masterScanRun"]
    log.info(f"saving file to: {filename}")
    with open(filename, "wb") as scFile:
        pickle.dump(scan, scFile, pickle.HIGHEST_PROTOCOL)

    return scan
    
def build_masterscan(options, listSurveyEntry, stems):
    """generate a generic masterscan for LX1 compatibility

    Args:
        options (dict like): setting used for generating 
        listSurveyEntry (iterable of surveyentries): the main content of the masterscan
        stems (list of str): the names of the spectra in listSurveyEntry

    Returns:
        scan: the masterscan
    """
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

