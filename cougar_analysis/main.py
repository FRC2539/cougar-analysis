import streamlit as st

import numpy as np

from cougar_analysis.log_helpers import *

st.write(
    """
# Cougar Analysis
"""
)

log_file = st.file_uploader("Select a log file for analysis", type=["wpilog"])

if log_file is not None:
    # Convert the log file to a dataframe
    log_as_bytes = log_file.getvalue()
    log_as_dataframe = read_log_to_dataframe(log_as_bytes)

    # Provide the option to download the file as a csv
    with st.expander("Download as CSV"):
        filename = st.text_input("Input the desired file name (no extension)")

        converted_csv = convert_df_to_csv(log_as_dataframe)

        st.download_button(
            label="Download converted file",
            data=converted_csv,
            file_name=f"{filename}.csv",
            mime="text/csv",
        )

    # Allow the user to select one key at a time
    all_keys = log_as_dataframe["Name"].unique()
    selected_key = st.selectbox("Select a numerical key to analyze", all_keys)

    key_only_df = filter_dataframe(log_as_dataframe, selected_key)
    ranged_df = key_only_df

    # Plot the selected key in the log
    plot_dataframe(ranged_df)

    st.subheader("Select a Range for Futher Analysis")

    timestamps = key_only_df["Timestamp"]

    range_start = st.select_slider(
        "Range Start", options=timestamps, value=timestamps.min()
    )
    range_end = st.select_slider(
        "Range End", options=timestamps, value=timestamps.max()
    )

    ranged_df = key_only_df.loc[
        key_only_df["Timestamp"].between(
            float(range_start), float(range_end), inclusive="both"
        )
    ]

    # Plot the selected range
    plot_dataframe(ranged_df)

    # Calculate 5 number summary
    [q1, med, q3] = np.percentile(ranged_df["Value"], [25, 50, 75])
    minimum, maximum = ranged_df["Value"].min(), ranged_df["Value"].max()
    mean = ranged_df["Value"].mean()

    st.subheader("5 Number Summary")
    st.write(f"Min: {minimum} | Q1: {q1} | Med: {med} | Q3: {q3} | Max: {maximum}")
    st.write(f"Mean: {mean}")

    # Calculate the 1st derivative
    derivative_series = ranged_df["Value"].diff() / ranged_df["Timestamp"].diff()
    derivative_series.name = "1st Derivative"

    # Construct a derivative dataframe
    derivative_df = pd.concat(
        [
            ranged_df["Timestamp"],
            derivative_series,
        ],
        axis=1,
    )

    st.subheader("Graph of 1st Derivative")
    st.line_chart(derivative_df, x="Timestamp", y="1st Derivative")

    # Calculate the 2nd derivative
    derivative2_series = (
        derivative_df["1st Derivative"].diff() / derivative_df["Timestamp"].diff()
    )
    derivative2_series.name = "2nd Derivative"

    # Construct a derivative dataframe
    derivative2_df = pd.concat(
        [
            ranged_df["Timestamp"],
            derivative2_series,
        ],
        axis=1,
    )

    st.subheader("Graph of 2nd Derivative")
    st.line_chart(derivative2_df, x="Timestamp", y="2nd Derivative")
