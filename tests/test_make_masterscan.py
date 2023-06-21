# Test Step 1: Check the master scan
import pytest
from lx.spectraImport import doImport, lpdxImportDEF_new
from lx.spectraTools import loadSC
from x_masterscan import compareMasterScans

from utils import masterscan_2_df

from utils import (
    expected_ms_path,
    expected_lx2ms_path,
    make_masterscan,
    proy_path,
    read_options,
)
from LX2_masterscan import make_lx2_masterscan
from LX1_masterscan import make_lx1_masterscan

# from memory_profiler import profile


def test_make_masterscan():
    '''this tests lx1 it has intermediate results
     file (eg. *.mzml) has a spectra
     a spectra has multiple scans
     scans can be ms1 or ms2
     scan have multiple peaks
     a peak has a mass and an intensity

    for one spectra, similar scans are grouped (eg.ms1 scans)
    for a group of scans peaks are clustered (eg. target mass +- reolution 456.89 +- 0.055)
    peaks are grouped by mass to average the intensity, (eg avereage mass, average intensity)
    a weighted average can be used where more intensse peaks influence the average mass more
    for each spectra masses can be "recalibrated" based on expected mass (see np.interp)

    lx1_bins_v1.pkl:    per scan grouping of ms1 peaks
    lx1_before_shift_or_recalibrate.pkl:    per scan averrage of grouping

    multiple spectra are "aligned" by grouping similar scans
    and clustering peaks from the different scans
    per scan intensity is keept as that is the information used in the outpu

    the colection of grouped / averaged and aligned spectra is stored  in a masterscan file
    that contains the averaged mass of the aligned spectra and the intensity for each spectra

    for ms2 there is a similar operation, of grouping, averaging and aligning

     '''

    options = read_options(proy_path)
    masterscan = make_masterscan(options, make_intermediate_output = False)  # original lx1
    expected = loadSC(expected_ms_path)
    expected.listSurveyEntry = expected.listSurveyEntry[:100]
    masterscan.listSurveyEntry = masterscan.listSurveyEntry[:100]
    assert compareMasterScans(masterscan, expected)

def test_compare_ms2s():
    expected_lx1 = loadSC(expected_ms_path)
    expected_lx2_manual = loadSC(expected_lx2ms_path)
    df1 = masterscan_2_df(expected_lx1)
    df2 = masterscan_2_df(expected_lx2_manual) # missing ms2 data
    print('compare ms2')

# TODO: @Jacobo
@pytest.mark.skip(
    reason="assert False"
)
def test_make_lx2_masterscan():
    options = read_options(proy_path)
    masterscan = make_lx2_masterscan(options)
    expected = loadSC(expected_lx2ms_path)
    expected.listSurveyEntry = expected.listSurveyEntry[:100]
    masterscan.listSurveyEntry = masterscan.listSurveyEntry[:100]
    assert compareMasterScans(masterscan, expected)


def test_make_lx1_masterscan():
    options = read_options(proy_path)
    masterscan = make_lx1_masterscan(options)  # refactored code of lx1
    expected = loadSC(expected_lx2ms_path)
    expected.listSurveyEntry = expected.listSurveyEntry[:100]
    masterscan.listSurveyEntry = masterscan.listSurveyEntry[:100]
    assert compareMasterScans(masterscan, expected)

