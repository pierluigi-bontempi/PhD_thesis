import io
import sys
import time
import numpy as np
import random
from itertools import chain
from scipy.stats import beta
from math import trunc

############################################################################################
############################# Creation of the global variables #############################
############################################################################################

midi_notes_dict = {}            # dict - all the 128 possible MIDI notes, {0: "C-1", 1: "Cs-1", ...}
midi_notes_list = []            # list -  all the 128 possible MIDI notes, ["C-1", "Cs-1", ...}

chosen_instrument = []          # list -  list with description of the available instruments
instrument_selection = 0        # int - ID the selected instrument
s_max = 0                       # int - number of strings of the selected instrument
f_max = 0                       # int -  number of frets of the selected instrument
strings_tuning_MIDI = []        # list - tuning of the strings - MIDI note numbers
lowest_note = 0                 # int - lowest note possible on the selected instrument
highest_note = 0                # int - highest note possible on the selected instrument
PlayableSounds = ""             # string - all the playable notes on the selected instrument - for CPlex
playable_sounds_MIDI = []       # list -  all the playable notes on the selected instrument - MIDI note numbers
OpenStrings = ""                # string - all the notes of the open strings on the selected instrument - for CPlex
Combinations = ""               # string - all the string/fret combinations on the selected instrument - for CPlex

chords = []                     # list - all the supported chords
scales = []                     # list - all the supported scales
root_MIDI = 0                   # int - MIDI note number of the root of the chord and scale
chord_type_id = 0               # int - index of the chord type
scale_type_id = 0               # int - index of the scale type
chosen_chord_notes_MIDI = []    # np array - MIDI note numbers belonging to the selected chord, in the first one or two octaves (ex. [0,4,7] --> C major)
chosen_chord_MIDI = []          # np array - MIDI note numbers of the chord tones in the full instrument range
chosen_scale_notes_MIDI = []    # np array - MIDI note numbers of the scale notes in the first one or two octaves
chosen_scale_MIDI = []          # np array - MIDI note numbers of the scale notes in the full instrument range

bpm = 0                         # int - beats per minute
notes_durations_sequence = []   # list -  duration of the notes in MIDI ticks
onbeat_sequence = []            # list -  boolean list for onbeat parameter
durations_sequence_ms = []      # np array - duration of the notes in ms
availableTime = ""              # string - time available to play each note - for CPlex

starting_note = 0               # int - starting note - MIDI note number
starting_note_index = 0         # int - starting note index in chosen_scale_MIDI
length_of_sequence = 0          # int - length of the melodic sequence
generated_sequence = []         # list -  sequence of MIDI note numbers of the generated melody
note = ""                       # string - sequence of notes - for CPlex

lambda_HA = ""                  # string - hammer on sequence - for CPlex
lambda_PU = ""                  # string - pull off - for CPlex
lambda_VI = ""                  # string - vibrato sequence - for CPlex
lambda_DS = ""                  # string - legato slide sequence - for CPlex
lambda_BE = ""                  # string - bending on sequence - for CPlex

t_PC, t_SC, d_HS, d_DH, HS_max, FS_max, f_lb, f_ub, BE_max, q_NO, q_AF, q_AS = 0, 0, 0, 0, [], [], 0, 0, [], 0, 0, 0  # user preferences

time_of_generation = 0          # int - epoch to name the melodies


############################################################################################
####################### Generation of MIDI notes list and dictionary #######################
############################################################################################

# notes_list

notes = ["C", "Cs", "D", "Ds", "E", "F", "Fs", "G", "Gs", "A", "As", "B"]

# MIDI notes dictionary and list generation

octave = -1
notes_dict = {0: "C", 1: "Cs", 2: "D", 3: "Ds", 4: "E", 5: "F", 6: "Fs", 7: "G", 8: "Gs", 9: "A", 10: "As", 11: "B"}

for i in range(128):
    mod = i % 12
    midi_notes_dict[i] = str(notes_dict[mod]) + str(octave)
    midi_notes_list.append([i, str(notes_dict[mod]) + str(octave)])
    if mod == 0 and i != 0:
        octave += 1


############################################################################################
########################## Generation of the instrument setup data #########################
############################################################################################


