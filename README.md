[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3483976.svg)](https://doi.org/10.5281/zenodo.3483976)
# LipidXplorer

LipidXplorer is a software that is designed to support bottom-up and top-down shotgun lipidomics experiments performed 
on all types of tandem mass spectrometers. Lipid identification does not rely on a database resource of reference 
or simulated mass spectra but uses user-defined molecular fragment queries. It supports accurate, isotope-corrected 
quantification based on the identified MS1 or MS2 level fragments.

## Downloading LipidXplorer

The latest (binary) release version of LipidXplorer is available from the [LIFS Portal](https://lifs-tools.org/lipidxplorer.html). 
We publish release versions to [Zenodo](https://doi.org/10.5281/zenodo.3483976).

## Running LipidXplorer on Windows

For Windows, we provide a single executable for LipidXplorer for download from the [LIFS Portal](https://lifs-tools.org/lipidxplorer.html).
Please download the zip-archive to a location of your choice and extract (unzip) the contents. 
Change to the unzipped LipidXplorer archive directory and simply double-click on `LipidXplorer.exe` to start it.

## Installation and Tutorials

Please see more detailed installation instructions on our [Wiki](https://lifs-tools.org/wiki/index.php/LipidXplorer_Installation).
These also cover the case of working with the source code.

[The Wiki](https://lifs-tools.org/wiki/index.php) also offers an overview of the concepts behind LipidXplorer, as well as tutorial and reference materials.

## Working with the LipidXplorer Source Code

We recommend [PyCharm](https://www.jetbrains.com/pycharm/) for development of the LipidXplorer codebase and [Anaconda 3](https://www.anaconda.com/distribution/) to manage a stable, versioned Python environment.
Any other Python IDE will also work just as well.
Please see the `environment.yml` file in the project's source root folder for reference of an exported Anaconda environment. You can import it in your local Anaconda installation, call 
 
    conda env create -f environment.yml 

## Creating a Windows Executable

We use `pyinstaller` (part of the Anaconda environment) to create a Python executable of LipidXplorer that can be easily run on Windows.
To create the exe in the `LipidXplorer-1.2.8` folder, please run the following command:

    pyinstaller --distpath="LipidXplorer-1.2.8" LipidXplorer.spec

This will also create a zip archive of the `distpath` folder in the root directory of the project: `LipidXplorer-1.2.8.zip`.

## Creating a Linux Executable

The same instructions for creation of a standalone executable also apply under Linux. Please make sure, that you have a proper Anaconda environment
installed and activated. Then run the following command:

    pyinstaller --distpath="LipidXplorer-1.2.8" LipidXplorer.spec

This will also create a zip archive of the `distpath` folder in the root directory of the project: `LipidXplorer-1.2.8.zip`.

## Versioning

We use [Semantic Versioning](http://semver.org/) for versioning of the software.
 
To browse available versions and releases, please see the [tags on this repository](https://gitlab.isas.de/lifs/lipidxplorer/tags). 

## Authors

* **Ronny Herzog** - *Initial work*
* **Jacobo Miranda Ackermann** - *Current Developer*
* **Fadi Al Machot** - *Contributor*
* **Nils Hoffmann** - *Contributor*

## License

This project is licensed under the GNU GPL License, version 2 - see the [COPYRIGHT.txt](COPYRIGHT.txt) file for details

## Help and Support

Please check our [Wiki](https://lifs-tools.org/wiki/index.php) on details on how to contact us to receive help and report errors.

## known issues
to run it in a virtual environment in on macOS use pythonw instead of python

## Citing the Software
Herzog R, Schwudke D, Shevchenko A: ***LipidXplorer: Software for Quantitative Shotgun Lipidomics Compatible with Multiple Mass Spectrometry Platforms***. **Current Protocols in Bioinformatics 2013 Oct 15** [PUBMED](https://www.ncbi.nlm.nih.gov/pubmed/26270171)
