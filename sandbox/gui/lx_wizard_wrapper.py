import os
import wx
from lx_wizard import MyWizard1
import wx.propgrid as wxpg
from data import default_props


class LX_model:
    input_dir = None
    input_files = []
    mfql_dir = None
    mfql_files = []
    props = {}

    def populate_props(self):
        if not self.props:
            self.props = default_props


class Controller:
    def __init__(self, LX_model, LX_wizard):
        self.lx_model = LX_model
        self.lx_wizard = LX_wizard

    def update(self):
        self.update_m()
        self.update_v()

    def update_m(self):
        self.lx_model.input_dir = self.lx_wizard.m_dirPicker_input.GetPath()
        self.lx_model.input_files = self.getSpectraFiles(self.getInput())
        self.lx_model.mfql_dir = (
            self.lx_wizard.m_dirPicker_rootMFQLdir.GetPath()
        )
        self.lx_model.mfql_files = self.getMFQLFiles(self.getMFQLroot())
        self.lx_model.populate_props()

    def update_v(self):
        items = self.getSpectraFiles(self.getInput())
        self.lx_wizard.m_checkList1_inputfiles.AppendItems(items)
        mfqls = self.getMFQLFiles(self.getMFQLroot())
        self.lx_wizard.m_checkList2_mfqlfiles.AppendItems(mfqls)
        self.update_props()

    def update_props(self):
        # https://github.com/wxWidgets/Phoenix/blob/master/demo/PropertyGrid.py
        pg = self.lx_wizard.m_propertyGridManager_props
        props = self.lx_model.props
        if pg.GetFirst():
            return  # already filled
        for k in props:
            v = str(props[k])
            pg.Append(wxpg.StringProperty(k, value=v))

    def getInput(self):
        return self.lx_model.input_dir

    def getSpectraFiles(self, path):
        # extensions = ['.mzXML', '.mzML','.raw']
        filenames = []
        for dirpath, dirnames, filenames in os.walk(path):
            filenames = filenames
            break
        f = [
            fn
            for fn in filenames
            if fn[-4:] == ".raw" or fn[-5:] == ".mzML" or fn[-6:] == ".mzXML"
        ]
        return f

    def getMFQLroot(self):
        return self.lx_model.mfql_dir

    def getMFQLFiles(self, path):
        f = []
        for dirpath, dirnames, filenames in os.walk(path):
            f.extend([fn for fn in filenames if fn[-5:] == ".mfql"])
        return f


class LX_wizard(MyWizard1):
    def __init__(self):
        super(LX_wizard, self).__init__(None)
        self.lx_controller = Controller(LX_model(), self)

    def wiz_finished(self, event):
        print("finised")

    def page_changed(self, event):
        self.lx_controller.update()


def run_lx_wizard():
    app = wx.App(False)
    lx_wizard = LX_wizard()
    lx_wizard.RunWizard(lx_wizard.m_pages[0])
    lx_wizard.Destroy()
    app.MainLoop()


if __name__ == "__main__":
    run_lx_wizard()
