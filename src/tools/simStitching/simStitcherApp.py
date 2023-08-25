"""
Created on 26.05.2017

@author: mirandaa
"""
from tools.simStitching.simStitcherGUI import SimStitcherFrame
import wx
from tools.simStitching.simStitcher import simStitcher
import os
import traceback


class mySimStitcherFrame(SimStitcherFrame):
    def __init__(self, parent):
        super(mySimStitcherFrame, self).__init__(parent)

    def browseClicked(self, event):
        #         doCompare = self.m_checkBox1.GetValue()
        #         simStitcher(filepath, doCompare)
        wildcard = "mzXML (*.mzXML)|*.mzxml;*MZXML"
        dlg = wx.FileDialog(
            self,
            message="Select your files",
            defaultDir=os.getcwd(),
            defaultFile="*.mzXML",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_MULTIPLE,
        )

        if dlg.ShowModal() == wx.ID_OK:
            self.path, file = os.path.split(dlg.GetPath())
            self.fileNames = dlg.GetFilenames()

            self.m_textCtrl1.SetValue(
                str(self.path).replace("\\\\", "\\")
                + " "
                + str(len(self.fileNames))
                + " files"
            )
            self.m_button2.Enable(True)
            self.m_gauge1.SetValue(0)

    def clickStart(self, event):
        status = self.run_all()
        if status:
            self.Close()

    def radioDefault(self, event):
        self.RadioCustom(event)

    def RadioCustom(self, event):
        self.m_textCtrl4.Enable(self.m_radioBtn41.GetValue())

    def checkCut(self, event):
        print("checkCut" + str(self.m_checkBox11.GetValue()))
        if self.m_checkBox11.GetValue():
            pass
        else:
            self.m_checkBox1.SetValue(False)
            self.checkScale(event)

    def checkScale(self, event):
        #         print 'checkScale' + str(self.m_checkBox1.GetValue())
        if self.m_checkBox1.GetValue():
            self.m_checkBox11.SetValue(True)
            self.checkCut(event)
        else:
            self.m_checkBox12.SetValue(False)
            self.checkAdapt(event)

    def checkAdapt(self, event):
        #         print 'checkAdapt' + str(self.m_checkBox12.GetValue())
        if self.m_checkBox12.GetValue():
            self.m_checkBox1.SetValue(True)
            self.checkScale(event)
        else:
            pass

        if self.m_checkBox12.GetValue():
            dlg = wx.MessageDialog(
                self,
                "This option is used to show SIM edges are not consistent\n please use with caution. ",
                "Warning",
                wx.OK | wx.ICON_WARNING,
            )
            dlg.ShowModal()
            dlg.Destroy()

    def get_simEdge(self):
        if self.m_radioBtn31.GetValue():
            return 5  # its default
        try:
            return float(self.m_textCtrl4.GetValue())
        except ValueError:
            dlg = wx.MessageDialog(
                self,
                "There was a problem with value {} \n it will not be used".format(
                    self.m_textCtrl4.GetValue()
                ),
                "Warning",
                wx.OK | wx.ICON_WARNING,
            )
            dlg.ShowModal()
            dlg.Destroy()
            raise ValueError("text must be a float")

    def run_all(self):
        #         self.path
        #         self.fileNames
        gaugeStep = 100.0 / (len(self.fileNames) + 1)

        scaleToCenterMass = self.m_checkBox1.GetValue()
        adaptByRegresion = self.m_checkBox12.GetValue()
        #         cut1 = self.m_checkBox11.GetValue()
        daltons = self.get_simEdge() if self.m_checkBox11.GetValue() else 0.0
        loglevel = int(self.m_slider1.GetValue())

        ststus = False
        for onefile in self.fileNames:
            filepath = str(self.path + "\\" + onefile)
            self.m_gauge1.SetValue(self.m_gauge1.GetValue() + gaugeStep)
            try:
                simStitcher(
                    filepath,
                    scaleToCenterMass,
                    adaptByRegresion,
                    daltons,
                    csvPath1=None,
                    loglevel=loglevel,
                )
                self.m_gauge1.SetValue(self.m_gauge1.GetValue() + gaugeStep)
                ststus = True
            except Exception as e:
                print(e)
                print(traceback.print_exc())
                dlg = wx.MessageDialog(
                    self,
                    "There was a problem processing the file {} \n{} \n{}".format(
                        onefile, e, traceback.print_exc()
                    ),
                    "Warning",
                    wx.OK | wx.ICON_WARNING,
                )
                dlg.ShowModal()
                dlg.Destroy()
                self.m_gauge1.SetValue(self.m_gauge1.GetValue() - gaugeStep)

        return ststus

    def filecChanged(self, event):
        filepath = self.m_filePicker1.GetPath()
        doCompare = self.m_checkBox1.GetValue()
        simStitcher(filepath, doCompare, self.callback)

    def callback(self, message):
        print(message)


def main():
    app = wx.App(False)
    frame = mySimStitcherFrame(None)
    frame.Show(True)
    app.MainLoop()


def openSimStitcher(parent):
    frame = mySimStitcherFrame(parent)
    frame.Show(True)


if __name__ == "__main__":
    main()
