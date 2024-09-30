import midi_import
import df_creation
import expressiveness_search
import os

print("Welcome to the Player Piano Rolls Expressiveness Finder - batch version!")

folder_path = input("Please type the path of the MIDI files folder (with final \): ")
try:
    os.path.exists(folder_path)
except:
    print("Invalid path. Please type a valid path: ")
    folder_path = input()
else:
    pass
files_list = os.listdir(folder_path)
# print(files_list)

for midi_file in files_list:
    if os.path.splitext(midi_file)[1] == ".mid":
        midi_file_path = (folder_path + midi_file)
        print("\n____________________________________________________________________________")
        print("____________________________________________________________________________\n")
        midi_import.import_midi(midi_file_path)  # select MIDI file path
        if df_creation.df_create() == "quit": # creates MIDO object and python dataframe (list of lists)
            print(os.path.splitext(midi_file)[0])
            print(df_creation.return_message)
        else:
            print(os.path.splitext(midi_file)[0])
            expressiveness_search.expressiveness_search()  # searches the df to find expressive

print("\n\nThat's all, thanks for using this software!")