def instrument_setup():
    global midi_notes_dict, midi_notes_list, strings_tuning_MIDI, f_max, s_max, lowest_note, highest_note, playable_sounds_MIDI, PlayableSounds, \
        OpenStrings, Combinations, chosen_instrument, instrument_selection

    s_max = 0  # int - number of strings of the selected instrument
    f_max = 0  # int -  number of frets of the selected instrument
    strings_tuning_MIDI = []  # list - tuning of the strings - MIDI note numbers
    lowest_note = 0  # int - lowest note possible on the selected instrument
    highest_note = 0  # int - highest note possible on the selected instrument
    PlayableSounds = ""  # string - all the playable notes on the selected instrument - for CPlex
    playable_sounds_MIDI = []  # list -  all the playable notes on the selected instrument - MIDI note numbers
    OpenStrings = ""  # string - all the notes of the open strings on the selected instrument - for CPlex
    Combinations = ""  # string - all the string/fret combinations on the selected instrument - for CPlex

    def strings_tuning_MIDI_func(strings_tuning_fn, strings_tuning_MIDI_fn):
        global strings_tuning_MIDI
        strings_tuning_MIDI = []
        for m in range(len(strings_tuning_fn)):
            for t in range(128):
                if midi_notes_list[t][1] == strings_tuning_fn[m]:
                    strings_tuning_MIDI_fn.append(t)
                    break
        strings_tuning_MIDI = strings_tuning_MIDI_fn

    instrument_selection = random.randint(0, 5)
    if instrument_selection > 2:
        instrument_selection = 0

    if instrument_selection == 0:
        strings_tuning = ["E2", "A2", "D3", "G3", "B3", "E4"]
        strings_tuning_MIDI_func(strings_tuning, strings_tuning_MIDI)
        f_max = 24
        s_max = 6
    elif instrument_selection == 1:
        strings_tuning = ["D2", "A2", "D3", "G3", "B3", "E4"]
        strings_tuning_MIDI_func(strings_tuning, strings_tuning_MIDI)
        f_max = 24
        s_max = 6
    elif instrument_selection == 2:
        strings_tuning = ["B1", "E2", "A2", "D3", "G3", "B3", "E4"]
        strings_tuning_MIDI_func(strings_tuning, strings_tuning_MIDI)
        f_max = 24
        s_max = 7

    chosen_instrument = ["6-string electric guitar, standard tuning (E2 -> E4)",
                         "6-string electric guitar, Drop-D tuning (D2 -> E4)",
                         "7-string electric guitar, standard tuning with added low B (B1 -> E4)"]

    strings_notes = []
    for string in range(s_max):
        strings_notes.append([strings_tuning_MIDI[string]])
        for fret in range(1, f_max + 1):
            strings_notes[string].append(strings_notes[string][fret - 1] + 1)

    strings_notes_np = np.array(strings_notes)
    lowest_note = np.min(strings_notes_np)
    highest_note = np.max(strings_notes_np)

    # Generation of the PlayableSounds data

    PlayableSounds = ""
    playable_sounds_MIDI = []
    note = lowest_note
    for hn_ln in range(highest_note - lowest_note + 1):
        PlayableSounds = PlayableSounds + str(midi_notes_dict[note]) + ","
        playable_sounds_MIDI.append(int(note))
        note += 1
    PlayableSounds = PlayableSounds[:-1]

    # Generation of the OpenStrings data

    OpenStrings = ""

    for ln_hn in range(lowest_note, highest_note + 1):
        open_string_found = False
        for s in range(s_max):
            if ln_hn == strings_notes[s][0]:
                OpenStrings = OpenStrings + "{" + str(s_max - s) + "},"
                open_string_found = True
                break
        if not open_string_found:
            if ln_hn < highest_note:
                OpenStrings = OpenStrings + "{},"
            else:
                OpenStrings = OpenStrings + "{}"

    # Generation of the Combinations data

    Combinations = ""

    for i in range(lowest_note, highest_note + 1):
        Combinations = Combinations + "{"
        combination_found = False
        for s in range(s_max):
            for f in range(1, f_max + 1):
                if i == strings_notes[s][f]:
                    Combinations = Combinations + "<" + str(s_max - s) + "," + str(f) + ">,"
                    combination_found = True
                    break
        if combination_found:
            Combinations = Combinations[:-1]
        if i < highest_note:
            Combinations = Combinations + "},"
        else:
            Combinations = Combinations + "}"

    """
    print("\n################## Output of instrument_setup() function ##################\n")

    print("\nChosen instrument: " + str(chosen_instrument[instrument_selection]))

    print("\nS_MAX: " + str(s_max))

    print("\nF_MAX: " + str(f_max))

    print("\nSTRINGS TUNING MIDI")
    print(strings_tuning_MIDI)

    print("\nPLAYABLE SOUNDS")
    print(PlayableSounds)

    print("\nPLAYABLE SOUNDS MIDI")
    print(playable_sounds_MIDI)

    print("\nOPEN STRINGS")
    print(OpenStrings)

    print("\nCOMBINATIONS")
    print(Combinations)
    """

