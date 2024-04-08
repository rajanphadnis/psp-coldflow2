import re
from typing import OrderedDict
from nptdms import TdmsFile, TdmsGroup, TdmsChannel
from numpy import float64
from numpy.typing import NDArray
import pickle
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os


class DigitalChannelData:
    def __init__(
        self,
        rawData: NDArray[float64],
        properties: OrderedDict,
        name: str,
        description: str,
        channel_type: str,
    ):
        self._rawData = rawData
        self._properties = properties
        self._name = name
        self._channel_type = channel_type
        self._description = description

    @property
    def data(self) -> NDArray[float64]:
        return self._rawData

    @property
    def properties(self) -> OrderedDict:
        return self._properties

    @property
    def name(self) -> str:
        return self._name

    @property
    def channelType(self) -> str:
        return self._channel_type

    @property
    def description(self) -> str:
        return self._description


class AnalogChannelData:
    def __init__(
        self,
        rawData: NDArray[float64],
        properties: OrderedDict,
        name: str,
        slope: float,
        offset: float,
        zeroing_target: float,
        zeroing_correction: float,
        description: str,
        units: str,
        channel_type: str,
        constant_cjc: float,
        tc_type: str,
        min_v: float,
        max_v: float,
    ):
        self._rawData = rawData
        self._properties = properties
        self._name = name
        self._slope = slope
        self._offset = offset
        self._zeroing_target = zeroing_target
        self._zeroing_correction = zeroing_correction
        self._description = description
        self._units = units
        self._channel_type = channel_type
        self._tc_type = tc_type
        self._constant_cjc = constant_cjc
        self._min_v = min_v
        self._max_v = max_v

    @property
    def rawData(self) -> NDArray[float64]:
        return self._rawData

    @property
    def data(self) -> NDArray[float64]:
        return (self._rawData * self._slope) + self._zeroing_correction + self._offset

    @property
    def properties(self) -> OrderedDict:
        return self._properties

    @property
    def name(self) -> str:
        return self._name

    @property
    def slope(self) -> float:
        return self._slope

    @property
    def offset(self) -> float:
        return self._offset

    @property
    def zeroing_target(self) -> float:
        return self._zeroing_target

    @property
    def zeroing_correction(self) -> float:
        return self._zeroing_correction

    @property
    def description(self) -> str:
        return self._description

    @property
    def units(self) -> str:
        return self._units

    @property
    def channelType(self) -> str:
        return self._channel_type

    @property
    def constant_cjc(self) -> float:
        return self._constant_cjc

    @property
    def tc_type(self) -> str:
        return self._tc_type

    @property
    def min_v(self) -> float:
        return self._min_v

    @property
    def max_v(self) -> float:
        return self._max_v


def parseTDMS(
    dev_num: int, file_path_custom: str = "", dev_group: str = "Data (1000.000000 Hz)"
) -> dict[str, AnalogChannelData | DigitalChannelData | list[float]]:
    """## Parse a TDMS file (or an equivalent pickle file)
    ### Arguments:
    - `dev_num` (Type: `int`): dev box number (i.e: the `5` or `6` in dev5 or dev6)
    - (Optional) `file_path_custom` (Type: `str`): the dynamic file path to a `.TDMS` file (use this in case you don't want to keep selecting the tdms file to parse every time you run the script)
    - (Optional) `dev_group` (Type: `str`): the TDMS group header. You usually don't have to touch this unless the data isn't high frequency sampling data
    ### Description
    If `file_path_custom` isn't specified, the file picker dialog comes up to select a tdms file. Then, we check to see if there's an equivalent pickle file in the same directory as the chosen tdms file.
    If there's a pickle file, we parse that. Otherwise, we parse the TDMS file and save the resulting object to a pickle file for later.
    """
    if file_path_custom == "":
        root = tk.Tk()
        root.withdraw()
        filepath: str = filedialog.askopenfilename(
            initialdir="./", title="Choose Dev" + str(dev_num) + " TDMS file"
        )
        print(
            f'to skip the filepicker, use "parseTDMS({dev_num}, file_path_custom={filepath})"'
        )
    else:
        filepath = file_path_custom
    pickle_filepath: str = filepath[:-5] + ".pickle"
    if os.path.exists(pickle_filepath):
        print("unpickling...")
        with open(pickle_filepath, "rb") as f:
            unpickledData: dict[
                str, AnalogChannelData | DigitalChannelData | list[float]
            ] = pickle.loads(f.read())
            print("unpickled data")
            return unpickledData
    else:
        channel_data_map: dict[
            str, AnalogChannelData | DigitalChannelData | list[float]
        ] = {}
        tdms_file: TdmsFile = TdmsFile.read(filepath)
        group: TdmsGroup = tdms_file[dev_group]
        dev5_channels = compileChannels(group.channels())
        channel_data_map.update(dev5_channels[0])
        channel_data_map.update(dev5_channels[1])
        channel_data_map["time"] = getTime(channel_data_map, dev_group)
        with open(pickle_filepath, "wb") as f:
            pickle.dump(channel_data_map, f, pickle.HIGHEST_PROTOCOL)
        print(
            f'conversion done!\n\n\nNext time you want to run the converter, consider calling the function with: "parseTDMS({dev_num}, file_path_custom={pickle_filepath[:-7] + ".tdms"})"'
        )
        return channel_data_map


