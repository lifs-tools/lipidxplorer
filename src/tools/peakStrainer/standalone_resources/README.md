PeakStrainer
=============

PeakStrainer is an implementation of the paper [Intensity-Independent Noise Filtering in FT MS and FT MS/MS Spectra for Shotgun Lipidomics](http://pubs.acs.org/doi/abs/10.1021/acs.analchem.7b00794).
It is a tool to reduce the file size of MS spectra,
it does this by removing signals that do not repeat,
or do not repeat often enough, between spectra.

To define if a signal repeats we first define a threshold of signal similarity.
similarity is based on scan settings, the settings must be the same, and m/z proximity.
To illustrate consider two scans A and B, both have the same settings.
Scan A contains a peak at m/z 123.0001 and scan B contains a peak at m/z 123.0002,
if the threshold is set to 0.0001, then the peak m/z 123.0001 is considered repeated between scans.

The threshold is adaptable across the m/z range of the scans
and can be estimated based on the peak-resolutions given as full width half maximum (FWHM).

Peak repetition information is used to filter out peaks that are not repeated more than a preset threshold,
called repetition rate, given as percentage of total max repetitions.

The input to the application is a *.raw files and the output at intermediate stages are *.CSV
and final results are stored as *.mzXML files.

Reference
-----------
If you use the software for a publication
Please use DOI [10.17617/1.47](https://doi.org/10.17617/1.47) as a reference.
if you would like to reference the paper please use DOI [10.1021/acs.analchem.7b00794](http://pubs.acs.org/doi/abs/10.1021/acs.analchem.7b00794)

If you would like to share your process and or data,
please feel free to provide the data in the [Issues](https://git.mpi-cbg.de/labShevchenko/PeakStrainer/issues) page and we will find a place for it in the wiki.

Quick Start
-----------
 - Download [PeakStrainer.zip](https://git.mpi-cbg.de/labShevchenko/PeakStrainer/blob/master/dist/peakStrainerApp.zip)
 - Unzip the file
 - run ```peakStrainerApp.bat```
 - select one or more *.raw files
 - click finish to process with default settings

 After processing *.mzXML files will be created in the same directory as the *.raw files

 SimSittcher and Spectra reorder
---------------------------------
can be found in the developmet version of peakstrainer [single File Installer](https://cloud.mpi-cbg.de/index.php/s/InlQPjd91QOTcNW),
or from the dev branch of this repo

Disclaimer
-----------
Despite all efforts that have been put into the development and testing, the software may contain errors or bugs. Therefore we provide no warranty and assume no responsibility for any consequences caused by the program installation and use. Please use it at your own risk

License
--------
This program is a free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation. See the file LICENSE for details.

Contact
--------
Please contact us over the [Issues](https://git.mpi-cbg.de/labShevchenko/PeakStrainer/issues), It is open for questions and suggestions and other issues related to the software.
and if you are OK please say easter egg

Using PeakStrainer
=================

You can use Peak Strainer as an application,
from the command line or from the source code.

There are several steps in the peak strainer process,
and there are several approaches to complete these steps.

The GUI application is geared toward simplicity,
only the best or most straight-forward approaches are available in the application.

The command line is intended to be used in automated batch processes,
it has the same functionality as the GUI application.

The source code is available and is intended to be readable and extensible.

For more about the command line and source code,
please go to [implementation Notes](Implementation_notes)

changeLog
----------
when stitching together if there is a gap in the "lock" scans then the non-lock peaks will be used in that gap.

Known Issues
------------
Peakstriner uses msfilereader that requires a dll from thermo xrawfile_2 this file is searched for in the 'lib' folder in Peakstrainer
if you run the python standalone, most likely some pyc files are created and thay may conflict with other windows version, so avoid running python on the distributed python standlone
