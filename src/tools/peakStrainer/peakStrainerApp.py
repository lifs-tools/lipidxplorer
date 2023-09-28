"""
Created on 04.05.2017

@author: mirandaa
"""
import sys, os

sys.path.append(os.environ.get("SRC_DIR"))

from tools.peakStrainer.utils.peakStrainerGUI import MyFrame2
import wx
import os
import traceback
from tools.peakStrainer.peakStrainer import *

from tools.reorderScans.reorderScans import openReorderScans as reorderscans
from tools.simStitching.simStitcherApp import openSimStitcher as simStitcher

import pandas as pd


def main():
    app = wx.App(False)
    frame = MyFrame(None)
    frame.Show(True)
    app.MainLoop()


def openPeakStrainer(parent):
    frame = MyFrame(parent)
    frame.Show(True)


class MyFrame(MyFrame2):
    def __init__(self, parent):
        super(MyFrame, self).__init__(parent)

    # Virtual event handlers, overide them in your derived class
    def clickedBrowse(self, event):
        wildcard = "Thermo raw (*.raw)|*.raw;*RAW"
        dlg = wx.FileDialog(
            self,
            message="Select your files",
            defaultDir=os.getcwd(),
            defaultFile="*.raw",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_MULTIPLE,
        )

        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            if len(paths) > 0:
                self.path, file = os.path.split(paths[0])
                self.fileNames = dlg.GetFilenames()

                self.m_textCtrl1.SetValue(
                    str(self.path).replace("\\\\", "\\")
                    + " "
                    + str(len(self.fileNames))
                    + " files"
                )
                # ----
                self.m_buttonFinish.Enable(True)

    def clickOpenSpecReord(self, event):
        reorderscans(self)
        event.EventObject.Destroy()
        # raise SystemExit

    def radioBin(self, event):
        self.m_staticText23.Enable(self.m_radioBtn1.GetValue())
        #         ----
        self.m_staticText231.Enable(self.m_radioBtn4.GetValue())
        self.m_staticText241.Enable(self.m_radioBtn4.GetValue())
        self.m_textCtrl61.Enable(self.m_radioBtn4.GetValue())
        self.m_staticText2511.Enable(self.m_radioBtn4.GetValue())
        self.m_textCtrl711.Enable(self.m_radioBtn4.GetValue())
        self.m_staticText381.Enable(self.m_radioBtn4.GetValue())
        self.m_checkBox11.Enable(self.m_radioBtn4.GetValue())
        self.m_staticText251.Enable(self.m_radioBtn4.GetValue())
        self.m_textCtrl71.Enable(self.m_radioBtn4.GetValue())
        self.m_staticText38.Enable(self.m_radioBtn4.GetValue())
        self.m_staticText2411.Enable(self.m_radioBtn4.GetValue())
        self.m_textCtrl611.Enable(self.m_radioBtn4.GetValue())

    def radioPre(self, event):
        self.m_staticText14.Enable(self.m_radioBtn11.GetValue())
        self.m_spinCtrl2.Enable(self.m_radioBtn11.GetValue())
        self.m_staticText15.Enable(self.m_radioBtn11.GetValue())
        self.m_spinCtrl1.Enable(self.m_radioBtn11.GetValue())
        self.m_staticText22.Enable(self.m_radioBtn11.GetValue())

    def checkScanRet(self, event):
        self.m_textCtrl2.Enable(self.m_checkBox5.GetValue())
        self.m_textCtrl3.Enable(self.m_checkBox5.GetValue())

    def checkScanHead(self, event):
        self.m_textCtrl4.Enable(self.m_checkBox6.GetValue())
        self.m_radioBox1.Enable(self.m_checkBox6.GetValue())

    def checkRoundCollision(self, event):
        self.m_spinCtrl11.Enable(self.m_checkBox61.GetValue())

    def checkOutcsv(self, event):
        self.m_dirPicker1.Enable(self.m_checkBox8.GetValue())

    def checkoutLog(self, event):
        self.m_slider1.Enable(self.m_checkBox9.GetValue())

    def checkOutConf(self, event):
        self.m_filePicker2.Enable(self.m_checkBox10.GetValue())

    def radioFil(self, event):
        self.m_staticline1812.Enable(self.m_radioBtn111.GetValue())
        self.m_spinCtrl21.Enable(self.m_radioBtn111.GetValue())
        self.m_staticText26.Enable(self.m_radioBtn111.GetValue())
        # signal to noise ratio
        self.m_staticline18121.Enable(self.m_radioBtn111.GetValue())
        self.m_textCtrl612.Enable(self.m_radioBtn111.GetValue())

    def clickedFinish(self, event):
        self.m_notebook1.SetSelection(self.m_notebook1.GetPageCount() - 1)
        self.run_all()

    def clickedSimStitcher(self, event):
        self_ = self
        simStitcher(self)
        # TODO fix this bug, for now I only know this works, but throws dead object error
        # the identity of self gets lost
        event.EventObject.Destroy()

    # ===========================================================================
    # Backend
    # ===========================================================================

    def run_all(self):
        self.path
        self.fileNames

        for onefile in self.fileNames:
            filepath = str(onefile)
            self.m_statuslog.WriteText("Starting filepath " + filepath + "\n")
            try:
                self.run_once(filepath, onefile)
            except Exception as e:
                self.m_statuslog.WriteText(
                    "\n *** THERE WAS A PROBLEM PROCESSING THE FILE *** \n"
                    + filepath
                    + "\n"
                )
                self.m_statuslog.WriteText(str(e))
                self.m_statuslog.WriteText(str(traceback.print_exc()))
                print(traceback.print_exc())

            self.m_statuslog.WriteText("finished filepath " + filepath + "\n")
            self.m_statuslog.WriteText("==========================" + "\n")

        self.m_statuslog.WriteText(
            "finished All " + str(len(self.fileNames)) + " files \n"
        )
        # self.m_buttonFinish.Enable(True)

        if self.m_checkBox2.GetValue():
            reorderscans(self, self.path)

    #         raise SystemExit

    def getLoglevel(self):
        if not self.m_checkBox9.GetValue():
            return logging.WARNING
        elif self.m_slider1.GetValue() == 1:
            return logging.CRITICAL
        elif self.m_slider1.GetValue() == 2:
            return logging.ERROR
        elif self.m_slider1.GetValue() == 3:
            return logging.WARNING
        elif self.m_slider1.GetValue() == 4:
            return logging.INFO
        elif self.m_slider1.GetValue() == 5:
            return logging.DEBUG

    def statusLog(self, text):
        self.m_statuslog.WriteText(text + "\n")

    def getCSVpath_file(self, fileName):
        Base_fileName = fileName[:-4]
        return self.m_dirPicker1.GetPath() + "\\" + Base_fileName

    def run_once(self, filepath, rawfilename):
        log.setLevel(self.getLoglevel())
        if log.level == logging.DEBUG:
            log.addHandler(logging.StreamHandler())  # log to console
        if self.m_checkBox9.GetValue():
            logging.basicConfig(filename=filepath[:-4] + ".log", filemode="w")

        log.debug("Start %f", time.process_time())

        self.statusLog("Read and select scans from raw file...")
        dropElbowIIT = self.m_checkBox611.GetValue()
        scans = ThermoRawfile2Scans(filepath, dropElbowIIT)
        # get the maximum number of scans
        df = pd.DataFrame(scans)
        max_count = df.iloc[:, 1].value_counts().max()

        if self.m_checkBox8.GetValue():
            ThermoRawfile2Scans_csv(
                scans, self.getCSVpath_file(rawfilename) + "-raw.csv"
            )

        # scans = filterScanBy_first(scans)

        if self.m_checkBox61.GetValue():
            dp = int(self.m_spinCtrl11.GetValue())
            scans = roundCollisionEnergy(scans, dp)

        if self.m_checkBox5.GetValue():
            scans = filterScanBy_retentionTime(
                scans,
                float(self.m_textCtrl2.GetValue()),
                float(self.m_textCtrl3.GetValue()),
            )
        # NOTE use try catch notify to validate input
        if self.m_checkBox6.GetValue():
            scans = filterScanBy_filterline(
                scans,
                self.m_textCtrl4.GetValue(),
                self.m_radioBox1.GetSelection() == 0,
            )
        if self.m_checkBox61.GetValue():
            scans = removeLockFromHeader(scans)
        """ filtering by scan
        scans = filterScanBy_samples(scans, step_size = 3)
        """

        self.statusLog("Merge scans based on Header...")
        # Note: mergePeaksOnFilterline_withRandom to generate testing data
        filterLines = mergePeaksOnFilterline(scans)
        if self.m_checkBox8.GetValue():
            filterlinePeaks_csv(
                filterLines,
                self.getCSVpath_file(rawfilename)
                + "-mergePeaksOnFilterline.csv",
            )

        self.statusLog("Run Preliminary filter...")
        if self.m_radioBtn10.GetValue():
            preFiltered_filterlines = {
                k: preliminaryFilter(v) for k, v in filterLines.items()
            }
        if self.m_radioBtn11.GetValue():
            preFiltered_filterlines = {
                k: preliminaryFilter(
                    v, self.m_spinCtrl2.GetValue(), self.m_spinCtrl1.GetValue()
                )
                for k, v in filterLines.items()
            }
        # preFiltered_filterlines = {k: preliminaryReductionFilter(v) for k, v in filterLines.iteritems()}
        if self.m_checkBox8.GetValue():
            filterlinePeaks_csv(
                preFiltered_filterlines,
                self.getCSVpath_file(rawfilename) + "-preliminaryFilter.csv",
            )

        self.statusLog("Generate bins ...")
        """ create bins for peaks
        filterlines_withBins = {k: generateBins_decimalPlaces(v) for k, v in filterLines.iteritems()}
        filterlines_withBins = {k: generateBins_resolution(v) for k, v in filterLines.iteritems()}
        filterlines_withBins = {k: generateBins_theoreticalResolution(v) for k, v in preFiltered_filterlines.iteritems()}
        filterlines_withBins = {k: generateBins_resolutionPowerFunc(v,a,b) for k, v in preFiltered_filterlines.iteritems()} # 5408000.0, 2096000.0
        """
        if self.m_radioBtn9.GetValue():
            filterlines_withBins = {
                k: generateBins_resolutionPowerFunc(v, 5408000.0, 0.5)
                for k, v in filterLines.items()
            }  # values as per Kai S.
        if self.m_radioBtn1.GetValue():
            filterlines_withBins = {
                k: generateBins_theoreticalResolution(v)
                for k, v in preFiltered_filterlines.items()
            }
        if self.m_radioBtn4.GetValue():
            #     for different function for ms and for msms
            a = float(self.m_textCtrl61.GetValue())
            b = float(self.m_textCtrl71.GetValue())
            aa = float(self.m_textCtrl611.GetValue())
            bb = float(self.m_textCtrl711.GetValue())
            filterlines_withBins_ms = {
                k: generateBins_resolutionPowerFunc(v, a, b)
                for k, v in filterLines.items()
                if " ms " in k
            }
            filterlines_withBins_msms = {
                k: generateBins_resolutionPowerFunc(v, aa, bb)
                for k, v in filterLines.items()
                if " ms " not in k
            }
            filterlines_withBins = filterlines_withBins_ms
            filterlines_withBins.update(filterlines_withBins_msms)
            print(len(filterlines_withBins))

        if self.m_checkBox8.GetValue():
            filterlinePeaks_csv(
                filterlines_withBins,
                self.getCSVpath_file(rawfilename) + "-generateBins.csv",
            )

        self.statusLog("Merge bins ...")
        if self.m_checkBox11.GetValue():
            filterlines_withBins = {
                k: alterBins_mergeOverlap(v)
                for k, v in filterlines_withBins.items()
            }
        if self.m_checkBox8.GetValue():
            filterlinePeaks_csv(
                filterlines_withBins,
                self.getCSVpath_file(rawfilename) + "-mergeBins.csv",
            )

        self.statusLog("Sort peaks into bins ...")
        """ put each mass in a bin
        filterlines_inBins = {k: sortMassIn_sortWindow(v) for k, v in filterlines_withBins.iteritems()}
        filterlines_inBins = {k: sortMassIn_FirstBin(v) for k, v in filterlines_withBins.iteritems()}
        filterlines_inBins = {k: sortMassIn_NarrowestBin(v) for k, v in filterlines_withBins.iteritems()}
        """
        filterlines_inBins = {
            k: sortMassIn_FirstBin(v) for k, v in filterlines_withBins.items()
        }
        if self.m_checkBox8.GetValue():
            filterlinePeaks_csv(
                filterlines_inBins,
                self.getCSVpath_file(rawfilename) + "-sortMassIn.csv",
            )

        self.statusLog("Generate aggregate bin data ...")
        filterlines_binData = {
            k: aggregateBinData(v, max_count)
            for k, v in filterlines_inBins.items()
        }
        if self.m_checkBox8.GetValue():
            filterlineBins_csv(
                filterlines_binData,
                self.getCSVpath_file(rawfilename) + "-aggregateBinData.csv",
            )

        self.statusLog("Filter out bins ...")
        if self.m_radioBtn101.GetValue():
            filterlines_filtered = {
                k: filterBins(v) for k, v in filterlines_binData.items()
            }
        if self.m_radioBtn111.GetValue():
            minRepetitionRate = self.m_spinCtrl21.GetValue() * 0.01
            minSingnal2Noise = float(self.m_textCtrl612.GetValue())
            filterlines_filtered = {
                k: filterBins(
                    v,
                    minRepetitionRate=minRepetitionRate,
                    minSignal2Noise=minSingnal2Noise,
                )
                for k, v in filterlines_binData.items()
            }

        if self.m_checkBox8.GetValue():
            filterlineBins_csv(
                filterlines_filtered,
                self.getCSVpath_file(rawfilename) + "-filteredBins.csv",
            )

        self.statusLog("Recall Peaks from bins ...")
        filtered_peaks = {
            k: bins2Peaks(v, filterlines_inBins[k])
            for k, v in filterlines_filtered.items()
        }
        if self.m_checkBox8.GetValue():
            filterlinePeaks_csv(
                filtered_peaks,
                self.getCSVpath_file(rawfilename) + "-mzXMLdata.csv",
            )

        # can't use filtered bins in mzxml because it is not readable by seems
        filtered_bins = {
            k: formatPeaks(v) for k, v in filterlines_filtered.items()
        }

        self.statusLog("Write mzXML file")
        newfilename = filepath[:-4] + ".mzXML"
        log.info("Writing results to %s", newfilename)
        filtered_bins_r = reorder4lipidxplorer(filtered_bins)
        write2templateMzXML(newfilename, filtered_bins_r)

        log.debug("finish %f", time.process_time())


if __name__ == "__main__":
    main()
