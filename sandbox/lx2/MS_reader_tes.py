import unittest
from LX2_MS_reader import SpectraUtil


class TestLX2_MS_reader(unittest.TestCase):
    def setUp(self):
        filename = "test_resources\\small_test\\190321_Serum_Lipidextract_368723_01.mzML"
        self.spectraUtil = SpectraUtil.fromFile(filename, test_sample=True)

    def test_read(self):
        scan_cols = [
            "idx",
            "filter_string",
            "time",
            "msLevel",
            "positive_scan",
            "precursor_id",
            "max_i",
            "tic",
            "target_mz",
        ]
        peak_cols = ["m", "i"]
        self.assertListEqual(
            self.spectraUtil.scansDF.columns.tolist(), scan_cols
        )
        self.assertListEqual(
            self.spectraUtil.peaksDF.columns.tolist(), peak_cols
        )


if __name__ == "__main__":
    unittest.main()
