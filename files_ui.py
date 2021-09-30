"""'
call lipidxplore using files
+ mfql files
+ mzxml files
lxp file
"""
import sys, os
import glob, configparser, re, fnmatch

import lximport, lxrun

# from https://gitlab.isas.de/lifs/lipidxplorer-web/-/tree/master/lipidxplorer-linux-128/src/main/python

# https://stackoverflow.com/questions/37265888/how-to-remove-a-section-from-an-ini-file-using-python-configparser
def insensitive_glob(baseDir, pattern):
    print(baseDir)
    print(pattern)
    paths = [
        os.path.join(baseDir, f)
        for f in os.listdir(baseDir)
        if f.lower().endswith(pattern)
    ]
    print(paths)
    return paths


#    def either(c):
#        return '[%s%s]' % (c.lower(), c.upper()) if c.isalpha() else c
#    return glob.glob(''.join(map(either, pattern)))


def files_UI(path, calctol=True):
    """generates the lxp project file for a given path

    Args:
        path (str): directory where to find the mfql and mzml files
        calctol (bool, optional): Automatically calculate the tolerences based on the peak data, simulates LX 2 funcitonality. Defaults to False.

    """
    # get lxp file

    LXP_files = insensitive_glob(path, ".lxp")

    if len(LXP_files) != 1:
        raise IOError(" there must be one and only one lxp file")
    LXPfile = LXP_files[0]

    MFQL_files = insensitive_glob(path, ".mfql")
    if len(MFQL_files) == 0:
        raise IOError(" there must at least one mfql file")

    # MZXML_files = insensitive_glob(path, '.mzxml')
    MZML_files = insensitive_glob(path, ".mzml")
    if len(MZML_files) == 0:
        raise IOError(" there must at least one mzxml or mzml file")

    # update lxp conten

    config = configparser.ConfigParser()

    config.read(LXP_files)

    basepath = path  # base directory

    config["project"]["importDir"] = basepath
    config["project"]["masterscanrun"] = os.path.join(basepath, "session.sc")
    config["project"]["masterscanimport"] = os.path.join(basepath, "session.sc")
    config["project"]["ini"] = os.path.join(basepath, "ImportSettings.ini")
    config["project"]["resultfile"] = os.path.join(basepath, "session-out.csv")

    if calctol:
        config["project"]["alignmentMethodMS"] = "calctol"
        config["project"]["alignmentMethodMSMS"] = "calctol"
        config["project"]["scanAveragingMethod"] = "calctol"

        config["project"]["optionalMStolerance"] = "5"
        config["project"]["optionalMStoleranceType"] = "ppm"
        config["project"]["optionalMSMStolerance"] = "5"
        config["project"]["optionalMSMStoleranceType"] = "ppm"

        # will ignore the following settings: but still read because they are needed for validation
        # ['MSresolution', #self.text_ctrl_SettingsSection_resolution_ms,
    # 	'MSMSresolution',# self.text_ctrl_SettingsSection_resolution_msms,
    # 	'MSresolutionDelta',# self.text_ctrl_SettingsSection_resDelta_ms,
    # 	'MSMSresolutionDelta',# self.text_ctrl_SettingsSection_resDelta_msms,
    # 	'MStolerance',# self.text_ctrl_SettingsSection_tolerance_ms,
    # 	'MSMStolerance',# self.text_ctrl_SettingsSection_tolerance_msms,
    # 	'selectionWindow',# self.text_ctrl_SettingsSection_selectionWindow,
    # 	'MSthreshold',# self.text_ctrl_SettingsSection_threshold_ms,
    # 	'MSMSthreshold',# self.text_ctrl_SettingsSection_threshold_msms,
    # 	'MSminOccupation',# self.text_ctrl_SettingsSection_occupationThr_ms,
    # 	'MSMSminOccupation'# self.text_ctrl_SettingsSection_occupationThr_msms
    # 	# ] update to p3 in https://gitlab.isas.de/lifs/lipidxplorer-web/-/blob/master/lipidxplorer-linux-13/src/main/python/files_ui.py

    # clear mfql section if there is one
    config.remove_section("mfql")
    config.add_section("mfql")

    for file in MFQL_files:
        filename = os.path.basename(file)
        config["mfql"][filename + "-name"] = filename
        config["mfql"][filename] = file

    session_lxp = os.path.join(path, "session.lxp")

    with open(session_lxp, "w") as configfile:
        config.write(configfile)
        fullpath = configfile.name

    lximport.lpdxImportCLI(fullpath)
    lxrun.lpdxImportCLI(fullpath)


if __name__ == "__main__":
    path = " ".join(sys.argv[1:])
    print(("path: {}".format(path)))

    files_UI(path, True)
