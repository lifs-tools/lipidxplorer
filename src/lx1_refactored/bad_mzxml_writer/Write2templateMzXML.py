import copy
import os
import sys
import xml.etree.ElementTree as ET
from array import array
from base64 import b64encode


def _encodePeaks(masses, intens):
    peak_list = []
    for mass, intens in sorted(zip(masses, intens)):
        peak_list.append(mass)
        peak_list.append(intens)
    
    peaks = array('f',peak_list)
    if sys.byteorder != 'big':
        peaks.byteswap()
        
    encoded = b64encode(peaks).decode("utf-8")
    return encoded

def getMZXMLEncondedScans(filePath):
    #     TODO:handle different namespaces of mzxml 
    namespaces = {'xmlns': 'http://sashimi.sourceforge.net/schema_revision/mzXML_3.0'}
    ET.register_namespace('', 'http://sashimi.sourceforge.net/schema_revision/mzXML_3.0')
    tree = ET.parse(filePath)
 
    scanElems = tree.findall('.//xmlns:scan', namespaces)
    
    rawscans = []
    for scan in scanElems:
        encodedPeaks = scan.find('.//xmlns:peaks', namespaces).text
        scanNo = int(scan.attrib['num'])
        filterLine = scan.attrib['filterLine']
        retTime =  scan.attrib['retentionTime']
        object = (scanNo, filterLine, encodedPeaks, retTime)
        rawscans.append(object)

    return zip(*rawscans)


def write2templateMzXML(newfilename, df):
    #NOTE https://git.mpi-cbg.de/labShevchenko/PeakStrainer/-/blob/master/utils/peakStrainer_util.py
    namespaces = {'xmlns': 'http://sashimi.sourceforge.net/schema_revision/mzXML_3.0'}
    ET.register_namespace('', 'http://sashimi.sourceforge.net/schema_revision/mzXML_3.0')
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    tree = ET.parse(scriptPath+'\\template.mzXML')
    
    msRunElement = tree.find('.//xmlns:msRun', namespaces)
    scanTemplete = msRunElement.find('.//xmlns:scan', namespaces)
    
    idx = 0
    for filter_string, gdf in df.groupby('filter_string'):
        idx +=1
        (masses, intens) = gdf['mz'], gdf['inty'] 
        newScan = copy.deepcopy(scanTemplete)
        newScan.attrib['filterLine'] = filter_string
        newScan.attrib['peaksCount'] = str(len(masses))
        newScan.attrib['num']=str(idx+1)
        newScan.attrib['scanType']='ms2' if gdf.iloc[0].at['precursor_mz'] == 0 else 'ms1' 
        
        msLevel = 1#  if ' ms ' in scan else 2
        if msLevel == 1:
            newScan.remove(newScan.find('.//xmlns:precursorMz', namespaces))
        else:
            raise NotImplementedError('not implemented yet')
            precursorMz = newScan.find('.//xmlns:precursorMz', namespaces)
            match = re.match( r'.* (.*)@(...)', scan, re.M|re.I)
            precursorMz.attrib['activationMethod'] = match.group(2)
            precursorMz.text = match.group(1)

        newScan.attrib['msLevel'] = str(msLevel)
        newScan.attrib['polarity'] = str(gdf.iloc[0].at['polarity'])
        newScan.attrib['retentionTime'] = 'PT{}S'.format(0.0+idx)
        
        encodedPeaks = _encodePeaks(masses, intens)
        newScan.find('.//xmlns:peaks', namespaces).text = encodedPeaks
        msRunElement.append(newScan)
    
    msRunElement.remove(scanTemplete)
    
    tree.write(newfilename, encoding='ISO-8859-1', xml_declaration=True)
    return tree