############################################################################################
###################### Generation of the reference chord and scale data ####################
############################################################################################


def scale_chord_generation():
    global lowest_note, highest_note, root_MIDI, chord_type_id, chosen_chord_notes_MIDI, chosen_chord_MIDI, scale_type_id, chosen_scale_notes_MIDI, \
        chosen_scale_MIDI, chords, scales

    root_MIDI = 0  # int - MIDI note number of the root of the chord and scale
    chord_type_id = 0  # int - index of the chord type
    scale_type_id = 0  # int - index of the scale type
    chosen_chord_notes_MIDI = []  # np array - MIDI note numbers belonging to the selected chord, in the first one or two octaves (ex. [0,4,7] --> C major)
    chosen_chord_MIDI = []  # np array - MIDI note numbers of the chord tones in the full instrument range
    chosen_scale_notes_MIDI = []  # np array - MIDI note numbers of the scale notes in the first one or two octaves
    chosen_scale_MIDI = []  # np array - MIDI note numbers of the scale notes in the full instrument range

    # scales and chords

    scales = [["major", [0, 2, 4, 5, 7, 9, 11]],
              ["minor", [0, 2, 3, 5, 7, 8, 10]],
              ["min_pent", [0, 3, 5, 7, 10]],
              ["blues", [0, 3, 5, 6, 7, 10]],
              ["mixolydian", [0, 2, 4, 5, 7, 9, 10]]]
    chords = [["major_chord", [0, 4, 7]],
              ["minor_chord", [0, 3, 7]],
              ["seventh_chord", [0, 4, 7, 10]]]

    # random choose root

    root_MIDI = random.randint(0, 11)

    # Random choose chord

    chord_type_id = random.randint(0, 2)

    # (Random) choose scale

    if chord_type_id == 0:
        scale_type_id = 0
    elif chord_type_id == 1:
        scale_type_id = random.randint(1, 3)
    elif chord_type_id == 2:
        scale_type_id = 4

    chosen_chord_notes_MIDI = np.array(chords[chord_type_id][1]) + root_MIDI

    chosen_chord_MIDI = chosen_chord_notes_MIDI
    for octave_count in range(1, 11):
        new_octave = chosen_chord_notes_MIDI + (octave_count * 12)
        chosen_chord_MIDI = np.append(chosen_chord_MIDI, new_octave)

    chosen_chord_MIDI = chosen_chord_MIDI[(lowest_note <= chosen_chord_MIDI)]
    chosen_chord_MIDI = chosen_chord_MIDI[chosen_chord_MIDI <= highest_note]

    chosen_scale_notes_MIDI = np.array(scales[scale_type_id][1]) + root_MIDI

    chosen_scale_MIDI = chosen_scale_notes_MIDI
    for i in range(1, 11):
        new_octave = chosen_scale_notes_MIDI + (i * 12)
        chosen_scale_MIDI = np.append(chosen_scale_MIDI, new_octave)

    chosen_scale_MIDI = chosen_scale_MIDI[(lowest_note <= chosen_scale_MIDI)]
    chosen_scale_MIDI = chosen_scale_MIDI[chosen_scale_MIDI <= highest_note]

    """
    print("\n################## Output of scale_chord_generation() function ##################\n")
    print("Root note MIDI: " + str(notes[root_MIDI]))
    print("Chord type: " + str(chords[chord_type_id][0]))
    print("Scale type: " + str(scales[scale_type_id][0]))
    print("\nChosen chord notes MIDI: ")
    print(chosen_chord_notes_MIDI)
    print("\nComplete chosen chord notes MIDI: ")
    print(chosen_chord_MIDI)
    print("\nChosen scale notes MIDI: ")
    print(chosen_scale_notes_MIDI)
    print("\nComplete chosen scale notes MIDI: ")
    print(chosen_scale_MIDI)
    """

############################################################################################
############################# Generation of the rhythm structure ###########################
############################################################################################

