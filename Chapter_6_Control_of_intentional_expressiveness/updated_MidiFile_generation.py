from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
import pandas as pd

import MidiFile_parser
import df_update_with_predictions_and_user_prefs


def generate_updt_MidiFile():
    tempo = MidiFile_parser.tempo
    ticks_per_beat = MidiFile_parser.ticks_per_beat
    meter = (MidiFile_parser.numerator, MidiFile_parser.denominator)

    updated_df = df_update_with_predictions_and_user_prefs.updated_df

    # Create a new df with all the need data to generate the expressive MidiFile
    df_MidiFile = pd.DataFrame()
    df_MidiFile['note_numb'] = updated_df['note_numb'].copy()
    df_MidiFile['t_dt_note_on'] = updated_df['t_dt_note_on'] + updated_df['delta_onsets_updt']
    if df_MidiFile['t_dt_note_on'].iloc[0] < 0:
        df_MidiFile.at[df_MidiFile.index[0], 't_dt_note_on'] = 0

    # Calculate offsets based on prec_rest
    following_note_prec_rest = updated_df['prec_rest_mod'].shift(-1)
    following_note_on = df_MidiFile['t_dt_note_on'].shift(-1)
    df_MidiFile['t_dt_note_off'] = (following_note_on - following_note_prec_rest).fillna(updated_df['t_dt_note_off']).astype(int)
    df_MidiFile.loc[df_MidiFile.index[-1], 't_dt_note_off'] = updated_df['t_dt_note_off'].iloc[-1]

    # Avoid overlaps
    df_MidiFile['t_dt_note_off'] = df_MidiFile.apply(
        lambda row: min(row['t_dt_note_off'], following_note_on[row.name]) if pd.notna(following_note_on[row.name]) else
        row['t_dt_note_off'],
        axis=1
    )

    df_MidiFile['velocity'] = updated_df['velocity_updt'].copy()
    df_MidiFile['string'] = updated_df['string'].copy()
    df_MidiFile['fret'] = updated_df['fret'].copy()
    df_MidiFile['hammer-on'] = updated_df['hammer-on'].copy()
    df_MidiFile['pull-off'] = updated_df['pull-off'].copy()
    df_MidiFile['bending'] = updated_df['bending'].copy()
    df_MidiFile['vibrato'] = updated_df['vibrato'].copy()
    df_MidiFile['slide_legato'] = updated_df['slide_legato'].copy()

    df_MidiFile.to_csv('out_MidiFile_df_test.csv')

    # Create a new MIDI file, add a track and the basic meta messages
    mid = MidiFile(ticks_per_beat=ticks_per_beat)
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(MetaMessage('set_tempo', tempo=tempo))
    track.append(MetaMessage('time_signature', numerator=meter[0], denominator=meter[1]))

    total_delta_time = 0

    # Create messages
    for index, row in df_MidiFile.iterrows():
        note_number = int(row['note_numb'])
        velocity = int(row['velocity'])
        string = int(row['string'])
        fret = int(row['fret'])
        hammer_on = bool(row['hammer-on'])
        pull_off = bool(row['pull-off'])
        bending = int(row['bending'])
        vibrato = bool(row['vibrato'])
        slide_legato = bool(row['slide_legato'])

        # Calculate delta_note_on as the difference between the current note's onset and total_delta_time
        delta_note_on = int(row['t_dt_note_on'] - total_delta_time)

        # Update total_delta_time now for the note-on timing
        total_delta_time += delta_note_on

        # Add CC messages
        track.append(Message('control_change', control=102, value=string * 10, time=delta_note_on))  # string
        track.append(Message('control_change', control=103, value=fret * 5, time=0))  # fret

        if hammer_on:
            track.append(Message('control_change', control=104, value=127, time=0))  # hammer-on
            turn_off_hammer_on = True
        else:
            turn_off_hammer_on = False
        if pull_off:
            track.append(Message('control_change', control=105, value=127, time=0))  # pull-off
            turn_off_pull_off = True
        else:
            turn_off_pull_off = False
        if bending > 0:
            track.append(Message('control_change', control=106, value=bending*10, time=0))  # bending
            turn_off_bending = True
        else:
            turn_off_bending = False
        if vibrato:
            track.append(Message('control_change', control=107, value=127, time=0))  # vibrato
            turn_off_vibrato = True
        else:
            turn_off_vibrato = False
        if slide_legato:
            track.append(Message('control_change', control=108, value=127, time=0))  # slide_legato
            turn_off_slide_legato = True
        else:
            turn_off_slide_legato = False

        # Add the note-on message
        track.append(Message('note_on', note=note_number, velocity=velocity, time=0))

        delta_note_off = int(row['t_dt_note_off'] - total_delta_time)

        # Add note-off message
        track.append(Message('note_off', note=note_number, velocity=0, time=delta_note_off))
        total_delta_time += delta_note_off

        # Turn off the CCs
        if turn_off_hammer_on:
            track.append(Message('control_change', control=104, value=0, time=0))  # hammer-on
        if turn_off_pull_off:
            track.append(Message('control_change', control=105, value=0, time=0))  # pull-off
        if turn_off_bending:
            track.append(Message('control_change', control=106, value=0, time=0))  # bending
        if turn_off_vibrato:
            track.append(Message('control_change', control=107, value=0, time=0))  # vibrato
        if turn_off_slide_legato:
            track.append(Message('control_change', control=108, value=0, time=0))  # slide_legato

    # Save the MIDI file
    mid.save('expressive_MidiFile.mid')