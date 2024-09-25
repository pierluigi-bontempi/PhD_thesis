import MidiFile_parser

def CPLEX_generator():
    inst = open('code_import/instrument_settings.txt', 'r')
    instrument_settings = inst.read()

    notes_list_pd_df = MidiFile_parser.notes_list_pd_df
    number_of_notes = len(notes_list_pd_df.index)
    notes_list = notes_list_pd_df['note_name'].values.tolist()
    notes_list_string = ",".join(str(element) for element in notes_list)

    available_time_list = notes_list_pd_df['IOI_ms'].values.tolist()
    available_time_list[0] = 1000
    available_time_list_string = ",".join(str(element) for element in available_time_list)

    opt = open('code_import/optimization_settings.txt', 'r')
    optimization_settings = opt.read()

    with open("CPLEX_data_file.dat", "w") as f:
        f.write(instrument_settings)
        f.write(f"\n\n//---------------------------melody\n\n\
m = {number_of_notes};\n\n\
note = [{notes_list_string}];\n\n\
availableTime = [{available_time_list_string}];\n")
        f.write(optimization_settings)