def rhythm_generation():
    global bpm, notes_durations_sequence, onbeat_sequence, durations_sequence_ms, availableTime

    bpm = 0  # int - beats per minute
    notes_durations_sequence = []  # list -  duration of the notes in MIDI ticks
    onbeat_sequence = []  # list -  boolean list for onbeat parameter
    durations_sequence_ms = []  # np array - duration of the notes in ms
    availableTime = ""  # string - time available to play each note - for CPlex

    # rhythms list [virtuosity level,number of beats,durations,onbeat]

    rhythm_struct = [[1, 8, [480, 240, 240, 240, 240, 240, 240, 960, 480, 240, 240],
                      [1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0]],
                     [1, 8, [240, 120, 120, 240, 240, 240, 240, 480, 480, 480, 480, 240, 240],
                      [1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0]],
                     [1, 8, [160, 160, 160, 160, 160, 160, 480, 480, 240, 240, 240, 240, 240, 240, 240, 240],
                      [1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0]],
                     [1, 8, [160, 320, 320, 160, 160, 160, 160, 160, 160, 160, 480, 480, 480, 480],
                      [1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1]],
                     [2, 8,
                      [320, 160, 160, 160, 160, 320, 160, 160, 160, 160, 160, 160, 160, 160, 160, 160, 480, 160, 160,
                       160],
                      [1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0]],
                     [2, 8, [240, 120, 120, 120, 120, 120, 120, 240, 240, 480, 480, 160, 160, 160, 240, 240, 480],
                      [1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1]],
                     [2, 8,
                      [160, 160, 160, 160, 160, 160, 120, 120, 120, 120, 480, 160, 160, 160, 160, 160, 160, 120, 120,
                       720],
                      [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0]],
                     [2, 8,
                      [240, 240, 240, 240, 240, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 480, 480, 160, 160,
                       160],
                      [1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0]],
                     [3, 8,
                      [120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 240, 120, 120,
                       120, 120, 120, 120, 160, 160, 160, 160, 160, 160],
                      [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0]],
                     [3, 8,
                      [120, 240, 120, 120, 240, 120, 120, 240, 120, 120, 240, 120, 120, 120, 120, 120, 120, 120, 120,
                       120, 120, 120, 240, 120, 120, 120, 120],
                      [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0]],
                     [3, 8,
                      [80, 80, 80, 120, 120, 80, 80, 80, 120, 120, 80, 80, 80, 120, 120, 80, 80, 80, 120, 120, 80, 80,
                       80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 480],
                      [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
                       1, 0, 0, 0, 0, 0, 1]],
                     [3, 8,
                      [120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 120, 80, 80, 80, 80, 80, 80, 120, 240,
                       120, 240, 120, 120, 240, 240, 80, 80, 80, 80, 80, 80],
                      [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]]]

    # bpm random choose

    bpm = random.randint(60, 160)

    # transition matrix
    # 1 = easy; 2 = medium; 3 = expert

    transition_matrix = {
        1: {1: 0.6, 2: 0.3, 3: 0.1},
        2: {1: 0.2, 2: 0.6, 3: 0.2},
        3: {1: 0.1, 2: 0.3, 3: 0.6}
    }

    def generate_markov_sequence(start_state, length):
        current_state = start_state
        sequence = [current_state]

        for _ in range(length - 1):
            next_state_probs = list(transition_matrix[current_state].items())
            next_states, probabilities = zip(*next_state_probs)
            next_state = random.choices(next_states, probabilities)[0]
            sequence.append(next_state)
            current_state = next_state

        return sequence

    rhythm_modules_sequence = generate_markov_sequence(random.randint(1, 3), 8)
    # print(rhythm_modules_sequence)

    notes_durations_sequence = []
    onbeat_sequence = []
    for rhythm_module in range(len(rhythm_modules_sequence)):
        rand_value = random.randint(1, 3)
        notes_durations_sequence.append(rhythm_struct[rhythm_modules_sequence[rhythm_module] * rand_value][2])
        onbeat_sequence.append(rhythm_struct[rhythm_modules_sequence[rhythm_module] * rand_value][3])

    notes_durations_sequence = list(chain.from_iterable(notes_durations_sequence))

    MIDI_tick_duration_ms = 60000 / bpm / 480
    durations_sequence_ms = np.array(notes_durations_sequence)
    durations_sequence_ms = durations_sequence_ms * MIDI_tick_duration_ms
    durations_sequence_ms = np.rint(durations_sequence_ms)

    availableTime = "1000,"
    for i in range(len(durations_sequence_ms) - 1):
        t = int(durations_sequence_ms[i])
        availableTime = availableTime + str(t) + ","
    availableTime = availableTime[:-1]

    onbeat_sequence = list(chain.from_iterable(onbeat_sequence))

    """
    print("\n################## Output of rhythm_generation() function ##################\n")

    print("\nBPM: " + str(bpm))

    print("\nDURATIONS SEQUENCE")
    print(notes_durations_sequence)
    print(len(notes_durations_sequence))

    print("\nDURATIONS SEQUENCE MS")
    print(durations_sequence_ms)
    print(len(durations_sequence_ms))

    print("\nAVAILABLE TIME")
    print(availableTime)

    print("\nONBEAT SEQUENCE")
    print(onbeat_sequence)
    print(len(onbeat_sequence))
    """
    
