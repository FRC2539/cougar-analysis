from datetime import datetime
from numpy import average

import pandas as pd
import streamlit as st

from cougar_analysis.data_log_reader import DataLogReader

HEADER_LIST = ["Timestamp", "Name", "Value"]


def filter_dataframe(dataframe: pd.DataFrame, name_filter: str):
    return dataframe.loc[dataframe[HEADER_LIST[1]] == name_filter]


def exclude_from_dataframe(dataframe: pd.DataFrame, name_to_exclude: str):
    return dataframe.loc[dataframe[HEADER_LIST[1]] != name_to_exclude]


def read_log_to_dataframe(input_file_bytes: bytes):
    [output, error] = convert_data_log_to_list(input_file_bytes=input_file_bytes)

    # Convert the log data to a pandas dataframe
    log_as_dataframe = pd.DataFrame(output)

    log_as_dataframe.columns = HEADER_LIST

    return log_as_dataframe


def convert_data_log_to_list(input_file_bytes: bytes):
    output = []

    error = None

    error_message = "Invalid file, verify that the file is a wpilog or try downloading the log file again."

    reader = DataLogReader(input_file_bytes)

    entries = {}

    for record in reader:
        # Store all record starting data in the entries dictionary
        if record.isStart():
            try:
                data = record.getStartData()
                entries[data.entry] = data
            except TypeError as e:
                error = error_message

        # Delete the finish entry of the current record
        elif record.isFinish():
            try:
                entry = record.getFinishEntry()
                if entry in entries:
                    del entries[entry]
            except TypeError as e:
                error = error_message

        # Verify any available metadata
        elif record.isSetMetadata():
            try:
                data = record.getSetMetadataData()
            except TypeError as e:
                error = error_message

        # Verify that the type of the record is recognized
        elif record.isControl():
            error = error_message

        # Extract and store the information from the current record
        else:
            entry = entries.get(record.entry, None)

            if entry is None:
                continue

            output.append(extract_value_from_entry(entry, record))

    return [output, error]


def extract_value_from_entry(entry, record):
    timestamp = record.timestamp / 1000000

    value = None

    # Handle the system time-type entries
    if entry.name == "systemTime" and entry.type == "int64":
        dt = datetime.fromtimestamp(record.getInteger() / 1000000)
        value = "{:%Y-%m-%d %H:%M:%S.%f}".format(dt)
    else:
        match entry.type:
            case "double":
                value = record.getDouble()
            case "int64":
                value = record.getInteger()
            case "string" | "json":
                value = record.getString()
            case "boolean":
                value = record.getBoolean()
            case "boolean[]":
                value = list(record.getBooleanArray())
            case "double[]":
                value = list(record.getDoubleArray())
            case "float[]":
                value = list(record.getFloatArray())
            case "int64[]":
                value = list(record.getIntegerArray())
            case "string[]":
                value = list(record.getStringArray())

    return [timestamp, entry.name, value]


def plot_dataframe(dataframe: pd.DataFrame):
    # Include only timestamps and values
    key_only_df = dataframe[[HEADER_LIST[0], HEADER_LIST[2]]]

    st.line_chart(key_only_df, x="Timestamp", y="Value")


@st.cache
def convert_df_to_csv(dataframe: pd.DataFrame):
    # Cache the conversion to prevent computation on every rerun
    return dataframe.to_csv().encode("utf-8")
