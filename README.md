# LipidXplorer

LipidXplorer is a software that supports a variety of shotgun lipidomics experiments. It is designed to support bottom-up and top-down shotgun lipidomics experimenters performed at all type of tandem mass spectrometers. Lipid identification does not rely on a database resource of reference or simulated mass spectra. 

## Running LipidXplorer on Windows

For Windows, we provide a single executable for LipidXplorer. Go to the unzipped LipidXplorer directory and simply double-click on `LipidXplorer.exe` to start it.

## Installation and Tutorials

Please see the installation instructions on our [Wiki](https://lifs.isas.de/wiki/index.php/LipidXplorer_Installation)

[The Wiki](https://lifs.isas.de/wiki/index.php) also offers an overview of the concepts behind LipidXplorer, as well as tutorial and reference materials.

## Creating a Windows Executable

We use pyinstaller to create a Python executable of LipidXplorer that can be easily run on Windows.
To create the exe in the dist folder, please run the following command:

    pyinstaller LipidXplorer.spec

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

Please check our [Wiki](https://lifs.isas.de/wiki/index.php) on details on how to contact us to receive help and report errors.

## Citing the Software
Herzog R, Schwudke D, Shevchenko A: ***LipidXplorer: Software for Quantitative Shotgun Lipidomics Compatible with Multiple Mass Spectrometry Platforms***. **Current Protocols in Bioinformatics 2013 Oct 15** [PUBMED](https://www.ncbi.nlm.nih.gov/pubmed/26270171)