############################################################################################
########################## Generation of the sequence of the notes #########################
############################################################################################


# Calculate transition probabilities based on a beta distribution

def calculate_platykurtic_probabilities(current, alpha, beta_param, onbeat):
    global chosen_scale_MIDI, chosen_chord_MIDI, midi_notes_list

    # move the center of the bell + or - one position
    random_value = random.randint(-1, 1)
    current += random_value

    # normalize the numbers to a range [0, 1] for the beta distribution
    min_num, max_num = current - 7, current + 7

    numbers = range(min_num, max_num)

    normalized_numbers = (np.array(numbers) - min_num) / (max_num - min_num)
    normalized_current = (current - min_num) / (max_num - min_num)

    # Calculate the distances
    distances = np.abs(normalized_numbers - normalized_current)

    # Beta PDF values for the distances
    probs = beta.pdf(distances, alpha, beta_param)
    # print(type(probs))
    # print(probs)

    if onbeat == 1:
        #print("onbeat note")
        chord_tones_list = []
        for i in range(len(chosen_scale_MIDI)):
            if chosen_scale_MIDI[i] in chosen_chord_MIDI:
                chord_tones_list.append(1)
            else:
                chord_tones_list.append(0)
        # print(chord_tones_list)

        for i in range(min_num, max_num):
            # print(i)
            if i in range(len(chord_tones_list)):
                # print("In range")
                if chord_tones_list[i] == 1:
                    # print(chord_tones_list[i])
                    probs[i - current] *= 2
                # print(midi_notes_list[chosen_scale_MIDI[i]])
            else:
                pass
        # print("NEW PROBS")
        # print(probs)

    else:
        pass

    probs[7 - random_value] /= 3  # to avoid frequent repetitions of the same note
    # print(probs[7 - random_value])
    # print(probs)
    return probs / np.sum(probs)  # Normalize


# Generate the melody

def melody_generation():
    global notes_durations_sequence, length_of_sequence, starting_note, starting_note_index, note, generated_sequence, durations_sequence_ms

    starting_note = chosen_scale_MIDI[random.randint(5, len(chosen_scale_MIDI)-1)]
    starting_note_index = np.where(chosen_scale_MIDI == starting_note)[0][0]

    def generate_markov_sequence(length, alpha=1.0, beta_param=5.0):
        global notes_durations_sequence, starting_note_index
        # print(length)
        current = starting_note_index
        sequence = [current]

        for counter in range(length - 1):
            # Calculate base probabilities using the platykurtic beta distribution
            if onbeat_sequence[counter] == 1:
                onbeat = 1
            else:
                onbeat = 0
            base_probs = calculate_platykurtic_probabilities(current, alpha, beta_param, onbeat)

            # Choose the next number
            min_num, max_num = current - 7, current + 7
            numbers = range(min_num, max_num)
            next_number = random.choices(numbers, base_probs)[0]
            if next_number < 0:
                if onbeat == 0:
                    max_jump = trunc(durations_sequence_ms[
                                         counter] / 25 / 3)  # 25 is the highest t_PC value, must be changed if user settings are changed
                    next_number = random.randint(0, min(max_jump, len(chosen_scale_MIDI) - 1))
                else:
                    max_jump = trunc(durations_sequence_ms[counter] / 25 / 3)
                    next_number_chord_tone = chosen_chord_MIDI[
                        random.randint(0, min(max_jump, len(chosen_chord_MIDI) - 1))]
                    next_number = np.where(chosen_scale_MIDI == next_number_chord_tone)[0][0]
            elif next_number > len(chosen_scale_MIDI) - 1:
                if onbeat == 0:
                    max_jump = trunc(durations_sequence_ms[counter] / 25 / 3)
                    next_number = random.randint(len(chosen_scale_MIDI) - max_jump, len(chosen_scale_MIDI) - 1)
                else:
                    max_jump = trunc(durations_sequence_ms[counter] / 25 / 3)
                    next_number_chord_tone = chosen_chord_MIDI[
                        random.randint(len(chosen_chord_MIDI) - max_jump, len(chosen_chord_MIDI) - 1)]
                    next_number = np.where(chosen_scale_MIDI == next_number_chord_tone)[0][0]

            sequence.append(next_number)
            current = next_number

        return sequence

    length_of_sequence = len(notes_durations_sequence)  # Length of the generated sequence

    # Generate the sequence
    generated_sequence_indexes = generate_markov_sequence(length_of_sequence)

    # print("\nMIDI notes indexes sequence")
    # print(generated_sequence_indexes)

    generated_sequence = []
    for i in generated_sequence_indexes:
        generated_sequence.append(int(chosen_scale_MIDI[i]))

    note = ""
    for i in generated_sequence_indexes:
        note = note + midi_notes_dict[chosen_scale_MIDI[i]] + ","
    note = note[:-1]

    """
    print("\n################## Output of melody_generation() function ##################\n")

    print("Starting note: " + str(starting_note))
    print("Starting note index: " + str(starting_note_index))

    print("\nGENERATED SEQUENCE MIDI")
    print(generated_sequence)
    print(len(generated_sequence))

    print("\nNOTE")
    print(note)
    print(len(note))
    """


