import os
from mido import MidiFile
import mido
import pandas as pd
import numpy as np
import gui

# Declare global variables at the module level
notes_names = None
notes_list_pd_df = None
ticks_per_beat = None
tempo = None
bpm = None
numerator = None
denominator = None


###############################################################
##################### MidFile df creation #####################
###############################################################

def midifile_df_create():
    
    global notes_names, notes_list_pd_df, ticks_per_beat, tempo, bpm, numerator, denominator

    midifile_path = gui.midifile_path

    notes_names = ["C-1", "Cs-1", "D-1", "Ds-1", "E-1", "F-1", "Fs-1", "G-1", "Gs-1", "A-1", "As-1", "B-1", "C0", "Cs0",
                   "D0", "Ds0", "E0", "F0", "Fs0", "G0", "Gs0", "A0", "As0", "B0", "C1", "Cs1", "D1", "Ds1", "E1", "F1",
                   "Fs1", "G1", "Gs1", "A1", "As1", "B1", "C2", "Cs2", "D2", "Ds2", "E2", "F2", "Fs2", "G2", "Gs2",
                   "A2", "As2", "B2", "C3", "Cs3", "D3", "Ds3", "E3", "F3", "Fs3", "G3", "Gs3", "A3", "As3", "B3", "C4",
                   "Cs4", "D4", "Ds4", "E4", "F4", "Fs4", "G4", "Gs4", "A4", "As4", "B4", "C5", "Cs5", "D5", "Ds5",
                   "E5", "F5", "Fs5", "G5", "Gs5", "A5", "As5", "B5", "C6", "Cs6", "D6", "Ds6", "E6", "F6", "Fs6", "G6",
                   "Gs6", "A6", "As6", "B6", "C7", "Cs7", "D7", "Ds7", "E7", "F7", "Fs7", "G7", "Gs7", "A7", "As7",
                   "B7", "C8", "Cs8", "D3", "Ds8", "E8", "F8", "Fs8", "G8", "Gs8", "A8", "As8", "B8", "C9", "Cs9", "D9",
                   "Ds9", "E9", "F9", "Fs9", "G9"]
    
    ##########################################################################
    #######   MIDI object creation and basic metamessages retrieval   ########
    ##########################################################################

    midifile = MidiFile(midifile_path)  # creates MIDO MidiFile object
    # print("// File name: " + str(os.path.splitext(os.path.basename(midifile_path))[0]))
    
    num_midi_tracks = len(midifile.tracks)
    # print("// Number of track in the MIDI file: " + str(num_midi_tracks))
    
    ticks_per_beat = midifile.ticks_per_beat
    # print("// Ticks per beat of the MIDI file: " + str(ticks_per_beat))

    for i in range(len(midifile.tracks[0])):
        try:
            midifile.tracks[0][i].tempo
        except:
            pass
        else:
            tempo = midifile.tracks[0][i].tempo
            # print("// Tempo of the MIDI file: " + str(tempo))
            bpm = int(round(mido.tempo2bpm(tempo), 2))
            # print("// BPM of the MIDI file: " + str(bpm))
            break

    for i in range(len(midifile.tracks[0])):
        try:
            midifile.tracks[0][i].numerator
        except:
            pass
        else:
            numerator = midifile.tracks[0][i].numerator
            denominator = midifile.tracks[0][i].denominator
            # print("// Time signature: " + str(numerator) + "/" + str(denominator) + "\n")
            break

        ##########################################################################
        ####################   Dataframe creation   ##############################
        ##########################################################################

    columns_names = ["note_numb", "note_name", "dt_note_on", "t_dt_note_on", "dt_note_off", "t_dt_note_off", "note_lng",
                     "IOI", "prec_rest", "fllw_rest", "velocity"]
    total_delta_time = 0
    notes_list = []
    note_on_counter = -1

    for counter in range(len(midifile.tracks[num_midi_tracks - 1])):

        try:  # I check the presence of delta time and possibly sum it to the total_delta_time
            midifile.tracks[num_midi_tracks - 1][counter].time
        except:
            pass
        else:
            total_delta_time += midifile.tracks[num_midi_tracks - 1][counter].time

        try:  # I check if the message is a note
            midifile.tracks[num_midi_tracks - 1][counter].note
        except:
            pass
        else:  # I collect note data

            # if note on

            if (midifile.tracks[num_midi_tracks - 1][counter].type == "note_on" and
                    midifile.tracks[num_midi_tracks - 1][counter].velocity != 0):
                note_on_counter += 1
                notes_list.append([midifile.tracks[num_midi_tracks - 1][counter].note,
                                   notes_names[midifile.tracks[num_midi_tracks - 1][counter].note],
                                   midifile.tracks[num_midi_tracks - 1][counter].time, total_delta_time, "tbp", "tbp",
                                   "tbp", "tbp", "tbp", "tbp", midifile.tracks[num_midi_tracks - 1][
                                       counter].velocity])  # "tbp" stands for "to be populated"
                if len(notes_list) == 1:
                    notes_list[0][7] = total_delta_time
                if len(notes_list) > 1:
                    notes_list[len(notes_list) - 1][7] = (total_delta_time - notes_list[len(notes_list) - 2][3])
                notes_list[note_on_counter][8] = notes_list[note_on_counter][2]
                if len(notes_list) > 1:
                    notes_list[note_on_counter - 1][9] = notes_list[note_on_counter][8]

            # if note off

            elif midifile.tracks[num_midi_tracks - 1][counter].type == "note_off" or \
                    midifile.tracks[num_midi_tracks - 1][counter].velocity == 0:
                for v in range(len(notes_list)):
                    if (notes_list[v][0] == midifile.tracks[num_midi_tracks - 1][counter].note) and (
                            notes_list[v][4] == "tbp"):
                        notes_list[v][4] = midifile.tracks[num_midi_tracks - 1][counter].time
                        notes_list[v][5] = total_delta_time
                        notes_list[v][6] = notes_list[v][5] - notes_list[v][3]
                        break

            notes_list_pd_df = pd.DataFrame(notes_list, columns=columns_names)

    notes_list_pd_df.iat[-1, 9] = 0 # manually sets 0 for the pause following the last note

    ms_per_tick = tempo / ticks_per_beat / 1000

    notes_list_pd_df['t_dt_note_on_ms'] = np.rint(notes_list_pd_df['t_dt_note_on'] * ms_per_tick).astype(np.int64)
    notes_list_pd_df['t_dt_note_off_ms'] = np.rint(notes_list_pd_df['t_dt_note_off'] * ms_per_tick).astype(np.int64)
    notes_list_pd_df['note_lng_ms'] = np.rint(notes_list_pd_df['note_lng'] * ms_per_tick).astype(np.int64)
    notes_list_pd_df['IOI_ms'] = np.rint(notes_list_pd_df['IOI'] * ms_per_tick).astype(np.int64)

    number_of_notes = len(notes_list_pd_df.index)