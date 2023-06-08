import wx
from  dump2out_frame import Dump2outFrame

class dump2outApp(Dump2outFrame):
    def init(self,parent):
        Dump2outFrame.__init__(self,parent)



def main():
    app = wx.App()
    frame = dump2outApp(None)
    frame.Show(True)
    # start the applications
    app.MainLoop()


if __name__ == "__main__":
    main()