############################################################################################
################################ Insertion of the techniques ###############################
############################################################################################


def articulations_generation():
    global generated_sequence, lambda_HA, lambda_PU, lambda_VI, lambda_DS, lambda_BE

    lambda_HA = ""
    lambda_PU = ""
    lambda_VI = ""
    lambda_DS = ""
    lambda_BE = ""

    ################################################
    ################################################

    hammer_on_list = [0]

    for i in range(1, len(generated_sequence)):
        interval = generated_sequence[i] - generated_sequence[i - 1]
        if 1 < interval < 4:
            if random.randint(1, 100) > 70:
                hammer_on_list.append(1)
            else:
                hammer_on_list.append(0)
        else:
            hammer_on_list.append(0)

    for i in hammer_on_list:
        lambda_HA = lambda_HA + str(i) + ","
    lambda_HA = lambda_HA[:-1]

    # print(len(hammer_on_list))

    ################################################
    ################################################

    pull_off_list = [0]

    for i in range(1, len(generated_sequence)):
        interval = generated_sequence[i] - generated_sequence[i - 1]
        if -1 > interval > -4:
            if random.randint(1, 100) > 70:
                pull_off_list.append(1)
            else:
                pull_off_list.append(0)
        else:
            pull_off_list.append(0)

    for i in pull_off_list:
        lambda_PU = lambda_PU + str(i) + ","
    lambda_PU = lambda_PU[:-1]

    # print(len(pull_off_list))

    ################################################
    ################################################

    vibrato_list = []

    for i in range(len(durations_sequence_ms)):
        if durations_sequence_ms[i] > 500:
            vibrato_list.append(1)
        else:
            vibrato_list.append(0)

    for i in vibrato_list:
        lambda_VI = lambda_VI + str(i) + ","
    lambda_VI = lambda_VI[:-1]

    # print(len(vibrato_list))

    ################################################
    ################################################

    slide_list = [0]

    for i in range(1, len(generated_sequence)):
        interval = abs(generated_sequence[i] - generated_sequence[i - 1])
        if hammer_on_list[i] == 0 and pull_off_list[i] == 0 and interval > 0:
            if random.randint(1, 100) > 95:
                slide_list.append(1)
            else:
                slide_list.append(0)
        else:
            slide_list.append(0)

    for i in slide_list:
        lambda_DS = lambda_DS + str(i) + ","
    lambda_DS = lambda_DS[:-1]

    # print(len(slide_list))

    ################################################
    ################################################

    bending_list = []

    for i in range(len(durations_sequence_ms)):
        if durations_sequence_ms[i] > 250:
            valid_lower_notes = chosen_scale_MIDI[(generated_sequence[i] > chosen_scale_MIDI)]
            if len(valid_lower_notes) > 0:
                nearest_lower_note = np.max(valid_lower_notes)
                bend_value = generated_sequence[i] - nearest_lower_note
                if hammer_on_list[i] == 0 and pull_off_list[i] == 0 and slide_list[i] == 0:
                    if random.randint(1, 100) > 70:
                        bending_list.append(bend_value)
                    else:
                        bending_list.append(0)
                else:
                    bending_list.append(0)
            else:
                bending_list.append(0)
        else:
            bending_list.append(0)

    for i in bending_list:
        lambda_BE = lambda_BE + str(i) + ","
    lambda_BE = lambda_BE[:-1]

    # print(len(bending_list))
    # print(len(generated_sequence))
    # print(len(durations_sequence_ms))

    """
    print("\n################## Output of articulation_generation() function ##################\n")

    print("\nLAMBDA HA")
    print(lambda_HA)
    print("\nLAMBDA PU")
    print(lambda_PU)
    print("\nLAMBDA VI")
    print(lambda_VI)
    print("\nLAMBDA DS")
    print(lambda_DS)
    print("\nLAMBDA BE")
    print(lambda_BE)
    """

