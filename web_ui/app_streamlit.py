import streamlit as st
from lx.project import Project
from enum import Enum


class ToleranceEnum(Enum):
    ppm = 0
    Da = 1


class ThresholdEnum(Enum):
    relative = 0
    absolute = 1


model_keys = {
    # underscore indicates key is not same as in the project file
    "selectionWindow": "",
    "_timerange0": "",
    "_timerange1": "",
    "MScalibration": "",
    "MSMScalibration": "",
    "_MSmassrange0": "",
    "_MSmassrange1": "",
    "_MSMSmassrange0": "",
    "_MSMSmassrange1": "",
    # below to be used to calucalte resolution delta given two resolution points
    # "_MSresolution0": "",
    # "_MSresolution1": "",
    # "_MSMSresolution0": "",
    # "_MSMSresolution1": "",
    # "_MSresolution_MZ0": "",
    # "_MSresolution_MZ1": "",
    # "_MSMSresolution_MZ0": "",
    # "_MSMSresolution_MZ1": "",
    "MSresolutionDelta": "",
    "MSMSresolutionDelta": "",
    "MStolerance": "",
    "MSMStolerance": "",
    "_MStolerance_v": "",
    "_MSMStolerance_v": "",
    "_MStolerance_unit": ToleranceEnum.ppm.name,
    "_MSMStolerance_unit": ToleranceEnum.ppm.name,
    "MSthreshold": "",
    "MSthresholdType": ThresholdEnum.relative.name,
    "MSMSthreshold": "",
    "MSMSthresholdType": ThresholdEnum.relative.name,
    "MSminOccupation": "",
    "MSMSminOccupation": "",
    "MSfilter": 70,
    "MSMSfilter": 70,
    "precursorMassShift": "",
    "precursorMassShiftOrbi": "",
}


def init_session():
    if "project" not in st.session_state:
        st.session_state["project"] = Project()

    for k, v in model_keys.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()  # create the variable for the widgits


def load_project(proj=None):
    def proj_t2str(proj, item, index):
        """helper for tuples"""
        return str(proj.options_formatted.get(item, ("", ""))[index])

    def cascade_calibrations(proj):
        """helper for usign ms1 calibration on ms2"""
        if proj.options.get("MScalibration", "") and not proj.options.get(
            "MSMScalibration", ""
        ):
            return "from MS"
        return proj.options.get("MSMScalibration", "")

    proj = st.session_state["project"]
    st.session_state["selectionWindow"] = proj.options.get("selectionWindow", "")
    st.session_state["_timerange0"] = proj_t2str(proj, "timerange", 0)
    st.session_state["_timerange1"] = proj_t2str(proj, "timerange", 1)
    st.session_state["MScalibration"] = proj.options.get("MScalibration", "")
    st.session_state["MSMScalibration"] = cascade_calibrations(proj)
    st.session_state["_MSmassrange0"] = proj_t2str(proj, "MSmassrange", 0)
    st.session_state["_MSmassrange1"] = proj_t2str(proj, "MSmassrange", 1)
    st.session_state["_MSMSmassrange0"] = proj_t2str(proj, "MSMSmassrange", 0)
    st.session_state["_MSMSmassrange1"] = proj_t2str(proj, "MSMSmassrange", 1)
    # ---- see above ... below to be used to calucalte resolution delta given two resolution points
    # st.session_state["_MSresolution0"] = proj.options.get("_MSresolution0", "")
    # st.session_state["_MSresolution1"] = proj.options.get("_MSresolution1", "")
    # st.session_state["_MSMSresolution0"] = proj.options.get("_MSMSresolution0", "")
    # st.session_state["_MSMSresolution1"] = proj.options.get("_MSMSresolution1", "")
    # st.session_state["_MSresolution_MZ0"] = proj.options.get("_MSresolution_MZ0", "")
    # st.session_state["_MSresolution_MZ1"] = proj.options.get("_MSresolution_MZ1", "")
    # st.session_state["_MSMSresolution_MZ0"] = proj.options.get(
    #     "_MSMSresolution_MZ0", ""
    # )
    # st.session_state["_MSMSresolution_MZ1"] = proj.options.get(
    #     "_MSMSresolution_MZ1", ""
    # )
    st.session_state["MSresolutionDelta"] = proj.options.get("MSresolutionDelta", "")
    st.session_state["MSMSresolutionDelta"] = proj.options.get(
        "MSMSresolutionDelta", ""
    )
    st.session_state["MStolerance"] = proj.options.get("MStolerance", "")
    st.session_state["MSMStolerance"] = proj.options.get("MSMStolerance", "")
    st.session_state["MStoleranceType"] = proj.options.get(
        "MSMStoleranceType", ToleranceEnum.ppm.name
    )
    st.session_state["MSMStoleranceType"] = proj.options.get(
        "MSMStoleranceType", ToleranceEnum.ppm.name
    )
    st.session_state["MSthreshold"] = proj.options.get("MSthreshold", "")
    st.session_state["MSthresholdType"] = proj.options.get(
        "MSthresholdType", ThresholdEnum.relative.name
    )
    st.session_state["MSMSthreshold"] = proj.options.get("MSMSthreshold", "")
    st.session_state["MSMSthresholdType"] = proj.options.get(
        "MSMSthresholdType", ThresholdEnum.relative.name
    )
    st.session_state["MSminOccupation"] = proj.options.get("MSminOccupation", "")
    st.session_state["MSMSminOccupation"] = proj.options.get("MSMSminOccupation", "")
    st.session_state["MSfilter"] = proj.options_formatted.get("MSfilter", 0.7) * 100
    st.session_state["MSMSfilter"] = proj.options_formatted.get("MSMSfilter", 0.7) * 100
    st.session_state["precursorMassShift"] = proj.options.get("precursorMassShift", "")
    st.session_state["precursorMassShiftOrbi"] = proj.options.get(
        "precursorMassShiftOrbi", ""
    )


