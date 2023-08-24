'''
Created on 09.03.2017

@author: mirandaa
'''

import logging
from subprocess import call
import sys, os, re
import xml.etree.ElementTree as ET

def getFilePath():
    #TODO: read from command line
    #get the file path if its valid
    filePath = sys.argv[1]
    absFilePath = os.path.abspath(filePath) 
    logging.info('filePath '+absFilePath ) 
    return absFilePath 


def getProteoWizardPath():
    #my own fixed path
    # TODO: make it a resource\
    path = 'C:\\Program Files\\ProteoWizard\\ProteoWizard 3.0.10505'
    logging.info('proteowizard path '+path)
    return path


def callMSConvert(filepath):
    proteoWizardPath = getProteoWizardPath()
    msConvert = proteoWizardPath + '\\msConvert.exe'
    outputpath = os.path.dirname(filepath)
    splitext = os.path.splitext(filepath)
    call([msConvert, filepath, '--mzXML', '--inten64','--filter', '"peakPicking true 1-"', '--outdir', outputpath])
    return splitext[0]+'.mzXML'


def replace(file_path, pattern, subst):
    from tempfile import mkstemp
    from shutil import move
    from os import remove, close

    #Create temp file
    fh, abs_path = mkstemp()
    with open(abs_path,'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    close(fh)
    #Remove original file
    remove(file_path)
    #Move new file
    move(abs_path, file_path)


def adatpToMZXML3(newFilepath):
    ET.register_namespace('', 'http://sashimi.sourceforge.net/schema_revision/mzXML_3.2')
    tree = ET.parse(newFilepath)
    tag = tree.getroot().tag
    namespace = re.match('\{(.*)\}', tag).group(0)
    
    namespaces = {'ns1':namespace[1:-1]}
 
    scanElems = tree.findall('.//ns1:scan', namespaces)
    
    for scan in scanElems:
        msLevel = str(scan.attrib['msLevel'])
        if msLevel != '1':
            precursorMz = str(scan.find('.//ns1:precursorMz', namespaces).text)
            activationMethod = scan.find('.//ns1:precursorMz', namespaces).attrib['activationMethod']
        else:
            precursorMz = ''
            activationMethod = ''
            
        polarity = str(scan.attrib['polarity'])
        psudofilterLine = '{} {} {} {}'.format(precursorMz, activationMethod, msLevel, polarity)
        scan.attrib['filterLine'] = psudofilterLine
        
    logging.info('Finished adapting')
    tree.write(newFilepath)
    logging.info('File written to ', newFilepath )
    
# TODO: make this with elementree
    logging.info('Manually changing namespace ')
    #http://sashimi.sourceforge.net/schema_revision/mzXML_3.0
    #http://sashimi.sourceforge.net/schema_revision/mzXML_3.2
    replace(newFilepath, 'http://sashimi.sourceforge.net/schema_revision/mzXML_3.2', 'http://sashimi.sourceforge.net/schema_revision/mzXML_3.0')

if __name__ == '__main__':
       
    filepath = getFilePath()
    newFilepath = callMSConvert(filepath)
    adatpToMZXML3(newFilepath)