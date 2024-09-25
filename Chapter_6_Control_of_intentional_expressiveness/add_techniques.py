import os
import pandas as pd
import numpy as np
from random import randint
import MidiFile_parser
import gui

df = None

def add_techniques():

    global df

    # Load df generated from MidiFile and merge with CPLEX output

    notes_list_pd_df = MidiFile_parser.notes_list_pd_df
    output_CPLEX_df = pd.read_csv('CPLEX_output.csv')

    if notes_list_pd_df['note_name'].equals(output_CPLEX_df['note']):
        print("Good match between CPLEX output and original df")
        # Delete the .dat and . csv files
        os.remove('CPLEX_output.csv')
        os.remove('CPLEX_data_file.dat')
    else:
        print("Warning: mismatch between CPLEX output and original df")
        print(notes_list_pd_df['note_name'])
        print("###########")
        print((output_CPLEX_df['note']))

    df = pd.concat([notes_list_pd_df, output_CPLEX_df], axis=1)
    df.drop('note', axis=1, inplace=True)

    # Add techniques

    df['int'], df['int_horizon'], df['bending_prob'], df['bending'], df['vibrato'], df['ho_prob'], df['hammer-on'], df[
        'po_prob'], df['pull-off'], df['slide_legato'] = [np.nan, np.nan, 0, 0, False, 0, False, 0, False, False]

    df['int'] = df['int'].astype('object')
    df['int_horizon'] = df['int_horizon'].astype('object')
    df['hammer-on'] = df['hammer-on'].astype(bool)
    df['pull-off'] = df['pull-off'].astype(bool)
    df['vibrato'] = df['vibrato'].astype(bool)
    df['slide_legato'] = df['slide_legato'].astype(bool)

    #############################################
    ################## Bending ##################
    #############################################

    bending_min_duration_ms = 150

    # Reference scale (to know where to start bends from)

    major_scale = np.array([0, 2, 4, 5, 7, 9, 11])
    minor_scale = np.array([0, 2, 3, 5, 7, 8, 10])
    major_pentatonic_scale = np.array([0, 2, 4, 7, 9])
    minor_pentatonic_scale = np.array([0, 3, 5, 7, 10])
    blues_scale = np.array([0, 3, 5, 6, 7, 10])

    selected_root = gui.selected_root
    selected_scale = gui.selected_scale

    notes = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]
    root_note_numb = notes.index(selected_root)

    valid_notes = np.array([])

    if selected_scale == "Major":
        valid_notes = root_note_numb + major_scale
    elif selected_scale == "Minor":
        valid_notes = root_note_numb + minor_scale
    elif selected_scale == "Major Pentatonic":
        valid_notes = root_note_numb + major_pentatonic_scale
    elif selected_scale == "Minor Pentatonic":
        valid_notes = root_note_numb + minor_pentatonic_scale
    elif selected_scale == "Blues":
        valid_notes = root_note_numb + blues_scale

    valid_notes = valid_notes.astype('int')

    len_scale = -len(valid_notes)
    for i in range(8):
        valid_notes = np.append(valid_notes, valid_notes[len_scale:] + 12)

    # Bends parameters (frequency etc.)

    max_bending = [2, 3, 4, 0]  # max bending for each finger 1st to 4th

    bending_frequency_dataset = np.array(
        [4.6, 5.4, 6, 0.6, 1.2, 1])  # Bending frequency for each string in percentage - 1st to 6th

    # Initiate the array with the number of notes on each string, first to sixth
    number_of_notes_each_string = np.array([0, 0, 0, 0, 0, 0])

    for i in df.index:
        number_of_notes_each_string[df.at[i, 'string'] - 1] += 1

    # Calculate the target number of bendings for each string

    target_number_bends = np.round(number_of_notes_each_string * bending_frequency_dataset / 100).astype(int)

    actual_bends_each_string = np.array([0, 0, 0, 0, 0, 0])

    # Generate intervals direction labels

    for i in range(len(df.index) - 1):
        if df.at[i, 'note_numb'] - df.at[i + 1, 'note_numb'] < 0:
            df.at[i, 'int'] = "asc"
            df.at[i, 'int_horizon'] = "asc"
        elif df.at[i, 'note_numb'] - df.at[i + 1, 'note_numb'] > 0:
            df.at[i, 'int'] = "desc"
            df.at[i, 'int_horizon'] = "desc"
        elif df.at[i, 'note_numb'] - df.at[i + 1, 'note_numb'] == 0:
            df.at[i, 'int'] = "unison"
            df.at[i, 'int_horizon'] = float("nan")

    df.at[len(df.index) - 1, 'int'] = "None"
    df.at[len(df.index) - 1, 'int_horizon'] = "None"

    df['int_horizon'] = df['int_horizon'].bfill()

    # Find nearest lower note and returns the distance from the actual one

    def find_nearest_lower_note_int(note_numb):
        valid_lower_notes = valid_notes[(note_numb > valid_notes)]
        nearest_lower_note = np.max(valid_lower_notes)
        bend_start_interval = note_numb - nearest_lower_note
        return (bend_start_interval)

    # Check there are not other bendings

    def no_current_prev_bending():
        if df.at[i - 1, 'bending'] == 0 or df.at[i, 'bending'] == 0:
            return True
        else:
            return False

    def no_current_fllw_bending():
        if df.at[i, 'bending'] == 0 or df.at[i + 1, 'bending'] == 0:
            return True
        else:
            return False

    def no_current_prev_fllw_bending():
        if df.at[i - 1, 'bending'] == 0 or df.at[i, 'bending'] == 0 or df.at[i + 1, 'bending'] == 0:
            return True
        else:
            return False

            # Bending on lower string generation

    def prev_finger_correction():
        if i == 0:
            pass
        else:
            if df.at[i, 'string'] == df.at[i - 1, 'string'] and df.at[i, 'fret'] == df.at[i - 1, 'fret']:
                df.at[i - 1, 'finger'] = df.at[i, 'finger']

    def bend_lower_string_generation():
        if df.at[i, 'string'] == 2:  # Bending on 3rd string
            if bend_start_interval <= 2:  # Less or equal to 2 half steps --> bending with the ring finger
                if max_bending[2] >= bend_start_interval:
                    def bend_func_3rd_str_3rd_finger():
                        if target_number_bends[df.at[i, 'string']] - actual_bends_each_string[df.at[i, 'string']] >= 0:
                            df.at[i, 'string'] = df.at[i, 'string'] + 1
                            df.at[i, 'fret'] = df.at[i, 'fret'] + (4 - bend_start_interval)
                            df.at[i, 'finger'] = 3
                            df.at[i, 'bending'] = bend_start_interval
                            actual_bends_each_string[df.at[i, 'string'] - 1] += 1
                            prev_finger_correction()
                    if i == 0:
                        bend_func_3rd_str_3rd_finger()
                    elif df.at[i - 1, 'finger'] != 3:
                        bend_func_3rd_str_3rd_finger()
                    else:
                        pass
            if bend_start_interval == 3:  # Equal to 3 half steps --> bending with the middle finger
                if max_bending[1] >= bend_start_interval:
                    def bend_3rd_str_2nd_finger():
                        if target_number_bends[df.at[i, 'string']] - actual_bends_each_string[df.at[i, 'string']] >= 0:
                            df.at[i, 'string'] = df.at[i, 'string'] + 1
                            df.at[i, 'fret'] = df.at[i, 'fret'] + (4 - bend_start_interval)
                            df.at[i, 'finger'] = 2
                            df.at[i, 'bending'] = bend_start_interval
                            actual_bends_each_string[df.at[i, 'string'] - 1] += 1
                            prev_finger_correction()
                    if i == 0:
                        bend_func_3rd_str_2nd_finger()
                    elif df.at[i - 1, 'finger'] != 2:
                        bend_func_3rd_str_2nd_finger()
                    else:
                        pass
        else:  # Bending on other strings (not 3rd)
            if bend_start_interval <= 3:  # Less or equal to 3 half steps --> bending with the ring finger
                if max_bending[2] >= bend_start_interval:
                    def bend_func_no3rd_str_3rd_finger():
                        if target_number_bends[df.at[i, 'string']] - actual_bends_each_string[df.at[i, 'string']] >= 0:
                            df.at[i, 'string'] = df.at[i, 'string'] + 1
                            df.at[i, 'fret'] = df.at[i, 'fret'] + (5 - bend_start_interval)
                            df.at[i, 'finger'] = 3
                            df.at[i, 'bending'] = bend_start_interval
                            actual_bends_each_string[df.at[i, 'string'] - 1] += 1
                            prev_finger_correction()

                    if i == 0:
                        bend_func_no3rd_str_3rd_finger()
                    elif df.at[i - 1, 'finger'] != 3:
                        bend_func_no3rd_str_3rd_finger()
                    else:
                        pass
            if bend_start_interval == 4:  # Equal to 4 half steps --> bending with the middle finger
                if max_bending[1] >= bend_start_interval:
                    def bend_no3rd_str_2nd_finger():
                        if target_number_bends[df.at[i, 'string']] - actual_bends_each_string[df.at[i, 'string']] >= 0:
                            df.at[i, 'string'] = df.at[i, 'string'] + 1
                            df.at[i, 'fret'] = df.at[i, 'fret'] + (5 - bend_start_interval)
                            df.at[i, 'finger'] = 2
                            df.at[i, 'bending'] = bend_start_interval
                            actual_bends_each_string[df.at[i, 'string'] - 1] += 1
                            prev_finger_correction()
                    if i == 0:
                        bend_func_no3rd_str_2nd_finger()
                    elif df.at[i - 1, 'finger'] != 3:
                        bend_func_no3rd_str_2nd_finger()
                    else:
                        pass

                        # In case of unison interval and ascending horizon interval

    def unis_asc_bend():
        if df.at[i, 'int'] == "unison" and df.at[i, 'int_horizon'] == "asc":
            if df.at[i, 'finger'] == 1 and df.at[i, 'string'] != 6 and df.at[i + 1, 'finger'] == 1:
                bend_lower_string_generation()

    # In case of unison interval and descending horizon interval

    def unis_desc_bend():
        if no_current_prev_fllw_bending() and df.at[i - 1, 'int'] == "unison" and df.at[i - 1, 'int_horizon'] == "desc":
            if df.at[i, 'finger'] == 1 and df.at[i, 'string'] != 6 and df.at[i - 1, 'finger'] == 1:
                bend_lower_string_generation()
                if df.at[i, 'string'] == df.at[i + 1, 'string'] and df.at[i, 'fret'] == df.at[
                    i + 1, 'fret']:  # If following note is on the same string/fret use the same finger
                    df.at[i + 1, 'finger'] = df.at[i, 'finger']

    # In case of groups of three notes with the first and third of the same pitch and the second higher (within max_bend)

    def three_grp_up():
        bending = df.at[i + 1, 'note_numb'] - df.at[i, 'note_numb']
        if no_current_fllw_bending() and df.at[i + 2, 'bending'] == 0 and df.at[i, 'string'] == df.at[
            i + 2, 'string'] and df.at[i, 'fret'] == df.at[i + 2, 'fret'] and df.at[i, 'note_numb'] == df.at[
            i + 2, 'note_numb'] and 0 < bending <= max_bending[df.at[i, 'finger'] - 1]:
            if target_number_bends[df.at[i, 'string'] - 1] - actual_bends_each_string[df.at[i, 'string'] - 1] >= 0:
                df.at[i + 1, 'string'] = df.at[i, 'string']
                df.at[i + 1, 'fret'] = df.at[i, 'fret']
                df.at[i + 1, 'finger'] = df.at[i, 'finger']
                df.at[i + 1, 'bending'] = bending
                actual_bends_each_string[df.at[i, 'string'] - 1] += 1

                # In case of small descending interval on same string (and same fret with bending)

    def small_int_desc():
        bend_interval = df.at[i, 'note_numb'] - df.at[i + 1, 'note_numb']
        if bend_interval > max(max_bending) or bend_interval < 1 or not no_current_prev_fllw_bending():
            pass
        else:
            if df.at[i, 'string'] == df.at[i + 1, 'string'] and df.at[i - 1, 'fret'] != df.at[i + 1, 'fret']:
                if bend_interval <= max_bending[df.at[i + 1, 'finger'] - 1]:
                    if target_number_bends[df.at[i, 'string'] - 1] - actual_bends_each_string[df.at[i, 'string'] - 1] >= 0:
                        df.at[i, 'fret'] = df.at[i + 1, 'fret']
                        df.at[i, 'finger'] = df.at[i + 1, 'finger']
                        df.at[i, 'bending'] = bend_interval
                        actual_bends_each_string[df.at[i, 'string'] - 1] += 1
                else:
                    pass

                    # In case of small ascending interval on same string

    def small_int_asc():
        bend_interval = df.at[i + 1, 'note_numb'] - df.at[i, 'note_numb']
        if i == len(df.index) - 2 or bend_interval > max(
                max_bending) or bend_interval < 1 or not no_current_prev_fllw_bending():
            pass
        else:
            if df.at[i, 'string'] == df.at[i + 1, 'string']:
                if bend_interval <= max_bending[df.at[i, 'finger']] and df.at[i + 2, 'finger'] != df.at[i, 'finger']:
                    if target_number_bends[df.at[i, 'string'] - 1] - actual_bends_each_string[df.at[i, 'string'] - 1] >= 0:
                        df.at[i + 1, 'fret'] = df.at[i, 'fret']
                        df.at[i + 1, 'finger'] = df.at[i, 'finger']
                        df.at[i + 1, 'bending'] = bend_interval
                        actual_bends_each_string[df.at[i, 'string'] - 1] += 1
                else:
                    pass

                    # In case of note followed by a rest or last note

    def note_rest_end():
        if i == 0:
            if no_current_fllw_bending() and df.at[i, 'fllw_rest'] > 0:
                if df.at[i, 'finger'] == 1 and df.at[i, 'string'] != 6:
                    bend_lower_string_generation()
                    # print("note_rest_end at ID " + str(i))  # <<<<---- Remove
                elif df.at[i, 'finger'] != 1:
                    if target_number_bends[df.at[i, 'string'] - 1] - actual_bends_each_string[df.at[i, 'string'] - 1] >= 0:
                        df.at[i, 'fret'] = df.at[i, 'fret'] - bend_start_interval
                        df.at[i, 'finger'] = 3
                        df.at[i, 'bending'] = bend_start_interval
                        actual_bends_each_string[df.at[i, 'string'] - 1] += 1
                else:
                    pass
        elif i == (len(df.index) - 1):
            if no_current_prev_bending() and (df.at[i, 'finger'] == 1 or df.at[i, 'prec_rest'] > 0):
                bend_lower_string_generation()
        else:
            if no_current_prev_fllw_bending() and df.at[i, 'fllw_rest'] > 0:
                if df.at[i, 'finger'] == 1:
                    bend_lower_string_generation()

    # Bending generation

    for i in range(len(df.index) - 1):
        if df.at[i, 'note_lng_ms'] < bending_min_duration_ms:  # Check min duration
            pass
        else:
            bend_start_interval = find_nearest_lower_note_int(df.at[i, 'note_numb'])
            unis_asc_bend()

    for i in range(1, len(df.index) - 1):
        if df.at[i, 'note_lng_ms'] < bending_min_duration_ms:  # Check min duration
            pass
        else:
            bend_start_interval = find_nearest_lower_note_int(df.at[i, 'note_numb'])
            unis_desc_bend()

    for i in range(len(df.index) - 2):
        if df.at[i, 'note_lng_ms'] < bending_min_duration_ms:  # Check min duration
            pass
        else:
            three_grp_up()

    for i in range(1, len(df.index) - 1):
        if df.at[i, 'note_lng_ms'] < bending_min_duration_ms:  # Check min duration
            pass
        else:
            small_int_desc()

    for i in range(1, len(df.index) - 1):
        if df.at[i, 'note_lng_ms'] < bending_min_duration_ms:  # Check min duration
            pass
        else:
            small_int_asc()

    for i in range(len(df.index)):
        if df.at[i, 'note_lng_ms'] < bending_min_duration_ms:  # Check min duration
            pass
        else:
            bend_start_interval = find_nearest_lower_note_int(df.at[i, 'note_numb'])
            note_rest_end()

    # Initiate again the array with the number of notes on each string, first to sixth (bends application may have changed the distribution)
    number_of_notes_each_string = np.array([0, 0, 0, 0, 0, 0])

    for i in df.index:
        number_of_notes_each_string[df.at[i, 'string'] - 1] += 1


    #############################################
    ################## Vibrato ##################
    #############################################

    vibrato_min_duration_ms = 400  # Min ms note duration to allow a vibrato
    vibrato_hp_min_duration_ms = 800  # Min ms note duration to consider a vibrato highly probable
    always_vibrato_on_longer_notes = "Y"
    always_vibrato_on_compatible_notes = "N"

    vibrato_frequency_dataset = [4.7, 5.2, 5.6, 4.4, 2.6, 2.0]  # Probability of having a vibrato for each string, from the first to the sixth
    vibrato_hp_options = np.array([0, 0, 0, 0, 0, 0])  # Options to insert a high probability vibrato, for each string, first to sixth
    vibrato_options = np.array([0, 0, 0, 0, 0, 0])  # Options to insert vibrato, for each string, first to sixth
    vibrato_hp_options_perc = np.array([0, 0, 0, 0, 0, 0])  # Percentage options to insert a high probability vibrato, for each string, first to sixth
    vibrato_options_perc = np.array([0, 0, 0, 0, 0, 0])  # Percentage options to insert vibrato, for each string, first to sixth

    # Identify notes with high probability of vibrato and those to which vibrato can be applied
    for i in df.index:
        if df.at[i, 'fret'] != 0:
            if df.at[i, 'note_lng_ms'] >= vibrato_hp_min_duration_ms:  # not on open string and enough note duration
                df.at[i, 'vibrato_prob'] = 2
                vibrato_hp_options[df.at[i, 'string'] - 1] += 1
            elif df.at[i, 'note_lng_ms'] >= vibrato_min_duration_ms:  # not on open string and enough note duration
                df.at[i, 'vibrato_prob'] = 1
                vibrato_options[df.at[i, 'string'] - 1] += 1
        else:
            df.at[i, 'vibrato_prob'] = 0

    for i in range(len(number_of_notes_each_string)):
        if number_of_notes_each_string[i] > 0:
            vibrato_hp_options_perc[i] = (vibrato_hp_options[i] * 100 / number_of_notes_each_string[i]).astype(int)
            vibrato_options_perc[i] = (vibrato_options[i] * 100 / number_of_notes_each_string[i]).astype(int)
        else:
            vibrato_hp_options_perc[i] = 0
            vibrato_options_perc[i] = 0

    general_stats_vibrato = np.array([5, 5, 6, 4, 3, 2])

    # Add the vibrato technique

    actual_vibrato_each_string = np.array([0, 0, 0, 0, 0, 0])  # Count vibrato occurrences on each string
    actual_vibrato_each_string_perc = np.array([0, 0, 0, 0, 0, 0])  # Count vibrato occurrences percentage on each string

    for i in df.index:
        if df.at[i, 'vibrato_prob'] == 2:
            if always_vibrato_on_longer_notes == "Y" or vibrato_hp_options_perc[df.at[i, 'string'] - 1] <= \
                    general_stats_vibrato[df.at[i, 'string'] - 1]:
                df.at[i, 'vibrato'] = True
                actual_vibrato_each_string[df.at[i, 'string'] - 1] += 1
            else:
                if vibrato_hp_options_perc[df.at[i, 'string'] - 1] != 0:
                    probability = general_stats_vibrato[df.at[i, 'string'] - 1] / vibrato_hp_options_perc[
                        df.at[i, 'string'] - 1] * 100
                    if randint(0, 100) < probability:
                        df.at[i, 'vibrato'] = True
                        actual_vibrato_each_string[df.at[i, 'string'] - 1] += 1

    for i in range(len(number_of_notes_each_string)):
        if number_of_notes_each_string[i] > 0:
            actual_vibrato_each_string_perc[i] = (
                        actual_vibrato_each_string[i] / number_of_notes_each_string[i] * 100).astype(int)
        else:
            actual_vibrato_each_string_perc[i] = 0

    for i in df.index:
        if df.at[i, 'vibrato_prob'] == 1:
            if always_vibrato_on_compatible_notes == "Y" or (
                    vibrato_hp_options_perc[df.at[i, 'string'] - 1] + vibrato_options_perc[df.at[i, 'string'] - 1]) <= \
                    general_stats_vibrato[df.at[i, 'string'] - 1]:
                df.at[i, 'vibrato'] = True
                actual_vibrato_each_string[df.at[i, 'string'] - 1] += 1
            else:
                if vibrato_options_perc[df.at[i, 'string'] - 1] != 0:
                    probability = (general_stats_vibrato[df.at[i, 'string'] - 1] - actual_vibrato_each_string_perc[
                        df.at[i, 'string'] - 1]) / vibrato_options_perc[df.at[i, 'string'] - 1] * 100
                    if randint(0, 100) < probability:
                        df.at[i, 'vibrato'] = True
                        actual_vibrato_each_string[df.at[i, 'string'] - 1] += 1

    for i in df.index:
        if df.at[i, 'vibrato'] == 0:
            df.at[i, 'vibrato'] = False

    #############################################
    ############ Hammer on / Pull off ###########
    #############################################

    hammer_on_frequency_dataset = np.array([3, 3, 2, 3, 3, 7])  # Probability of having a hammer-on for each string, from the first to the sixth
    pull_off_frequency_dataset = np.array([8, 5, 4, 3, 5, 1])  # Probability of having a hammer-on for each string, from the first to the sixth

    hammer_on_options = np.array([0, 0, 0, 0, 0, 0])  # Options to insert hammer-on, for each string, first to sixth
    pull_off_options = np.array([0, 0, 0, 0, 0, 0])  # Options to insert pull-off, for each string, first to sixth
    hammer_on_options_perc = np.array(
        [0, 0, 0, 0, 0, 0])  # Options percentage to insert hammer-on, for each string, first to sixth
    pull_off_options_perc = np.array(
        [0, 0, 0, 0, 0, 0])  # Options percentage to insert pull-off, for each string, first to sixth


    def legato_test():
        if df.at[i, 'string'] == df.at[i + 1, 'string'] and df.at[i, 'note_numb'] != df.at[i + 1, 'note_numb'] and df.at[i, 'bending'] == 0 and df.at[i + 1, 'bending'] == 0:
            if df.at[i, 'note_numb'] > df.at[i + 1, 'note_numb']:
                # df.at[i, 'po_prob'] = 1
                pull_off_options[df.at[i, 'string'] - 1] += 1
            elif df.at[i, 'note_numb'] < df.at[i + 1, 'note_numb']:
                # df.at[i, 'ho_prob'] = 1
                hammer_on_options[df.at[i, 'string'] - 1] += 1

    for i in range(len(df.index) - 1):
        legato_test()

    hammer_on_target = (number_of_notes_each_string * hammer_on_frequency_dataset / 100).astype(int)
    pull_off_target = (number_of_notes_each_string * pull_off_frequency_dataset / 100).astype(int)

    for i in range(len(number_of_notes_each_string)):
        if number_of_notes_each_string[i] > 0:
            hammer_on_options_perc[i] = (hammer_on_options[i] * 100 / number_of_notes_each_string[i]).astype(int)
            pull_off_options_perc[i] = (pull_off_options[i] * 100 / number_of_notes_each_string[i]).astype(int)
        else:
            hammer_on_options_perc[i] = 0
            pull_off_options_perc[i] = 0

    actual_number_hammer_on = np.array([0, 0, 0, 0, 0, 0])  # Actual number of hammer-on, for each string, first to sixth
    actual_number_pull_off = np.array([0, 0, 0, 0, 0, 0])  # Actual number of pull-off, for each string, first to sixth

    def hammer_on_pull_off():
        if df.at[i, 'string'] == df.at[i + 1, 'string'] and df.at[i, 'note_numb'] != df.at[i + 1, 'note_numb'] and \
                df.at[i, 'bending'] == 0 and df.at[i + 1, 'bending'] == 0:
            if df.at[i, 'note_numb'] > df.at[i + 1, 'note_numb']:
                if pull_off_options_perc[df.at[i, 'string'] - 1] <= \
                        pull_off_frequency_dataset[df.at[i, 'string'] - 1]:
                    df.at[i + 1, 'pull-off'] = True
                    actual_number_pull_off[df.at[i, 'string'] - 1] += 1
                elif pull_off_options_perc[df.at[i, 'string'] - 1] != 0:
                    probability = pull_off_frequency_dataset[df.at[i, 'string'] - 1] / pull_off_options_perc[
                        df.at[i, 'string'] - 1] * 100
                    if randint(0, 100) < probability:
                        df.at[i + 1, 'pull-off'] = True
                        actual_number_pull_off[df.at[i, 'string'] - 1] += 1
            elif df.at[i, 'note_numb'] < df.at[i + 1, 'note_numb']:
                if hammer_on_options_perc[df.at[i, 'string'] - 1] <= \
                        hammer_on_frequency_dataset[df.at[i, 'string'] - 1]:
                    df.at[i + 1, 'hammer-on'] = True
                    actual_number_hammer_on[df.at[i, 'string'] - 1] += 1
                elif hammer_on_options_perc[df.at[i, 'string'] - 1] != 0:
                    probability = hammer_on_frequency_dataset[df.at[i, 'string'] - 1] / \
                                  hammer_on_options_perc[df.at[i, 'string'] - 1] * 100
                    if randint(0, 100) < probability:
                        df.at[i + 1, 'hammer-on'] = True
                        actual_number_hammer_on[df.at[i, 'string'] - 1] += 1

    for i in range(len(df.index) - 1):
        hammer_on_pull_off()

    df.at[0, 'hammer-on'] = False
    df.at[0, 'pull-off'] = False

    #############################################
    ################ Legato slide ###############
    #############################################

    for i in range(len(df.index)-1):
        if df.at[i, 'string'] == df.at[i+1, 'string'] and df.at[i, 'note_numb'] != df.at[i+1, 'note_numb'] and df.at[i, 'bending'] == 0 and df.at[i+1, 'bending'] == 0 and df.at[i, 'finger'] == df.at[i+1, 'finger']:
            df.at[i, 'slide_legato'] = True
        else:
            df.at[i, 'slide_legato'] = False