def save_project(proj=None):
    proj = st.session_state["project"]
    proj.options["selectionWindow"] = st.session_state["selectionWindow"]
    proj.options[
        "timerange"
    ] = f"({st.session_state['_timerange0']}, {st.session_state['_timerange1']})"
    proj.options["MScalibration"] = st.session_state["MScalibration"]
    proj.options["MSMScalibration"] = (
        st.session_state["MScalibration"]
        if st.session_state["MSMScalibration"] == "from MS"  # see cascade_calibrations
        else st.session_state["MSMScalibration"]
    )
    proj.options[
        "MSmassrange"
    ] = f"({st.session_state['_MSmassrange0']}, {st.session_state['_MSmassrange1']})"
    proj.options[
        "MSMSmassrange"
    ] = f"({st.session_state['_MSMSmassrange0']}, {st.session_state['_MSMSmassrange1']})"
    proj.options["MSresolutionDelta"] = st.session_state["MSresolutionDelta"]
    proj.options["MSMSresolutionDelta"] = st.session_state["MSMSresolutionDelta"]
    proj.options["MStolerance"] = st.session_state["MStolerance"]
    proj.options["MSMStolerance"] = st.session_state["MSMStolerance"]
    proj.options["MStoleranceType"] = st.session_state["MStoleranceType"]
    proj.options["MSMStoleranceType"] = st.session_state["MSMStoleranceType"]
    proj.options["MSthreshold"] = st.session_state["MSthreshold"]
    proj.options["MSthresholdType"] = st.session_state["MSthresholdType"]
    proj.options["MSMSthreshold"] = st.session_state["MSMSthreshold"]
    proj.options["MSMSthresholdType"] = st.session_state["MSMSthresholdType"]
    proj.options["MSminOccupation"] = st.session_state["MSminOccupation"]
    proj.options["MSMSminOccupation"] = st.session_state["MSMSminOccupation"]
    proj.options["MSfilter"] = st.session_state["MSfilter"]
    proj.options["MSMSfilter"] = st.session_state["MSMSfilter"]
    proj.options["precursorMassShift"] = st.session_state["precursorMassShift"]
    proj.options["precursorMassShiftOrbi"] = st.session_state["precursorMassShiftOrbi"]
    # ----
    proj.testOptions()
    proj.formatOptions()  # converts from strings to types... optoins go into options_formatted
    st.session_state["project"] = proj


