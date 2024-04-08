import numpy as np
from tdms_conversion import parseTDMS

from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

channel_data = parseTDMS(
    5,
    file_path_custom="./cf2/DataLog_2024-0406-1828-28_CMS_Data_Wiring_5.tdms",
)
channel_data.update(
    parseTDMS(
        6,
        file_path_custom="./cf2/DataLog_2024-0406-1828-28_CMS_Data_Wiring_6.tdms",
    )
)

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
df_list_constant.update({"time": np.pad(time, (0, total_length - len(time)), "edge")})
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


app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1(children="Coldflow 2 Data", style={"textAlign": "center", "fontFamily": "sans-serif"}),
        html.I("scale PI/binary data by: "),
        dcc.Input(
            id="input_{}".format("number"),
            type="number",
            placeholder="input type {}".format("number"),
            debounce=True,
            value=5000,
        ),
        dcc.Graph(id="graph-content", style={"width": "95vw", "height": "85vh"}),
    ]
)


# This is called whenver input is submitted (usually by the user clicking out of the input box), and re-draws the UI
@callback(Output("graph-content", "figure"), Input("input_number", "value"))
def update_graph(value):
    binary_multiplier: float = float(value)

    # PT_FU_04 = channel_data["pt-fu-04"].data
    # PT_HE_01 = channel_data["pt-he-01"].data
    # PT_OX_04 = channel_data["pt-ox-04"].data
    # PT_N2_01 = channel_data["pt-n2-01"].data
    # PT_FU_02 = channel_data["pt-fu-02"].data
    # PT_OX_02 = channel_data["pt-ox-02"].data
    # TC_OX_04 = channel_data["tc-ox-04"].data
    # TC_FU_04 = channel_data["tc-fu-04"].data
    # TC_OX_02 = channel_data["tc-ox-02"].data
    # TC_FU_02 = channel_data["tc-fu-02"].data
    # RTD_FU = channel_data["rtd-fu"].data
    # RTD_OX = channel_data["rtd-ox"].data
    # PT_FU_202 = channel_data["pt-fu-202"].data
    # PT_HE_201 = channel_data["pt-he-201"].data
    # PT_OX_202 = channel_data["pt-ox-202"].data
    # PT_TEST_AI_20 = channel_data["pt-test-ai-20"].data
    # PI_HE_01 = channel_data["pi-he-01"].data * binary_multiplier
    # PI_FU_02 = channel_data["pi-fu-02"].data * binary_multiplier
    # PI_OX_02 = channel_data["pi-ox-02"].data * binary_multiplier
    # PI_FU_03 = channel_data["pi-fu-03"].data * binary_multiplier
    # PI_OX_03 = channel_data["pi-ox-03"].data * binary_multiplier
    # REED_BP_01 = channel_data["reed-bp-01"].data * binary_multiplier
    # PI_FU_201 = channel_data["pi-fu-201"].data * binary_multiplier
    # PI_OX_201 = channel_data["pi-ox-201"].data * binary_multiplier
    # REED_MAROTTA_1 = channel_data["reed-marotta-1"].data * binary_multiplier
    # REED_MAROTTA_2 = channel_data["reed-marotta-2"].data * binary_multiplier
    # REED_N2_02 = channel_data["reed-n2-02"].data * binary_multiplier
    # REED_MAROTTA_3 = channel_data["reed-marotta-3"].data * binary_multiplier
    # TC_OX_201 = channel_data["tc-ox-201"].data
    # TC_FU_201 = channel_data["tc-fu-201"].data
    # time: list[float] = channel_data["time"]

    print(available_channels)
    df_list = {}
    df_list.update(df_list_constant)

    for channel in available_channels:
        if "reed-" in channel or "pi-" in channel:
            df_list.update(
                {
                    channel: df_list[channel] * binary_multiplier,
                }
            )
    df = pd.DataFrame.from_dict(df_list)
    fig = px.line(df, x="time", y=df.columns[0:-1])
    return fig


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="80")