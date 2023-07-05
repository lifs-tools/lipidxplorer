Communications
--

## Meetings
### 17th May 2023
* Jacobo, Sofia, HongKee
* Discussed how to proceed for LipidExplorer 2 development
* Jacobo explained the structure of the software and pipeline process
* Sofia added detailed information for additional types of data which are tSIM and MS2
* We setup https://git.mpi-cbg.de/labShevchenko/lx2 for the repository
* Jacobo and HongKee arrange the regular meeting for update every week


### 25th May 2023
* Jacobo, HongKee
* Restructure of project folders
* We rearranged the folders and handled legacy codes
* Better test environment needs to be setup
* The clean repo is located in https://git.mpi-cbg.de/labShevchenko/lx2/-/tree/dev
* Complete the test scenarios until the next week


### 7th June 2023
* Jacobo, HongKee
* @moon: make a main GUI panel with lx2, lx1, tools tabs
* @mirandaa: dump2out.py in tools with test routines and test dataset


### 21st June 2023
* Jacobo, HongKee
* @moon: add todo points for Jacobo can easily find the entries to add appropriate modules for source and test codes
* @mirandaa: implement method calling flow in `src/lx/lpdxGUI.py` according to the user specified version and fix failures in tests


### 5th July 2023
* Jacobo, HongKee
* The test framework is setup
* CI/CD is configured for automatic release generation
* @mirandaa: create json format intermediate files in order to be validated
* @moon: as soon as json files are provided, develop the web interface for validation
