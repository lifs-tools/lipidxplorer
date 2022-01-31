import pytest
from lx.spectraImport import doImport, lpdxImportDEF_new
from lx.spectraTools import loadSC
from x_masterscan import compareMasterScans

from utils import expected_ms_path, make_masterscan, proy_path, read_options
from LX2_masterscan import make_lx2_masterscan


def test_make_masterscan():
    options = read_options(proy_path)
    masterscan = make_masterscan(options)
    expected = loadSC(expected_ms_path)
    expected.listSurveyEntry = expected.listSurveyEntry[:100]
    masterscan.listSurveyEntry = masterscan.listSurveyEntry[:100]
    assert compareMasterScans(masterscan, expected)


def test_make_lx2_masterscan():
    options = read_options(
        r"d:\fork\lipidxplorer-evaluation\190731_benchmark_data_files_infos\190731_mzML_no_zlib\for_paper_lipidxplorer128.lxp"
    )
    masterscan = make_lx2_masterscan(options)
    import pickle

    sc_path = r"d:\fork\lipidxplorer-evaluation\190731_benchmark_data_files_infos\190731_mzML_no_zlib\for_paper_from_df.sc"
    with open(sc_path, "wb") as fh:
        pickle.dump(masterscan, fh)

    expected = loadSC(expected_ms_path)
    expected.listSurveyEntry = expected.listSurveyEntry[:100]
    masterscan.listSurveyEntry = masterscan.listSurveyEntry[:100]
    assert compareMasterScans(masterscan, expected)
