# An innovative computer-based model for the generation of expressive lead guitar performances (PhD Thesis, by Pierluigi Bontempi (Centro di Sonologia Computazionale, Department of Information Engineering, University of Padua) 

## Description 

The materials in this folder pertain to Chapter 6 of the PhD thesis, titled "Control of intentional expressiveness." 

A brief description of the role of the Python files is listed below:

- main.py
This is the core of the software. All other files are imported here, and their respective functions are executed from this point in the predefined order.

- gui.py
This is responsible for the graphical interface, developed using Python’s native library Tkinter. It requires loading the quantized MIDI File, which is to be rendered expressively, and input of data related to the scale, root, and user preferences for loudness and positioning of the onsets relative to the beat.

- MidiFile_parser.py
This parses the input MIDI File, extracting relevant data for generating its expressive version (e.g., notes’ onsets and offsets delta time, MIDI note number, etc.). It then generates a Pandas dataframe containing this information.

- CPLEX_data_generator.py
Based on the dataframe generated in the previous step, this creates a .dat file containing the instructions for the subsequent automatic fingering generation, correctly encoded for the CPLEX model.

- CPLEX_fingering_generator.py
This uses the CPLEX Python API to provide the solver with the two necessary files: CPLEX_data_file.dat (generated in the previous step) and CPLEX_model.mod (the mathematical model in OPL, which also includes a JavaScript section for exporting the results
in CSV format).

- add_techiques.py
This merges the data generated in the previous step with the dataframe created by MidiFile_parser.py. It then automatically inserts articulations and expressive techniques (based on the MySongBook stats), creating and populating the corresponding dataframe columns.

- predict_deviations.py
This calculates the unintended deviations in timing and velocity based on the dataframe generated in the previous steps, using the offline versions of the previously trained predictive models (Random Forest and RNN with 4 time steps). For the first note, values that cannot be derived from earlier steps but are necessary for subsequent predictions are generated randomly. In the case of the parameters prec_rest_ms and velocity, since the predictive models require data for the first 4 notes to start making predictions, these values are calculated based on the PC and SC (for prec_rest_ms) or randomly within a range of 80-100 (for velocity).

- df_update_with_predictions_and_user_prefs.py
This modifies the dataframe created in the previous steps by calculating and applying intentional deviations in timing and loudness, based on the user preferences provided earlier. Data validity checks are also performed, with interventions made if
necessary (for example, setting the delta time of the onset of the first note to 0 if it results to be less than 0, preventing the predicted value of prec_rest_ms from completely removing the previous note if it exceeds its duration, and avoiding note overlap: the delta time between the note-off of one note and the note-on of the next is constrained to be ≥ 0).

- updated_MidiFile_generation.py
Based on the updated dataframe and the data previously extracted from the input MIDI File, this generates a new MIDI File that includes the expressive timing and velocity-related modifications, and the information related to fingering, articulations, and expressive techniques in the form of MIDI Control Change messages.

## Table of Contents 

- Dependencies 
- License 
- Contact 

## Dependencies 

To run these notebooks, the following Python packages are required: 

- mido 1.3.0 
- pandas 2.0.3 
- numpy 1.24.3 
- CPLEX 22.1.1.2
- docplex 2.28.240
- joblib 1.2.0 

## License 

This project is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0). You are free to use, share, and adapt the material as long as appropriate credit is given. For more details, see the LICENSE file or visit the Creative Commons website (https://creativecommons.org/licenses/by/4.0/). 

## Contact 

For any questions or inquiries, please contact: Pierluigi Bontempi - pierluigi.bontempi@phd.unipd.it

