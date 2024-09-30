import os


def import_midi():
    global roll_midi_path

    roll_midi_path = input("Please insert the MIDI file path: ")

    def path_check(path):
        if os.path.exists(path):
            accept_ext = [".mid", ".midi", ".kar"]
            global split_path
            split_path = os.path.splitext(path)
            if split_path[1] not in accept_ext:
                print("Invalid file format. Please insert the path to a standard MIDI file: ")
                return False
            else:
                return True
        else:
            print("Invalid path. Please insert a valid path to a standard MIDI file: ")
            return False

    while not path_check(roll_midi_path):
        roll_midi_path = input()

    print("Valid path.")