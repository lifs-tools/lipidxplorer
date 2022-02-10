import streamlit as st
from pathlib import Path


st.title("LipidXplorer Web dev")
folder_path = st.text_input("Spectra Directory")
p = Path(folder_path)


with st.expander("Spectra files"):
    mzmls = list(p.glob("*.mzml"))
    for i in mzmls:
        cols = st.columns([3, 1])
        cols[0].write(i.stem)
        cols[1].selectbox("", ["Repicate", "Blank", "Int. Std."], key=i.stem)

with st.expander("Set limits"):
    mode = st.radio("Mode", ["pos", "neg", "both"])
    seconds = st.slider("Select a Time range in seconds", 0.0, 100.0, (0.0, 75.0))
    seconds = st.slider("Select m/z range ", 200.0, 1000.0, (300.0, 1200.0))

with st.expander("Offset and calibration"):
    offset_ms1 = st.number_input("MS1 offset")

with st.expander("Tolerance & resolution"):
    tolerance_ms1 = st.number_input("Identification  Tolerance")
    resolution_ms1 = st.number_input("Grouping resolution")
    resolution_gradient_ms1 = st.number_input("Resolution Gradient")
    """TODO provide the resolition at m/z for two points to self calculate"""
    sel_window_st = st.empty()
    if True:
        prec_sel_tol = sel_window_st.number_input("Precursor assignment tolerance")

with st.expander("Filtering"):
    col1, col2 = st.columns(2)
    min_intensity = col1.number_input("min intensity")
    min_intensity_type = col2.radio("type", ["ppm", "absolute"])
    frequency_rate = st.number_input("min repetition rate")
    min_ocupation = st.number_input("min occupation")

with st.expander("Logging"):
    save_mastersscan_as_csv = st.checkbox("save mastersscan as csv")
    log_isotopic_correction = st.checkbox("log isotopic correction")

