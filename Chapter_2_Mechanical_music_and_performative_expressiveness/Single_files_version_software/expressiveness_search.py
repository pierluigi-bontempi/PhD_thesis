import df_creation

def expressiveness_search():
    sensitivity = int(input("Please type an integer number to se the sensitivity of the detection (the higher "
                            "the number, the lower the sensitivity). If you do not know what to insert, try with "
                            "80 >>> "))
    range_exp_search = int(input("Please type an integer number corresponding to the search range"))
    pd_df_notes_list_cleaned = df_creation.pd_df_notes_list_cleaned
    tempo = df_creation.tempo
    ticks_per_beat = df_creation.ticks_per_beat
    np_norm_distance_score = pd_df_notes_list_cleaned["norm_distance_score"].to_numpy()
    flag_expressiveness = []
    for n in range(range_exp_search):
        flag_expressiveness.append(False)
    for i in range(range_exp_search, len(np_norm_distance_score)):
        total_distance_score = 0
        for g in range(range_exp_search):
            total_distance_score += np_norm_distance_score[i - g]
        # print(total_distance_score)
        if total_distance_score > sensitivity:
            flag_expressiveness.append(True)
        else:
            flag_expressiveness.append(False)
    # print(flag_expressiveness)
    pd_df_notes_list_cleaned['expressiveness_check'] = flag_expressiveness
    # print(pd_df_notes_list_cleaned.tail(50))

    array_exp_areas_IDs = []
    exp_section_open = False
    for i in range(1, len(flag_expressiveness)):
        if flag_expressiveness[i] == False and exp_section_open == False:
            pass
        elif flag_expressiveness[i] == False and exp_section_open == True:
            array_exp_areas_IDs[-1].append(i-1)
            exp_section_open = False
        elif flag_expressiveness[i] == True and exp_section_open == True:
            pass
        elif flag_expressiveness[i] == True and exp_section_open == False:
            array_exp_areas_IDs.append([i-range_exp_search])
            exp_section_open = True

    # print(array_exp_areas_IDs)

    if not array_exp_areas_IDs:
        print("No expressive area detected")

    for n in range(len(array_exp_areas_IDs)):
        const = tempo / ticks_per_beat / 1000000
        start = pd_df_notes_list_cleaned.iloc[array_exp_areas_IDs[n][0]]['tDtNoteOn']
        try:
            array_exp_areas_IDs[n][1]
        except:
            array_exp_areas_IDs[n].append(len(flag_expressiveness))
            end = pd_df_notes_list_cleaned.iloc[array_exp_areas_IDs[n][1]-1]['tDtNoteOn']
        else:
            end = pd_df_notes_list_cleaned.iloc[array_exp_areas_IDs[n][1]]['tDtNoteOn']
        print("Potential expressive area from " + str(int(start * const // 60)) + " minutes and " + str(round((start * const % 60),1)) + " seconds to " + str(int(end * const // 60)) + " minutes and " + str(round((end * const % 60),1)) + " seconds")