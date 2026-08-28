[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3483976.svg)](https://doi.org/10.5281/zenodo.3483976)
# LipidXplorer

LipidXplorer is a software that is designed to support bottom-up and top-down shotgun lipidomics experiments performed 
on all types of tandem mass spectrometers. Lipid identification does not rely on a database resource of reference 
or simulated mass spectra but uses user-defined molecular fragment queries. It supports accurate, isotope-corrected 
quantification based on the identified MS1 or MS2 level fragments.

## Downloading LipidXplorer

The latest (binary) release version of LipidXplorer is available from the [LIFS Portal](https://lifs-tools.org/lipidxplorer.html). 
You can obtain the source code for LipidXplorer from our [GitLab server](https://github.com/lifs-tools//lipidxplorer) and release version archives from [here](https://github.com/lifs-tools//lipidxplorer/-/releases).

## Running LipidXplorer on Windows

For Windows, we provide a single executable for LipidXplorer for download from the [LIFS Portal](https://lifs-tools.org/lipidxplorer.html).
Please download the zip-archive to a location of your choice and extract (unzip) the contents. 
Change to the unzipped LipidXplorer archive directory and simply double-click on `LipidXplorer.exe` to start it.

## Installation and Tutorials

Please see more detailed installation instructions on our [Wiki](https://lifs-tools.org/wiki/index.php/LipidXplorer_Installation).
These also cover the case of working with the source code.

[The Wiki](https://lifs-tools.org/wiki/index.php) also offers an overview of the concepts behind LipidXplorer, as well as tutorial and reference materials.

## Working with the LipidXplorer Source Code

LipidXplorer uses [uv](https://docs.astral.sh/uv/) to manage its Python
environment. Install uv, then from the project root:

    uv sync

This creates a `.venv` with the exact dependency versions recorded in
`uv.lock`, using the Python version pinned in `.python-version` (3.12).

Run the application with:

    uv run python LipidXplorer.py

Run the tests with:

    uv run pytest

On Linux, wxPython is installed from the wxPython project's own package
index, because no Linux wheel for it is published on PyPI. This is
configured in `pyproject.toml` and requires no manual steps, but it does
pin the Linux build to Ubuntu 24.04's GTK3 ABI. You will also need the GTK3
runtime libraries:

    sudo apt-get install libgtk-3-0 libglib2.0-0 libsm6 libxxf86vm1 \
                         libnotify4 libsdl2-2.0-0 libwebkit2gtk-4.1-0

## Building a Standalone Executable

The same command works on all three platforms:

    uv run pyinstaller --noconfirm LipidXplorer.spec

Output is `dist/LipidXplorer/` on Windows and Linux, and
`dist/LipidXplorer.app` on macOS.

PyInstaller cannot cross-compile: a Windows executable must be built on
Windows, a macOS app on macOS, and so on. Released binaries for all three
platforms are produced by the GitHub Actions workflow in
`.github/workflows/build.yml`.

### macOS

macOS builds are neither signed nor notarized. On first launch, Gatekeeper
will refuse to open the app. Right-click it in Finder and choose **Open**,
then confirm — this is only needed once. (On Linux, PyInstaller does not
embed an application icon in the binary — it prints a warning and skips
that step, so the Linux binary has no embedded icon.)

## Versioning

We use [Semantic Versioning](http://semver.org/) for versioning of the software.
 
To browse available versions and releases, please see the [tags on this repository](https://github.com/lifs-tools//lipidxplorer/tags). 

## Authors

* **Ronny Herzog** - *Initial work*
* **Ballal Md. Hossen** - *Current Developer*
* **Jacobo Miranda Ackermann** - *Former Developer*
* **Lukas Müller** - *Contributor*
* **Fadi Al Machot** - *Contributor*
* **Nils Hoffmann** - *Contributor*

## License

This project is licensed under the GNU GPL License, version 2 - see the [COPYRIGHT.txt](COPYRIGHT.txt) file for details

## Help and Support

Please check our [Wiki](https://lifs-tools.org/wiki/index.php) on details on how to contact us to receive help and report errors.

## Citing the Software
Herzog R, Schwudke D, Shevchenko A: ***LipidXplorer: Software for Quantitative Shotgun Lipidomics Compatible with Multiple Mass Spectrometry Platforms***. **Current Protocols in Bioinformatics 2013 Oct 15** [PUBMED](https://www.ncbi.nlm.nih.gov/pubmed/26270171)
