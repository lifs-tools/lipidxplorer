# File Selection Drop Down
import streamlit as st
from pathlib import Path

# from https://discuss.streamlit.io/t/upload-files-to-streamlit-app/80/46
# def st_file_selector(st_placeholder, path=".", label="Please, select a file/folder..."):
#     # get base path (directory)
#     base_path = "." if path is None or path is "" else path
#     base_path = base_path if os.path.isdir(base_path) else os.path.dirname(base_path)
#     base_path = "." if base_path is None or base_path is "" else base_path
#     # list files in base path directory
#     files = os.listdir(base_path)
#     if base_path is not ".":
#         files.insert(0, "..")
#     files.insert(0, ".")
#     selected_file = st_placeholder.selectbox(label=label, options=files, key=base_path)
#     selected_path = os.path.normpath(os.path.join(base_path, selected_file))
#     if selected_file is ".":
#         return selected_path
#     if os.path.isdir(selected_path):
#         selected_path = st_file_selector(
#             st_placeholder=st_placeholder, path=selected_path, label=label
#         )
#     return selected_path


st.title("LipidXplorer Web dev")
folder_path = st.text_input("Path to MZML files")
p = Path(folder_path)
if p.is_dir:
    st.write(folder_path)

with st.expander("See files"):
    for i in p.iterdir():
        st.write(i)

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