############################################################################################
############################### Insertion of user preferences #############################
############################################################################################


def user_preferences(level, quality):

    global t_PC, t_SC, d_HS, d_DH, HS_max, FS_max, f_lb, f_ub, BE_max, q_NO, q_AF, q_AS

    user_skills = level
    quality_option = quality

    if user_skills == "beginner":
        t_PC = 25
        t_SC = 15
        d_HS = 50
        d_DH = 10
        HS_max = [0, 1, 1, 1]
        FS_max = [[0, 1, 2, 3], [1, 0, 1, 2], [2, 1, 0, 1], [3, 2, 1, 0]]
        f_lb = 7
        f_ub = 12
        BE_max = [0, 2, 3, 0]
    if user_skills == "intermediate":
        t_PC = 15
        t_SC = 10
        d_HS = 40
        d_DH = 20
        HS_max = [0, 1, 1, 2]
        FS_max = [[0, 1, 2, 3], [1, 0, 1, 2], [2, 1, 0, 1], [3, 2, 1, 0]]
        f_lb = 5
        f_ub = 15
        BE_max = [1, 2, 3, 0]
    if user_skills == "advanced":
        t_PC = 10
        t_SC = 8
        d_HS = 30
        d_DH = 30
        HS_max = [0, 1, 2, 3]
        FS_max = [[0, 1, 2, 3], [1, 0, 1, 2], [2, 1, 0, 1], [3, 2, 1, 0]]
        f_lb = 3
        f_ub = 17
        BE_max = [2, 3, 4, 0]

    if quality_option == "NO":
        q_NO = 0.6
        q_AF = 0.2
        q_AS = 0.2
    if quality_option == "AF":
        q_NO = 0.2
        q_AF = 0.6
        q_AS = 0.2
    if quality_option == "AS":
        q_NO = 0.2
        q_AF = 0.2
        q_AS = 0.6


number_of_solos = int(input("Please type the number of the solos to be generated. Each solo will generate 9 .dat files, with different optimization model settings"))