# Start the UI #############################################################################################
st.title("LipidXplorer Web")
# st.file_uploader("Upload a files", type=["mzML", "mzXML", "mzML.gz", "mzXML.gz"], accept_multiple_files=True)
st.text_input("Spectra folder path")

p_path = r"test_resources\small_test\small_test-project.lxp"
col010, col020 = st.columns([3, 1])

project_path = col010.text_input(
    "Project (*.lxp) file path:", value=p_path, key="project file path"
)

if col020.button("Load Project"):
    project = st.session_state["project"]
    project.load(project_path)
    project.testOptions()
    project.formatOptions()
    load_project(project)

"****"
with st.expander("project Options"):
    project = st.session_state["project"]
    st.write(project.options_formatted, key="project options formatted")

"****"
col110, col120, col121 = st.columns([2, 1, 1])

col110.text_input("Selection Window (Da)", key="selectionWindow")
col120.text_input("Time Start (Sec)", key="_timerange0")
col121.text_input("Time end", key="_timerange1")

col210, col220, = st.columns([2, 2])

col210.text_input("Calibratoin masses MS", key="MScalibration")
col220.text_input("MSMS", key="MSMScalibration")

col310, col320, col330, col340 = st.columns([1, 1, 1, 1])
col310.text_input("M/Z range MS from", key="_MSmassrange0")
col320.text_input("to", key="_MSmassrange1")
col330.text_input("M/Z range MS/MS from", key="_MSMSmassrange0")
col340.text_input("to", key="_MSMSmassrange1")

"----"
# ---- see above ... below to be used to calucalte resolution delta given two resolution points
# (
#     col300,
#     col310,
#     col311,
#     col320,
#     col321,
#     col325,
#     col330,
#     col331,
#     col340,
#     col341,
# ) = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
# col300.write("MS")
# col310.text_input("Low M/Z", key="_MSresolution_MZ0")
# col311.text_input("Resolution", key="_MSresolution0")
# col320.text_input("High M/Z", key="_MSresolution_MZ1")
# col321.text_input("Resolution", key="_MSresolution1")
# col325.write("MS/MS")
# col330.text_input("Low M/Z", key="_MSMSresolution_MZ0")
# col331.text_input("Resolution", key="_MSMSresolution0")
# col340.text_input("High M/Z", key="_MSMSresolution_MZ1")
# col341.text_input("Resolution", key="_MSMSresolution1")


col410, col420 = st.columns(2)
col410.text_input("Resolution Gradient MS", key="MSresolutionDelta")
col420.text_input("Resolution Gradient MS/MS", key="MSMSresolutionDelta")
# with st.expander("Calculate based on resolution at given masses"):
# ---- see above ... below to be used to calucalte resolution delta given two resolution points
#     "Automatically calculate the _Resoltion gradient_ based on the resolution at a given mass"

"----"
col510, col520, col530, col540 = st.columns([2, 1, 2, 1])
col510.text_input("Tolerance MS", key="MStolerance")
col520.selectbox("unit", [e.name for e in ToleranceEnum], key="MStoleranceType")

col530.text_input("MS/MS", key="MSMStolerance")
col540.selectbox(
    "unit", [e.name for e in ToleranceEnum], key="MSMStoleranceType",
)

col610, col620, col630, col640 = st.columns([2, 1, 2, 1])
col610.text_input("Threshold MS", key="MSthreshold")
col620.selectbox(
    "unit", [e.name for e in ThresholdEnum], key="MSthresholdType",
)
col630.text_input("MS/MS", key="MSMSthreshold")
col640.selectbox(
    "unit", [e.name for e in ThresholdEnum], key="MSMSthresholdType",
)

col810, col820 = st.columns([1, 1])
col810.slider(r"In % of MS spectra files:", 0, 100, key="MSfilter")
col820.slider(
    r"In % of MS/MS spectra files:", 0, 100, key="MSMSfilter",
)

col910, col920, col930 = st.columns([1, 1, 1])


col910.text_input("MS1 offset", key="precursorMassShift")
col920.text_input("PMO", key="precursorMassShiftOrbi")

cont = col930.container()
if cont.button("Save project"):
    proj = st.session_state["project"]
    st.session_state["project options formatted"] = proj.options_formatted
    save_project(proj)
if cont.button("import project"):
    st.balloons()

