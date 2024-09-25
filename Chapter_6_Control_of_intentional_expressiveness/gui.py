import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinter import PhotoImage

midifile_path = None
selected_root = None
selected_scale = None
loudness = None
positioning_to_the_beat = None
slider_positioning = None

def open_gui():
    global midifile_path, selected_root, selected_scale, loudness, positioning_to_the_beat, slider_positioning

    # Select the MIDI file
    def select_midi_file():
        global midifile_path
        midifile_path = filedialog.askopenfilename(
            title="Select MIDI file",
            filetypes=[("MIDI/KAR files", "*.mid *.midi *.kar")]
        )
        if midifile_path:
            if not midifile_path.lower().endswith(('.mid', '.midi', '.kar')):
                messagebox.showerror("Invalid file", "Please select a valid MIDI (.mid, .midi) or Karaoke (.kar) file.")
                midifile_path = None
            else:
                print(f"Selected file: {midifile_path}")
        else:
            print("No file selected")

    # Slider settings

    def set_positioning(value):
        positioning_to_the_beat.set(value)
        slider_positioning.set(0)

    def set_slider_positioning(value):
        positioning_to_the_beat.set(value)
        pressing_checkbox.deselect()
        precise_checkbox.deselect()
        relaxed_checkbox.deselect()

    # Collect data/confirmation
    def get_expressive():
        global selected_root, selected_scale, loudness, positioning_to_the_beat, slider_positioning

        # Check if MIDI File/Root/Scale fields are filled
        if midifile_path is None:
            messagebox.showerror("Error", "Please select a valid MIDI or KAR file.")
            return
        if not root_menu.get():
            messagebox.showerror("Error", "Please select a musical root.")
            return
        if not scale_menu.get():
            messagebox.showerror("Error", "Please select a scale.")
            return

        # Convert Tkinter variables to standard Python variables
        selected_root = root_menu.get()
        selected_scale = scale_menu.get()
        loudness = loudness_slider.get() - 1
        positioning_to_the_beat = positioning_to_the_beat.get()
        slider_positioning = slider_positioning.get()

        messagebox.showinfo(
            "Got it!",
            "Got it, You will find the expressive MIDI File in the same folder as the initial one."
        )
        root.destroy()

    # Create the main window
    root = tk.Tk()
    root.title("Expressive MIDI Generator")
    root.geometry("420x800")

    # Background image
    try:
        background_img = PhotoImage(file="images/background.png")
        background_label = tk.Label(root, image=background_img)
        background_label.place(relwidth=1, relheight=1)
    except Exception as e:
        print(f"Error loading background image: {e}")
        root.configure(bg='#f0f0f0')

    # Variables to store selections
    selected_root_var = tk.StringVar()
    selected_scale_var = tk.StringVar()
    loudness_var = tk.IntVar()
    positioning_to_the_beat = tk.IntVar()
    slider_positioning = tk.IntVar()

    # Comboboxes transparent
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TCombobox', fieldbackground='#f0f0f0', background='#f0f0f0')

    # MIDI file selection
    select_button = tk.Button(root, text="Select MIDI File", command=select_midi_file, font=("Arial", 12), bg="#ff6c00", fg="white")
    select_button.place(relx=0.5, y=150  + 30, anchor='center', width=200, height=30)

    # Root and Scale
    root_label = tk.Label(root, text="Root:", font=("Arial", 10, "bold"), bg='#f0f0f0')
    root_label.place(relx=0.5, y=200  + 30, anchor='center')
    root_menu = ttk.Combobox(root, textvariable=selected_root_var, values=["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"], style='TCombobox')
    root_menu.place(relx=0.5, y=230  + 30, anchor='center', width=150)

    scale_label = tk.Label(root, text="Scale:", font=("Arial", 10, "bold"), bg='#f0f0f0')
    scale_label.place(relx=0.5, y=270  + 30, anchor='center')
    scale_menu = ttk.Combobox(root, textvariable=selected_scale_var, values=["Major", "Minor", "Major Pentatonic", "Minor Pentatonic", "Blues", "Chromatic"], style='TCombobox')
    scale_menu.place(relx=0.5, y=300  + 30, anchor='center', width=150)

    # Loudness
    loudness_label = tk.Label(root, text="Loudness:", font=("Arial", 10, "bold"), bg='#f0f0f0')
    loudness_label.place(relx=0.5, y=340  + 30, anchor='center')
    loudness_slider = tk.Scale(root, from_=1, to=5, orient=tk.HORIZONTAL, variable=loudness_var, bg='#f0f0f0')
    loudness_slider.set(1)
    loudness_slider.place(relx=0.5, y=370  + 30, anchor='center', width=150)

    # Positioning with respect to the beat
    positioning_label = tk.Label(root, text="Positioning with respect to the beat:", font=("Arial", 10, "bold"), bg='#f0f0f0')
    positioning_label.place(relx=0.5, y=420  + 30, anchor='center')

    pressing_checkbox = tk.Radiobutton(root, text="Pressing", value=-10, variable=positioning_to_the_beat, command=lambda: set_positioning(-10), bg='#f0f0f0')  # Match the background color
    pressing_checkbox.place(relx=0.3, y=450  + 30, anchor='center')
    precise_checkbox = tk.Radiobutton(root, text="Precise", value=0, variable=positioning_to_the_beat, command=lambda: set_positioning(0), bg='#f0f0f0')  # Match the background color
    precise_checkbox.place(relx=0.5, y=450  + 30, anchor='center')
    relaxed_checkbox = tk.Radiobutton(root, text="Relaxed", value=10, variable=positioning_to_the_beat, command=lambda: set_positioning(10), bg='#f0f0f0')  # Match the background color
    relaxed_checkbox.place(relx=0.7, y=450  + 30, anchor='center')

    # Advanced slider for positioning
    expert_label = tk.Label(root, text="I'm an expert, I choose my time deviations!\n(the average deviation from the incoming MIDI melody, in ms) \nDanger, don't touch if you don't know what you are doing ;-)", font=("Arial", 10, "italic"), bg='#f0f0f0')  # Match the background color
    expert_label.place(relx=0.5, y=490  + 30, anchor='center')
    expert_slider = tk.Scale(root, from_=-15, to=15, orient=tk.HORIZONTAL, variable=slider_positioning, bg='#f0f0f0')  # Match the background color
    expert_slider.place(relx=0.5, y=540  + 30, anchor='center', width=300)

    # Final button
    get_expressive_button = tk.Button(root, text="Get expressive!", command=get_expressive, font=("Arial", 12), bg="#ff6c00", fg="white")
    get_expressive_button.place(relx=0.5, y=600  + 30, anchor='center', width=200, height=30)

    root.mainloop()