'''
Created on 28.04.2017

@author: mirandaa
'''
from .reorderScansUI import MyFrame1
import wx
import xml.etree.ElementTree as ET


def main():
    app = wx.App(False)
    frame = MyFrame(None)
    frame.Show(True)
    app.MainLoop()
    
#     -----------------------
def getScanHeaders(filePath):
        #     TODO:handle different namespaces of mzxml 
    namespaces = {'xmlns': 'http://sashimi.sourceforge.net/schema_revision/mzXML_3.0'}
    ET.register_namespace('', 'http://sashimi.sourceforge.net/schema_revision/mzXML_3.0')
    tree = ET.parse(filePath)
 
    scanElems = tree.findall('.//xmlns:scan', namespaces)
    
    scans = []
    for scan in scanElems:
#             scanNo = int(scan.attrib['num'])
#         scanNo = scan.attrib['num'].zfill(5)
#  scan number ges confused with other values so its not good
# maybe add zerowidth space to solve '\u200b'
        filterLine = scan.attrib['filterLine']
        scans.append(filterLine)

    return scans


def saveFile(filePath, destination_model):
       #     TODO:handle different namespaces of mzxml 
    namespaces = {'xmlns': 'http://sashimi.sourceforge.net/schema_revision/mzXML_3.0'}
    ET.register_namespace('', 'http://sashimi.sourceforge.net/schema_revision/mzXML_3.0')
    tree = ET.parse(filePath)
 
    msRunElement = tree.find('.//xmlns:msRun', namespaces)
    scanElems = msRunElement.findall('.//xmlns:scan', namespaces)
    
    for scan in scanElems:
        msRunElement.remove(scan)
    
    for selectionLine in destination_model:
        for scan in scanElems:
            scanLine = scan.attrib['filterLine']
            if  selectionLine == scanLine:
                msRunElement.append(scan)
                break
    

    newfilename = filePath[:-4]+ '-ordered.mzXML'
    tree.write(newfilename, encoding='ISO-8859-1', xml_declaration=True)


class MyFrame(MyFrame1):
    
    def __init__(self, parent):
        super(MyFrame, self).__init__(parent)
        self.lastEntry =None
        self.sourceModel = []
        self.destinationModel = []
        self.selectionModel = []
        self.sublist = []
        self.searchIncluding =True
        
    
    # Virtual event handlers, overide them in your derived class
    def updateFile( self, event ):
        self.sourceModel = getScanHeaders(self.m_filePicker1.GetPath())
        self.sublist = self.sourceModel
        self.selectionModel = self.sublist
        self.m_textCtrl_1.SetValue(str(len(self.selectionModel)))
        self.m_listBox1.Set(self.selectionModel)
        self.destinationModel = []
        self.m_listBox2.Set(self.destinationModel)
        self.clear_subandsearch(None)
        
    
    def updateSourceList( self, event ):
        if not self.m_searchCtrl2.GetValue():
            self.selectionModel = self.sublist
        else: 
            if self.searchIncluding:
                self.selectionModel = [item for item in self.sublist if self.m_searchCtrl2.GetValue() in item]
            else:
                self.selectionModel = [item for item in self.sublist if self.m_searchCtrl2.GetValue() not in item]
            
        self.m_textCtrl_1.SetValue(str(len(self.selectionModel)))
        self.m_listBox1.Set(self.selectionModel)
    
    def toggleSearch( self, event ):
        self.searchIncluding = not self.searchIncluding 
        if self.searchIncluding:
            self.m_searchCtrl2.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
        else:
            self.m_searchCtrl2.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_INFOBK ) )
        self.m_searchCtrl2.Refresh()
        self.updateSourceList( None)
        
    
    def makeSublist( self, event ):
        self.sublist = self.selectionModel
        self.m_searchCtrl2.Clear()
        
    def clear_subandsearch( self, event ):
        self.sublist = self.sourceModel
        self.selectionModel = self.sublist
        self.m_listBox1.Set(self.selectionModel)
        self.m_searchCtrl2.Clear()
        self.searchIncluding = False # false because next call will flip it  and update gui
        self.toggleSearch(None)
    
    def addToTargetList( self, event ):
        self.destinationModel = self.destinationModel + self.selectionModel
        self.m_textCtrl_2.SetValue(str(len(self.destinationModel)))
        self.m_listBox2.Set(self.destinationModel)
    
    def removeFromTargetList( self, event ):
        self.destinationModel = [val for idx, val in enumerate(self.destinationModel) if idx not in self.m_listBox2.GetSelections()]
        self.m_textCtrl_2.SetValue(str(len(self.destinationModel)))
        self.m_listBox2.Set(self.destinationModel)
        
    
    def finish( self, event ):
        saveFile(self.m_filePicker1.GetPath(), self.destinationModel)
        raise SystemExit


if __name__ == '__main__':
    main()
    