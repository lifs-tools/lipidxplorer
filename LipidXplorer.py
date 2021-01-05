import os
from lx.gui import lpdxGUI
import wx

class MyApp(wx.App):

	def OnInit(self):
		self.frame = lpdxGUI.LpdxFrame(None, -1, "",
				rawimport = False,
				lipidxplorer = True,
				version = "1.3.2")
		self.frame.SetIcon(wx.Icon("lx/stuff/lipidx_ico2.ico", wx.BITMAP_TYPE_ICO))
		self.frame.Show(True)
		self.frame.Center()
		self.SetTopWindow(self.frame)
		return True

def main():

	app = MyApp(0)
	os.chdir(os.getcwd())
	app.MainLoop()
	wx.Exit()
	## end of the software

if __name__ == "__main__":
	main()
