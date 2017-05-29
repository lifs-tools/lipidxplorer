from lx.gui import lpdxGUI
import wx

class MyApp(wx.App):

	def OnInit(self):
		self.frame = lpdxGUI.LpdxFrame(None, -1, "",
				rawimport = False,
				lipidxplorer = True,
				version = "1.2.7")
		self.frame.Show(True)
		self.frame.Center()
		self.SetTopWindow(self.frame)
		return True

def main():

	app = MyApp(0)
	app.MainLoop()
	## end of the software

if __name__ == "__main__":
	main()