def compileChannels(
    channels: list[TdmsChannel],
) -> tuple[dict[str, AnalogChannelData], dict[str, DigitalChannelData]]:
    toReturn_AI = {}
    toReturn_DI = {}

    for channel in channels:
        props = channel.properties
        type = props["Channel Type"]
        if "AI" in type:
            parsed_as = "AI"
            channel_data_obj = AnalogChannelData(
                rawData=channel.data,
                properties=props,
                name=props["Channel Name"],
                slope=props["Slope"],
                offset=props["Offset"],
                zeroing_target=props["Zeroing Target"],
                zeroing_correction=props["Zeroing Correction"],
                description=props["Description"],
                units=props["Unit"],
                channel_type=props["Channel Type"],
                constant_cjc=props["constant CJC"],
                tc_type=props["TC Type"],
                min_v=props["Minimum"],
                max_v=props["Maximum"],
            )
            toReturn_AI[channel_data_obj.name] = channel_data_obj
        else:
            parsed_as = "DI"
            channel_data_obj = DigitalChannelData(
                rawData=channel.data,
                properties=props,
                name=props["Channel Name"],
                channel_type=props["Channel Type"],
                description=props["Description"],
            )
            toReturn_DI[channel_data_obj.name] = channel_data_obj

        print("parsed " + channel_data_obj.name + " as " + parsed_as)
    return (toReturn_AI, toReturn_DI)


def getTime(
    channel_data: dict[str, AnalogChannelData | DigitalChannelData], group_name: str
) -> list[float]:
    samples: int = channel_data[next(iter(channel_data))].rawData.size
    pattern: str = r"\(([^()]+)\)"
    match: re.Match = re.search(pattern, group_name)
    sample_rate: float = float(match.group(1)[:-3])
    dt: float = 1 / sample_rate
    time: list[float] = np.arange(0, samples * dt, dt).tolist()
    return time


def extendDatasets(
    channel_data: dict[str, AnalogChannelData | DigitalChannelData | list[float]],
) -> tuple[list[str], dict[str, AnalogChannelData | DigitalChannelData | list[float]]]:
    # get all the available channel names
    available_channels = list(channel_data.keys())

    # get the length of the largest dataset
    total_length: int = 0
    for channel in available_channels:
        if channel != "time" and len(channel_data[channel].data) > total_length:
            total_length = len(channel_data[channel].data)

    # for each channel, pad the end of that channel's dataset with some value to
    # make all the channel's data the same length and simeltaneously convert it all to np arrays
    df_list_constant = {}
    time: list[float] = channel_data["time"]
    df_list_constant.update(
        {"time": np.pad(time, (0, total_length - len(time)), "edge")}
    )
    for channel in available_channels:
        # for binary channels, make the padding value 0.5 to make it easy to identify which data is to be ignored
        if "reed-" in channel or "pi-" in channel:
            df_list_constant.update(
                {
                    channel: np.pad(
                        channel_data[channel].data,
                        (0, total_length - len(channel_data[channel].data)),
                        "constant",
                        constant_values=(
                            0.5,
                            0.5,
                        ),
                    )
                }
            )
        # for all other channels, set the padding value to zero
        elif channel != "time":
            df_list_constant.update(
                {
                    channel: np.pad(
                        channel_data[channel].data,
                        (0, total_length - len(channel_data[channel].data)),
                        "constant",
                        constant_values=(0, 0),
                    )
                }
            )

    return (available_channels, df_list_constant)
