import midi_import
import df_creation
import expressiveness_search

print("Welcome to the Player Piano Rolls Expressiveness Finder!")
activity_check = True
while activity_check == True:
    midi_import.import_midi() # select MIDI file path
    df_creation.df_create() # creates MIDO object and python dataframe (list of lists)
    expressiveness_search.expressiveness_search() # searches the df to find expressive
    stop_flag = False
    while not stop_flag:
        search_again = input("Do you want to perform again the search, changing some parameters? Type Y or N")
        if search_again == "Y":
            expressiveness_search.expressiveness_search()
        else:
            print("Well done!")
            stop_flag = True
    continue_check = input("Do you want to process another MIDI file? Type Y or N")
    if continue_check == "N":
        activity_check = False
        print("Fine, goodbye!")

