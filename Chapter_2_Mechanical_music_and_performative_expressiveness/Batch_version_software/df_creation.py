from mido import MidiFile
import midi_import
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import sys

np.set_printoptions(threshold=sys.maxsize)

def df_create():
    global pd_df_notes_list
    global pd_df_notes_list_cleaned
    global tempo
    global ticks_per_beat
    global return_message

    roll_midi_path = midi_import.roll_midi_path

    roll_midi_file = MidiFile(roll_midi_path)  # creates MIDO MidiFile object
    num_midi_tracks = len(roll_midi_file.tracks)
    ticks_per_beat = roll_midi_file.ticks_per_beat

    ##########################################################################
    ####################   Dataframe creation   ##############################
    ##########################################################################

    columns_names = ["noteNmb", "msg", "note", "dtNoteOn", "tDtNoteOn", "dtNoteOff", "tDtNoteOff", "noteLng", "IOI"]
    notes_list = []
    notes_counter = 0
    total_delta_time = 0

    for i in range(len(roll_midi_file.tracks[0])):
        try:
            roll_midi_file.tracks[0][i].tempo
        except:
            pass
        else:
            tempo = roll_midi_file.tracks[0][i].tempo
            break

    for counter in range(len(roll_midi_file.tracks[num_midi_tracks - 1])):

        try:  # I check the presence of delta time and possibly sum it to the total_delta_time - in MIDI .time refers
            # to MIDI delta time
            roll_midi_file.tracks[num_midi_tracks - 1][counter].time
        except:
            pass
        else:
            total_delta_time += roll_midi_file.tracks[num_midi_tracks - 1][counter].time

        try:  # I check if the message is a note
            roll_midi_file.tracks[num_midi_tracks - 1][counter].note
        except:
            pass
        else:  # I collect note data

            # if note on

            if (roll_midi_file.tracks[num_midi_tracks - 1][counter].type == "note_on" and
                    roll_midi_file.tracks[num_midi_tracks - 1][counter].velocity != 0):
                notes_counter += 1
                notes_list.append([notes_counter, "note", roll_midi_file.tracks[num_midi_tracks - 1][counter].note,
                                   roll_midi_file.tracks[num_midi_tracks - 1][counter].time, total_delta_time, "tbp",
                                   "tbp", "tbp", "tbp"])  # "tbp" stands for "to be populated"
                if len(notes_list) == 1:
                    notes_list[0][8] = total_delta_time
                if len(notes_list) > 1:
                    notes_list[len(notes_list) - 1][8] = (total_delta_time - notes_list[len(notes_list) - 2][4])

            # if note off

            elif (roll_midi_file.tracks[num_midi_tracks - 1][counter].type == "note_off") or (
                    roll_midi_file.tracks[num_midi_tracks - 1][counter].type == "note_on" and
                    roll_midi_file.tracks[num_midi_tracks - 1][counter].velocity == 0):
                for v in range(len(notes_list)):
                    if (notes_list[v][1] == "note") and (
                            notes_list[v][2] == roll_midi_file.tracks[num_midi_tracks - 1][counter].note) and (
                            notes_list[v][5] == "tbp"):
                        notes_list[v][5] = roll_midi_file.tracks[num_midi_tracks - 1][counter].time
                        notes_list[v][6] = total_delta_time
                        notes_list[v][7] = notes_list[v][6] - notes_list[v][4]
                        break
    sync_val = 10  # MIDI ticks under which two consecutive notes are considered in sync
    buffer = 0
    for i in range(len(notes_list)):
        if (i < len(notes_list) - 1) and (notes_list[i + 1][8] <= sync_val):
            buffer += notes_list[i][8]
            notes_list[i][8] = "sync"
        elif (i < len(notes_list) - 1) and (notes_list[i + 1][8] > sync_val):
            notes_list[i][8] += buffer
            buffer = 0
        else:
            notes_list[i][8] += buffer

    sync_notes_indexes = []
    for n in range(0, len(notes_list)):
        if notes_list[n][8] == "sync":
            sync_notes_indexes.append(n)

    for g in range(len(sync_notes_indexes)):
        value = int(sync_notes_indexes[g])
        del notes_list[value - g]

    min_val =5  # length in MIDI ticks under which notes are excluded from consideration
    buffer = 0


    for i in range(len(notes_list)):
        if (i < len(notes_list) - 1) and (notes_list[i][7] <= min_val):
            buffer += notes_list[i][8]
            notes_list[i][8] = "short"
        elif (i < len(notes_list) - 1) and (notes_list[i + 1][7] > min_val):
            notes_list[i][8] += buffer
            buffer = 0
        else:
            notes_list[i][8] += buffer

    short_notes_indexes = []
    for n in range(0, len(notes_list)):
        if notes_list[n][8] == "short":
            short_notes_indexes.append(n)

    for g in range(len(short_notes_indexes)):
        value = int(short_notes_indexes[g])
        del notes_list[value - g]

    pd_df_notes_list = pd.DataFrame(notes_list, columns=columns_names)  # I create a Pandas df
    # print(pd_df_notes_list.head(50))

    np_IOIs_array = pd_df_notes_list["IOI"].to_numpy()
    np_IOIs_array_sorted = np.sort(np_IOIs_array).astype('int64')
    IOIs_occurences = np.bincount(np_IOIs_array_sorted)

    # print(np_IOIs_array_sorted)
    # print(IOIs_occurences)

    IOIs_occurences_peaks = find_peaks(IOIs_occurences, height=10, threshold=None, distance=5)

    if len(IOIs_occurences_peaks[0]) > 6:
        return_message = "Too many peaks, not analyzed"
        return("quit")
    else:
        l = len(IOIs_occurences_peaks[0])
        additional_peaks = []
        for i in range(l):
            if (IOIs_occurences_peaks[0][i] * 2) not in range(int(IOIs_occurences_peaks[0][0]),
                                                              int(IOIs_occurences_peaks[0][-1] + 10)):
                additional_peaks.append(IOIs_occurences_peaks[0][i] * 2)

        additional_peaks = np.array(additional_peaks)
        IOIs_occurences_peaks_complete = np.concatenate((IOIs_occurences_peaks[0], additional_peaks))
        IOIs_occurences_peaks_complete = np.sort(IOIs_occurences_peaks_complete)

        # print("#########################################################")
        # print("\nDetected peaks: " + str(IOIs_occurences_peaks_complete) + "\n")
        # print("#########################################################")

        distance_score = []  # I calculate the distance score of each IOI value from the detected peaks
        for i in range(len(IOIs_occurences_peaks_complete)):
            for n in range(len(np_IOIs_array_sorted)):
                if i == 0:
                    distance_score.append(abs(n - IOIs_occurences_peaks_complete[0]))
                else:
                    if abs(n - IOIs_occurences_peaks_complete[i]) < distance_score[n]:
                        distance_score[n] = abs(n - IOIs_occurences_peaks_complete[i])

        # print(distance_score)

        for g in range(len(distance_score)):
            not_appliable = True
            for h in range(len(IOIs_occurences_peaks_complete)):
                range_start = int(IOIs_occurences_peaks_complete[h] // 2)
                range_stop = int(IOIs_occurences_peaks_complete[h] * 1.5)
                if g in range(range_start, range_stop):
                    not_appliable = False
            if not_appliable == True:
                distance_score[g] = "na"

        # print(distance_score)

        distance_score_matched = []

        """
        print(len(np_IOIs_array))
        print(len(distance_score))
        print(distance_score[468])
        for g in range(len(np_IOIs_array)):
            print(distance_score[g])
        """

        for s in range(len(np_IOIs_array)):
            distance_score_matched.append(distance_score[np_IOIs_array[s]])


        # print(pd_df_notes_list.head(20))

        pd_df_notes_list['distance_score'] = distance_score_matched
        pd_df_notes_list_cleaned = pd_df_notes_list.copy()

        pd_df_notes_list_cleaned = pd_df_notes_list_cleaned.loc[pd_df_notes_list_cleaned["distance_score"] != "na"]

        pd_df_notes_list_cleaned['norm_distance_score'] = pd_df_notes_list_cleaned['distance_score'] / \
                                                          pd_df_notes_list_cleaned['IOI'] * 100
        pd_df_notes_list_cleaned = pd_df_notes_list_cleaned.reset_index(drop=True)
        # print("#########################################################")
        # print("Dataframe")
        # print(pd_df_notes_list_cleaned.head(20))
        # print("#########################################################")
