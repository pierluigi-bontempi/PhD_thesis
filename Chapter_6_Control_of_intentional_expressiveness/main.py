import gui
import MidiFile_parser
import CPLEX_data_generator
import CPLEX_fingering_generator
import add_techniques
import predict_deviations
import df_update_with_predictions_and_user_prefs
import updated_MidiFile_generation

# Launch the GUI
gui.open_gui()
print("gui loaded")

# Parse the MidiFile
MidiFile_parser.midifile_df_create()
print("MidiFile parsed")

# Generate data for CPLEX
CPLEX_data_generator.CPLEX_generator()
print("CPLEX .dat file created")
print("Please wait, depending on the complexity of the MidiFile CPLEX may need some time (up to 10 minutes) to generate the automatic fingering")

# Generate fingering
CPLEX_fingering_generator.solve_with_cplex()
print("CPLEX fingering generated")

# Add articulations and expressive techniques
add_techniques.add_techniques()
print("Articulations and expressive techniques added")

# Predict timing and velocity deviations
predict_deviations.predict_deviations()
print("Timing and velocity deviations predicted")

# Update the df with deviations and user preferences
df_update_with_predictions_and_user_prefs.df_update()
print("df updated with deviations and user preferences")

# Generate new MidiFile
updated_MidiFile_generation.generate_updt_MidiFile()
print("Expressive MidiFile generated!")