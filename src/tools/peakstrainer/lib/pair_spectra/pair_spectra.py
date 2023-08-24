from pathlib import Path
from ms_deisotope import MSFileLoader
from ms_deisotope.output.mzml import MzMLSerializer
import pandas as pd

# from https://github.com/mobiusklein/ms_deisotope/tree/master/ms_deisotope/test
FILTER_NAME_VERSION = "pair_filter_spectra_0.1.0"


def get_file_pairs(path):
    p = Path(path)
    files = p.glob("*.mzml")
    pairs = zip(*[iter(files)] * 2)
    return pairs


def print_reader(reader):
    for bunch in reader:
        print(bunch.precursor.title)
        print(bunch.precursor.annotations["filter string"])
        bunch.precursor.pick_peaks()
        print(bunch.precursor.peak_set)
        for p in bunch.products:
            print(p.title)
            print(p.annotations["filter string"])
            p.pick_peaks()
            print(p.peak_set)
            break
        break
    reader.reset()
    print("done")


def test_writer(reader):
    # https://mobiusklein.github.io/ms_deisotope/docs/_build/html/output/mzml.html
    with open("out.mzML", "wb") as fh:
        writer = MzMLSerializer(fh, n_spectra=len(reader))

        writer.copy_metadata_from(reader)
        bunch = next(reader)
        bunch.precursor.arrays = [
            bunch.precursor.arrays.mz[:100],
            bunch.precursor.arrays.intensity[:100],
        ]
        bunch.precursor.pick_peaks()
        bunch.products = None
        writer.save(bunch, deconvoluted=False)

        writer.close()


def cleanup(*args):
    for a in args:
        Path(a).unlink()
        print(f"deleted {a}")


def main():
    p = Path(r"lib\pair_spectra\tests\20211018_Peakstrainer_pairwise")
    p = next(p.glob("*.mzml"))
    reader = MSFileLoader(str(p))
    print_reader(reader)
    test_writer(reader)
    cleanup("out.mzML", "out.mzML-idx.json")
    print("TODO find_closest_with_iterator(reader1, reader2)")


def get_MS1_filterlines(path):
    filterlines = []
    scan_ids = []
    with MSFileLoader(str(path)) as r:
        for b in r:
            filterlines.append(b.precursor.annotations["filter string"])
            scan_ids.append(b.precursor.scan_id)
            # for p in b.producs:
            #     filterlines.append(p.precursor.title)
            #     scan_ids.append(p.precursor.scan_id)
    return scan_ids, filterlines


def get_MS2_filterlines(path):
    filterlines = []
    scan_ids = []
    with MSFileLoader(str(path)) as r:
        for b in r:
            # filterlines.append(b.precursor.annotations["filter string"])
            # scan_ids.append(b.precursor.scan_id)
            for p in b.products:
                filterlines.append(p.annotations["filter string"])
                scan_ids.append(p.scan_id)
    return scan_ids, filterlines


def path_filterline2df(filterline, path):
    dfs = []
    with MSFileLoader(str(path)) as r:
        for b in r:
            if b.precursor.annotations["filter string"] == filterline:
                a = b.precursor.arrays
                df = pd.DataFrame({"mz": a.mz, "intensitiy": a.intensity})
                df["path"] = path.stem  # TODO  make them categoriacal?
                df["scan_id"] = b.precursor.scan_id
                dfs.append(df)
            for p in b.products:
                if p.annotations["filter string"] == filterline:
                    a = p.arrays
                    df = pd.DataFrame({"mz": a.mz, "intensitiy": a.intensity})
                    df["path"] = path.stem  # TODO  make them categoriacal?
                    df["scan_id"] = b.precursor.scan_id
                    dfs.append(df)
    return dfs


def filterline_pair(filterline, path1, path2, cutoff=0.01):
    # TODO # https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array
    # https://codereview.stackexchange.com/questions/28207/finding-the-closest-point-to-a-list-of-points
    # a.flat[np.abs(a - a0).argmin()]
    dfs = path_filterline2df(filterline, path1)
    dfs.extend(path_filterline2df(filterline, path2))
    df = pd.concat(dfs)

    df.sort_values("mz", inplace=True)
    mask = (-df.mz.diff(-1) < cutoff) & (df.mz.diff() < cutoff)
    p1_mask = df.path == path1.stem
    p2_mask = df.path == path2.stem

    mz_i_reader1 = df.loc[mask & p1_mask, ["mz", "intensitiy"]].T.to_numpy()
    mz_i_reader2 = df.loc[mask & p2_mask, ["mz", "intensitiy"]].T.to_numpy()

    return mz_i_reader1, mz_i_reader2


def filter_pair(path1, path2):

    # get ms1 scans
    _, ms1_filterlines = get_MS1_filterlines(path1)
    assert len(ms1_filterlines) == 1
    # filter ms1 scans
    mzi_ms1_reader_pair = filterline_pair(ms1_filterlines[0], path1, path2)
    # split ms1 scans
    _, ms2_filterlines = get_MS2_filterlines(path1)
    mzi_ms2_reader_pair = []
    for filterline in ms2_filterlines:
        mzi_reader_pair = filterline_pair(filterline, path1, path2)
        mzi_ms2_reader_pair.append(mzi_reader_pair)

    # Write out content
    reader1 = MSFileLoader(str(path1))
    with open(path1.stem + "-f.mzML", "wb") as fh:
        writer = MzMLSerializer(fh, n_spectra=1)

        writer.copy_metadata_from(reader1)
        writer.software_list.append(FILTER_NAME_VERSION)

        bunch = next(reader1)
        mzi_ms1_reader1 = mzi_ms1_reader_pair[0]
        bunch.precursor.arrays = [*mzi_ms1_reader1]
        bunch.precursor.pick_peaks()

        for product in bunch.products:
            idx = ms2_filterlines.index(product)
            mzi_ms2_reader1, _ = mzi_ms2_reader_pair[idx]
            product.arrays = [*mzi_ms2_reader1]
            product.pick_peaks()

        writer.save(bunch, deconvoluted=False)

        writer.close()

    reader2 = MSFileLoader(str(path2))
    with open(path2.stem + "-f.mzML", "wb") as fh:
        writer = MzMLSerializer(fh, n_spectra=1)

        writer.copy_metadata_from(reader2)
        writer.software_list.append(FILTER_NAME_VERSION)

        bunch = next(reader2)
        mzi_ms1_reader2 = mzi_ms1_reader_pair[1]
        bunch.precursor.arrays = [*mzi_ms1_reader2]
        bunch.precursor.pick_peaks()

        for product in bunch.products:
            idx = ms2_filterlines.index(product)
            _, mzi_ms2_reader2 = mzi_ms2_reader_pair[idx]
            product.arrays = [*mzi_ms2_reader2]
            product.pick_peaks()

        writer.save(bunch, deconvoluted=False)

        writer.close()


def pair_filter(path):
    pairs = get_file_pairs(path)
    for pair in pairs:
        filter_pair(*pair)
        break


if __name__ == "__main__":
    # main()
    pair_filter(r"lib\pair_spectra\tests\20211018_Peakstrainer_pairwise")

