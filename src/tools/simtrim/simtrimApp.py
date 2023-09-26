import traceback
import wx
from tools.simtrim.standalone_resources.simtrim_form import simtrim_Frame
from tools.simtrim.simtrim import simtrim


class simtrimControler(simtrim_Frame):
    def __init__(self, parent):
        super(simtrimControler, self).__init__(parent)

    def run_clicked(self, event):
        event.Skip()
        file = self.m_filePicker10.GetPath()
        try:
            da = self.m_textCtrl3.GetValue()
            da = float(da)
            start_rt = self.m_textCtrl4.GetValue()
            start_rt = float(start_rt)
            stop_rt = self.m_textCtrl41.GetValue()
            stop_rt = float(start_rt)

            kwargs = {}
            kwargs["start_rt"] = start_rt
            kwargs["stop_rt"] = stop_rt

            simtrim(file, da, **kwargs)

        except Exception as e:
            print(e)
            print(traceback.print_exc())
            dlg = wx.MessageDialog(
                self,
                "There was a problem processing the file {} \n{} \n{}".format(
                    file, e, traceback.print_exc()
                ),
                "Warning",
                wx.OK | wx.ICON_WARNING,
            )
            dlg.ShowModal()
            dlg.Destroy()

        dlg = wx.MessageDialog(
            self,
            "Completed",
            "Completed",
            wx.OK,
        )
        dlg.ShowModal()
        dlg.Destroy()


def main():
    app = wx.App(False)
    frame = simtrimControler(None)
    frame.Show(True)
    app.MainLoop()


def openSimTrim(parent):
    frame = simtrimControler(parent)
    frame.Show(True)


if __name__ == "__main__":
    main()
