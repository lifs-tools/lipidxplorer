import pytest
from lx.spectraImport import doImport, lpdxImportDEF_new
from lx.spectraTools import loadSC
from x_masterscan import compareMasterScans

from utils import (
    expected_ms_path,
    expected_lx2ms_path,
    make_masterscan,
    proy_path,
    read_options,
)
from LX2_masterscan import make_lx2_masterscan

# from memory_profiler import profile


def test_make_masterscan():
    options = read_options(proy_path)
    masterscan = make_masterscan(options)
    expected = loadSC(expected_ms_path)
    expected.listSurveyEntry = expected.listSurveyEntry[:100]
    masterscan.listSurveyEntry = masterscan.listSurveyEntry[:100]
    assert compareMasterScans(masterscan, expected)


def test_make_lx2_masterscan():
    left_sc_path = (
        r"D:\fork\lipidxplorer_128\test_resources\small_test\small_test-project.lxp"
    )
    options = read_options(left_sc_path)
    masterscan = make_lx2_masterscan(options)
    expected = loadSC(expected_lx2ms_path)
    expected.listSurveyEntry = expected.listSurveyEntry[:100]
    masterscan.listSurveyEntry = masterscan.listSurveyEntry[:100]
    assert compareMasterScans(masterscan, expected)


def main():
    from pathlib import Path
    import shutil
    import time, sys

    print("sameple number vs time chart")
    left_sc_path = r"D:\fork\lipidxplorer-evaluation\190731_benchmark_data_files_infos\190731_mzML_no_zlib\for_paper_lipidxplorer128.lxp"
    options = read_options(left_sc_path)
    options[
        "importDir"
    ] = r"D:\fork\lipidxplorer-evaluation\190731_benchmark_data_files_infos\perf_test"
    p = Path(options["importDir"])

    limit = 10
    count = 0

    log = []
    while count <= limit:
        try:
            mzmls = list(p.glob("*.mzml"))
            count = len(mzmls)
            # st = time.perf_counter()
            # masterscan_lx2 = make_lx2_masterscan(options)

            # log.append(
            #     ("LX2", count, sys.getsizeof(masterscan_lx2), time.perf_counter() - st,)
            # )

            listfiles = [str(mzml) for mzml in mzmls]
            st = time.perf_counter()
            masterscan_lx1 = make_masterscan(options)
            log.append(
                (
                    "LX1",
                    len(listfiles),
                    sys.getsizeof(masterscan_lx1),
                    time.perf_counter() - st,
                )
            )

            if time.perf_counter() - st > 3600:
                print("timed out")
                break

            # make 5 more files
            for idx, f in enumerate(mzmls[:5]):
                counter = len(mzmls) + idx
                newname = "duplicate_file" + str(counter) + ".mzML"
                shutil.copy(f, f.with_name(newname))
        except Exception as e:
            print(e)

    print("***********************************************************")
    print(f"lx_ver, testing count, memsysze, run time sec.")
    for line in log:
        print(",".join(map(str, line)))

    print("done")


if __name__ == "__main__":
    main()

