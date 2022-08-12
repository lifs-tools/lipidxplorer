import wx
from lx2_gui import Lx2_gui
from lx.project import Project
from collections import namedtuple

# TODO make this a dataclass
P_elem = namedtuple("P_element", "name index default", defaults=(None, None, ""))


class lx2_gui_controler(Lx2_gui):
    def __init__(self, parent, project=None):
        Lx2_gui.__init__(self, parent)
        self.project = project if project else Project()

    def load_project(self, path):
        self.project.load(path)
        self.project.testOptions()
        self.project.formatOptions()

        model_map = {
            "time_range1": P_elem("timerange", 0),
            "time_range2": P_elem("timerange", 1),
            "cal_masses_ms1": P_elem("MScalibration"),
            "cal_masses_ms2": P_elem("MSMScalibration"),
            "mass_range_ms1_1": P_elem("MSmassrange", 0),
            "mass_range_ms1_2": P_elem("MSmassrange", 1),
            "mass_range_ms2_1": P_elem("MSMSmassrange", 0),
            "mass_range_ms2_2": P_elem("MSMSmassrange", 1),
            # 'text_include'
            # 'text_exclude'
            "rep_rate_txt": P_elem("MSfilter", None, 0.7),
            # MSMSminOccupation is ignored
            # 'rep_rate_slider' done manually below
            "found_int_txt": P_elem("MSminOccupation"),
            # 'found_in_slider' done manually below
            # 'qc_count_txt'
            "signla_inty_ms1_txt": P_elem("MSthreshold"),
            "ms1_sig_inty_type": P_elem("MSthresholdType"),
            "signla_inty_ms2_txt": P_elem("MSMSthreshold"),
            "ms2_sig_inty_type": P_elem("MSMSthresholdType"),
            "prec_group_tol": P_elem("selectionWindow"),
            "cal_masses_ms1": P_elem("MScalibration"),
            "cal_masses_ms2": P_elem("MSMScalibration"),
            "ms1_low_mass_res_txt": P_elem("MSresolution"),
            "ms2_low_mass_res_txt": P_elem("MSMSresolution"),
            "ms1_res_gradient_txt": P_elem("MSresolutionDelta"),
            "ms2_res_gradient_txt": P_elem("MSMSresolutionDelta"),
            "ms1_tolerance_txt": P_elem("MStolerance"),
            "ms1_tolerance_type_choise": P_elem("MStoleranceType"),
            "ms2_tol_text": P_elem("MSMStolerance"),
            "ms2_tol_type_choise": P_elem("ms2_tol_type_choise"),
        }

        def proj_t2str(item, index, default=""):
            """helper for tuples"""
            return str(
                self.project.options_formatted.get(item, (default, default))[index]
            )

        for k, v in model_map.items():

            if v.index is None:
                value = self.project.options.get(v.name, v.default)
            else:
                value = proj_t2str(v.name, v.index, v.default)

            # special cases
            if k == "rep_rate_txt":
                value = int(value) * 100
                widget = getattr(self, "rep_rate_slider")
                widget.SetValue(value)
                value = str(value)
            elif k == "found_int_txt":
                value = int(value) * 100
                widget = getattr(self, "found_in_slider")
                widget.SetValue(value)
                value = str(value)
            elif k == "ms1_sig_inty_type" or k == "ms2_sig_inty_type":
                widget = getattr(self, k)
                idx = 0 if v == "absolute" else 1
                widget.SetSelection(idx)
                continue
            elif k == "ms1_tolerance_type_choise" or k == "ms2_tol_type_choise":
                widget = getattr(self, k)
                idx = 0 if v == "ppm" else 1
                widget.SetSelection(idx)
                continue

            widget = getattr(self, k)
            widget.SetValue(value)

    ################## add vals to controls

    ################ bind controls
    def ini_file_changed(self, event):
        path = self.ini_file.GetPath()
        self.load_project(path)

    def rep_rate_exited(self, event):
        try:
            num = int(self.rep_rate_txt.GetValue())
        except ValueError:
            wx.MessageBox(
                "Invalid repetition rate! \n must be between 0 - 100\n will reset to 70",
                "error",
                wx.OK | wx.ICON_ERROR,
            )
            num = 70

        if not 0 <= num <= 100:
            wx.MessageBox(
                "Invalid repetition rate! \n must be between 0 - 100\n will reset to 70",
                "error",
                wx.OK | wx.ICON_ERROR,
            )
            num = 70

        self.rep_rate_slider.SetValue(num)

    def rep_rate_txextenter(self, event):
        self.rep_rate_exited(event)  # delegate

    def rep_rate_slider_scroll(self, event):
        num = self.rep_rate_slider.GetValue()
        self.rep_rate_txt.SetValue(str(num))

    def found_in_exited(self, event):
        try:
            num = int(self.found_int_txt.GetValue())
        except ValueError:
            wx.MessageBox(
                "Invalid percentage rate! \n must be between 0 - 100\n will reset to 0",
                "error",
                wx.OK | wx.ICON_ERROR,
            )
            num = 0

        if not 0 <= num <= 100:
            wx.MessageBox(
                "Invalid percentage rate! \n must be between 0 - 100\n will reset to 0",
                "error",
                wx.OK | wx.ICON_ERROR,
            )
            num = 0

        self.found_in_slider.SetValue(num)

    def found_in_entered(self, event):
        self.found_in_exited(event)

    def found_in_slider_scrolled(self, event):
        num = self.found_in_slider.GetValue()
        self.found_int_txt.SetValue(str(num))


def main():
    app = wx.App()
    frame = lx2_gui_controler(None)
    frame.Show(True)
    # start the applications
    app.MainLoop()


if __name__ == "__main__":
    main()
