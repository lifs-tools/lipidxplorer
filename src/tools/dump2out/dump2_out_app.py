import wx
from  dump2out_frame import Dump2outFrame
from tools.dump2out.dump2out import suggest_result_file, check_and_relace_results

class dump2outApp(Dump2outFrame):
    def init(self,parent):
        Dump2outFrame.__init__(self,parent)

    def out_changed( self, event ):
        out_file = self.out_m_filePicker1.GetPath()
        result_file = suggest_result_file(out_file)
        self.new_m_textCtrl1.SetValue(result_file)

    def run_clicked( self, event ):
        out_file = self.out_m_filePicker1.GetPath()
        dump_file =  self.dump_m_filePicker11.GetPath()
        result_file = self.new_m_textCtrl1.GetValue()

        check_and_relace_results(out_file,dump_file,result_file)
        val = wx.MessageBox(
                f"Close the application ?\n\nThe file is complete \n {result_file}",
                "Close the application ?",
                wx.YES_NO|wx.STAY_ON_TOP,
            )
        if val == wx.YES:
            self.Close()

def main():
    app = wx.App()
    frame = dump2outApp(None)
    frame.Show(True)
    # start the applications
    app.MainLoop()


if __name__ == "__main__":
    main()
