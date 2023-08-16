import pytest
import pandas as pd
from pathlib import Path

from lx1_refactored.tools import masterscan_2_df as scan2df

from utils import (
    make_masterscan,
    proy_path,
    read_options,
)


ROOT_SMALL_TEST = r"tests/resources/small_test/"
EXPECTED_OUTPUT_PATH = r"tests/resources/small_test/small_test-out.csv"


def test_make_lx1_masterscan_partials():
    """this tests lx1 it has intermediate results
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

    """
    options = read_options(proy_path)
    masterscan = make_masterscan(
        options, make_intermediate_output=True
    )  # original lx1
########################
    # lx1_spectra_peak_groups.pkl contains peak contains clustering info for each specta
    # and ms2 data (not clustered)

    refpath = Path(options["importDir"]) / Path(
        "lx1_spectra_peak_groups_and_ms2_ref.pkl"
    )
    partial = Path(options["importDir"]) / Path("lx1_spectra_peak_groups.pkl")
    lx1_spectra_peak_groups_and_ms2_ref = pd.read_pickle(refpath)
    lx1_spectra_peak_groups_and_ms2 = pd.read_pickle(partial)

    assert lx1_spectra_peak_groups_and_ms2_ref.equals(
        lx1_spectra_peak_groups_and_ms2
    )  # NOTE use df.compare to find what is different between the two
    partial.unlink()  # deletes the file
###########################
    # lx1_spectra_peak_averaged contains the averaged peak for each spectra
    refpath = Path(options["importDir"]) / Path(
        "lx1_spectra_peak_averaged_ref.pkl"
    )
    partial = Path(options["importDir"]) / Path(
        "lx1_spectra_peak_averaged.pkl"
    )
    lx1_spectra_peak_averaged_ref = pd.read_pickle(refpath)
    lx1_spectra_peak_averaged = pd.read_pickle(partial)
    assert lx1_spectra_peak_averaged_ref.equals(
        lx1_spectra_peak_averaged
    )  # NOTE use df.compare to find what is different between the two
    partial.unlink()  # deletes the file
############################
    # lx1_spectra_peak_recalibrated after recalibration
    refpath = Path(options["importDir"]) / Path(
        "lx1_spectra_peak_recalibrated_ref.pkl"
    )
    partial = Path(options["importDir"]) / Path(
        "lx1_spectra_peak_recalibrated.pkl"
    )
    if partial.is_file():  # optional
        lx1_spectra_peak_recalibrated_ref = pd.read_pickle(refpath)
        lx1_spectra_peak_recalibrated = pd.read_pickle(partial)
        assert lx1_spectra_peak_recalibrated_ref.equals(
            lx1_spectra_peak_recalibrated
        )  # NOTE use df.compare to find what is different between the two
        partial.unlink()  # deletes the file
############################
    # lx1_masterscan_aligned_spectra after multi spectra alignment
    refpath = Path(options["importDir"]) / Path(
        "lx1_masterscan_aligned_spectra_ref.pkl"
    )
    partial = Path(options["importDir"]) / Path(
        "lx1_masterscan_aligned_spectra.pkl"
    )
    lx1_masterscan_aligned_spectra_ref = pd.read_pickle(refpath)
    lx1_masterscan_aligned_spectra = scan2df(
        partial
    )  # masterscan_2_df(partial) is more messy
    assert lx1_masterscan_aligned_spectra_ref.equals(
        lx1_masterscan_aligned_spectra
    )
    partial.unlink()
###########################
    # lx1_masterscan_collapsed_spectra mpotential missalignment correction
    refpath = Path(options["importDir"]) / Path(
        "lx1_masterscan_collapsed_spectra_ref.pkl"
    )
    partial = Path(options["importDir"]) / Path(
        "lx1_masterscan_collapsed_spectra.pkl"
    )
    if partial.is_file():  # optional
        lx1_masterscan_collapsed_spectra_ref = pd.read_pickle(refpath)
        lx1_masterscan_collapsed_spectra = scan2df(partial)
        assert lx1_masterscan_collapsed_spectra_ref.equals(
            lx1_masterscan_collapsed_spectra
        )
        partial.unlink()


###################
    # start ms2
    # ms2 peaks are read in from each spectra but not grouped
    # NOTE see lx1_spectra_peak_groups_and_ms2_ref file 
####################
    # grouping of ms2 spectra "lx1_ms2_groups.pkl"
    # group is "retention time string" 
    refpath = Path(options["importDir"]) / Path(
        "lx1_ms2_groups_ref.pkl"
    )
    partial = Path(options["importDir"]) / Path(
        "lx1_ms2_groups.pkl"
    )
    if partial.is_file():  # optional
        lx1_ms2_groups_ref= pd.read_pickle(refpath)
        lx1_ms2_groups = pd.read_pickle(partial)
        assert lx1_ms2_groups_ref.equals(
            lx1_ms2_groups
        )
        partial.unlink()

##################### lx1_ms2_averages NOTE: these might be collapse d
    refpath = Path(options["importDir"]) / Path(
        "lx1_ms2_averages_ref.pkl"
    )
    partial = Path(options["importDir"]) / Path(
        "lx1_ms2_averages.pkl"
    )
    if partial.is_file():  # optional
        lx1_ms2_averages_ref = pd.read_pickle(refpath)
        lx1_ms2_averages = pd.read_pickle(partial)
        assert lx1_ms2_averages_ref.equals(
            lx1_ms2_averages
        )
        partial.unlink()



################## lx1_ms2_to_ms1
    refpath = Path(options["importDir"]) / Path(
        "lx1_ms2_to_ms1_ref.pkl"
    )
    partial = Path(options["importDir"]) / Path(
        "lx1_ms2_to_ms1.pkl"
    )
    if partial.is_file():  # optional
        make_lx1_ms2_to_ms1_ref = pd.read_pickle(refpath)
        make_lx1_ms2_to_ms1 = pd.read_pickle(partial)
        assert make_lx1_ms2_to_ms1_ref.equals(
            make_lx1_ms2_to_ms1
        )
        partial.unlink()



