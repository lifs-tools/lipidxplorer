import wx
from simtrim_form import simtrim_Frame


class simtrimControler(simtrim_Frame):
    def __init__(self, parent):
        super(simtrimControler, self).__init__(parent)
	
    def run_clicked( self, event ):
        event.Skip()

def openSimtrimControler(parent):
    frame = simtrimControler(parent)
    frame.Show(True)

def main():
    app = wx.App(False)
    frame = simtrimControler(None)
    frame.Show(True)
    app.MainLoop()


if __name__ == "__main__":
    main()