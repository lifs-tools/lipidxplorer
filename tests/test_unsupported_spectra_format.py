"""An unsupported spectra format fails with a LipidXException, not a NameError.

The mzXML importer was removed in 1.5.1 but its call site was left behind,
so selecting mzXML crashed with NameError: add_mzXMLSample.
"""

import pytest

from lx.exceptions import LipidXException
from lx.spectraImport import doImport


def _do_import(spectra_format):
    doImport(
        options={"spectraFormat": spectra_format},
        scan=None, importDir="", output=None, parent=None,
        listFiles=[["/data/sample_a." + spectra_format, "/data"]],
        isTaken=True, isGroup=False,
        alignmentMS="linear", alignmentMSMS="linear", scanAvg="linear",
    )


def test_mzxml_is_rejected_with_a_conversion_hint():
    with pytest.raises(LipidXException, match="Convert them to mzML"):
        _do_import("mzXML")


def test_other_unknown_formats_are_rejected():
    with pytest.raises(LipidXException, match="not supported"):
        _do_import("raw")