def batch_generation(iterations):
    global chosen_instrument, instrument_selection, chords, scales, time_of_generation, time_of_generation

    def capture_function_output(func):
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            func()
            return captured_output.getvalue()
        finally:
            sys.stdout = sys.__stdout__

    def generate_common_data():
        global time_of_generation

        time_of_generation = int(time.time() * 10000)
        instrument_setup()
        scale_chord_generation()
        rhythm_generation()
        melody_generation()
        articulations_generation()

    def print_common_data():
        print("\n// GENERAL INFO")
        print("\n// Instrument: " + str(chosen_instrument[instrument_selection]))
        print("// Auto-generated lead part n. " + str(time_of_generation))
        print("// Scale: " + str(notes[root_MIDI]) + " " + str(str(scales[scale_type_id][0])))
        print("// Chord: " + str(notes[root_MIDI]) + " " + str(str(chords[chord_type_id][0])))
        print("// BPM: " + str(bpm))

        print("\n// INSTRUMENT")
        print("\ns_max = " + str(s_max) + ";")
        print("f_max = " + str(f_max) + ";")
        print("\nPlayableSounds  = {" + str(PlayableSounds) + "};")
        print("\nOpenStrings = [" + str(OpenStrings) + "];")
        print("\nCombinations = [" + str(Combinations) + "];")

        print("\n// MELODY")
        print("\nm = " + str(len(durations_sequence_ms)) + ";")
        print("note = [" + str(note) + "];")
        print("availableTime = [" + str(availableTime) + "];")
        print("\nlambda_HA = [" + str(lambda_HA) + "];")
        print("lambda_PU = [" + str(lambda_PU) + "];")
        print("lambda_VI = [" + str(lambda_VI) + "];")
        print("lambda_DS = [" + str(lambda_DS) + "];")
        print("lambda_BE = [" + str(lambda_BE) + "];")

    def print_user_preferences():
        print("\n\n//time")
        print("\nt_PC = " + str(t_PC) + ";")
        print("t_SC = " + str(t_SC) + ";")
        print("\n//discomfort parameters")
        print("\nd_HS = " + str(d_HS) + ";")
        print("d_DH = " + str(d_DH) + ";")
        print("HS_max = " + str(HS_max) + ";")
        print("FS_max = " + str(FS_max) + ";")
        print("f_lb = " + str(f_lb) + ";")
        print("f_ub = " + str(f_ub) + ";")
        print("\n//Quality [each value >= 0, sum = 1]")
        print("\nq_NO = " + str(q_NO) + ";")
        print("q_AF = " + str(q_AF) + ";")
        print("q_AS = " + str(q_AS) + ";")
        print("BE_max = " + str(BE_max) + ";")

    for counter in range(number_of_solos):
        generate_common_data()

        ############################################################################
        ############################################################################

        # Generation solo 1 - NO - beginner
        user_preferences("beginner", "NO")
        ########### GENERATE .dat FILE ###########
        filename = "Lead part " + str(time_of_generation) + " - beginner - NO.dat"
        with open(filename, 'a') as file:
            file.write(capture_function_output(print_common_data))
            file.write("\n// User preferences combination: beginner - NO")
            file.write(capture_function_output(print_user_preferences))

        ############################################################################
        ############################################################################

        # Generation solo 1 - NO - intermediate
        user_preferences("intermediate", "NO")
        ########### GENERATE .dat FILE ###########
        filename = "Lead part " + str(time_of_generation) + " - intermediate - NO.dat"
        with open(filename, 'a') as file:
            file.write(capture_function_output(print_common_data))
            file.write("\n// User preferences combination: intermediate - NO")
            file.write(capture_function_output(print_user_preferences))

        ############################################################################
        ############################################################################

        # Generation solo 1 - NO - advanced
        user_preferences("advanced", "NO")
        ########### GENERATE .dat FILE ###########
        filename = "Lead part " + str(time_of_generation) + " - advanced - NO.dat"
        with open(filename, 'a') as file:
            file.write(capture_function_output(print_common_data))
            file.write("\n// User preferences combination: advanced - NO")
            file.write(capture_function_output(print_user_preferences))

        ############################################################################
        ############################################################################

        # Generation solo 1 - AF - beginner
        user_preferences("beginner", "AF")
        ########### GENERATE .dat FILE ###########
        filename = "Lead part " + str(time_of_generation) + " - beginner - AF.dat"
        with open(filename, 'a') as file:
            file.write(capture_function_output(print_common_data))
            file.write("\n// User preferences combination: beginner - AF")
            file.write(capture_function_output(print_user_preferences))

        ############################################################################
        ############################################################################

        # Generation solo 1 - AF - intermediate
        user_preferences("intermediate", "AF")
        ########### GENERATE .dat FILE ###########
        filename = "Lead part " + str(time_of_generation) + " - intermediate - AF.dat"
        with open(filename, 'a') as file:
            file.write(capture_function_output(print_common_data))
            file.write("\n// User preferences combination: intermediate - AF")
            file.write(capture_function_output(print_user_preferences))

        ############################################################################
        ############################################################################

        # Generation solo 1 - AF - advanced
        user_preferences("advanced", "AF")
        ########### GENERATE .dat FILE ###########
        filename = "Lead part " + str(time_of_generation) + " - advanced - AF.dat"
        with open(filename, 'a') as file:
            file.write(capture_function_output(print_common_data))
            file.write("\n// User preferences combination: advanced - AF")
            file.write(capture_function_output(print_user_preferences))


        ############################################################################
        ############################################################################

        # Generation solo 1 - AS - beginner
        user_preferences("beginner", "As")
        ########### GENERATE .dat FILE ###########
        filename = "Lead part " + str(time_of_generation) + " - beginner - AS.dat"
        with open(filename, 'a') as file:
            file.write(capture_function_output(print_common_data))
            file.write("\n// User preferences combination: beginner - AS")
            file.write(capture_function_output(print_user_preferences))

        ############################################################################
        ############################################################################

        # Generation solo 1 - AS - intermediate
        user_preferences("intermediate", "AS")
        ########### GENERATE .dat FILE ###########
        filename = "Lead part " + str(time_of_generation) + " - intermediate - AS.dat"
        with open(filename, 'a') as file:
            file.write(capture_function_output(print_common_data))
            file.write("\n// User preferences combination: intermediate - AS")
            file.write(capture_function_output(print_user_preferences))

        ############################################################################
        ############################################################################

        # Generation solo 1 - AS - advanced
        user_preferences("advanced", "AS")
        ########### GENERATE .dat FILE ###########
        filename = "Lead part " + str(time_of_generation) + " - advanced - AS.dat"
        with open(filename, 'a') as file:
            file.write(capture_function_output(print_common_data))
            file.write("\n// User preferences combination: advanced - AS")
            file.write(capture_function_output(print_user_preferences))

    time.sleep(1)


batch_generation(number_of_solos)
