import os
import numpy as np
import pandas as pd

import MidiFile_parser
import predict_deviations
import gui

updated_df = None

def df_update():
    global updated_df

    tempo = MidiFile_parser.tempo
    ticks_per_beat = MidiFile_parser.ticks_per_beat
    updated_df = predict_deviations.df.copy()

    updated_df['delta_onset_mod'] = (updated_df['delta_onset_ms'] / (tempo / 1000 / ticks_per_beat)).round().astype(int)
    updated_df['prec_rest_mod'] = (updated_df['prec_rest_ms'] / (tempo / 1000 / ticks_per_beat)).round().astype(int)

    # Velocity normalization

    max_velocity = updated_df['velocity'].max()

    if gui.loudness == 4:
        new_max = 127
    elif gui.loudness == 3:
        new_max = 120
    elif gui.loudness == 2:
        new_max = 110
    elif gui.loudness == 1:
        new_max = 100
    elif gui.loudness == 0:
        new_max = 90
    else:
        raise ValueError("Invalid value for gui.loudness")

    updated_df['velocity_updt'] = (updated_df['velocity'] / max_velocity * new_max).round().astype(int)

    # Timing normalization

    mean_delta_onset_mod = updated_df['delta_onset_mod'].mean()
    adjustment_value = round(gui.positioning_to_the_beat - mean_delta_onset_mod)
    updated_df['delta_onsets_updt'] = (updated_df['delta_onset_mod'] + adjustment_value)