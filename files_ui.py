''''
call lipidxplore using files
+ mfql files
+ mzxml files
lxp file
'''
import sys, os
import glob, configparser, re, fnmatch

import lximport, lxrun
# from https://gitlab.isas.de/lifs/lipidxplorer-web/-/tree/master/lipidxplorer-linux-128/src/main/python

#https://stackoverflow.com/questions/37265888/how-to-remove-a-section-from-an-ini-file-using-python-configparser
def insensitive_glob(baseDir, pattern):
    print baseDir
    print pattern
    paths = [os.path.join(baseDir, f) for f in os.listdir(baseDir) if f.lower().endswith(pattern)]
    print paths
    return paths
#    def either(c):
#        return '[%s%s]' % (c.lower(), c.upper()) if c.isalpha() else c
#    return glob.glob(''.join(map(either, pattern)))


def files_UI(path):
    # get lxp file

    LXP_files = insensitive_glob(path,'.lxp')

    if len(LXP_files) != 1 :
        raise IOError(' there must be one and only one lxp file')
    LXPfile =LXP_files[0]

    MFQL_files = insensitive_glob(path,'.mfql')
    if len(MFQL_files) == 0:
        raise IOError(' there must at least one mfql file')

    MZXML_files = insensitive_glob(path, '.mzxml')
    MZML_files = insensitive_glob(path, '.mzml')
    if len(MZXML_files) == 0 and len(MZML_files) == 0:
        raise IOError(' there must at least one mzxml or mzml file')


    # update lxp conten

    config = configparser.ConfigParser()

    config.read(LXP_files)

    basepath = path  # base directory

    config['project']['importDir'] = basepath
    config['project']['masterscanrun'] = os.path.join(basepath, 'session.sc')
    config['project']['masterscanimport'] = os.path.join(basepath, 'session.sc')
    config['project']['ini'] = os.path.join(basepath, 'ImportSettings.ini')
    config['project']['resultfile'] = os.path.join(basepath, 'session-out.csv')

    # clear mfql section if there is one
    config.remove_section('mfql')
    config.add_section('mfql')

    for file in MFQL_files:
        filename = os.path.basename(file)
        config['mfql'][filename  + "-name"] = filename
        config['mfql'][filename] = file

    session_lxp = os.path.join(path,'session.lxp')

    with open(session_lxp,'w') as configfile:
       config.write(configfile)
       fullpath = configfile.name


    lximport.lpdxImportCLI(fullpath)
    lxrun.lpdxImportCLI(fullpath)


if __name__ == '__main__':
    path  = ' '.join(sys.argv[1:])
    print('path: {}'.format(path))

    files_UI(path)
