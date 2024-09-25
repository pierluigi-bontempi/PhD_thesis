import os
import numpy as np
import pandas as pd
from random import randint
import joblib
import MidiFile_parser
import add_techniques

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
from tensorflow.keras.models import load_model

df = None


def predict_deviations():

    global df

    bpm = MidiFile_parser.bpm
    ticks_per_beat = MidiFile_parser.ticks_per_beat
    df = add_techniques.df

    columns_to_drop = ['fllw_rest', 'note_lng', 'note_lng_ms', 'int', 'int_horizon', 'bending_prob', 'ho_prob',
                       'po_prob', 'vibrato_prob']
    df = df.drop(columns=columns_to_drop)

    df['velocity'] = df['velocity'].astype(int)

    df['delta_onset_ms'] = 0
    df['delta_onset_ms-1'] = df['delta_onset_ms'].shift(+1)
    df['prec_rest_ms'] = np.rint(df['prec_rest'] * (60 / bpm / 960) * 1000)
    df['velocity-1'] = df['velocity'].shift(+1)
    df['PC'] = df['handposition'] - df['handposition'].shift(1)
    df['PC'] = df['PC'].fillna(0)
    df['SC'] = df['string'] - df['string'].shift(1)
    df['SC'] = df['SC'].fillna(0)
    df['HS'] = df['fret'] - (df['handposition'] + df['finger']) + 1
    df['onbeat'] = np.where(df['t_dt_note_on'] % ticks_per_beat < 5, 1, 0)

    df['PC'] = df['PC'].astype(int)
    df['SC'] = df['SC'].astype(int)
    df['HS'] = df['HS'].astype(int)
    df['onbeat'] = df['onbeat'].astype(int)

    # Replace handposition = 0 with preceding non-zero HP (or following, in case it's the very first note)

    if df['handposition'].iloc[0] == 0:
        first_non_zero = df['handposition'][df['handposition'] != 0].iloc[0]
        df.at[0, 'handposition'] = first_non_zero
    df['handposition'] = df['handposition'].replace(0, pd.NA).ffill().fillna(0)

    # Random set the first note

    df.at[0, 'velocity'] = randint(80, 100)
    df.at[0, 'velocity-1'] = randint(80, 100)
    df.at[0, 'delta_onset_ms'] = randint(-10, 10)
    df.at[0, 'delta_onset_ms-1'] = randint(-10, 10)
    df.at[0, 'prec_rest_ms'] = 0
    df.at[1, 'velocity-1'] = df.at[0, 'velocity']
    df.at[1, 'delta_onset_ms-1'] = df.at[0, 'delta_onset_ms']

    df['velocity-1'] = df['velocity-1'].astype(int)
    df['delta_onset_ms'] = df['delta_onset_ms'].astype(int)
    df['delta_onset_ms-1'] = df['delta_onset_ms-1'].astype(int)
    df['prec_rest_ms'] = df['prec_rest_ms'].astype(int)

    ########################################################
    ############### Predict onsets deviation ###############
    ########################################################

    # Load and run the Random Forest
    random_forest_regressor = joblib.load('regressors/random_forest_regressor_onsets.pkl')
    columns_to_select = ['note_numb', 'onbeat', 'PC', 'SC', 'HS', 'hammer-on', 'pull-off', 'bending', 'velocity-1',
                         'delta_onset_ms', 'delta_onset_ms-1']
    df_onsets_predictions = df[columns_to_select].copy()
    for i in range(1, len(df_onsets_predictions)):
        input_features = df_onsets_predictions.drop(columns=['delta_onset_ms']).iloc[i:i + 1]  # Use DataFrame slice
        predicted_value = random_forest_regressor.predict(input_features)[0]
        predicted_value_rounded = round(predicted_value)
        df_onsets_predictions.at[i, 'delta_onset_ms'] = predicted_value_rounded
        if i + 1 < len(df_onsets_predictions):
            df_onsets_predictions.at[i + 1, 'delta_onset_ms-1'] = predicted_value_rounded

    df[['delta_onset_ms', 'delta_onset_ms-1']] = df_onsets_predictions[['delta_onset_ms', 'delta_onset_ms-1']].copy()

    ########################################################
    ############### Predict offsets deviation ##############
    ########################################################

    PC_prec_rest =[]
    SC_prec_rest = []

    for i in range(1,3):
        if df.iloc[i]['PC'] <= -6:
            PC_prec_rest.append(125)
        elif -6 < df.iloc[i]['PC'] <= -3:
            PC_prec_rest.append(80)
        elif -3 < df.iloc[i]['PC'] <= -1:
            PC_prec_rest.append(10)
        elif 1 <= df.iloc[i]['PC'] <= 2:
            PC_prec_rest.append(43)
        elif 2 < df.iloc[i]['PC'] <= 5:
            PC_prec_rest.append(70)
        elif df.iloc[i]['PC'] > 5:
            PC_prec_rest.append(91)
        else:
            PC_prec_rest.append(0)

    for i in range(1,3):
        if df.iloc[i]['SC'] == -5:
            SC_prec_rest.append(110)
        elif df.iloc[i]['SC'] == -4:
            SC_prec_rest.append(73)
        elif df.iloc[i]['SC'] == -3:
            SC_prec_rest.append(62)
        elif df.iloc[i]['SC'] == -2:
            SC_prec_rest.append(37)
        elif df.iloc[i]['SC'] >= -1:
            SC_prec_rest.append(6)
        else:
            SC_prec_rest.append(0)

    for i in range(1, 3):
        if PC_prec_rest[i-1] > SC_prec_rest[i-1]:
            df.at[i, 'prec_rest_ms'] = PC_prec_rest[i-1]
        else:
            df.at[i, 'prec_rest_ms'] = SC_prec_rest[i-1]

    # Load and run the RNN
    rnn_prec_rest_model = load_model('regressors/RNN-4_regressor_prec_rests.h5')

    scaler_X = joblib.load('regressors/scaler_X_prec_rest.pkl')
    scaler_y = joblib.load('regressors/scaler_y_prec_rest.pkl')

    columns_to_select = ['note_numb', 'onbeat', 'PC', 'SC', 'HS', 'hammer-on', 'pull-off', 'bending',
                         'delta_onset_ms-1', 'velocity-1']
    df_rnn_prec_rest_predictions = df[columns_to_select + ['prec_rest_ms']].copy()

    time_steps = 4

    for i in range(time_steps, len(df_rnn_prec_rest_predictions)):
        input_sequence = df_rnn_prec_rest_predictions[columns_to_select].iloc[i - time_steps:i].values
        input_sequence_scaled = scaler_X.transform(input_sequence)  # Scale the input sequence
        input_sequence_scaled = input_sequence_scaled.reshape(1, time_steps, -1)
        predicted_value_scaled = rnn_prec_rest_model.predict(input_sequence_scaled)
        predicted_value = scaler_y.inverse_transform(predicted_value_scaled)[0, 0]
        predicted_value_rounded = round(predicted_value)
        df_rnn_prec_rest_predictions.at[i, 'prec_rest_ms'] = predicted_value_rounded

    # Update the DataFrame with the predicted 'prec_rest_ms'
    df['prec_rest_ms'] = df_rnn_prec_rest_predictions['prec_rest_ms'].copy()


    ########################################################
    ################## Velocity deviation ##################
    ########################################################

    df.at[1, 'velocity'] = randint(80, 100)
    df.at[1, 'velocity-1'] = df.at[0, 'velocity']
    df.at[2, 'velocity'] = randint(80, 100)
    df.at[2, 'velocity-1'] = df.at[1, 'velocity']
    df.at[3, 'velocity'] = randint(80, 100)
    df.at[3, 'velocity-1'] = df.at[2, 'velocity']

    # Load and run the RNN
    rnn_velocity_model = load_model('regressors/RNN-4_regressor_velocity.h5')

    scaler_X_velocity = joblib.load('regressors/scaler_X_velocity.pkl')
    scaler_y_velocity = joblib.load('regressors/scaler_y_velocity.pkl')

    columns_to_select_velocity = ['note_numb', 'onbeat', 'PC', 'SC', 'HS', 'hammer-on', 'pull-off', 'bending',
                                  'delta_onset_ms-1', 'velocity-1']
    df_velocity_predictions = df[columns_to_select_velocity + ['velocity']].copy()

    time_steps = 4

    for i in range(time_steps, len(df_velocity_predictions)):
        input_sequence = df_velocity_predictions[columns_to_select_velocity].iloc[i - time_steps:i].values
        input_sequence_scaled = scaler_X_velocity.transform(input_sequence)  # Scale the input sequence
        input_sequence_scaled = input_sequence_scaled.reshape(1, time_steps, -1)
        predicted_value_scaled = rnn_velocity_model.predict(input_sequence_scaled)
        predicted_value = scaler_y_velocity.inverse_transform(predicted_value_scaled)[0, 0]
        predicted_value_rounded = round(predicted_value)
        df_velocity_predictions.at[i, 'velocity'] = predicted_value_rounded
        if i + 1 < len(df_velocity_predictions):
            df_velocity_predictions.at[i + 1, 'velocity-1'] = predicted_value_rounded

    # Update the DataFrame with the predicted 'velocity' and 'velocity-1'
    df[['velocity', 'velocity-1']] = df_velocity_predictions[['velocity', 'velocity-1']].copy()

    df.loc[df['prec_rest_ms'] < 0, 'prec_rest_ms'] = 0
    df.loc[df['prec_rest_ms'] > df['IOI_ms'], 'prec_rest_ms'] = (df['IOI_ms'] * 2 / 3).round().astype(int)